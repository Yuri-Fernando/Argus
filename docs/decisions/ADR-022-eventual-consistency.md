# ADR-022 — Consistência eventual entre bounded contexts

**Status:** Aceito · **Data:** 2026-09-10

## Contexto

Com database-per-service (ADR-020) e comunicação por eventos (ADR-018),
não há transação distribuída entre serviços.

## Decisão

- **Forte** dentro do agregado (transação ACID local + optimistic locking
  por `version`).
- **Eventual** entre contexts: o serviço A commita e publica o evento na
  mesma transação (outbox pattern); o serviço B consome e converge seu read
  model. Janela típica de convergência < 2 s.
- **Sagas** para fluxos multi-serviço com efeito colateral (ex.: ação de
  retenção sobre cliente): orquestração explícita com passos de compensação
  e **aprovação humana** antes do passo consequente (ADR-006).
- Idempotência do consumidor: dedupe por `event_id`.

## Alternativas

- **2PC / XA** — rejeitado: acopla disponibilidade dos serviços, não escala,
  operacionalmente frágil.
- **Transação distribuída via banco compartilhado** — viola ADR-020.

## Consequências

- (+) Serviços permanecem disponíveis independentemente.
- (−) A UI precisa lidar com "ainda propagando" (mostra estado + timestamp);
  relatórios usam snapshot consistente do gold, não leitura cross-serviço ao
  vivo.
