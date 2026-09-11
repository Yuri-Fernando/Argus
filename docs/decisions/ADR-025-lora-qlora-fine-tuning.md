# ADR-025 — Fine-tuning por LoRA/QLoRA (não fine-tuning completo)

**Status:** Aceito · **Data:** 2026-09-11

## Contexto

O `agents/llm_gateway/` já roteia entre múltiplos provedores de LLM
(prompt engineering + RAG). Para especializar respostas ao domínio de
Customer Intelligence (ex.: assistente de retenção com o vocabulário e as
políticas do Argus) sem depender só de prompt, é necessário fine-tuning.

## Decisão

Fine-tuning por **LoRA** (Hu et al., 2021) como padrão, com **QLoRA**
(Dettmers et al., 2023) como variante para modelos-base maiores que não
caibam em VRAM em precisão nativa. `ml/fine_tuning/`:

- `model.py` — carrega o modelo-base (`Qwen2.5-0.5B-Instruct` por padrão,
  trocável), com `load_in_4bit` opcional (QLoRA).
- `lora_finetune.py` — loop de treino compartilhado (LoRA e QLoRA usam o
  mesmo código; a diferença é só a quantização do modelo-base).
- `qlora_finetune.py` — wrapper com `load_in_4bit=True`.
- `evaluate.py` — compara gerações do modelo base vs. base+adapter.

Rodado de verdade (RTX 3060 Ti): LoRA treina **0,22% dos parâmetros**
(1,08M de 495M), loss 3,51→1,66 em 13s; QLoRA mesmo resultado sobre o
modelo em 4-bit, loss 3,62→1,78 em 24s.

## Alternativas

- **Fine-tuning completo** — atualiza 100% dos pesos; caro em memória/tempo
  e cada variante custa o modelo inteiro em disco. Rejeitado para este
  caso de uso (adaptar um modelo pequeno a um domínio específico).
- **Só prompt engineering / RAG** — funciona para conhecimento factual
  (é o que `rag/` já faz), mas não altera o *estilo*/formato de resposta do
  modelo de forma consistente; fine-tuning complementa, não substitui, o RAG.
- **P-Tuning / Prefix-Tuning** — alternativas leves consideradas; LoRA
  escolhido pelo suporte maduro em `peft` e por não adicionar tokens ao
  contexto (custo de inferência inalterado).

## Consequências

- (+) Adapter pequeno (~16MB neste modelo) por caso de uso; modelo-base
  compartilhado entre adapters; fácil trocar/remover sem retreinar do zero.
- (+) QLoRA abre caminho para modelos maiores (7B+) na mesma GPU de
  consumo, se o caso de uso exigir mais capacidade.
- (−) LoRA/QLoRA não superam RAG para conhecimento que muda com frequência
  (preço, política atualizada) — nesses casos, RAG continua sendo a
  ferramenta certa; fine-tuning é para *comportamento*, não para *fatos
  voláteis*.
