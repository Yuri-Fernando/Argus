# ADR-008 — Estratégia de providers Terraform para Snowflake (v1 vs. novo `snowflakedb/snowflake`)

**Status:** Aceito
**Data:** 2026-08-10

## Contexto

Pesquisa de agosto/2026 (ver [IMPROVEMENTS_AND_RESEARCH.md](../../IMPROVEMENTS_AND_RESEARCH.md)) mostrou que existem hoje dois providers Terraform para Snowflake: o histórico `Snowflake-Labs/snowflake` (v1, com parte dos recursos ainda marcados como *preview feature* dentro do provider, exigindo `preview_features_enabled` explícito) e o mais novo `snowflakedb/snowflake`, mantido oficialmente pela Snowflake. O design original (`rascunho.md`) só conhecia o primeiro.

## Decisão

Usar **`snowflakedb/snowflake`** como provider primário para todo recurso que ele já cobre; usar **`Snowflake-Labs/snowflake` v1** como fallback explícito, documentado por recurso, apenas para o que ainda não migrou — cada módulo Terraform declara no seu próprio README qual provider está usando e por quê (`terraform/modules/snowflake/*/README.md`).

## Alternativas consideradas

1. **Usar só `Snowflake-Labs/snowflake` v1** (o que o design original assumia) — funcional, mas ignora a direção clara do ecossistema em 2026 e corre o risco de o projeto nascer já "desatualizado" no dia em que for mostrado numa entrevista.
2. **Usar só `snowflakedb/snowflake`** — rejeitado como decisão única porque nem todo recurso necessário (ex: alguns objetos de Semantic View / Cortex) tem cobertura garantida no provider mais novo no momento desta escrita; forçar isso quebraria `terraform apply` para parte da infraestrutura.

## Consequências

- Positivas: infraestrutura alinhada com a direção atual do ecossistema Snowflake; decisão documentada e revisável por módulo, sem "mágica" escondida.
- Negativas: dois providers no mesmo `environments/dev/main.tf` exigem `required_providers` cuidadosamente versionado; revisitar este ADR a cada sprint que toque `terraform/modules/snowflake/` para migrar recursos assim que o provider novo os cobrir.
