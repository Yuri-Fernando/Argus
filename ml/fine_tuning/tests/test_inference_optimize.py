"""Testes reais de otimização de inferência — carregam o modelo-base
(~1GB), treinam um adapter LoRA mínimo, depois fundem/quantizam e medem
latência de verdade. Mesma convenção de `test_lora_finetune.py`: só rodam
com `RUN_FINETUNE=1`.

    RUN_FINETUNE=1 pytest ml/fine_tuning/tests -q -m finetune
"""
from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.finetune

TINY_EXAMPLES = [
    {"prompt": "Cliente com churn_score 0.9. O que fazer?",
     "completion": "Risco alto: contato humano prioritário."},
    {"prompt": "O que é churn_score?",
     "completion": "É a probabilidade estimada de o cliente cancelar o serviço."},
]


def _require_env():
    if os.getenv("RUN_FINETUNE") != "1":
        pytest.skip("RUN_FINETUNE != 1 (baixa ~1GB e treina de verdade — rode explicitamente)")


@pytest.fixture(scope="module")
def trained_adapter(tmp_path_factory):
    _require_env()
    from ml.fine_tuning.lora_finetune import run_finetune

    out_dir = tmp_path_factory.mktemp("inference-opt") / "adapter"
    run_finetune(out_dir, load_in_4bit=False, epochs=1, examples=TINY_EXAMPLES)
    return out_dir


def test_merge_adapter_produces_dense_model_with_no_peft_wrapper(trained_adapter):
    from peft import PeftModel

    from ml.fine_tuning.inference_optimize import merge_adapter

    merged = merge_adapter(str(trained_adapter))

    # merge_and_unload devolve o modelo-base "puro": não é mais um PeftModel
    assert not isinstance(merged, PeftModel)
    assert not hasattr(merged, "peft_config")


def test_quantize_dynamic_int8_shrinks_linear_layers_and_still_generates(trained_adapter):
    from ml.fine_tuning.inference_optimize import (
        benchmark,
        merge_adapter,
        model_size_mb,
        quantize_dynamic_int8,
    )
    from ml.fine_tuning.model import load_tokenizer

    merged = merge_adapter(str(trained_adapter))
    fp_size = model_size_mb(merged)

    quantized = quantize_dynamic_int8(merged)

    # ao menos uma camada Linear virou dynamic-quantized
    quantized_linear_found = any(
        "DynamicQuantizedLinear" in type(m).__name__ or "quantized" in type(m).__module__
        for m in quantized.modules()
    )
    assert quantized_linear_found

    quant_size = model_size_mb(quantized)
    assert quant_size < fp_size  # INT8 pesa menos que fp32/fp16

    # regressão real: se o modelo veio da GPU em bfloat16, um forward pass
    # sem o cast para float32 falha em runtime ("data type of input should
    # be float") — só checar tamanho/tipo do módulo não pegava isso.
    tokenizer = load_tokenizer()
    result = benchmark(quantized, tokenizer, max_new_tokens=8, warmup=0, runs=1)
    assert result["tokens_generated"] > 0


def test_benchmark_generates_real_tokens_and_reports_latency(trained_adapter):
    from ml.fine_tuning.inference_optimize import benchmark
    from ml.fine_tuning.model import load_tokenizer

    tokenizer = load_tokenizer()
    from ml.fine_tuning.inference_optimize import merge_adapter

    merged = merge_adapter(str(trained_adapter))
    result = benchmark(merged, tokenizer, max_new_tokens=8, warmup=1, runs=1)

    assert result["tokens_generated"] > 0
    assert result["avg_latency_s"] > 0
    assert result["model_size_mb"] > 0
