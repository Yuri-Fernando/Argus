# 🦉 Argus

### Python · Databricks · Snowflake · dbt · MLflow · LangGraph · Agno · MCP · RAG · Kubernetes · Terraform

## Status

🟡 **Em desenvolvimento** — pipeline completo e funcional em ambiente local. Deploy em nuvem real (Azure, Databricks, Snowflake, Power BI) ainda não executado.

Plataforma full-stack de Dados & IA para Customer Intelligence corporativo, cobrindo de ponta a ponta as competências técnicas mais recorrentes em vagas de Engenharia de Dados, Governança/MDM, MLOps e Engenharia de IA (LLMs, agentes, RAG, MCP). O projeto é inspirado em requisitos reais de mercado, mas não representa nenhuma empresa específica — é uma plataforma simulada, construída como peça de portfólio.

A partir da **v2 (arquitetura enterprise)**, o Argus também é usado como **referência de arquitetura de software e system design corporativo**: DDD com bounded contexts, microsserviços poliglotas (Java/Spring + Python/FastAPI), arquitetura orientada a eventos (Kafka + RabbitMQ), service mesh, ADRs/RFCs e documentação explícita de system design. *Customer Intelligence* passa a ser o **domínio de negócio** usado para demonstrar essa arquitetura. Ver **[Arquitetura Enterprise (v2)](#arquitetura-enterprise-v2)** e a tabela de status abaixo. Nada é anunciado como pronto antes de existir — cada capacidade tem status ✅ / 🚧 / 🗺️.

🇺🇸 Read in English: [README-en.md](README-en.md)

---

## Sobre o Projeto

Empresas de médio e grande porte costumam manter dados de clientes espalhados por sistemas independentes — loja online, CRM, marketing, atendimento, pagamentos — cada um com sua própria definição de quem é o cliente. O resultado típico é cadastros duplicados, métricas inconsistentes entre times, ausência de um critério confiável para identificar churn ou clientes de alto valor, e agentes de IA respondendo perguntas sem uma base de dados confiável para se apoiar.

O Argus resolve esse problema de ponta a ponta: unifica as fontes em um **Golden Record** governado, expõe métricas consistentes através de um semantic layer replicado em três implementações, e disponibiliza esse dado tanto para humanos (Power BI) quanto para agentes de IA (LangGraph, Agno, MCP), sempre com aprovação humana para qualquer ação de impacto sobre o cliente. Cada componente do projeto resolve um problema técnico específico e nomeado — a inclusão de uma ferramenta nunca é decidida apenas por ela constar em uma lista de tecnologias desejadas.

### Por que Argus

Na mitologia grega, Argos Panoptes — "o que tudo vê" — era um gigante com cem olhos, designado por Hera para vigiar Io. Sua característica definidora era nunca dormir por completo: enquanto parte dos olhos descansava, os demais permaneciam abertos, garantindo vigilância contínua sem um único ponto cego.

O nome reflete o princípio central da arquitetura: qualidade de dado, integridade de matching (MDM), drift de modelo, ações de agentes e conformidade fiscal são monitorados em paralelo, por processos automatizados e contínuos — não por verificação manual pontual. Ao final do mito, Hera transfere os cem olhos de Argos para a cauda do pavão; a vigilância, uma vez estabelecida, permanece visível na estrutura do sistema.

---

## Objetivo

- Consolidar cadastros de cliente fragmentados em um Golden Record único, através de Entity Resolution determinístico, probabilístico e por ML;
- Garantir qualidade de dado mensurável e rastreável, com quarentena real de registros que violam regras de negócio;
- Expor métricas governadas através de três implementações de semantic layer (dbt/MetricFlow, Databricks Unity Catalog Metric Views, Snowflake Semantic Views), com paridade testada entre elas;
- Treinar, avaliar e explicar modelos de Machine Learning (churn, segmentação, próxima-melhor-ação) com rastreabilidade completa via MLflow;
- Construir agentes de IA (LangGraph e Agno) que consultam esse dado governado através de MCP (Model Context Protocol), com aprovação humana obrigatória para decisões consequentes;
- Implementar RAG em duas variantes — Snowflake Cortex Search na nuvem e uma stack local-first (Crawl4AI, Docling, ChromaDB/FAISS) — incluindo um pipeline real de VLM (Vision-Language Model);
- Sustentar tudo isso com a disciplina de engenharia correspondente: IaC (Terraform e Kubernetes), CI/CD, observabilidade, governança e segurança de IA generativa.

---

## Arquitetura

```text
Fontes de dados (Olist real + CRM/Marketing/Suporte/Web/Financeiro/Fiscal sintéticos + documentos)
   │
   ▼
Ingestão (Azure Data Factory / Event Hubs)
   │
   ▼
Azure Data Lake Storage Gen2  (landing → raw → bronze → silver → gold)
   │
   ▼
Azure Databricks Lakehouse  (Delta Lake · PySpark · Unity Catalog · MLflow)
   │
   ├──► Data Quality (engine próprio, 10 tipos de regra + quarentena)
   ├──► MDM / Entity Resolution → Golden Record
   └──► Camada Gold (modelo dimensional)
              │
              ▼
        Snowflake (Enterprise DWH)
              │
   ┌──────────┴──────────┐
   ▼                      ▼
Semantic Layer         Snowflake Cortex
(dbt/MetricFlow ·      (Analyst · Search ·
UC Metric Views ·       Agents · AI Functions)
Snowflake Semantic
Views)
   │                      │
   ▼                      ▼
Power BI              Camada MCP / Agentic AI
                       (Customer · Data Quality ·
                        Recommendation · Monitoring ·
                        Knowledge Ingestion · Fiscal)
                              │
                              ▼
                     Aprovação humana obrigatória
                     para toda ação consequente
```

Diagrama completo (Mermaid), detalhamento camada a camada e o racional de cada ferramenta: **[ARCHITECTURE.md](ARCHITECTURE.md)**.

### Databricks e Snowflake

As duas plataformas não são redundantes — cada uma responde por uma camada distinta:

| Camada | Responsabilidade |
|---|---|
| Azure Data Lake (ADLS Gen2) | Armazenamento bruto, barato e durável — landing zone |
| Azure Databricks | Lakehouse: ingestão, ETL/ELT, PySpark, Delta Lake, Bronze/Silver/Gold, MDM, feature engineering, treino de modelos, MLflow |
| Snowflake | Enterprise Data Warehouse: modelo dimensional governado, Semantic Views, Cortex (Analyst/Search/Agents/AI Functions) como camada de serving de IA |
| Power BI | BI corporativo tradicional para consumo humano |
| MCP e agentes | Interface agentic — o mesmo dado governado, consultado em linguagem natural por agentes de IA |

Análise completa do trade-off: [`docs/decisions/ADR-002-lakehouse-vs-warehouse.md`](docs/decisions/ADR-002-lakehouse-vs-warehouse.md).

---

## Funcionamento

1. **Ingestão** — dataset real (Olist, aproximadamente 100 mil pedidos) combinado a seis geradores sintéticos determinísticos (CRM, Marketing, Suporte, Web Events, Financeiro, Fiscal/Tributário), cada um injetando problemas de dado controlados e nomeados — duplicatas, e-mails ausentes, telefones malformados, inconsistências de NCM/CFOP/CST — para que o pipeline de DQ/MDM tenha algo real a resolver.
2. **Bronze → Silver** — padronização, cast de tipos e deduplicação estrutural.
3. **Data Quality** — engine próprio em pandas com dez tipos de regra fechados (`not_null`, `unique`, `valid_email`, `valid_phone`, `valid_date`, `referential_integrity`, `range_check`, `duplicate_rate`, `schema_check`, `freshness`), quarentena de linhas que violam regras críticas e relatório em JSON/Markdown.
4. **MDM / Entity Resolution** — matching determinístico, fuzzy (Jaro-Winkler) e por ML, com sobrevivência de campo (survivorship) auditável e benchmark contra ground truth conhecido.
5. **Gold / Semantic Layer** — modelo dimensional consumido por três implementações de semantic layer em paralelo, com teste automatizado de paridade de métrica entre elas.
6. **Machine Learning** — features de RFM, engajamento e suporte alimentando um modelo de churn (comparação entre três algoritmos, campeão registrado no MLflow), segmentação por KMeans, próxima-melhor-ação via bandit epsilon-greedy, e explicabilidade real via SHAP.
7. **Agentes e MCP** — seis agentes (orquestrador conversacional, qualidade de dado, recomendação, monitoramento, ingestão de conhecimento, causa-raiz fiscal) consultam o dado governado através de sete grupos de ferramentas MCP; toda ação consequente passa por uma fila de aprovação humana.
8. **RAG** — duas implementações paralelas (Snowflake Cortex Search na nuvem; Crawl4AI, Docling e ChromaDB/FAISS localmente), incluindo um pipeline de VLM para documentos escaneados.
9. **Observabilidade e governança** — OpenTelemetry, Prometheus/Grafana, Unity Catalog, guardrails de IA generativa e conformidade com a LGPD.

---

## Inteligência e Modelagem

| Categoria | Implementação |
|---|---|
| ML supervisionado | Comparação entre três modelos de churn (Logistic Regression, Random Forest, Gradient Boosting) — campeão: Logistic Regression, ROC-AUC 0,882, registrado no MLflow Model Registry |
| ML não supervisionado | Segmentação KMeans em cinco segmentos, com distribuição balanceada (6%–28,4%) |
| ML por reforço | Bandit epsilon-greedy para próxima-melhor-ação, sujeito à mesma fila de aprovação humana das recomendações baseadas em regra |
| Explicabilidade | SHAP aplicado ao modelo campeão já registrado, sem retreino apenas para fins de explicação |
| Agentes de IA | Orquestrador conversacional (LangGraph, com gate de aprovação humana) e agente de ingestão de conhecimento (Agno, seleção autônoma de ferramenta por fonte) |
| MCP (Model Context Protocol) | Servidor customizado com 12 ferramentas, sem lógica de negócio na camada de registro |
| A2A (Agent2Agent) | Protocolo padronizado de comunicação entre agentes, com `AgentCard` de descoberta e endpoint JSON-RPC |
| LLM Gateway multi-provider | Roteador único (`complete(prompt, task_type)`) para Azure OpenAI, OpenAI, DeepSeek, Gemini e AWS Bedrock, com registro de custo e latência por tipo de tarefa |
| SLM (Small Language Model) | Classificador local TF-IDF + Logistic Regression para causa-raiz de problemas de qualidade de dado, sem custo de LLM nem round-trip de rede — 75–80% de acurácia held-out |
| VLM (Vision-Language Model) | Pipeline real (Docling + IBM Granite-Docling-258M) para documentos escaneados — detalhes e resultado do teste na seção abaixo |
| RAG | Duas implementações completas: Snowflake Cortex Search e Crawl4AI + Docling + ChromaDB/FAISS |

---

## Extensão Fiscal e Pipeline VLM

Um módulo dedicado simula itens de nota fiscal sob o modelo de tributação proposto pela Reforma Tributária brasileira (IBS, CBS e Imposto Seletivo), com discrepâncias controladas — código NCM inválido, combinação CST/CFOP inconsistente, alíquota fora da faixa esperada — e um agente próprio de diagnóstico de causa-raiz. O módulo também fornece o caso de uso para o pipeline de VLM da plataforma: documentos fiscais escaneados, gerados sinteticamente, processados de ponta a ponta por um modelo de visão-linguagem local.

O pipeline VLM (Docling com o modelo IBM Granite-Docling-258M) executa integralmente sem erros e carrega um modelo real, sem exigir credencial paga. No teste realizado, a extração apresentou baixa qualidade, com repetição de trechos de texto. O pipeline de OCR tradicional do mesmo framework, por comparação, extraiu o mesmo documento com alta precisão. O resultado é consistente com uma limitação conhecida de modelos VLM de propósito geral e pequena escala em tarefas de extração de texto plano e estruturado. Avaliação técnica completa em [`docs/decisions/ADR-015-fiscal-tax-reform-extension.md`](docs/decisions/ADR-015-fiscal-tax-reform-extension.md).

---

## Tecnologias

| Categoria | Stack |
|---|---|
| Linguagem | Python 3.10+ |
| Ingestão / Lake | Azure Data Factory, Azure Data Lake Storage Gen2, Azure Databricks, Delta Lake, PySpark, Unity Catalog |
| Data Quality | Engine próprio (pandas); Great Expectations (GX Core) documentado como alternativa |
| MDM | Jellyfish (Jaro-Winkler), scikit-learn, NetworkX |
| Warehouse / Semantic Layer | Snowflake, dbt / MetricFlow, Unity Catalog Metric Views |
| BI | Power BI, Power BI MCP |
| ML / MLOps | scikit-learn, XGBoost, SHAP, MLflow |
| GenAI / Agentes | LangGraph, Agno, Azure OpenAI, OpenAI, Gemini, DeepSeek, AWS Bedrock, MCP, A2A |
| RAG local | Crawl4AI, Docling (texto e VLM), ChromaDB, FAISS |
| API | FastAPI, GraphQL |
| Infraestrutura | Terraform (Azure/Databricks/Snowflake), Kubernetes, Docker, GitHub Actions |
| Observabilidade | OpenTelemetry, Prometheus, Grafana |
| Governança | Unity Catalog, Microsoft Purview, LGPD |

Racional de cada escolha de ferramenta: [ARCHITECTURE.md §3](ARCHITECTURE.md#3-tech-stack-rationale).

---

## Resultados

Métricas medidas em execução local contra os dados sintéticos e o dataset Olist:

| Métrica | Valor |
|---|---|
| Qualidade de dado — score geral da plataforma | 99,83% |
| Qualidade de dado — domínio fiscal isolado | 99,64%, com 10/10 discrepâncias injetadas corretamente quarentenadas |
| MDM / Entity Resolution | Recall 1,0000 · Precision 0,9687 · F1 0,9841 contra benchmark com ground truth conhecido |
| Churn (ML) | ROC-AUC 0,882 (Logistic Regression, campeão entre três modelos comparados) |
| Segmentação | 5 segmentos, sem colapso |
| Classificador de causa-raiz (DQ) | 75% acurácia held-out, F1 macro 0,739 |
| Classificador de discrepância fiscal | 80% acurácia held-out, F1 macro 0,822 |
| Terraform | 20/20 módulos validados (`terraform validate`) nos ambientes dev/staging/prod |

---

## Aplicações

O projeto cobre, na prática, os requisitos técnicos mais recorrentes em vagas de:

- Engenharia de Dados — ETL/ELT, Lakehouse, Data Warehouse, modelagem dimensional;
- Governança de Dados / MDM — Golden Record, lineage, RBAC, LGPD;
- Data Science / MLOps — feature engineering, MLflow, SHAP, ciclo de vida de modelo;
- Engenharia de IA / GenAI — LLMs multi-provider, agentes autônomos, RAG, MCP, A2A, VLM, human-in-the-loop;
- Contextos regulados — a extensão fiscal demonstra a mesma disciplina de rastreabilidade e governança avaliada em vagas de dados fiscais e contábeis.

---

## Arquitetura Enterprise (v2)

Camada adicionada como **evolução aditiva** — o pipeline de dados
Azure/Databricks/Snowflake existente permanece intacto (ADR-016). O objetivo
é demonstrar arquitetura de software distribuída usando o domínio de negócio
já modelado.

### Princípios

| Princípio | Onde | ADR |
|---|---|---|
| **Domain-Driven Design** — bounded contexts, camadas domain/application/infrastructure/interfaces | `services/` | ADR-014, ADR-018 |
| **Stack poliglota** — Java/Spring nos serviços de negócio, Python/FastAPI em Dados/ML/IA | `services/` | ADR-017 |
| **Event-Driven Architecture** — Kafka (event streaming) + RabbitMQ (work queue), papéis distintos | `platform/messaging/` | ADR-019 |
| **Database-per-service** + consistência eventual entre contexts | `services/` | ADR-020, ADR-022 |
| **REST na borda · GraphQL no BFF · gRPC interno** | `docs/system-design/05` | ADR-021 |
| **Cloud-native** — EKS + Istio (mTLS, retry, canary) + Argo CD (GitOps) | `terraform/modules/aws/`, `platform/service-mesh/` | ADR-023, ADR-024 |
| **Data Mesh** — Data Products por domínio (owner, SLA, contrato, lineage) | RFC-001 | — |
| **MLOps com gate** — robustez adversarial (ThemisAI) obrigatória antes de produção | `ml-platform/adversarial-evaluation/` | RFC-002 |

### Status das capacidades

| Capacidade | Status | Evidência |
|---|---|---|
| DDD / hexagonal (camadas) | ✅ Implementado | `services/inference-service/` (20 testes) |
| Design Patterns (Strategy · Factory · Adapter · Ports&Adapters) | ✅ Implementado | `services/inference-service/src/.../infrastructure/` |
| FastAPI (Python) — porta REST | ✅ Implementado | `inference-service` roda com `uvicorn` |
| **gRPC** (Protocol Buffers) — porta interna quente (ADR-021) | ✅ Implementado | `services/inference-service/proto/inference.proto` + `grpc_server.py`; teste garante REST e gRPC dão o mesmo score |
| **Transactional Outbox** (ADR-022) | ✅ Implementado | `infrastructure/outbox.py` (SQLite) + `relay()` idempotente; teste de recuperação pós-crash |
| Event-Driven Architecture | ✅ Implementado | `platform/messaging/` — `InMemoryBus` + demo + testes; `KafkaBus`/`RabbitBus` com `consume_batch` |
| **Kafka/RabbitMQ com broker real** | ✅ testado | `make up-enterprise` (Redpanda + RabbitMQ + Postgres via Docker) → `make test-integration` verde: roundtrip Kafka, roundtrip RabbitMQ e fluxo predição→outbox→relay→Kafka. Também no job `integration` do CI. |
| **Read models CQRS** (ADR-022, RFC-002) | ✅ Implementado | `platform/read_models/` — `ChurnReadModel` + teste de equivalência replay ↔ incremental |
| Schema Registry (JSON Schema por tópico) | ✅ Implementado | `platform/messaging/schemas/` + `ValidatingBus` |
| **Data Mesh — Data Product contracts** (RFC-001) | ✅ Implementado | `data-platform/data-products/*/contract.yaml` (4 domínios) + `validate.py` + testes |
| BDD (Gherkin PT-BR) | ✅ Implementado | `tests/bdd/` — behave, 2 cenários |
| System Design docs (requisitos, capacidade, escala, HA, consistência, cache, DR, trade-offs) | ✅ Implementado | `docs/system-design/00..14` |
| ADRs de arquitetura enterprise | ✅ Implementado | `docs/decisions/ADR-016..024` (total: 24 ADRs) |
| RFCs (Data Mesh, ML Platform) | ✅ Implementado | `docs/rfc/` |
| C4 model (context / container / component) | ✅ Implementado | `docs/c4/` (Mermaid) |
| Standards (código, API, observabilidade) | ✅ Implementado | `docs/standards/` |
| Robustness gate de MLOps (integra ThemisAI) | ✅ Implementado | `ml-platform/adversarial-evaluation/` (5 testes) |
| **CI da camada v2** | ✅ Implementado | `.github/workflows/enterprise-v2.yml` — job `unit` (pytest+behave+node) + job `integration` (brokers reais) |
| Terraform AWS (VPC · EKS · MSK · observability) | 🗺️ Referência | `terraform/modules/aws/` — `terraform fmt` passa; `apply` não executado |
| Java / Spring Boot (`customer-service`) | ✅ Compila e testa | `services/customer-service/` — `mvn verify` com JDK 17: **5 testes JUnit** (`CustomerAggregateTest`) verdes. Maven wrapper (`./mvnw`) incluído; job `java-customer-service` no CI. |
| Service Mesh (Istio — mTLS, canary) | 🗺️ Referência | `platform/service-mesh/istio/` — manifests válidos, requer cluster |
| Angular Microfrontends (`web-shell`) | 🗺️ Skeleton | `apps/web-shell/` — configs Module Federation válidas; `ng build` não roda no ambiente |
| Argo CD / GitOps | 🗺️ Planejado | ADR-024 |

### Evolução de versões

`v1.x` Plataforma de Dados & IA (Lakehouse, MDM, ML, RAG, agentes, governança) →
`v2.0` DDD + `inference-service` (REST) + messaging + system design + ADRs 16–24 →
`v2.1` gRPC + transactional outbox + read models CQRS + Data Product contracts + CI da camada v2 →
`v2.1` (planejado) Kafka/RabbitMQ com broker + `customer-service` compilando →
`v2.2` (planejado) EKS + Istio + Argo CD.

---

## Roadmap

Construído em 16 sprints ao longo de 8 fases (Fundação → Engenharia de Dados → MDM → Warehouse/BI → ML → GenAI/RAG → Agentic/MCP → Hardening Enterprise), com épicos, stories e critérios de aceite. Detalhamento completo: **[ROADMAP.md](ROADMAP.md)**.

### Próximos passos

- `terraform apply` contra contas reais de Azure/Databricks/Snowflake — hoje apenas `validate`/`plan` são executados, por decisão deliberada de não gerar custo de nuvem sem aprovação explícita;
- Configuração de chaves de LLM reais (Azure OpenAI, OpenAI, Gemini, DeepSeek) para que os agentes produzam raciocínio de LLM real;
- Download do dataset Olist real via `make download-olist` (requer login Kaggle interativo; a plataforma já degrada corretamente sem ele);
- Conexão de Power BI e Databricks Genie reais — os artefatos (semantic model, DAX, DDL) já estão prontos;
- Publicação de uma demo hospedada e um vídeo curto de walkthrough.

---

## Como rodar localmente

```bash
git clone https://github.com/Yuri-Fernando/Argus.git
cd Argus
cp .env.example .env
make up        # docker-compose: MinIO, Postgres, MLflow, GX
make seed      # gera os datasets sintéticos e tenta baixar o Olist
make test      # testes de unidade e dados
```

Os componentes de nuvem (Azure, Databricks, Snowflake, Power BI, Cortex) são opcionais, configuráveis via `terraform/environments/dev`, e não são necessários para explorar o pipeline local. Guia completo: [docs/deployment.md](docs/deployment.md).

---

## Estrutura do repositório

```text
agents/            6 agentes (orquestrador, qualidade, recomendação, monitoramento,
                    ingestão de conhecimento, causa-raiz fiscal) + MCP/A2A + LLM Gateway
api/                FastAPI + GraphQL
apps/              [v2] Angular web-shell + microfrontends (skeleton)
data/               Geradores sintéticos + documentos (RAG)
data-platform/     [v2] data-products/ — contratos de Data Product (Data Mesh, RFC-001)
data_quality/       Engine de regras + quarentena
dashboard/          Dashboard Streamlit
dbt/                Semantic layer (dbt/MetricFlow)
docs/decisions/     ADRs — Architecture Decision Records
governance/         LGPD, segurança de IA, políticas
k8s/                Manifests Kubernetes
lakehouse/          Pipeline Bronze → Silver
mcp/                Servidor MCP + ferramentas
mdm/                Entity Resolution + Golden Record
ml/                 Features, churn, segmentação, reforço, explicabilidade
ml-platform/       [v2] adversarial-evaluation — robustness gate de MLOps (ThemisAI)
notebooks/          9 notebooks executáveis, um por camada
platform/          [v2] messaging (Kafka/RabbitMQ + schemas) + read_models (CQRS) + service-mesh (Istio)
powerbi/            Semantic model, DAX, dashboard
rag/                RAG cloud (Cortex) + local-first (Crawl4AI/Docling/Chroma/FAISS)
services/          [v2] Serviços de domínio DDD: inference-service (Python, ✅) +
                    customer-service (Java/Spring, skeleton)
snowflake/          DDL, semantic views, local runner (DuckDB)
terraform/          IaC — Azure/Databricks/Snowflake (v1) + AWS modules EKS/MSK (v2, referência)
tests/              Pirâmide de testes (unit/integration/data/ml/ai) + bdd/ (behave)
docs/system-design/ [v2] 15 docs de system design
docs/c4/           [v2] C4 model (Mermaid)
docs/rfc/          [v2] RFC-001 Data Mesh, RFC-002 ML Platform
docs/standards/    [v2] padrões de código / API / observabilidade
```

Árvore completa e anotada: [ARCHITECTURE.md §20](ARCHITECTURE.md#20-repository-structure).

---

## Documentação

| Documento | Conteúdo |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Arquitetura completa, diagramas, racional de cada ferramenta |
| [ROADMAP.md](ROADMAP.md) | Sprints, épicos, stories, critérios de aceite |
| [CHANGELOG.md](CHANGELOG.md) | Histórico de versões |
| [DATA_MODEL.md](DATA_MODEL.md) | Datasets, schemas, modelo dimensional |
| [docs/decisions/](docs/decisions/) | ADRs — 24 decisões de arquitetura documentadas (16–24 = camada enterprise v2) |
| [docs/system-design/](docs/system-design/) | System design: requisitos, capacidade, escala, HA, consistência, cache, segurança, observabilidade, DR, trade-offs |
| [docs/c4/](docs/c4/) | C4 model — context / container / component (Mermaid) |
| [docs/rfc/](docs/rfc/) | RFC-001 Data Mesh · RFC-002 ML Platform |
| [docs/standards/](docs/standards/) | Padrões de código, API design e observabilidade |
| [governance/](governance/) | Governança, LGPD, segurança de IA |
| [services/inference-service/](services/inference-service/) | Serviço DDD de referência (Strategy/Factory/Adapter) |

---

## Projetos Relacionados

Argus é o **flagship de arquitetura** de um portfólio de projetos
especializados. Cada um prova um recorte; o Argus mostra como eles se
encaixam.

```text
                         ENTERPRISE AI SYSTEMS
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
    AI / ML / DATA           SOFTWARE ARCH.           CLOUD PLATFORM
          │                        │                        │
   ML · RAG · Agents        DDD · EDA · CQRS         AWS · K8s · IaC
   Adversarial ML           Kafka · RabbitMQ         Service Mesh · GitOps
   Data Eng · MLOps         Java · Python            Observability
          │                        │                        │
          └────────────────────────┼────────────────────────┘
                                   │
                                 ARGUS
```

| Projeto | Papel no portfólio | Ligação com o Argus |
|---|---|---|
| **ThemisAI** | AI Governance + AI Security + **Adversarial ML** (`core/adversarial_ml/`) | Gera o `ModelSecurityReport` que o `ml-platform/adversarial-evaluation/` do Argus usa como *production robustness gate* |
| **Enterprise Automation** | Cloud Platform Engineering (Terraform · EKS · GitOps · policy-as-code) | É a plataforma de infraestrutura+entrega sobre a qual o Argus roda (`docs/platform-consumers.md` de lá) |
| **RetentIQ** | Event-Driven SaaS (Kafka · RabbitMQ · CQRS · Next.js) | Mesma stack event-driven do `platform/messaging/` do Argus, aplicada a um produto SaaS |
| **VisionGuard** | Computer Vision (YOLO + ResNet) + **Adversarial Vision** (FGSM/PGD/patch) | Caso de uso de visão da trilha de AI Security; alimenta o mesmo gate |
| **Self-Evolving RL-PID-AGV** | RL + Controle + **Robust/Adversarial RL** | Caso de uso de RL da trilha de AI Security |
| **Credit Score (AWS)** | ML serverless (Lambda/SageMaker) + **Adversarial tabular** | Caso de uso tabular da trilha de AI Security |
| **Churn Intelligence** | ML + RAG + streaming distribuído + **Robustness Testing** | Caso de uso de robustez tabular empresarial |
| **AI Network Optimizer** | Telecom (O-RAN/xApp) · microsserviços gRPC · K8s + HPA | Referência de microsserviços cloud-native num domínio diferente |

---

## Autor

**Yuri Fernando Dubbern**

Engenheiro de Dados · AI Engineer · Data Science · MLOps · Automação · Sistemas Embarcados · Pesquisa e Desenvolvimento

[LinkedIn](https://www.linkedin.com/in/yuridubbern) · [GitHub](https://github.com/Yuri-Fernando) · [Lattes](http://lattes.cnpq.br/7151392692642166) · [Linktree](https://linktr.ee/yuri.f.dubbern)

---

## Licença

MIT — ver [LICENSE](LICENSE). Todo dado é público/anonimizado (Olist) ou sintético; nenhum dado pessoal real é utilizado neste repositório.
