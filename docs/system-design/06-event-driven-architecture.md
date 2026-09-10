# 06 — Event-Driven Architecture

## Backbones

- **Kafka** — event streaming durável: domain events, replay, integração com
  o data platform. Tópicos: `customer.created`, `customer.updated`,
  `customer.identity.resolved`, `order.created`, `model.prediction.created`,
  `model.drift.detected`, `security.adversarial.detected`.
- **RabbitMQ** — work queue: comandos/jobs assíncronos (`report.generate`,
  `adversarial.robustness.run`, `model.retrain`). Semântica de fila de
  trabalho com ack, retry e DLQ.

Ver ADR-019 (Kafka vs RabbitMQ — por que os dois, com papéis distintos).

## Garantias

| Preocupação | Abordagem |
|---|---|
| Ordenação | por partição (chave = `customer_id`) |
| Idempotência do consumidor | dedupe por `event_id` numa tabela de processados |
| Entrega | at-least-once; consumidores idempotentes |
| Schema | JSON Schema em `platform/messaging/schemas/`, validado no publish |
| Poison message | DLQ após N tentativas + alerta |
| Consistência entre contexts | eventual, com reconciliação por replay |
