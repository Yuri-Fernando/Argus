# ADR-019 — Kafka **e** RabbitMQ, com papéis distintos (não redundantes)

**Status:** Aceito · **Data:** 2026-09-10

## Contexto

Tanto Kafka quanto RabbitMQ aparecem como requisitos. A resposta preguiçosa
é instalar os dois e usá-los para a mesma coisa. A resposta de arquitetura é
usá-los pelas semânticas que só cada um oferece.

## Decisão

- **Kafka** = *event streaming* durável. Log append-only, retenção por
  tempo, replay, consumo por múltiplos consumer groups independentes,
  ordenação por partição. Usado para **domain events** e integração com o
  data platform: `customer.updated`, `model.prediction.created`,
  `model.drift.detected`, `security.adversarial.detected`.
- **RabbitMQ** = *work queue*. Roteamento flexível, ack por mensagem,
  prefetch, DLQ, prioridade. Usado para **comandos/jobs**:
  `report.generate`, `adversarial.robustness.run`, `model.retrain`.

Regra: se mais de um consumidor precisa do mesmo fato, ou se replay importa
→ Kafka. Se é uma tarefa a ser feita por um worker, uma vez, com retry →
RabbitMQ.

## Alternativas

- **Só Kafka** — dá para emular work-queue, mas ack por mensagem, DLQ e
  prioridade ficam manuais e frágeis.
- **Só RabbitMQ** — sem log retido/replay; integração analítica e
  multi-consumidor viram gambiarra.
- **SNS/SQS + Kinesis (AWS-nativo)** — considerado; Kafka+RabbitMQ escolhido
  por portabilidade e por serem as tecnologias que o mercado pede nominalmente.

## Consequências

- (+) Cada padrão de mensageria tem a ferramenta certa; a decisão é
  defensável ("escolhi Kafka para X e RabbitMQ para Y, não dois brokers para
  o mesmo Z").
- (−) Dois brokers para operar e monitorar. Mitigado: RabbitMQ só para um
  punhado de filas de job; Kafka é o backbone.
