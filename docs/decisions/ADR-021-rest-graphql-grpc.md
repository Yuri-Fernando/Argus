# ADR-021 — REST na borda, GraphQL no BFF, gRPC entre serviços

**Status:** Aceito · **Data:** 2026-09-10

## Decisão

| Camada | Protocolo | Motivo |
|---|---|---|
| APIs públicas / integrações | **REST/JSON** | ubíquo, cacheável, inspecionável, tooling universal |
| Agregação para o dashboard | **GraphQL** | o front seleciona campos; elimina over/under-fetching e N+1 de REST |
| Chamadas internas quentes (inference, identity) | **gRPC** | protobuf (contrato forte + evolução), HTTP/2 multiplexado, streaming, menor latência/overhead |
| Agente ↔ dados governados | **MCP** | ferramenta tipada padrão para LLM (ADR-004) |

## Alternativas

- **REST em tudo** — simples, mas GraphQL resolve melhor a agregação do
  dashboard e gRPC é mensuravelmente mais barato no caminho quente interno.
- **gRPC em tudo** — péssima DX na borda, sem cache HTTP, difícil de
  debugar por terceiros.

## Consequências

- (+) Cada fronteira usa o protocolo adequado; dá para explicar o porquê de
  cada um.
- (−) Três estilos de contrato para versionar e testar (mitigado por
  `tests/contract/`).
