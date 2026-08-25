# 🧠 Enterprise Customer Intelligence Platform

### Python · Databricks · Snowflake · dbt · MLflow · LangGraph · Agno · MCP · RAG · Kubernetes · Terraform

## Status

🟡 **Em desenvolvimento — pipeline completo funcional localmente, com deploy real em nuvem (Azure/Databricks/Snowflake/Power BI) ainda pendente**

Plataforma full-stack de Dados & IA para **Customer Intelligence corporativo**, construída para cobrir de ponta a ponta as competências mais pedidas em vagas reais de Engenharia de Dados, MDM/Governança, MLOps e Engenharia de IA (LLMs, agentes, RAG, MCP) — inspirada em requisitos de vagas reais do mercado, mas **não representa nenhuma empresa real**. É uma plataforma simulada, construída inteiramente como peça de portfólio.

🇺🇸 Read in English: [README-en.md](README-en.md)

---

# Sobre o Projeto

Uma empresa de e-commerce de médio porte tem dados de clientes espalhados por sistemas independentes — loja online, CRM, marketing, atendimento, pagamentos — cada um com sua própria visão de quem é o cliente. Isso gera cadastros duplicados, métricas inconsistentes ("Receita" significa uma coisa em cada dashboard), nenhuma forma confiável de detectar churn/fraude/clientes VIP, agentes de IA respondendo sem embasamento confiável, e dashboards manuais que nunca batem entre si.

Este projeto é a resposta ponta a ponta a esse problema: uma arquitetura coerente onde **cada tecnologia existe para resolver um problema real e nomeado** — não para inflar uma lista de skills. Essa disciplina ("Article I — No Invention") é uma regra formal seguida em toda a base de código, documentada em cada decisão de arquitetura (ver `docs/decisions/`).

---

# 🎯 Objetivo

- Construir um **Golden Record** único e governado de cliente a partir de fontes fragmentadas e propositalmente sujas (MDM/Entity Resolution);
- Garantir **qualidade de dado mensurável e rastreável** (Data Quality Engine com quarentena real);
- Expor **métricas governadas** através de três implementações de semantic layer (dbt/MetricFlow, Databricks Unity Catalog Metric Views, Snowflake Semantic Views) — uma métrica, uma definição, três motores;
- Treinar e explicar modelos de **Machine Learning** (churn, segmentação, recomendação por reforço) com rastreabilidade completa via MLflow;
- Construir **agentes de IA** (LangGraph + Agno) que consultam esse dado governado via **MCP (Model Context Protocol)**, sempre com humano no loop para decisões consequentes;
- Demonstrar **RAG** de ponta a ponta, tanto na versão cloud (Snowflake Cortex) quanto local-first (Crawl4AI + Docling + ChromaDB/FAISS), incluindo um pipeline real de **VLM** (Vision-Language Model);
- Cobrir a disciplina de engenharia que sustenta tudo isso: IaC (Terraform + Kubernetes), CI/CD, observabilidade, governança/LGPD e segurança de IA generativa.

---

# 🏗️ Arquitetura

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
   ├──► Data Quality (engine próprio, 10 tipos de regra + quarentena real)
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

Diagrama completo (Mermaid), detalhamento camada-a-camada e o racional de cada ferramenta: **[ARCHITECTURE.md](ARCHITECTURE.md)**.

## Por que Databricks *e* Snowflake?

Não são redundantes — cada um tem uma responsabilidade clara:

| Camada | Responsabilidade |
|---|---|
| **Azure Data Lake (ADLS Gen2)** | Armazenamento bruto, barato e durável — landing zone |
| **Azure Databricks** | Lakehouse: ingestão, ETL/ELT, PySpark, Delta Lake, Bronze/Silver/Gold, MDM, feature engineering, treino de ML, MLflow |
| **Snowflake** | Enterprise Data Warehouse: modelo dimensional governado, Semantic Views, Cortex (Analyst/Search/Agents/AI Functions) como camada de **serving de IA** |
| **Power BI** | BI corporativo tradicional para humanos |
| **MCP + agentes** | Interface agentic — o mesmo dado governado, consultado em linguagem natural por IA em vez de dashboards |

Detalhamento completo do trade-off: [`docs/decisions/ADR-002-lakehouse-vs-warehouse.md`](docs/decisions/ADR-002-lakehouse-vs-warehouse.md).

---

# ⚙️ Funcionamento

