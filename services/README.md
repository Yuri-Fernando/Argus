# services/ — serviços de domínio (Enterprise Architecture v2)

Decomposição do Argus em serviços orientados a domínio (DDD bounded
contexts), stack **poliglota** por característica de workload:

| Serviço | Linguagem | Bounded context | Status |
|---|---|---|---|
| `customer-service/` | Java / Spring Boot | Customer Management | 🗺️ skeleton (estrutura DDD + pom válido) |
| `inference-service/` | Python / FastAPI | Model Inference | ✅ implementado (Strategy + Adapter + Factory, testes) |
| `identity-service/` | Java / Spring Boot | Identity Resolution / MDM | 🗺️ planejado (ADR-018) |
| `churn-service/` | Python / FastAPI | Analytics — Churn | 🚧 reaproveita `ml/churn/` existente |
| `rag-service/` | Python / FastAPI | AI — RAG | 🚧 reaproveita `rag/` existente |
| `agent-orchestrator/` | Python / LangGraph | AI — Agent Orchestration | 🚧 reaproveita `agents/orchestrator/` existente |

> A escolha da linguagem segue a característica do workload, não uma regra
> única para toda a plataforma: Java/Spring nos serviços de negócio/domínio,
> Python/FastAPI nos serviços de dados/ML/IA. Ver
> [ADR-017](../docs/decisions/ADR-017-polyglot-java-python.md).

Cada serviço segue Clean/Hexagonal Architecture (ADR-014) com as camadas
`domain / application / infrastructure / interfaces`.
