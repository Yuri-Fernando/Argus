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
python -m ml.fine_tuning.inference_optimize --adapter ml/fine_tuning/adapters/lora-retention-assistant
```

`ml/fine_tuning/adapters/` (saída do treino) não é versionado
(`.gitignore`) — os adapters são reproduzíveis rodando os scripts acima.

## Otimização de inferência (`inference_optimize.py`)

Depois do fine-tuning, três variantes do mesmo modelo, medidas de verdade
(não estimadas — `benchmark()` roda `generate()` e cronometra):

| Variante | Device | Tokens/s | Tamanho |
|---|---|---|---|
| Adapter LoRA separado (não fundido) | GPU | 5,51 | 946 MB |
| Adapter fundido (`merge_and_unload`) | GPU | 8,82 | 942 MB |
| Fundido + quantização dinâmica INT8 | CPU | 3,77 | **519 MB** |

Duas técnicas reais de otimização, cada uma resolvendo um problema
diferente:

- **Merge do adapter** (`merge_adapter`) elimina o overhead de adapter
  (`x @ A @ B` a cada forward pass) fundindo os pesos LoRA nos pesos-base
  — resultado é 60% mais rápido aqui, na mesma GPU, porque deixa de pagar
  esse produto extra de matrizes.
- **Quantização dinâmica INT8** (`quantize_dynamic_int8`, `torch.quantization`,
  stdlib) reduz o footprint em memória em ~45% — o objetivo aqui não é
  velocidade (INT8 dinâmico em CPU é mais lento que fp16 em GPU, como os
  números mostram), é caber o modelo em ambientes sem GPU/com memória
  restrita, uma otimização real e proporcional, distinta da quantização
  usada em `root_cause_classifier.py` (que evita transformer inteiramente
  por ser um classificador de conjunto fechado — ver
  `agents/llm_gateway/README.md`).

## Testes

`tests/test_lora_finetune.py` — smoke real (baixa o modelo, treina 1 época
em 2 exemplos, verifica que a loss não explode e que o adapter salvo é
recarregável via `PeftModel.from_pretrained`).

`tests/test_inference_optimize.py` — treina um adapter mínimo, funde,
quantiza, e roda `generate()` de verdade no modelo fundido/quantizado
(pegou um bug real: modelo carregado em bfloat16 na GPU precisa de
`.float()` antes da quantização dinâmica, senão o forward falha em tempo
de execução).

Ambos gated por `RUN_FINETUNE=1` (baixa ~1GB e treina de verdade — não
roda no CI padrão):

```bash
RUN_FINETUNE=1 pytest ml/fine_tuning/tests -q -m finetune
```

Ver `notebooks/lora_qlora_finetuning.ipynb` para o walkthrough completo com
curva de loss e comparação qualitativa base vs. adaptado.
