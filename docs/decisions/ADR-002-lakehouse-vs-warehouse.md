# ADR-002 — Databricks (Lakehouse) e Snowflake (Warehouse) coexistem, sem sobreposição de função

**Status:** Aceito
**Data:** 2026-08-10

## Contexto

As três iterações do design (`rascunho.md`) oscilaram entre "Snowflake é extensão opcional" (v0.2) e "Snowflake é obrigatório" (v0.3, decisão explícita do usuário: *"eu quero terraform e snowflake cara isso tem que conter mesmo que fique extenso"*). Sem uma separação de responsabilidade clara, ter os dois é apenas redundância técnica ("Frankenstein de ferramentas") e fica indefensável em entrevista.

## Decisão

Databricks e Snowflake **não competem** — cada um é dono de uma responsabilidade exclusiva:

| Camada | Databricks | Snowflake |
|---|---|---|
| Ingestão/ETL/ELT bruto | ✅ dono | — |
| Processamento distribuído (PySpark) | ✅ dono | — |
| Bronze/Silver/Gold (Medallion) | ✅ dono | — |
| MDM / Golden Record / Feature Engineering | ✅ dono | — |
| Treino de ML / MLflow | ✅ dono | — |
| Data Warehouse dimensional governado para consumo | espelha via Streams/Tasks | ✅ dono |
| Semantic Views / Cortex Analyst / Cortex Search / Cortex Agents | — | ✅ dono |
| AI serving layer para agentes | — | ✅ dono |

Gold do Databricks é a fonte da verdade; Snowflake CORE é um **produto de dados derivado**, sincronizado incrementalmente (Streams + Tasks), nunca a origem.

## Alternativas consideradas

1. **Só Databricks (Databricks SQL Warehouse faz o papel de warehouse)** — rejeitado: perderia a demonstração de competência em Snowflake/Cortex, que é especificamente pedida pelo usuário e valiosa para o mercado (Cortex Analyst/Agents atingiram GA em nov/2025, ver [ADR-007](ADR-007-ai-guardrails.md)).
2. **Só Snowflake (ingestão e transformação também no Snowflake, via Snowpark)** — rejeitado: perderia a demonstração de Databricks/PySpark/Delta Lake, que é o requisito mais citado nas vagas-alvo.
3. **Duplicar toda a lógica de transformação nos dois** — rejeitado: é exatamente o anti-padrão que este ADR existe para evitar.

## Consequências

- Positivas: a arquitetura é defensável ("cada camada tem uma responsabilidade", não "usei tudo que sei"); demonstra competência simultânea em Lakehouse e Warehouse, que é rara e valorizada.
- Negativas: custo de manter uma sincronização incremental (Streams/Tasks) como componente extra a testar; risco de drift entre Gold (Databricks) e CORE (Snowflake) se a sincronização falhar — mitigado por um teste de paridade (`tests/data/test_gold_snowflake_parity.py`, Sprint 7).
