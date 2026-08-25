# ADR-005 — Três implementações de semantic layer, uma única definição canônica

**Status:** Aceito
**Data:** 2026-08-10

## Contexto

O problema central que o design original queria resolver era: *"Power BI mostrou R$ 10M e o agente mostrou R$ 13M."* Isso só se resolve se toda métrica tiver **uma** definição, independente de quem a consome. Em agosto de 2026, existem três formas maduras e concorrentes de implementar isso: dbt/MetricFlow (open source, portável), Unity Catalog Metric Views (nativo Databricks, GA abr/2026) e Snowflake Semantic Views (nativo Snowflake, recomendado para o Cortex Analyst).

## Decisão

Manter **uma definição canônica** por métrica em [`docs/semantic-dictionary.md`](../semantic-dictionary.md) (texto, não código) e implementá-la nas três camadas, com um teste automatizado de paridade (`tests/data/test_metric_parity.py`) que falha o CI se as três respostas divergirem para a mesma pergunta.

## Alternativas consideradas

1. **Escolher só uma (ex: só dbt/MetricFlow)** — mais simples, mas perde a chance de demonstrar e comparar as duas ofertas nativas de plataforma (que são exatamente o que Databricks/Snowflake cobram nas entrevistas de hoje) e não resolve o caso em que Genie ou Cortex Analyst precisam de uma métrica nativa da própria plataforma para funcionar bem.
2. **Implementar as três sem teste de paridade** — rejeitado: sem o teste automatizado, a garantia "uma métrica, uma definição" vira só uma promessa no README, não um fato verificável.

## Consequências

- Positivas: material de comparação real para entrevista ("eu implementei os três e aqui está o trade-off de cada um"); reduz o risco do "Power BI vs. agente discordam".
- Negativas: triplica o trabalho de manutenção de métricas — aceito conscientemente como parte do valor educacional/demonstrativo do projeto, documentado no README como tal.
