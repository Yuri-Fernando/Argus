# 12 — Observabilidade

Tratada como **capacidade de plataforma**, não add-on por serviço.

| Sinal | Ferramenta | Convenção |
|---|---|---|
| Traces | OpenTelemetry → (Tempo/X-Ray) | trace propagado no gateway, `traceparent` em eventos Kafka |
| Métricas | Prometheus + Grafana | RED (request rate/errors/duration) para serviços; USE para infra; lag de consumer group |
| Logs | JSON estruturado → Loki/CloudWatch | sempre com `trace_id`, `service`, `customer_id` (pseudonimizado) |
| ML | MLflow + Evidently | drift (PSI/KS), qualidade de predição, `model.drift.detected` |

SLOs em `docs/runbooks/slo.md`; runbooks por alerta em `docs/runbooks/`.
