# 10 — Caching

| Camada | Conteúdo | TTL / invalidação |
|---|---|---|
| CDN / BFF | respostas GET idempotentes do dashboard | 30–60 s, `Cache-Control` |
| Redis (feature cache) | features de cliente para inferência | 5 min; invalida em `customer.updated` |
| Redis (semantic layer) | resultado de métrica governada por (métrica, filtros) | 10 min; invalida no refresh do gold |
| In-process (LRU) | `PredictionStrategy` por `ModelId` (Factory) | vida do processo |
| Vector store | embeddings de documentos (RAG) | persistente; recomputa no re-ingest |

Padrão: **cache-aside**. Nunca cachear resposta de ação consequente.
Estratégia anti-stampede: request coalescing no BFF.
