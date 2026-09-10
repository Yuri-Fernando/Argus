# ADR-017 — Stack poliglota: Java/Spring nos serviços de negócio, Python/FastAPI em Dados/ML/IA

**Status:** Aceito · **Data:** 2026-09-10

## Contexto

O portfólio já tem muita evidência de Python. A vaga-referência e o mercado
de arquitetura pedem Java. Forçar uma linguagem única para toda a plataforma
seria uma decisão ideológica, não de engenharia.

## Decisão

Seleção por característica de workload:

| Workload | Linguagem | Serviços |
|---|---|---|
| Domínio de negócio / transacional / integração | **Java 17 + Spring Boot 3** | `customer-service`, `identity-service` |
| Dados, ML, IA generativa, orquestração de agentes | **Python 3.11 + FastAPI** | `inference-service`, `churn-service`, `rag-service`, `agent-orchestrator` |

Contrato entre eles: eventos Kafka (JSON Schema) + REST/gRPC. Nenhum
compartilhamento de código entre runtimes — só contratos.

## Alternativas

- **Tudo Python** — rejeitado: não demonstra a competência Java pedida; e
  serviços de domínio transacional se beneficiam do ecossistema Spring
  (Data JPA, validação, testes).
- **Tudo Java** — rejeitado: ecossistema de ML/DS/LLM é Python; reescrever
  seria custo puro.

## Consequências

- (+) Cada serviço usa a ferramenta mais forte para seu problema.
- (+) Demonstra arquitetura poliglota real (dois toolchains, duas imagens
  base, um contrato).
- (−) CI mais complexo (dois pipelines de build); dois conjuntos de
  convenções (mitigado por `docs/standards/`).
