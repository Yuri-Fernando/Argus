# ADR-011 — Stack de RAG local-first (Crawl4AI + Docling + ChromaDB/FAISS) e LangChain/Agno vs. LangGraph

**Status:** Aceito
**Data:** 2026-08-11

## Contexto

O pipeline de RAG descrito em [ARCHITECTURE.md §14](../../ARCHITECTURE.md#14-layer-11--rag--document-intelligence) depende de `AI_PARSE_DOCUMENT`, `AI_EMBED` e Cortex Search — todos recursos pagos do Snowflake, indisponíveis sem uma conta paga provisionada. Isso já é resolvido para o restante da plataforma pelo princípio local-first ([ADR-010](ADR-010-local-first-development.md)): MinIO no lugar de ADLS, Postgres/GX/PySpark locais. O RAG, porém, ainda não tinha um caminho local equivalente — era Snowflake ou nada. Paralelamente, `add2.txt` (requisitos de vaga do mercado) pede explicitamente: "estruturar e otimizar bancos vetoriais (ChromaDB, FAISS)", "web scraping (Crawl4AI)" e "parsing de documentos complexos (Docling)".

Esses três itens não são apenas itens de lista de tecnologias — encaixam exatamente no buraco que já existia: um caminho de desenvolvimento local para RAG, simétrico ao que já existe para Lakehouse/DQ/MDM.

Separadamente, `add2.txt` também pede "frameworks modernos como LangChain e Agno" para agentes autônomos. O `agents/orchestrator/customer_intelligence_agent.py` já existe e usa **LangGraph** (Sprint 14) — não deve ser duplicado ou reescrito só para "usar mais um framework". Esta ADR também decide onde Agno entra sem redundância.

## Decisão

### RAG local-first

Adicionar `rag/local_stack/` como o **caminho de desenvolvimento local** do pipeline de RAG, espelhando estágio-a-estágio o pipeline Snowflake-nativo já documentado em `rag/README.md`:

| Estágio | Produção (Snowflake) | Local-dev (`rag/local_stack/`) |
|---|---|---|
| Ingestão | PDFs sintéticos estáticos | **Crawl4AI** (`crawler.py`) — também permite ingerir páginas web ao vivo, não só arquivos estáticos |
| Parsing | `AI_PARSE_DOCUMENT` / `AI_EXTRACT` | **Docling** (`document_parser.py`) — parsing de layout (tabelas, PDF multi-coluna) local |
| Embedding + índice | `AI_EMBED` → Cortex Search | **ChromaDB** (padrão) ou **FAISS** (alternativa documentada) via `vector_store.py` |

Cortex Search permanece o caminho de nuvem/produção — nada aqui o substitui, apenas dá ao projeto um caminho de demo/desenvolvimento sem depender de crédito Snowflake, exatamente como MinIO faz para ADLS.

**ChromaDB é o padrão**, por ergonomia de desenvolvimento local e filtragem de metadados nativa (necessária para escopar memória de longo prazo por cliente, ver [ADR-013](ADR-013-agent-memory.md)). **FAISS é a alternativa documentada** para quando a escala ultrapassa o que ChromaDB atende confortavelmente (ver tabela de trade-off em `rag/local_stack/README.md`) — a interface `VectorStore` em `vector_store.py` é comum às duas implementações, então trocar de backend é uma linha, não um redesenho.

### LangChain vs. Agno vs. LangGraph — divisão de responsabilidade, não redundância

Em vez de reescrever um agente já existente para "usar LangChain também", a decisão é: **um agente novo, com responsabilidade genuinamente diferente, construído com Agno** — o `agents/knowledge_ingestion/agent.py` ("Knowledge Ingestion Agent"). Ele decide, por fonte, se usa Crawl4AI, Docling ou um arquivo estático, e orquestra o pipeline de RAG ponta a ponta — exatamente o padrão de "agente multi-ferramenta" no qual Agno é forte (seleção de ferramenta + fluxo, não um grafo de estado explícito com gate de aprovação humana).

| Framework | Onde é usado | Por quê |
|---|---|---|
| **LangGraph** | `agents/orchestrator/customer_intelligence_agent.py` (Sprint 14, já existente) | Precisa de uma máquina de estados explícita com nós condicionais para o gate de aprovação humana (ADR-006) — LangGraph é feito para isso |
| **Agno** | `agents/knowledge_ingestion/agent.py` (novo) | Agente de ferramenta múltipla que decide autonomamente qual extrator usar (Crawl4AI vs. Docling vs. arquivo estático) — não precisa de um grafo de estado com aprovação humana, porque ingestão de conhecimento não é uma ação consequente sobre o cliente (não passa pelo `approval_queue.py`) |
| **LangChain (puro)** | Não usado como um agente separado | O que "LangChain" tipicamente supriria (chains, integração de ferramentas, memória) já é coberto por LangGraph (que é construído sobre primitivas do ecossistema LangChain) no orquestrador e por Agno no ingestion agent — adicionar uma terceira implementação de agente com LangChain puro seria redundância, não amplitude real de skill, violando ARCHITECTURE.md §1 |

## Alternativas consideradas

1. **Reescrever o Customer Intelligence Agent em Agno em vez de LangGraph** — rejeitado: o agente já implementado (Sprint 14, LangGraph) depende de um grafo de estado explícito para o gate de aprovação humana (ADR-006); trocar de framework não agregaria skill nova, só reescrita sem propósito.
2. **Usar Cortex Search também localmente via um proxy/mock** — rejeitado: um mock não demonstra a competência real de estruturar e otimizar um banco vetorial, que é justamente o que `add2.txt` pede.
3. **FAISS como padrão em vez de ChromaDB** — rejeitado para o caso de uso atual (poucas dezenas de documentos + memória por cliente): a filtragem de metadados nativa do Chroma é usada diretamente por `agents/memory/long_term.py`; FAISS é mantido como caminho documentado de escala, não descartado.
4. **Um único agente único cobrindo tanto orquestração de resposta quanto ingestão de conhecimento** — rejeitado: são responsabilidades diferentes (responder pergunta vs. decidir como alimentar a base de conhecimento) — combiná-las tornaria o grafo do orquestrador maior sem necessidade e esconderia a decisão de framework atrás de uma única classe.

## Consequências

- Positivas: o projeto agora tem um caminho de RAG 100% local e sem custo (`docker-compose up` + `make seed`, sem crédito Snowflake), simétrico ao resto da plataforma; demonstra amplitude real de skill em bancos vetoriais e frameworks de agente, sem redundância de tecnologia; a interface comum `VectorStore` evita duplicar lógica de retrieval entre RAG e memória de agente (ver ADR-013).
- Negativas: mais um par de bibliotecas (`crawl4ai`, `docling`) cuja maturidade é mais recente que o resto do stack (ChromaDB desde 2022, mas com limitações conhecidas de escala documentadas em `rag/local_stack/README.md`; Crawl4AI e Docling ambos com menos de 2 anos de histórico de release em ago/2026) — ver [IMPROVEMENTS_AND_RESEARCH.md §4](../../IMPROVEMENTS_AND_RESEARCH.md) para os achados de pesquisa sobre maturidade dessas ferramentas específicas.
