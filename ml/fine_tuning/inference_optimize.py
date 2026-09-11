"""Otimização de inferência de modelos open-source.

Duas técnicas, aplicadas sobre o modelo que este projeto já fine-tunou
(`ml/fine_tuning/`), não sobre um modelo novo só para demonstração:

1. **Merge do adapter LoRA nos pesos base** (`merge_adapter`): o adapter
   LoRA, enquanto não fundido, adiciona um produto de matrizes extra a cada
   forward pass (`x @ A @ B`). `PeftModel.merge_and_unload()` soma esse
   produto direto nos pesos originais — o resultado é um modelo denso comum,
   sem overhead de adapter, pronto para servir/exportar como qualquer
   checkpoint padrão.
2. **Quantização dinâmica INT8** (`quantize_dynamic_int8`): reduz o
   footprint em memória das camadas lineares e acelera inferência em CPU —
   `torch.quantization` é stdlib do PyTorch, sem dependência extra além do
   que `ml/fine_tuning/` já usa.

Relação com o backlog do LLM Gateway: `agents/llm_gateway/README.md` §
"LLM optimization: quantization and fine-tuning as a cost lever" descreve
esse item para `dq_category_classification` e conclui, corretamente
(`agents/quality/root_cause_classifier.py`), que uma transformer
quantizada seria desproporcional para aquela tarefa de 10 classes — por
isso aquele módulo usa TF-IDF + Logistic Regression, não isto. Este módulo
é a demonstração de otimização de inferência de LLM onde ela é
proporcional: sobre um modelo generativo real (`ml/fine_tuning/`), não
bolted on para um classificador que não precisava disso.
"""
from __future__ import annotations

import time

import torch
from peft import PeftModel

from ml.fine_tuning.dataset import EVAL_PROMPTS, SYSTEM_PROMPT
from ml.fine_tuning.model import MODEL_NAME, load_base_model, load_tokenizer


def merge_adapter(adapter_dir: str, model_name: str = MODEL_NAME):
    """Carrega o modelo-base + adapter e funde os dois num único checkpoint
    denso (`merge_and_unload`)."""
    base = load_base_model(model_name)
    tuned = PeftModel.from_pretrained(base, adapter_dir)
    merged = tuned.merge_and_unload()
    merged.eval()
    return merged


def quantize_dynamic_int8(model):
    """Quantização dinâmica INT8 das camadas `nn.Linear` — CPU apenas (é a
    limitação real do backend `qnnpack`/`fbgemm` do PyTorch, não uma
    simplificação nossa). O kernel dinâmico exige ativações em float32 —
    se o modelo veio da GPU em bfloat16 (`load_base_model`), o `.float()`
    é obrigatório, não cosmético: sem ele o forward falha com
    "data type of input should be float"."""
    cpu_model = model.to("cpu").float()
    return torch.quantization.quantize_dynamic(cpu_model, {torch.nn.Linear}, dtype=torch.qint8)


def model_size_mb(model) -> float:
    total_bytes = sum(p.numel() * p.element_size() for p in model.parameters())
    total_bytes += sum(b.numel() * b.element_size() for b in model.buffers())
    return round(total_bytes / (1024 * 1024), 2)


@torch.no_grad()
def benchmark(model, tokenizer, prompt: str | None = None, max_new_tokens: int = 40,
              warmup: int = 1, runs: int = 3) -> dict:
    """Latência real de geração — não estimada. `warmup` descarta a
    primeira chamada (compilação/cache de kernel); `runs` faz a média."""
    prompt = prompt or EVAL_PROMPTS[0]
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    device = next(model.parameters()).device
    inputs = tokenizer(text, return_tensors="pt").to(device)

    gen_kwargs = dict(max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=tokenizer.pad_token_id)

    for _ in range(warmup):
        model.generate(**inputs, **gen_kwargs)

    times, n_new = [], 0
    for _ in range(runs):
        t0 = time.perf_counter()
        out = model.generate(**inputs, **gen_kwargs)
        times.append(time.perf_counter() - t0)
        n_new = out.shape[1] - inputs["input_ids"].shape[1]

    avg_time = sum(times) / len(times)
    return {
        "device": str(device),
        "avg_latency_s": round(avg_time, 4),
        "tokens_generated": int(n_new),
        "tokens_per_sec": round(n_new / avg_time, 2) if avg_time > 0 else None,
        "model_size_mb": model_size_mb(model),
    }


def compare_optimizations(adapter_dir: str, model_name: str = MODEL_NAME) -> dict:
    """Compara três variantes do mesmo modelo fine-tunado:

    - `adapter_unmerged`: modelo-base + adapter LoRA separado (overhead de
      adapter a cada forward pass), na GPU se disponível.
    - `merged_fp`: adapter fundido nos pesos, mesma precisão, mesmo device.
    - `merged_int8_cpu`: fundido + quantizado dinamicamente para CPU.
    """
    tokenizer = load_tokenizer(model_name)
    results: dict[str, dict] = {}

    base = load_base_model(model_name)
    tuned = PeftModel.from_pretrained(base, adapter_dir)
    tuned.eval()
    results["adapter_unmerged"] = benchmark(tuned, tokenizer)

    merged = merge_adapter(adapter_dir, model_name)
    results["merged_fp"] = benchmark(merged, tokenizer)

    quantized = quantize_dynamic_int8(merged)
    results["merged_int8_cpu"] = benchmark(quantized, tokenizer)

    return results


def main() -> None:
    import argparse
    import json

    from ml.fine_tuning.lora_finetune import DEFAULT_OUTPUT_DIR

    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", type=str, default=str(DEFAULT_OUTPUT_DIR))
    args = ap.parse_args()

    results = compare_optimizations(args.adapter)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
