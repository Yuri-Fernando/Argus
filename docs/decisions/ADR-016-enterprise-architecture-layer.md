# ADR-016 — Camada de Arquitetura Enterprise (v2) sobre a plataforma existente

**Status:** Aceito · **Data:** 2026-09-10

## Contexto

O Argus v1/v2.x entregou uma plataforma de Dados & IA funcional (Lakehouse,
MDM, ML, RAG, agentes, governança) com orientação Azure e execução
local-first. Um brainstorm de consolidação de portfólio (`up.txt`) pede que
o Argus passe a ser também a **referência de arquitetura de software e
system design corporativo**: DDD com bounded contexts, microsserviços
poliglotas (Java + Python), arquitetura orientada a eventos (Kafka +
RabbitMQ), service mesh, e documentação explícita de decisões (ADR/RFC/
system-design).

## Decisão

Adicionar a camada enterprise como **evolução aditiva**, não reescrita:

- `services/` — serviços de domínio (Clean/Hexagonal, camadas
  `domain/application/infrastructure/interfaces`). `inference-service`
  (Python) implementado; `customer-service`/`identity-service` (Java/Spring)
  como skeleton estrutural.
- `platform/messaging/` — abstração de bus com `InMemoryBus` (dev/teste),
  `KafkaBus`, `RabbitBus` + JSON Schemas de tópicos.
- `platform/service-mesh/istio/` — manifests de referência (mTLS, retry,
  canary).
- `docs/system-design/`, ADR-017..024, `docs/rfc/`, `docs/c4/`,
  `docs/standards/`.
- `README.md` ganha uma **Capability Status table** (✅/🚧/🗺️) separando o
  implementado do planejado.

O pipeline de dados Azure/Databricks/Snowflake existente permanece
inalterado.

## Alternativas

1. **Repo novo só de arquitetura** — rejeitado: fragmenta o portfólio e
   perde o domínio real (Customer Intelligence) que dá sentido à arquitetura.
2. **Reescrever o Argus todo em torno da nova stack** — rejeitado: joga fora
   trabalho funcional e testado; risco alto sem ganho de aprendizado.

## Consequências

- (+) Um único flagship prova Data/IA **e** arquitetura de sistemas.
- (+) Cada tecnologia nova tem ADR — nada entra "por checklist".
- (−) O repo fica maior e com duas "gerações" de estrutura coexistindo;
  mitigado pela Capability Status table e por este ADR.
- (−) Java/Angular/Istio ficam como skeleton até um ciclo dedicado; a table
  deixa isso explícito.
