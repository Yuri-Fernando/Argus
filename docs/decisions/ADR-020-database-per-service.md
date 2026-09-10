# ADR-020 — Database por serviço

**Status:** Aceito · **Data:** 2026-09-10

## Contexto

Serviços de domínio precisam evoluir schema de forma independente e não
podem falhar juntos por causa de um banco compartilhado.

## Decisão

Cada serviço com deploy próprio tem seu **próprio banco** (schema Postgres
isolado no dev local; instância/DB dedicada em nuvem). Sem acesso
cross-serviço ao banco de outro. Dados de que um serviço precisa e não
possui chegam por **evento** (Kafka) e são materializados numa tabela local
de leitura (read model).

Exceção: o **Lakehouse/Gold** é leitura analítica compartilhada, populada
por CDC/eventos — não é o banco operacional de ninguém.

## Alternativas

- **Banco compartilhado** — acoplamento de schema, falha conjunta,
  contenção. Rejeitado.
- **Schema compartilhado com tabelas por serviço** — melhor, mas ainda
  falha conjunta e tentação de JOIN cross-serviço. Rejeitado.

## Consequências

- (+) Deploy e evolução de schema independentes; blast radius menor.
- (−) Sem JOIN cross-serviço; duplicação controlada de dados via read
  models; consistência eventual (ADR-022).
