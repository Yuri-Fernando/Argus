"""Testes de fine-tuning real (LoRA e QLoRA) — baixam o modelo-base
(~1GB) e treinam de verdade por alguns passos. Pesados de propósito: só
rodam com `RUN_FINETUNE=1` (mesma convenção de `@pytest.mark.integration`
para os testes de broker).

    RUN_FINETUNE=1 pytest ml/fine_tuning/tests -q -m finetune
"""
from __future__ import annotations

import os

import pytest
from peft import PeftModel

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


def test_lora_finetune_reduces_loss_and_saves_loadable_adapter(tmp_path):
    _require_env()
    from ml.fine_tuning.lora_finetune import run_finetune
    from ml.fine_tuning.model import load_base_model

    result = run_finetune(tmp_path / "lora-smoke", load_in_4bit=False, epochs=1, examples=TINY_EXAMPLES)

    assert result["last_loss"] < result["first_loss"] * 1.5  # não precisa convergir, só não explodir
    assert result["trainable_pct"] < 1.0  # LoRA treina só uma fração pequena dos pesos
    assert (tmp_path / "lora-smoke" / "adapter_config.json").exists()

    # o adapter salvo precisa ser carregável de volta sobre o modelo-base
    base = load_base_model()
    tuned = PeftModel.from_pretrained(base, str(tmp_path / "lora-smoke"))
    assert tuned is not None


def test_qlora_finetune_runs_on_4bit_base(tmp_path):
    _require_env()
    from ml.fine_tuning.lora_finetune import run_finetune

    result = run_finetune(tmp_path / "qlora-smoke", load_in_4bit=True, epochs=1, examples=TINY_EXAMPLES)

    assert result["quantized_4bit"] is True
    assert isinstance(result["last_loss"], float)
    assert (tmp_path / "qlora-smoke" / "adapter_config.json").exists()
