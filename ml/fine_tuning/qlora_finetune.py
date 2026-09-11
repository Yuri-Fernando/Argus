"""QLoRA — LoRA sobre um modelo-base quantizado em 4 bits (Dettmers et al.,
2023). Mesmo mecanismo de `lora_finetune.py`; a diferença é só
`load_in_4bit=True` em `model.load_base_model`, que troca os pesos do
modelo-base por sua versão NF4 (bitsandbytes) antes de injetar os adapters
LoRA — o footprint de memória do modelo-base cai ~4x, então cabe treinar
modelos maiores na mesma GPU.

Uso:
    python -m ml.fine_tuning.qlora_finetune
"""
from __future__ import annotations

import argparse
from pathlib import Path

from ml.fine_tuning.lora_finetune import DEFAULT_OUTPUT_DIR, run_finetune
from ml.fine_tuning.model import MODEL_NAME

QLORA_OUTPUT_DIR = DEFAULT_OUTPUT_DIR.parent / "qlora-retention-assistant"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--output", type=str, default=str(QLORA_OUTPUT_DIR))
    args = ap.parse_args()

    result = run_finetune(Path(args.output), load_in_4bit=True, epochs=args.epochs, model_name=MODEL_NAME)
    print(f"\n[QLoRA] parâmetros treináveis: {result['trainable_params']:,} / "
          f"{result['total_params']:,} ({result['trainable_pct']}%)")
    print(f"loss: {result['first_loss']:.4f} -> {result['last_loss']:.4f} em {result['seconds']}s")
    print(f"adapter salvo em: {result['output_dir']}")


if __name__ == "__main__":
    main()
