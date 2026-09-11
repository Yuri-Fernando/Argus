# ml/fine_tuning/ — LoRA / QLoRA

Adapta um LLM open-source (`Qwen/Qwen2.5-0.5B-Instruct`, Apache-2.0) ao
domínio de Customer Intelligence do Argus (assistente de retenção), sem
tocar nos pesos originais do modelo-base.

## Por quê LoRA/QLoRA em vez de fine-tuning completo

Fine-tuning completo atualiza todos os pesos do modelo — caro em memória e
tempo, e cada variante do modelo (um adapter por caso de uso) custa o
tamanho inteiro do modelo em disco. **LoRA** (Hu et al., 2021) congela o
modelo-base e treina só um par de matrizes de baixo posto injetadas nas
projeções de atenção — aqui, **0,22% dos parâmetros** (1.081.344 de
495.114.112). **QLoRA** (Dettmers et al., 2023) é o mesmo mecanismo sobre o
modelo-base quantizado em 4 bits (NF4 + double quantization via
`bitsandbytes`), reduzindo o footprint de memória do modelo-base em ~4x —
o que importa é caber modelos maiores na mesma GPU, não a velocidade deste
modelo pequeno em particular.

## Rodado de verdade (RTX 3060 Ti, 8GB)

| | Parâmetros treináveis | Loss (início → fim) | Tempo |
|---|---|---|---|
| LoRA (16-bit) | 1.081.344 / 495.114.112 (0,22%) | 3,51 → 1,66 | 13,0 s |
| QLoRA (4-bit) | 1.081.344 / 495.114.112 (0,22%) | 3,62 → 1,78 | 24,2 s |

Dataset pequeno e sintético de propósito (`dataset.py`, 8 exemplos) — o
objetivo é demonstrar o **mecanismo** de ponta a ponta (carregar → injetar
adapter → treinar → convergir → salvar → recarregar), não treinar um
modelo de produção. Para isso, basta trocar `MODEL_NAME`
(`ml/fine_tuning/model.py`) por um modelo maior e o dataset por um real —
o pipeline não muda.

## Uso

```bash
python -m ml.fine_tuning.lora_finetune                 # LoRA, 3 épocas
python -m ml.fine_tuning.qlora_finetune                 # QLoRA, 3 épocas
python -m ml.fine_tuning.evaluate --adapter ml/fine_tuning/adapters/lora-retention-assistant
```

`ml/fine_tuning/adapters/` (saída do treino) não é versionado
(`.gitignore`) — os adapters são reproduzíveis rodando os scripts acima.

## Testes

`tests/test_lora_finetune.py` — smoke real (baixa o modelo, treina 1 época
em 2 exemplos, verifica que a loss não explode e que o adapter salvo é
recarregável via `PeftModel.from_pretrained`). Gated por `RUN_FINETUNE=1`
(baixa ~1GB e treina de verdade — não roda no CI padrão):

```bash
RUN_FINETUNE=1 pytest ml/fine_tuning/tests -q -m finetune
```

Ver `notebooks/lora_qlora_finetuning.ipynb` para o walkthrough completo com
curva de loss e comparação qualitativa base vs. adaptado.
