# ADR-014 — Arquitetura Hexagonal (Ports & Adapters): formalizando um padrão já implícito

**Status:** Aceito
**Data:** 2026-08-21

## Contexto

O projeto já cresceu, ao longo dos Sprints 1-16, uma separação de fato entre **núcleo de domínio**
e **adaptadores de protocolo**, sem que isso jamais tivesse sido nomeado ou documentado como uma
decisão arquitetural deliberada:

- `mdm/`, `ml/`, `graph/` e `data_quality/` implementam a lógica de negócio da plataforma
  (entity resolution, Golden Record, features/modelos de churn e segmentação, grafo de clientes,
  validação de qualidade) e **nunca importam** `mcp/`, `api/` ou (agora) `agents/a2a/` — foi
  verificado diretamente nesta consolidação: `api/services/customer_service.py` e
  `mcp/tools/customer.py` leem os artefatos parquet que `mdm/`/`ml/`/`graph/` produzem em
  `data/mdm/`, `data/ml/`, `data/graph/` — a dependência aponta sempre do adaptador para o
  núcleo, nunca o contrário.
- `mcp/tools/*.py` expõe exatamente essas capacidades como ferramentas MCP tipadas
  (ADR-004) — chamada de ferramenta MCP.
- `api/services/*.py` expõe as mesmas capacidades como rotas REST/JSON (`api/README.md`) —
  chamada HTTP.
- `agents/a2a/server.py` (Sprint 17, esta consolidação) agora expõe um subconjunto dessas
  mesmas capacidades — via os quatro agentes de `agents/` — como tasks do protocolo A2A.

`tributario.txt`/`add2.txt` (segunda rodada de requisitos de mercado, ver
[IMPROVEMENTS_AND_RESEARCH.md §5](../../IMPROVEMENTS_AND_RESEARCH.md#5-integração-dos-requisitos-de-tributariotxt--complemento-de-add2txt-agosto2026))
pedem explicitamente "Arquitetura Hexagonal (Ports & Adapters)" e "baixo acoplamento/alta
coesão" como competências demonstráveis. Isso não é um padrão novo a impor sobre o código — é o
padrão que a estrutura de pastas já seguia de fato desde o Sprint 13 (mcp/) e o Sprint 17 (api/,
já entregue por um agente irmão nesta mesma consolidação). O gap real era a ausência de um
registro formal — sem ele, "isso já é hexagonal" era uma afirmação não verificável, não um fato
documentado.

## Decisão

Formalizar, sem refatorar nenhum código que já funciona, a seguinte leitura do projeto em termos
de Ports & Adapters:

### O núcleo (domain core / "hexágono interno")

`mdm/`, `ml/`, `graph/`, `data_quality/` — implementam as regras de negócio da plataforma
(ARCHITECTURE.md §1) e não conhecem nenhum protocolo de transporte. Cada um produz artefatos
(parquet em `data/*/`, modelos registrados no MLflow, relatórios GX) que são o **port de saída**
implícito do núcleo — a interface pela qual qualquer adaptador pode ler o resultado do domínio,
sem que o domínio precise saber quem está lendo.

### Os adaptadores (três, paralelos, expondo a mesma capacidade)

| Adaptador | Protocolo | Onde |
|---|---|---|
| MCP tool-call | Model Context Protocol (JSON-RPC sobre stdio/SSE) | `mcp/tools/*.py` + `mcp/server/server.py` |
| REST | HTTP/JSON | `api/services/*.py` + `api/routes/*.py` |
| A2A task | Agent2Agent (JSON sobre HTTP) | `agents/a2a/server.py` (Sprint 17) |

Os três adaptadores expõem **a mesma capacidade de domínio** — golden record, churn, duplicatas
MDM, métricas de plataforma — por três protocolos diferentes, exatamente o padrão Ports & Adapters
descreve: múltiplos adaptadores diferentes ao redor do mesmo núcleo, sem que o núcleo precise
mudar quando um quarto adaptador for adicionado (nem quando os três atuais mudarem de forma
independente). Prova concreta desta consolidação: `agents/a2a/server.py` foi adicionado sem
tocar em nenhuma linha de `mdm/`, `ml/`, `graph/` ou `data_quality/` — apenas envolveu os quatro
agentes de `agents/` (que já liam do núcleo via `mcp/tools/`), exatamente o comportamento que a
regra "núcleo nunca importa adaptador" prediz.

### Regra que torna isso verificável, não apenas retórico

`mdm/`, `ml/`, `graph/`, `data_quality/` **nunca** devem importar `mcp/`, `api/` ou
`agents/a2a/` (nem `agents/orchestrator|quality|recommendation|monitoring/`, que também são
consumidores, não parte do núcleo). Um import nessa direção proibida é, por definição, uma
violação desta ADR e deveria ser pego em code review — não há hoje um lint/CI gate automatizado
para isso (documentado como item de acompanhamento, não implementado nesta consolidação, para não
inflar o escopo do Sprint 17 além do que foi pedido).

## Alternativas consideradas

1. **Não formalizar nada — deixar como "estrutura de pastas orgânica"** — rejeitado: sem o nome e
   a regra explícita, a alegação "o projeto usa Ports & Adapters" (pedida por `tributario.txt`)
   não seria uma decisão auditável, só uma coincidência de organização de diretórios.
2. **Refatorar para introduzir interfaces Python explícitas (ABC/Protocol) representando os
   ports** — rejeitado para esta consolidação: os três adaptadores já convergem para o mesmo
   formato de dado (dicts com o mesmo schema, documentado em cada `mcp/tools/*.py` docstring) sem
   precisar de uma interface formal em código; introduzir isso agora seria refatoração de código
   que já funciona apenas para "caber num nome bonito", o oposto do que ADR-011 e outras ADRs
   deste projeto já rejeitaram pelo mesmo motivo.
3. **Tratar `agents/a2a/` como parte do núcleo em vez de um adaptador** — rejeitado: `agents/a2a/`
   não implementa nenhuma regra de negócio nova, apenas serializa/desserializa chamadas para os
   quatro agentes existentes (que por sua vez chamam `mcp/tools/`) — é estruturalmente idêntico a
   um adaptador, não a domínio.

## Consequências

- Positivas: a alegação de arquitetura hexagonal agora é verificável por uma regra de import
  simples, não apenas descritiva; `agents/a2a/server.py` (Sprint 17) já nasceu seguindo a regra,
  servindo como prova de que o padrão é seguível na prática, não apenas teórico; um quarto
  adaptador futuro (ex: gRPC, GraphQL) teria exatamente o mesmo caminho de implementação que os
  três atuais — ler os artefatos do núcleo, nunca modificá-los.
- Negativas: a regra depende de disciplina de code review até que um gate de CI a automatize (item
  de acompanhamento, não implementado agora); os três adaptadores hoje duplicam parcialmente a
  forma de acessar os dados do núcleo (cada um lê os mesmos parquets/relatórios com sua própria
  função de leitura) em vez de compartilhar uma camada de repositório única — aceitável no estágio
  atual do projeto (cada adaptador ainda é pequeno o suficiente para isso não ser dor real), mas
  um candidato razoável de consolidação se um quinto adaptador for adicionado no futuro.
