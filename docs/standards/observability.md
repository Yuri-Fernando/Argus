# Standard — Observabilidade

- **Trace**: propagação W3C `traceparent` na borda; incluir `trace_id` em
  todo log e no header de eventos Kafka.
- **Log**: JSON, uma linha por evento. Campos obrigatórios: `ts`, `level`,
  `service`, `trace_id`, `msg`. `customer_id` sempre pseudonimizado.
- **Métrica**: serviços expõem RED (rate, errors, duration) em `/metrics`
  (Prometheus). Consumidores Kafka expõem `consumer_lag`.
- **SLO**: definido por serviço em `docs/runbooks/slo.md`; alerta dispara
  em queima de orçamento de erro (multi-window burn rate).
- **Runbook**: todo alerta tem um runbook em `docs/runbooks/` com passos de
  diagnóstico e mitigação.
- **ML**: drift (PSI/KS) e qualidade de predição em dashboard próprio;
  `model.drift.detected` é evento de primeira classe.
