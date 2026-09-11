"""Carregamento do modelo-base para fine-tuning.

`Qwen2.5-0.5B-Instruct` (Apache-2.0, Qwen Team): pequeno o suficiente para
treinar em GPU de consumo (ou até CPU, mais devagar) em minutos, grande o
suficiente para produzir respostas coerentes — adequado para demonstrar o
mecanismo de LoRA/QLoRA de ponta a ponta sem exigir um cluster de GPUs.

Para uso em produção, o mesmo pipeline (`lora_finetune.py` /
`qlora_finetune.py`) serve para um modelo maior (ex.: Qwen2.5-7B-Instruct,
Llama-3.1-8B-Instruct) apenas trocando `MODEL_NAME` — a única mudança
adicional necessária seria mais VRAM/tempo de treino.
"""
from __future__ import annotations

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

# Módulos-alvo do LoRA: as projeções de atenção. Presentes na maioria das
# arquiteturas Llama-like (Qwen2, Llama, Mistral) — mesma escolha funciona
# ao trocar de modelo-base.
LORA_TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj"]


def load_tokenizer(model_name: str = MODEL_NAME):
    tok = AutoTokenizer.from_pretrained(model_name)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    return tok


def load_base_model(
    model_name: str = MODEL_NAME,
    load_in_4bit: bool = False,
    device_map: str | dict = "auto",
):
    """Carrega o modelo-base. `load_in_4bit=True` ativa a quantização NF4
    (bitsandbytes) usada no QLoRA — mesmo modelo, footprint de memória
    ~4x menor, permitindo fine-tuning em GPUs menores."""
    if load_in_4bit:
        from transformers import BitsAndBytesConfig

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_name, quantization_config=bnb_config, device_map=device_map,
        )
    else:
        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        model = AutoModelForCausalLM.from_pretrained(
            model_name, dtype=dtype, device_map=device_map,
        )
    return model
