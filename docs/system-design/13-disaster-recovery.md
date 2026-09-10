# 13 — Disaster Recovery

| Recurso | Backup | RPO | RTO |
|---|---|---|---|
| Postgres (RDS) | snapshot automático + PITR | <= 5 min | <= 30 min |
| Kafka (MSK) | replicação 3 AZ + tiered storage / mirror | ~0 (multi-AZ) | <= 15 min |
| S3 / Lakehouse | versionamento + replicação cross-region | <= 15 min | <= 1 h |
| MLflow registry | backup do backend store + artefatos S3 | <= 15 min | <= 1 h |
| IaC | estado remoto (S3 + DynamoDB lock), tudo reconstruível via `terraform apply` | — | <= 2 h (rebuild ambiente) |

Exercício de restore documentado em `docs/runbooks/`. Ambiente é
*cattle*: um `terraform apply` + replay de Kafka reconstrói o plano de
dados.
