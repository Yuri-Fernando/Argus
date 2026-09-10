# 07 — Escalabilidade

- **Stateless services** → escala horizontal via HPA (CPU + RPS custom
  metric). Sem afinidade de sessão.
- **Kafka** → paralelismo limitado pelo nº de partições; chave por
  `customer_id` mantém ordenação por cliente.
- **Postgres por serviço** → réplicas de leitura para consultas pesadas;
  particionamento por range de data nas tabelas de fato operacionais.
- **Lakehouse** → processamento distribuído (Spark/Databricks); jobs
  incrementais (merge por chave), não full refresh.
- **inference-service** → modelos carregados em memória por pod; cache de
  feature lookup (ver 10-caching).
- **Backpressure** → se o consumo de `model.prediction.created` atrasa, o
  lag do consumer group dispara scale-out do worker.
