# Standard — Código

## Geral
- Um serviço = um bounded context. Camadas `domain / application /
  infrastructure / interfaces`. Dependência sempre aponta para dentro
  (domínio não importa infra).
- Nada de lógica de negócio em controller/rota nem em repositório.
- Erros de domínio são exceções de domínio; a camada de interface as
  traduz para HTTP/gRPC.

## Python
- 3.11+, type hints obrigatórios em assinaturas públicas. `ruff` + `mypy`
  no CI. `from __future__ import annotations` no topo.
- `pydantic` só na borda (interfaces/schemas); o domínio usa dataclasses.
- Testes: `pytest`, nome `test_*`, um comportamento por teste.

## Java
- 17+, Spring Boot 3. Records para value objects. `@Transactional` só na
  camada de aplicação. Bean Validation nos DTOs de entrada.
- Testes: JUnit 5 + Testcontainers para integração; Cucumber para BDD.

## Commits
- Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, ...).
- Toda decisão de arquitetura → ADR em `docs/decisions/`.
