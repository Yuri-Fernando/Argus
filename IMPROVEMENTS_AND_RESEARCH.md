# Melhorias e Pesquisa (documento interno, PT-BR)

Este documento tem dois objetivos: (1) registrar o que a pesquisa de agosto/2026 encontrou sobre o estado atual de cada tecnologia citada no design original, corrigindo suposições desatualizadas; (2) listar lacunas do design original (`rascunho.md`) que esta consolidação preencheu, e um backlog priorizado do que ainda vale agregar depois do Sprint 16.

## 1. Achados de pesquisa (agosto/2026) — correções ao design original

| Item | Suposição no `rascunho.md` | Estado real (ago/2026) | Fonte | Impacto na arquitetura |
|---|---|---|---|---|
| **Databricks Managed MCP (Genie MCP)** | Tratado como "avançado/experimental" | **GA desde o início de 2026**, dentro da iniciativa "Week of Agents". Em ago/2026, conectores MCP gerenciados já integram com o Unity AI Gateway (Beta), que por sua vez já é GA. Toda chamada de ferramenta herda as permissões do Unity Catalog do usuário automaticamente. | [Databricks blog — Announcing managed MCP servers](https://www.databricks.com/blog/announcing-managed-mcp-servers-unity-catalog-and-mosaic-ai-integration), [Databricks docs — managed MCP](https://docs.databricks.com/aws/en/generative-ai/mcp/managed-mcp) | Promovido de "experimental" para **"Production-like"** na tabela de readiness. Vira o caminho MCP primário do projeto, não o Power BI MCP. |
| **Snowflake Cortex Agents** | Tratado como recurso novo/em evolução, sem status GA claro | **GA em 4 de novembro de 2025.** Em abr/2026, ganhou conectores MCP para sistemas externos (Jira, GitHub, Salesforce, Slack) e "Skills" para descrever workflows em linguagem natural. | [Snowflake blog — Cortex Sense](https://www.snowflake.com/en/blog/enterprise-ai-agents-grounded-context/) | Cortex Agents tratado como **core**, não como extensão enterprise opcional. |
| **Snowflake Semantic Views** | Descritas como a abstração recomendada, sem data de maturidade | Consulta SQL padrão sobre Semantic Views atingiu **GA em 2 de março de 2026**; são agora a abordagem recomendada para o Cortex Analyst. | [Atlan — Snowflake Semantic Views 2026 Guide](https://atlan.com/know/snowflake/snowflake-semantic-views/), [Snowflake docs — Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst) | Confirma a Semantic View como implementação primária do semantic layer para o Cortex (ver [ADR-005](docs/decisions/ADR-005-semantic-layer.md)). |
| **Cortex AI Guardrails** | Não mencionado no design original | **GA em maio de 2026**, cobre Snowflake Intelligence e Cortex Agents — relevante para deploy com dados regulados. | [Flexera — Snowflake Intelligence 101](https://www.flexera.com/blog/finops/snowflake-intelligence/) | Motivou o [ADR-007](docs/decisions/ADR-007-ai-guardrails.md) (lacuna de segurança de IA do design original). |
| **Power BI MCP (remoto + local)** | Já apontado como "Preview" no design original — suposição correta | Confirmado: **ainda em Public Preview em meados de 2026** (lançado no Ignite, nov/2025). Contratos de ferramenta, autenticação e preços podem mudar antes do GA. | [Microsoft Learn — Power BI MCP overview](https://learn.microsoft.com/en-us/power-bi/developer/mcp/mcp-servers-overview) | Mantido como integração explicitamente experimental — a cautela original estava correta, agora com data-limite confirmada. |
| **Unity Catalog Metric Views** | **Não existia / não mencionado** no design original | Atingiu **GA em abril de 2026**; Databricks está open-sourcing a implementação na Apache Spark. Consumível via SQL, notebooks, dashboards, Genie Agents e alertas. | [Databricks docs — Metric Views](https://docs.databricks.com/gcp/en/business-semantics/metric-views/) | **Adição nova** ao projeto — terceira implementação de semantic layer (ver [ADR-005](docs/decisions/ADR-005-semantic-layer.md)), não presente em nenhuma versão do rascunho. |
| **dbt Semantic Layer / MetricFlow** | Tratado como componente maduro, sem detalhe de licenciamento | MetricFlow foi **open-sourced sob Apache 2.0** no final de 2025; entrou no Apache Incubator como "Apache Ossie" (Open Semantic Interchange) em jun/2026, com conversor dbt já mesclado. | [dbt Labs blog — Open source MetricFlow](https://www.getdbt.com/blog/open-source-metricflow-governed-metrics) | Reforça a escolha de MetricFlow como implementação portátil/open-source do semantic layer. |
| **Databricks Asset Bundles (DABs)** | Não mencionado no design original | GA desde 2024; **renomeado para "Declarative Automation Bundles" em 16/mar/2026** (sigla DABs mantida por afeto). Recebeu suporte a vector search endpoints (mai/2026) e templates customizados (abr/2026). | [Databricks blog — GA announcement](https://www.databricks.com/blog/announcing-general-availability-databricks-asset-bundles) | **Adição nova** — usado para deploy declarativo de jobs Databricks (Sprint 2), evitando agendamento manual de notebooks. |
| **Great Expectations (GX Core)** | Citado genericamente como "Great Expectations" | A versão atual é **GX Core 1.0+** (breaking changes desde ago/2024), com Expectations totalmente tipadas e integração de IDE. | [Great Expectations — GX Core 1.0](https://greatexpectations.io/blog/introducing-gx-core-1-0/) | Especificado corretamente como "GX Core" nesta consolidação, evitando código de exemplo baseado na API antiga (pré-1.0). |
| **Snowflake Terraform provider** | Só menciona `Snowflake-Labs/snowflake` | Existem hoje **dois providers**: `Snowflake-Labs/snowflake` (v1, com recursos ainda marcados preview dentro do provider) e o mais novo **`snowflakedb/snowflake`**, mantido oficialmente. | [Terraform Registry — snowflakedb/snowflake](https://registry.terraform.io/providers/snowflakedb/snowflake/latest/docs) | Motivou o [ADR-008](docs/decisions/ADR-008-terraform-providers.md) — estratégia de provider dupla, por recurso. |

## 2. Lacunas do design original preenchidas nesta consolidação

Nenhuma destas aparece em nenhuma das três iterações do `rascunho.md`:

1. **Segurança de IA generativa** (prompt injection, escopo mínimo de ferramentas MCP, guardrails) — [ADR-007](docs/decisions/ADR-007-ai-guardrails.md), [governance/security.md](governance/security.md).
2. **Ground truth verificável para o benchmark de MDM** — o design original descrevia entity resolution conceitualmente, mas nunca especificava como medir precisão/recall contra uma resposta certa conhecida. Implementado em `data/synthetic/generators/crm.py` (arquivo `*_ground_truth.csv`) + Sprint 4/5 do roadmap.
3. **Reprodutibilidade determinística dos dados sintéticos** (seed fixa) — sem isso, nenhuma métrica de DQ/MDM/ML seria comparável entre execuções.
4. **Trilha de auditoria de survivorship** no Golden Record (qual fonte venceu qual campo, e por quê) — necessária para responsabilização LGPD, ausente no design original.
5. **Teste automatizado de paridade de métricas** entre as três implementações do semantic layer — sem isso, "uma métrica, uma definição" era só uma frase no design, não um fato verificável.
6. **Pirâmide de testes formal** (unit/integration/data/ML/contrato) — o design original nunca detalhou estratégia de teste além de "dbt tests" e "unit tests" genéricos.
7. **Gate de aprovação humana explícito e testável** — o design original mencionava "human-in-the-loop" como conceito, mas não como mecanismo (fila de aprovação, log de decisão) — ver [ADR-006](docs/decisions/ADR-006-human-in-the-loop.md).
8. **SLA/SLO por camada** (freshness máxima, score de DQ mínimo, latência de agente) — ausente; agora definido em `docs/runbooks/slo.md` (a criar no Sprint 16).
9. **Estratégia de Disaster Recovery / backup** — completamente ausente nas três iterações.
10. **Link e script de download do dataset real** — o design original descrevia o Olist conceitualmente, mas nunca deixou pronto um comando executável para obtê-lo; corrigido em [DATA_MODEL.md §1](DATA_MODEL.md#1-datasets--how-to-get-them) + `ingestion/olist/download.py`.

## 3. Backlog priorizado pós-Sprint 16

Ordenado por relação custo/impacto para portfólio:

| # | Item | Por quê vale a pena |
|---|---|---|
| 1 | **Demo hospedada** (Streamlit/FastAPI + deploy gratuito) apontando para um snapshot estático dos dados Gold | Recrutador consegue interagir sem precisar de credenciais de nuvem — maior taxa de conversão de "olhei o repo" para "impressionado" |
| 2 | **Vídeo curto (3-5 min) de walkthrough** no README | A maioria dos recrutadores não vai rodar `make seed`; um vídeo reduz o atrito a zero |
| 3 | **Data contracts** entre fontes (JSON Schema versionado + teste de contrato no CI) | Demonstra maturidade de engenharia além do ETL básico; tema crescente em times de dados sênior |
| 4 | **Databricks Metric Views ↔ Genie**, demo dedicada perguntando a mesma coisa por Genie vs. Cortex Analyst vs. Power BI MCP lado a lado | É literalmente o "AI/BI vs. BI tradicional" que o design original queria mostrar, agora com as três pernas GA/testáveis |
| 5 | **Automação de guardrails de custo (FinOps)** — alerta automático se o custo diário ultrapassar um teto, com desligamento automático de recursos de nuvem | Mostra maturidade operacional, não só técnica |
| 6 | **Extensão Neo4j** do grafo de clientes (hoje NetworkX apenas) | Valioso se uma vaga específica pedir grafo/Neo4j; não é core |
| 7 | **CDC real (Debezium ou Databricks Delta CDF)** em vez de Streams/Tasks simulados para a sincronização Databricks→Snowflake | Mais realista para o caso de uso enterprise, mas adiciona complexidade operacional significativa — avaliar depois que o MVP estiver estável |

## 4. Integração dos requisitos do add2.txt (mercado de trabalho)

`add2.txt` é um trecho de requisitos extraído de uma vaga-alvo real, listando: Crawl4AI, bancos vetoriais (ChromaDB/FAISS) + RAG avançado, cultura de MLOps (experimentação/versionamento/publicação), múltiplos LLMs (OpenAI/Gemini/DeepSeek), memória de agente conversacional (curto/longo prazo, rastreável), frameworks de agente modernos (LangChain/Agno), extração inteligente (Crawl4AI + Docling), ML supervisionado/não supervisionado/por reforço, MLOps para ciclo de vida de modelo, e otimização de LLM (quantização/fine-tuning). Esta seção documenta onde cada item foi integrado e por quê — seguindo o mesmo princípio "cada ferramenta resolve um problema nomeado" (ARCHITECTURE.md §1) que rege o resto do projeto, em vez de simplesmente adicionar itens a uma lista de tecnologias.

### 4.1 O que foi adicionado e onde

| Requisito do add2.txt | Onde foi integrado | Por quê ali (não noutro lugar) |
|---|---|---|
| Crawl4AI (web scraping) | [`rag/local_stack/crawler.py`](rag/local_stack/crawler.py) | Equivalente local-first ao `AI_PARSE_DOCUMENT`/ingestão web do Snowflake — resolve exatamente o problema que o projeto já tinha (RAG sem crédito Snowflake), não um caso de uso novo inventado ([ADR-011](docs/decisions/ADR-011-local-rag-stack.md)) |
| ChromaDB / FAISS | [`rag/local_stack/vector_store.py`](rag/local_stack/vector_store.py), reaproveitado por [`agents/memory/long_term.py`](agents/memory/long_term.py) | Um único store vetorial serve tanto RAG de documentos quanto memória de agente — evita duplicar a mesma abstração duas vezes |
| RAG avançado (conectando agentes a dados corporativos) | [`agents/knowledge_ingestion/agent.py`](agents/knowledge_ingestion/agent.py) orquestra o pipeline ponta a ponta | O Knowledge Ingestion Agent é o elo que liga extração (Crawl4AI/Docling) → índice vetorial → agentes consumidores |
| Docling (parsing de documentos complexos) | [`rag/local_stack/document_parser.py`](rag/local_stack/document_parser.py) | Mesma lógica do Crawl4AI: equivalente local ao `AI_PARSE_DOCUMENT`/`AI_EXTRACT` |
| Cultura de MLOps (experimentação/versionamento/publicação) | [`versioning/experimentation_pipeline.md`](versioning/experimentation_pipeline.md) (novo), complementando [`versioning/model_versioning.md`](versioning/model_versioning.md) já existente | O ciclo de vida de modelo já existia (MLflow + `model_versioning.md`); faltava nomear explicitamente que a mesma disciplina se aplica a comparações de LLM/RAG, não só a modelos de ML clássico |
| Múltiplos LLMs (OpenAI/Gemini/DeepSeek) com avaliação de trade-off | [`agents/llm_gateway/`](agents/llm_gateway/) (`router.py` + `models.yaml`) | Um roteador único (`complete(prompt, task_type)`) evita acoplar cada agente a um provedor; DeepSeek/OpenAI reaproveitam o mesmo cliente HTTP compatível com o formato OpenAI, sem SDK extra ([ADR-012](docs/decisions/ADR-012-llm-gateway-multimodel.md)) |
| Memória de agente (curto/longo prazo, rastreável) | [`agents/memory/`](agents/memory/) (`short_term.py` + `long_term.py`) | Curto prazo por thread (efêmero); longo prazo por cliente, construído sobre o mesmo `VectorStore` do RAG, com atribuição obrigatória a uma interação de origem (mesma disciplina do survivorship log) ([ADR-013](docs/decisions/ADR-013-agent-memory.md)) |
| LangChain e Agno (frameworks de agente) | [`agents/knowledge_ingestion/agent.py`](agents/knowledge_ingestion/agent.py) construído com **Agno** | O `agents/orchestrator/` já existente usa LangGraph e não foi tocado; Agno entra em um agente com responsabilidade genuinamente diferente (seleção autônoma de ferramenta), evitando duplicação — ver a seção "LangChain vs. Agno vs. LangGraph" do [ADR-011](docs/decisions/ADR-011-local-rag-stack.md) |
| ML por reforço | [`ml/reinforcement/next_best_action.py`](ml/reinforcement/next_best_action.py) | Bandit epsilon-greedy escolhendo a mesma ação de retenção que `agents/recommendation/` já modela por regras — rotulado explicitamente como EXTENSÃO, não MVP core, e gated pelo mesmo `approval_queue.py` (ADR-006) |
| MLOps para automação do ciclo de vida de modelos | Já coberto por `mlflow/` + `model_versioning.md`; reforçado por `versioning/experimentation_pipeline.md` | Evitar duplicar conteúdo — apenas nomeado explicitamente como pipeline único, cross-linkado |
| Otimização de LLM (quantização, fine-tuning) | Documentado como item de backlog em [`agents/llm_gateway/README.md`](agents/llm_gateway/README.md) e nesta seção (§4.3) | Implementar agora seria desproporcional ao escopo de portfólio; documentado com alvo concreto (classificador local quantizado substituindo a chamada de categorização do Data Quality Agent) em vez de implementado às pressas ou ignorado |

### 4.2 Achados de pesquisa (agosto/2026) — maturidade das ferramentas mais novas do stack

Diferente da maioria das ferramentas já presentes neste projeto (Databricks, Snowflake, dbt — todas com anos de maturidade enterprise), Crawl4AI e Agno são bibliotecas mais recentes. Honestidade sobre isso importa para uma escolha de portfólio — a tabela abaixo documenta o que a pesquisa encontrou:

| Ferramenta | Estrelas GitHub (jul/2026) | Última release | Status de manutenção |
|---|---|---|---|
| **Crawl4AI** | ~71.000+ | v0.9.2 (patch de manutenção) | Repositório trending #1 no GitHub; mantido ativamente por `unclecode` e comunidade; licença Apache 2.0 |
| **Agno** (ex-Phidata) | ~40.900 | v2.6.20 (final de jun/2026) | Rebrand de Phidata para Agno em jan/2025; agora inclui AgentOS (runtime FastAPI de produção); desenvolvimento ativo |
| **Docling** (IBM) | ~37.000+ | 100+ releases desde ago/2025 | Doado à Linux Foundation (Agentic AI Foundation) em 2026; lançou Granite-Docling-258M (VLM) e um Operator OpenShift com a Red Hat — sinal de investimento institucional contínuo |
| **ChromaDB** | maduro para prototipagem | — | Consenso da comunidade em 2026: excelente para desenvolvimento local (setup em ~90s), mas **não recomendado além de ~1-5M vetores** — tratado neste projeto explicitamente como ferramenta de prototipagem/dev, não produção (ver trade-off table em `rag/local_stack/README.md`) |

Conclusão prática: todas as quatro ferramentas têm sinais de manutenção ativa e adoção real em 2026, o que justifica usá-las — mas nenhuma tem o histórico de maturidade enterprise de Databricks/Snowflake, e por isso o projeto as posiciona onde essa maturidade não é crítica (desenvolvimento local, não o caminho de produção primário, que continua sendo Snowflake Cortex).

### 4.3 Backlog: otimização de LLM (quantização/fine-tuning)

Não implementado nesta consolidação — alvo concreto documentado para uma extensão futura: substituir a chamada LLM de classificação de categoria de causa-raiz do Data Quality Agent (hoje roteada para `azure-gpt-4o-mini` via `agents/llm_gateway/models.yaml`) por um classificador local pequeno (ex: `distilbert`), fine-tuned sobre categorias de DQ rotuladas e quantizado (INT8, via `onnxruntime` ou `bitsandbytes`) para inferência em CPU — eliminando custo de chamada LLM e round-trip de rede para uma tarefa de classificação de conjunto fechado que não precisa de um LLM de propósito geral. Ver [`agents/llm_gateway/README.md`](agents/llm_gateway/README.md).
