# 09 — Modelos de Consistência

| Fronteira | Modelo | Justificativa |
|---|---|---|
| Dentro do agregado (ex.: `Customer`) | forte (transação ACID no Postgres do serviço) | invariantes de negócio |
| Entre bounded contexts | eventual (via Kafka) | desacoplamento, disponibilidade (ADR-022) |
| Golden Record (MDM) | eventual, convergente | rematching é assíncrono; `valid_from` versiona |
| Métricas do semantic layer | consistência de leitura por snapshot | paridade testada entre as 3 implementações |
| Saga de ação sobre cliente | orquestrada, com compensação + aprovação humana | ações consequentes exigem HITL (ADR-006) |

Conflitos de escrita concorrente: `updated_at` + optimistic locking
(`version` no agregado).
