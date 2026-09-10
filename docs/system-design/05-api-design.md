# 05 — API Design

| Estilo | Onde | Por quê |
|---|---|---|
| **REST/JSON** | APIs externas e BFF | ubíquo, cacheável, fácil de inspecionar (ADR-021) |
| **GraphQL** | agregação para o dashboard | o front escolhe os campos; evita N+1 de REST |
| **gRPC** | chamadas internas de baixa latência (inference, identity) | contrato forte (protobuf), streaming, menor overhead (ADR-021) |
| **MCP** | agentes ↔ dados governados | ferramenta padronizada para LLM (ADR-004) |

## Convenções REST

- Versionamento por path: `/v1/...`.
- Erros: RFC 7807 (`application/problem+json`).
- Idempotência: `Idempotency-Key` header em `POST` que geram efeito.
- Paginação: cursor (`?cursor=`), nunca offset em coleções grandes.
- Contratos versionados em `docs/` e testados por testes de contrato
  (`tests/contract/`).
