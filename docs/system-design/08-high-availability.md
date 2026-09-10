# 08 — Alta Disponibilidade

| Componente | Estratégia |
|---|---|
| Serviços | >= 2 réplicas, multi-AZ, `PodDisruptionBudget`, liveness/readiness probes |
| Kafka (MSK) | 3 brokers multi-AZ, `replication.factor=3`, `min.insync.replicas=2` |
| Postgres (RDS) | Multi-AZ, failover automático, réplicas de leitura |
| Istio | retry (2x, backoff), timeout por rota, circuit breaker (outlier detection) |
| Deploy | canary (10% → 50% → 100%) com rollback automático por métrica |
| Degradação graciosa | inference cai para estratégia linear se GBDT/LLM indisponível; RAG cai para stack local |

Alvo: 99.9% nas APIs de leitura (≈ 43 min/mês de orçamento de erro).
