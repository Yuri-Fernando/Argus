# Standard — API Design

- Versionar por path (`/v1`). Mudança incompatível = nova versão, nunca
  quebra da atual.
- Erros: `application/problem+json` (RFC 7807) com `type`, `title`,
  `status`, `detail`, `instance`.
- `POST` com efeito colateral aceita `Idempotency-Key`.
- Coleções: paginação por cursor; nunca `LIMIT/OFFSET` em tabela grande.
- Nomes de recurso no plural (`/customers/{id}`). Verbo só em ações que não
  são CRUD (`/customers/{id}:merge`).
- Todo endpoint tem: contrato OpenAPI/proto no repo, teste de contrato,
  limite de rate no gateway.
- Campos de data em ISO-8601 UTC. IDs opacos (não expor PK sequencial).
