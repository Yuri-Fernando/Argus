# ADR-010 — Desenvolvimento local-first; nuvem é opt-in via Terraform

**Status:** Aceito
**Data:** 2026-08-10

## Contexto

Manter Azure Databricks + Snowflake + Power BI + Azure OpenAI ligados continuamente durante todo o desenvolvimento tem custo real e não é necessário para a maior parte do trabalho de engenharia (escrever/testar PySpark, GX, MDM, agentes). O design original já sinalizava essa preocupação ("não precisamos pagar por tudo", v0.3 §61) mas não formalizava como.

## Decisão

Todo componente abaixo da linha de nuvem em ARCHITECTURE.md §1 (princípio 6) roda localmente via `docker-compose` (MinIO no lugar de ADLS, Postgres, MLflow local, GX, PySpark local) — ver [`docs/deployment.md`](../deployment.md). Recursos de nuvem são provisionados sob demanda via `terraform apply -var-file=environments/dev` **somente** quando o sprint específico exige (ex: Sprint 7 precisa de Snowflake real; Sprint 9 precisa de Power BI real) e podem ser destruídos entre sessões de demo (`terraform destroy`).

## Alternativas consideradas

1. **Ambiente de nuvem sempre ligado** — rejeitado: custo desnecessário para um projeto pessoal, sem benefício de velocidade de desenvolvimento proporcional.
2. **Nunca usar a nuvem, só simular tudo localmente** — rejeitado: perderia a validação real de que os Terraform modules e as integrações Databricks/Snowflake/Power BI de fato funcionam — que é justamente parte do que se quer provar no portfólio.

## Consequências

- Positivas: custo controlado, onboarding rápido (`make up && make seed` sem precisar de nenhuma credencial de nuvem), e ainda assim a infraestrutura de nuvem é real e testável quando necessário.
- Negativas: exige manter dois "caminhos" de configuração (endpoint local vs. cloud) em cada componente que fala com storage/warehouse — mitigado centralizando isso em variáveis de ambiente (`.env`, ver `.env.example`) e nunca hard-codando endpoints no código.
