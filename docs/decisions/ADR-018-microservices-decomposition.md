# ADR-018 — Decomposição em microsserviços por bounded context (DDD)

**Status:** Aceito · **Data:** 2026-09-10

## Contexto

A plataforma v1 é um "modular monolith" de fato (pastas `mdm/`, `ml/`,
`rag/`, `agents/` sem fronteira de processo). Para exercitar system design
distribuído, alguns contextos passam a ser serviços com deploy próprio.

## Decisão

Bounded contexts → serviços:

- **Customer** → `customer-service`
- **Identity / MDM** → `identity-service`
- **Analytics** (churn, segmentação, forecasting) → `churn-service` +
  reuso de `ml/`
- **Model Inference** → `inference-service`
- **AI** (RAG, agentes) → `rag-service`, `agent-orchestrator` + reuso de
  `rag/`, `agents/`
- **Governance** → ThemisAI (repo externo) + `ml-platform/adversarial-evaluation`

Não decompor abaixo disso agora (evitar "nano-serviços"). Data Quality e
Lakehouse continuam como plataforma compartilhada, não serviço de domínio.

## Alternativas

- **Manter monólito modular** — válido e mais simples, mas não exercita
  comunicação distribuída, consistência eventual, mesh — que é o objetivo.
- **Decompor tudo** — rejeitado: overhead operacional sem ganho de
  aprendizado; DQ/Lakehouse não são contextos de negócio.

## Consequências

- (+) Limites de time/deploy claros; falha isolada.
- (−) Consistência eventual entre contexts (ADR-022); testes de contrato
  passam a ser obrigatórios.
