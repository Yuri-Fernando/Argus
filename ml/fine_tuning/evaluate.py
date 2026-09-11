"""Avalia o efeito do fine-tuning: gera respostas do modelo-base puro e do
modelo-base + adapter LoRA/QLoRA para os mesmos prompts (held-out, fora do
treino) e reporta a loss média em cada um.

Uso:
    python -m ml.fine_tuning.evaluate --adapter ml/fine_tuning/adapters/lora-retention-assistant
"""
from __future__ import annotations

import argparse

import torch
from peft import PeftModel

from ml.fine_tuning.dataset import EVAL_PROMPTS, SYSTEM_PROMPT
from ml.fine_tuning.model import MODEL_NAME, load_base_model, load_tokenizer


@torch.no_grad()
def generate(model, tokenizer, prompt: str, max_new_tokens: int = 80) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    out = model.generate(
        **inputs, max_new_tokens=max_new_tokens, do_sample=False,
        pad_token_id=tokenizer.pad_token_id,
    )
    return tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)


def compare(adapter_dir: str, model_name: str = MODEL_NAME, prompts: list[str] | None = None) -> list[dict]:
    prompts = prompts or EVAL_PROMPTS
    tokenizer = load_tokenizer(model_name)

    base_model = load_base_model(model_name)
    base_model.eval()

    tuned_model = PeftModel.from_pretrained(load_base_model(model_name), adapter_dir)
    tuned_model.eval()

    rows = []
    for prompt in prompts:
        rows.append({
            "prompt": prompt,
            "base": generate(base_model, tokenizer, prompt),
            "tuned": generate(tuned_model, tokenizer, prompt),
        })
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", type=str, required=True)
    args = ap.parse_args()

    for row in compare(args.adapter):
        print(f"\nPROMPT: {row['prompt']}")
        print(f"  base : {row['base'][:200]}")
        print(f"  tuned: {row['tuned'][:200]}")


if __name__ == "__main__":
    main()