1. **Ingestão** — dataset real (Olist, ~100 mil pedidos) + 6 geradores sintéticos determinísticos (CRM, Marketing, Suporte, Web Events, Financeiro, **Fiscal/Tributário**), cada um injetando problemas de dado propositais e nomeados (duplicatas, e-mails ausentes, telefones malformados, NCM/CFOP/CST inconsistentes na Reforma Tributária) para o pipeline de DQ/MDM resolver de verdade.
2. **Bronze → Silver** — padronização, cast de tipos, deduplicação estrutural.
3. **Data Quality** — engine próprio em pandas (10 tipos de regra fechados: `not_null`, `unique`, `valid_email`, `valid_phone`, `valid_date`, `referential_integrity`, `range_check`, `duplicate_rate`, `schema_check`, `freshness`), quarentena real de linhas que falham regra `hard`, relatório JSON/Markdown.
4. **MDM / Entity Resolution** — matching determinístico + fuzzy (Jaro-Winkler) + ML, sobrevivência de campo (survivorship) com trilha de auditoria, benchmark contra ground truth conhecido.
5. **Gold / Semantic Layer** — modelo dimensional consumido por três implementações de semantic layer em paralelo, com teste automatizado de paridade de métrica entre elas.
6. **ML** — features RFM/engajamento/suporte → churn (comparação de 3 modelos, campeão registrado no MLflow), segmentação (KMeans), próxima-melhor-ação (bandit epsilon-greedy), explicabilidade real via SHAP.
7. **Agentes + MCP** — 6 agentes (orquestrador conversacional, qualidade de dado, recomendação, monitoramento, ingestão de conhecimento, causa-raiz fiscal) consultam o dado governado por 7 grupos de ferramentas MCP; toda ação consequente passa por uma fila de aprovação humana.
8. **RAG** — duas implementações lado a lado (Snowflake Cortex Search na nuvem; Crawl4AI + Docling + ChromaDB/FAISS localmente), incluindo um pipeline real de VLM para documentos escaneados.
9. **Observabilidade e governança** — OpenTelemetry, Prometheus/Grafana, Unity Catalog, guardrails de IA generativa, conformidade LGPD.

---

# 🧠 Inteligência / Modelagem

| Categoria | O que foi implementado |
|---|---|
| **ML supervisionado** | Comparação de 3 modelos de churn (Logistic Regression, Random Forest, Gradient Boosting) — campeão real: **Logistic Regression, ROC-AUC 0,882**, registrado no MLflow Model Registry |
| **ML não supervisionado** | Segmentação KMeans, 5 segmentos balanceados (6%–28,4% de distribuição, sem colapso) |
| **ML por reforço** | Bandit epsilon-greedy para próxima-melhor-ação, gated pela mesma fila de aprovação humana das recomendações baseadas em regra |
| **Explicabilidade** | SHAP real (não simulado) — carrega o modelo campeão já registrado, nunca retreina só para explicar |
| **IA generativa / Agentes** | Orquestrador conversacional (LangGraph, máquina de estados com gate de aprovação humana) + Agente de Ingestão de Conhecimento (Agno, seleção autônoma de ferramenta) |
| **MCP (Model Context Protocol)** | Servidor customizado com 12 ferramentas reais, camada de registro fina sem lógica de negócio própria |
| **A2A (Agent2Agent)** | Protocolo padronizado de comunicação entre agentes (`AgentCard` de descoberta + endpoint JSON-RPC) |
| **LLM Gateway multi-provider** | Roteador único (`complete(prompt, task_type)`) para Azure OpenAI / OpenAI / DeepSeek (mesmo cliente HTTP compatível) / Gemini / AWS Bedrock — registro de custo/latência por tarefa, avaliado, não "vibes-based" |
| **SLM (Small Language Model)** | Classificador local TF-IDF + Logistic Regression para causa-raiz de problemas de qualidade de dado — zero custo de LLM, zero round-trip de rede, **75–80% de acurácia real** |
| **VLM (Vision-Language Model)** | Pipeline real (Docling + IBM Granite-Docling-258M) para documentos escaneados — testado ao vivo, com resultado documentado honestamente (ver seção abaixo) |
| **RAG** | Duas implementações completas: Snowflake Cortex Search (nuvem) e Crawl4AI + Docling + ChromaDB/FAISS (local-first, zero custo) |

---

# 💼 Extensão Fiscal / Tributária (Reforma Tributária)

