"""Fine-Tuning / LoRA / QLoRA — adapta um LLM open-source (Qwen2.5-0.5B-
Instruct) ao domínio de Customer Intelligence do Argus (assistente de
retenção), sem tocar nos pesos originais do modelo-base.

- `lora_finetune.py` — LoRA (Hu et al., 2021): treina adapters de baixo
  posto sobre o modelo-base em precisão nativa.
- `qlora_finetune.py` — QLoRA (Dettmers et al., 2023): mesmo mecanismo
  sobre o modelo-base quantizado em 4 bits (NF4), reduzindo o footprint de
  memória em ~4x.
- `evaluate.py` — compara gerações do modelo base vs. base+adapter em
  prompts held-out.
"""
from __future__ import annotations
