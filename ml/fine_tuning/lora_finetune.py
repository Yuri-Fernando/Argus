"""Fine-tuning com LoRA (Low-Rank Adaptation, Hu et al. 2021).

Em vez de atualizar todos os pesos do modelo, LoRA congela o modelo-base e
treina apenas um par de matrizes de baixo posto (`A`, `B`) injetadas nas
projeções de atenção — reduz drasticamente o número de parâmetros
treináveis (tipicamente <1% do total) e o footprint de memória, sem tocar
nos pesos originais (o adapter pode ser trocado/removido a qualquer momento).

QLoRA (`qlora_finetune.py`) é este mesmo mecanismo aplicado sobre um
modelo-base carregado em 4 bits (`model.load_base_model(load_in_4bit=True)`)
— por isso o loop de treino é compartilhado aqui (`run_finetune`) e
parametrizado por `load_in_4bit`.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from torch.optim import AdamW

from ml.fine_tuning.dataset import TRAIN_EXAMPLES, to_chat_messages
from ml.fine_tuning.model import LORA_TARGET_MODULES, MODEL_NAME, load_base_model, load_tokenizer

DEFAULT_OUTPUT_DIR = Path(__file__).parent / "adapters" / "lora-retention-assistant"


def build_lora_config(r: int = 8, alpha: int = 16, dropout: float = 0.05) -> LoraConfig:
    return LoraConfig(
        r=r,
        lora_alpha=alpha,
        lora_dropout=dropout,
        target_modules=LORA_TARGET_MODULES,
        bias="none",
        task_type="CAUSAL_LM",
    )


def _tokenize_examples(tokenizer, examples: list[dict], max_length: int = 256):
    """Tokeniza cada exemplo via chat template do próprio modelo, mascarando
    a loss no prompt (só o `assistant` conta para o gradiente)."""
    batches = []
    for ex in examples:
        messages = to_chat_messages(ex)
        full_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        prompt_only = tokenizer.apply_chat_template(messages[:-1], tokenize=False, add_generation_prompt=True)

        full_ids = tokenizer(full_text, truncation=True, max_length=max_length, return_tensors="pt")
        prompt_ids = tokenizer(prompt_only, truncation=True, max_length=max_length, return_tensors="pt")

        input_ids = full_ids["input_ids"]
        labels = input_ids.clone()
        prompt_len = prompt_ids["input_ids"].shape[1]
        labels[:, :prompt_len] = -100  # ignora o prompt na loss

        batches.append({
            "input_ids": input_ids,
            "attention_mask": full_ids["attention_mask"],
            "labels": labels,
        })
    return batches


def run_finetune(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    load_in_4bit: bool = False,
    epochs: int = 3,
    lr: float = 2e-4,
    model_name: str = MODEL_NAME,
    examples: list[dict] | None = None,
    log_every: int = 4,
) -> dict:
    """Roda o fine-tuning LoRA (ou QLoRA, se `load_in_4bit=True`) de ponta a
    ponta e salva o adapter em `output_dir`. Retorna um dict com a curva de
    loss — usado pelos testes e pelo notebook para provar convergência real."""
    examples = examples if examples is not None else TRAIN_EXAMPLES
    tokenizer = load_tokenizer(model_name)
    model = load_base_model(model_name, load_in_4bit=load_in_4bit)

    if load_in_4bit:
        model = prepare_model_for_kbit_training(model)

    model = get_peft_model(model, build_lora_config())
    trainable, total = model.get_nb_trainable_parameters()
    model.train()

    batches = _tokenize_examples(tokenizer, examples)
    device = next(model.parameters()).device
    optimizer = AdamW([p for p in model.parameters() if p.requires_grad], lr=lr)

    losses: list[float] = []
    t0 = time.time()
    step = 0
    for _epoch in range(epochs):
        for batch in batches:
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**batch)
            loss = outputs.loss

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            losses.append(float(loss.item()))
            step += 1
            if step % log_every == 0:
                print(f"step {step:03d} | loss {loss.item():.4f}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    return {
        "output_dir": str(output_dir),
        "trainable_params": trainable,
        "total_params": total,
        "trainable_pct": round(100 * trainable / total, 4),
        "losses": losses,
        "first_loss": losses[0],
        "last_loss": losses[-1],
        "seconds": round(time.time() - t0, 1),
        "quantized_4bit": load_in_4bit,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--qlora", action="store_true", help="carrega o modelo-base em 4-bit (QLoRA)")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_DIR))
    args = ap.parse_args()

    result = run_finetune(Path(args.output), load_in_4bit=args.qlora, epochs=args.epochs)
    print(f"\nparâmetros treináveis: {result['trainable_params']:,} / {result['total_params']:,} "
          f"({result['trainable_pct']}%)")
    print(f"loss: {result['first_loss']:.4f} -> {result['last_loss']:.4f} em {result['seconds']}s")
    print(f"adapter salvo em: {result['output_dir']}")


if __name__ == "__main__":
    main()