Módulo dedicado simulando itens de nota fiscal sob a Reforma Tributária brasileira (IBS/CBS/Imposto Seletivo) — 100% sintético, com discrepâncias injetadas de propósito (NCM inválido, combinação CST/CFOP inconsistente, alíquota fora da faixa), um agente próprio de diagnóstico de causa-raiz, e o caso de uso real que fecha o pipeline de VLM: documentos fiscais **escaneados** gerados sinteticamente e processados pelo pipeline de visão-linguagem.

**Achado de engenharia honesto, documentado sem retoque**: o pipeline VLM roda de ponta a ponta sem erro (baixa e carrega um modelo real, sem exigir credencial paga), mas produziu saída de baixa qualidade num teste real — enquanto o OCR tradicional do mesmo framework leu o mesmo documento quase perfeitamente. Um modelo VLM pequeno de propósito geral perdendo para OCR tradicional num documento de texto plano é uma conclusão de engenharia real, registrada em [`docs/decisions/ADR-015-fiscal-tax-reform-extension.md`](docs/decisions/ADR-015-fiscal-tax-reform-extension.md) em vez de escondida atrás de um exemplo escolhido a dedo.

---

# 🛠️ Tecnologias

| Categoria | Stack |
|---|---|
| Linguagem | Python 3.10+ |
| Ingestão / Lake | Azure Data Factory, Azure Data Lake Storage Gen2, Azure Databricks, Delta Lake, PySpark, Unity Catalog |
| Data Quality | Engine próprio (pandas), Great Expectations (GX Core) documentado como alternativa |
| MDM | Jellyfish (Jaro-Winkler), scikit-learn, NetworkX (grafo de relacionamento) |
| Warehouse / Semantic Layer | Snowflake, dbt / MetricFlow, Unity Catalog Metric Views |
| BI | Power BI, Power BI MCP |
| ML / MLOps | scikit-learn, XGBoost, SHAP, MLflow |
| GenAI / Agentes | LangGraph, Agno, Azure OpenAI, OpenAI, Gemini, DeepSeek, AWS Bedrock, MCP, A2A |
| RAG local | Crawl4AI, Docling (texto + VLM), ChromaDB, FAISS |
| API | FastAPI, GraphQL |
| Infraestrutura | Terraform (Azure/Databricks/Snowflake), Kubernetes, Docker, GitHub Actions |
| Observabilidade | OpenTelemetry, Prometheus, Grafana |
| Governança | Unity Catalog, Microsoft Purview, LGPD |

