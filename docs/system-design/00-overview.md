# System Design — Overview

Argus é usado como veículo para exercitar decisões de **system design de
plataforma corporativa**. O domínio de negócio (Customer Intelligence) é
estável e conhecido; o foco destes documentos é o *como* — escala,
disponibilidade, consistência, comunicação, falha.

## Escopo

| Capacidade de negócio | Serviço | Padrão de comunicação |
|---|---|---|
| Gestão de cliente | `customer-service` (Java) | REST síncrono + eventos `customer.*` |
| Resolução de identidade / MDM | `identity-service` (Java) | consome `customer.*`, publica `customer.identity.resolved` |
| Churn / segmentação / NBA | `churn-service`, `inference-service` (Python) | REST + eventos `model.prediction.created` |
| RAG / agentes | `rag-service`, `agent-orchestrator` (Python) | REST + MCP |
| Governança / risco de modelo | ThemisAI (externo) + `ml-platform/adversarial-evaluation` | gate no pipeline de deploy |

## Documentos

`01-requirements` · `02-capacity-estimation` · `03-high-level-design` ·
`04-data-model` · `05-api-design` · `06-event-driven-architecture` ·
`07-scalability` · `08-high-availability` · `09-consistency` · `10-caching` ·
`11-security` · `12-observability` · `13-disaster-recovery` · `14-trade-offs`