Racional completo de cada escolha de ferramenta: [ARCHITECTURE.md §3](ARCHITECTURE.md#3-tech-stack-rationale).

---

# 📊 Resultados

Métricas reais, medidas em execução local contra os dados sintéticos + Olist — nenhum número estimado ou "de vitrine":

- **Qualidade de dado**: score geral da plataforma **99,83%**; domínio fiscal isolado **99,64%**, com 10/10 discrepâncias injetadas corretamente quarentenadas.
- **MDM / Entity Resolution**: **Recall 1,0000, Precision 0,9687, F1 0,9841** contra benchmark com ground truth conhecido.
- **Churn (ML)**: **ROC-AUC 0,882** (Logistic Regression, campeão entre 3 modelos comparados).
- **Segmentação**: 5 segmentos balanceados, sem colapso.
- **Classificador de causa-raiz (DQ)**: 75% acurácia held-out, F1 macro 0,739.
- **Classificador de discrepância fiscal**: 80% acurácia held-out, F1 macro 0,822.
- **Testes automatizados**: suíte de dados/integração passando de ponta a ponta (pirâmide unit/integration/data/ML/contract).
- **Terraform**: 20/20 módulos validados (`terraform validate`) nos 3 ambientes (dev/staging/prod).

---

# 🎯 Aplicações

Este projeto cobre, na prática, os requisitos técnicos mais recorrentes em vagas reais de:

- Engenharia de Dados (ETL/ELT, Lakehouse, Data Warehouse, modelagem dimensional);
- Governança de Dados / MDM (Golden Record, lineage, RBAC, LGPD);
- Data Science / MLOps (feature engineering, MLflow, SHAP, ciclo de vida de modelo);
- Engenharia de IA / GenAI (LLMs multi-provider, agentes autônomos, RAG, MCP, A2A, VLM, human-in-the-loop);
- Contextos regulados/fiscais (a extensão de Reforma Tributária demonstra a mesma disciplina de rastreabilidade e governança que uma vaga fiscal/contábil real avalia).

---

# 🔭 Visão de Longo Prazo

```text
Especificação (ARCHITECTURE.md)
   │
   ▼
Implementação local (dados sintéticos + Olist, tudo real e testado)
   │
   ▼
Deploy em nuvem real (Terraform apply · Databricks · Snowflake · Power BI)
   │
   ▼
Demo hospedada pública (dashboard Streamlit/FastAPI apontando pra um snapshot Gold)
```

---

# 🗺️ Roadmap

Construído em 16 sprints ao longo de 8 fases (Fundação → Engenharia de Dados → MDM → Warehouse/BI → ML → GenAI/RAG → Agentic/MCP → Hardening Enterprise), com épicos, stories e critérios de aceite. Detalhamento completo: **[ROADMAP.md](ROADMAP.md)**.

## Próximos Passos

- [ ] `terraform apply` real contra contas Azure/Databricks/Snowflake (hoje só `validate`/`plan` — decisão deliberada para não gerar custo de nuvem sem aprovação explícita);
- [ ] Configurar chaves de LLM reais (`AZURE_OPENAI_API_KEY` / `OPENAI_API_KEY` / `GEMINI_API_KEY` / `DEEPSEEK_API_KEY`) para os agentes gerarem raciocínio de LLM de verdade;
- [ ] Baixar o dataset Olist real via `make download-olist` (login Kaggle interativo — a plataforma já degrada graciosamente sem ele);
- [ ] Conectar Power BI e Databricks Genie reais (artefatos — semantic model, DAX, DDL — já prontos);
- [ ] Demo hospedada pública + vídeo curto de walkthrough no README.

---

# 🚀 Como rodar localmente

```bash
git clone https://github.com/Yuri-Fernando/enterprise-customer-intelligence-platform.git
cd enterprise-customer-intelligence-platform
cp .env.example .env
make up        # docker-compose: MinIO, Postgres, MLflow, GX
make seed      # gera os datasets sintéticos + tenta baixar o Olist
make test      # testes de unidade + dados
```

Os componentes de nuvem (Azure, Databricks, Snowflake, Power BI, Cortex) são opt-in via `terraform/environments/dev` e **não são necessários** para explorar o pipeline local. Guia completo: [docs/deployment.md](docs/deployment.md).

---

# 📂 Estrutura do repositório

```text
agents/            6 agentes (orquestrador, qualidade, recomendação, monitoramento,
                    ingestão de conhecimento, causa-raiz fiscal) + MCP/A2A + LLM Gateway
api/                FastAPI + GraphQL
data/               Geradores sintéticos + documentos (RAG)
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
notebooks/          9 notebooks executáveis, um por camada
powerbi/            Semantic model, DAX, dashboard
rag/                RAG cloud (Cortex) + local-first (Crawl4AI/Docling/Chroma/FAISS)
snowflake/          DDL, semantic views, local runner (DuckDB)
terraform/          IaC — Azure/Databricks/Snowflake, 3 ambientes
tests/              Pirâmide de testes (unit/integration/data/ml/ai)
```

Árvore completa e anotada: [ARCHITECTURE.md §20](ARCHITECTURE.md#20-repository-structure).

---

# 📚 Índice de documentação

| Doc | Conteúdo |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Arquitetura completa, diagramas, racional de cada ferramenta |
| [ROADMAP.md](ROADMAP.md) | Sprints, épicos, stories, critérios de aceite |
| [CHANGELOG.md](CHANGELOG.md) | Histórico de versões |
| [DATA_MODEL.md](DATA_MODEL.md) | Datasets, schemas, modelo dimensional |
| [docs/decisions/](docs/decisions/) | ADRs — 15 decisões de arquitetura documentadas |
| [governance/](governance/) | Governança, LGPD, segurança de IA |

---

# 👤 Autor

**Yuri Fernando Dubbern**

Engenheiro de Dados · AI Engineer · Data Science · MLOps · Automação · Sistemas Embarcados · Pesquisa e Desenvolvimento

[LinkedIn](https://www.linkedin.com/in/yuridubbern) · [GitHub](https://github.com/Yuri-Fernando) · [Lattes](http://lattes.cnpq.br/7151392692642166) · [Linktree](https://linktr.ee/yuri.f.dubbern)

---

# Licença

MIT — ver [LICENSE](LICENSE). Todo dado é público/anonimizado (Olist) ou sintético; nenhum PII real é usado neste repositório.
