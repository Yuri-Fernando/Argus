# 🦉 Argus

### Python · Databricks · Snowflake · dbt · MLflow · LangGraph · Agno · MCP · RAG · Kubernetes · Terraform

## Status

🟡 **In development** — full pipeline functional in local environment. Real cloud deployment (Azure, Databricks, Snowflake, Power BI) not yet executed.

Full-stack Data & AI platform for enterprise customer intelligence, covering end to end the technical competencies most commonly required in Data Engineering, Data Governance/MDM, MLOps and AI Engineering (LLMs, agents, RAG, MCP) roles. The project is inspired by real market requirements but does not represent any specific company — it is a simulated platform, built as a portfolio piece.

🇧🇷 Leia em português: [README.md](README.md)

---

## About

Mid-size and large companies typically keep customer data scattered across independent systems — online store, CRM, marketing, support, payments — each with its own definition of who the customer is. The usual outcome is duplicated records, metrics that disagree across teams, no reliable way to identify churn or high-value customers, and AI agents answering questions without a trustworthy data foundation to ground them.

Argus addresses this end to end: it unifies these sources into a governed **Golden Record**, exposes consistent metrics through a semantic layer implemented three separate ways, and serves that data to both humans (Power BI) and AI agents (LangGraph, Agno, MCP) — with mandatory human approval for any action with customer impact. Every component solves a specific, named technical problem; a tool is never included solely because it appears on a target job description.

### Why Argus

In Greek mythology, Argus Panoptes — "the all-seeing" — was a giant with a hundred eyes, set by Hera to guard Io. His defining trait was that he never slept entirely: while some eyes rested, the rest stayed open, giving continuous watch with no single blind spot.

The name reflects the platform's core design principle: data quality, MDM matching integrity, model drift, agent actions and fiscal compliance are all monitored in parallel, by continuous automated processes rather than periodic manual checks. At the end of the myth, Hera transfers Argus's hundred eyes to the peacock's tail — vigilance, once established, remains visible in the structure of the system.

---

## Objectives

- Consolidate fragmented customer records into a single Golden Record via deterministic, probabilistic and ML-based entity resolution;
- Guarantee measurable, traceable data quality, with real quarantine for records that violate business rules;
- Expose governed metrics through three parallel semantic layer implementations (dbt/MetricFlow, Databricks Unity Catalog Metric Views, Snowflake Semantic Views), with tested parity between them;
- Train, evaluate and explain ML models (churn, segmentation, next-best-action) with full traceability via MLflow;
- Build AI agents (LangGraph and Agno) that query this governed data through MCP (Model Context Protocol), with mandatory human approval for consequential decisions;
- Implement RAG in two variants — Snowflake Cortex Search in the cloud and a local-first stack (Crawl4AI, Docling, ChromaDB/FAISS) — including a real VLM (Vision-Language Model) pipeline;
- Support all of this with the corresponding engineering discipline: IaC (Terraform and Kubernetes), CI/CD, observability, governance and generative AI security.

---

## Architecture

```text
Data sources (real Olist + synthetic CRM/Marketing/Support/Web/Finance/Fiscal + documents)
   │
   ▼
Ingestion (Azure Data Factory / Event Hubs)
   │
   ▼
Azure Data Lake Storage Gen2  (landing → raw → bronze → silver → gold)
   │
   ▼
Azure Databricks Lakehouse  (Delta Lake · PySpark · Unity Catalog · MLflow)
   │
   ├──► Data Quality (custom engine, 10 rule types + quarantine)
   ├──► MDM / Entity Resolution → Golden Record
   └──► Gold layer (dimensional model)
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
Power BI              MCP / Agentic AI layer
                       (Customer · Data Quality ·
                        Recommendation · Monitoring ·
                        Knowledge Ingestion · Fiscal)
                              │
                              ▼
                     Mandatory human approval
                     for every consequential action
```

Full layer-by-layer breakdown, diagrams and tool rationale: **[ARCHITECTURE.md](ARCHITECTURE.md)**.

### Databricks and Snowflake

The two platforms are not redundant — each owns a distinct layer:

| Layer | Owns |
|---|---|
| Azure Data Lake (ADLS Gen2) | Raw, cheap, durable storage — landing zone |
| Azure Databricks | Lakehouse: ingestion, ETL/ELT, PySpark, Delta Lake, Bronze/Silver/Gold, MDM, feature engineering, model training, MLflow |
| Snowflake | Enterprise Data Warehouse: governed dimensional model, Semantic Views, Cortex (Analyst/Search/Agents/AI Functions) as the AI serving layer |
| Power BI | Traditional enterprise BI for human consumption |
| MCP and agents | Agentic interface — the same governed data, queried in natural language by AI agents |

Full trade-off analysis: [`docs/decisions/ADR-002-lakehouse-vs-warehouse.md`](docs/decisions/ADR-002-lakehouse-vs-warehouse.md).

---

## How it works

1. **Ingestion** — the real Olist dataset (~100k orders) combined with six deterministic synthetic generators (CRM, Marketing, Support, Web Events, Finance, Fiscal/Tax) — each injecting controlled, named data problems (duplicates, missing emails, malformed phone numbers, NCM/CFOP/CST inconsistencies) so the DQ/MDM pipeline has something real to solve.
2. **Bronze → Silver** — standardization, type casting, structural deduplication.
3. **Data Quality** — a custom pandas engine with ten closed rule types (`not_null`, `unique`, `valid_email`, `valid_phone`, `valid_date`, `referential_integrity`, `range_check`, `duplicate_rate`, `schema_check`, `freshness`), real quarantine for rows that violate a hard rule, and a JSON/Markdown report.
4. **MDM / Entity Resolution** — deterministic, fuzzy (Jaro-Winkler) and ML-based matching, with an auditable survivorship trail and a benchmark against known ground truth.
5. **Gold / Semantic Layer** — a dimensional model consumed by three parallel semantic layer implementations, with automated metric-parity testing between them.
6. **Machine Learning** — RFM, engagement and support features feeding a churn model (three algorithms compared, champion registered in MLflow), KMeans segmentation, epsilon-greedy bandit for next-best-action, and real SHAP-based explainability.
7. **Agents and MCP** — six agents (conversational orchestrator, data quality, recommendation, monitoring, knowledge ingestion, fiscal root-cause) query the governed data through seven MCP tool groups; every consequential action goes through a human approval queue.
8. **RAG** — two parallel implementations (Snowflake Cortex Search in the cloud; Crawl4AI, Docling and ChromaDB/FAISS locally), including a VLM pipeline for scanned documents.
9. **Observability and governance** — OpenTelemetry, Prometheus/Grafana, Unity Catalog, generative AI guardrails, and LGPD compliance.

---

## Intelligence and Modeling

| Category | Implementation |
|---|---|
| Supervised ML | Three churn models compared (Logistic Regression, Random Forest, Gradient Boosting) — champion: Logistic Regression, ROC-AUC 0.882, registered in the MLflow Model Registry |
| Unsupervised ML | KMeans segmentation into five balanced segments (6%–28.4% distribution) |
| Reinforcement learning | Epsilon-greedy bandit for next-best-action, subject to the same human approval queue as rule-based recommendations |
| Explainability | SHAP applied to the already-registered champion model, with no retraining solely for explanation |
| AI agents | Conversational orchestrator (LangGraph, with a human-approval gate) and knowledge ingestion agent (Agno, autonomous tool selection per source) |
| MCP (Model Context Protocol) | Custom server with 12 tools; the registration layer carries no business logic |
| A2A (Agent2Agent) | Standardized inter-agent communication protocol, with a discovery `AgentCard` and a JSON-RPC endpoint |
| Multi-provider LLM Gateway | A single router (`complete(prompt, task_type)`) for Azure OpenAI, OpenAI, DeepSeek, Gemini and AWS Bedrock, with cost/latency tracking per task type |
| SLM (Small Language Model) | Local TF-IDF + Logistic Regression classifier for data-quality root-cause classification — no LLM cost, no network round-trip, 75–80% held-out accuracy |
| VLM (Vision-Language Model) | Real pipeline (Docling + IBM Granite-Docling-258M) for scanned documents — details and test result below |
| RAG | Two full implementations: Snowflake Cortex Search and Crawl4AI + Docling + ChromaDB/FAISS |

---

## Fiscal Extension and VLM Pipeline

A dedicated module simulates invoice line items under the Brazilian tax-reform model (IBS, CBS and Imposto Seletivo), with controlled discrepancies — invalid NCM code, inconsistent CST/CFOP combination, out-of-range tax rate — and its own root-cause diagnosis agent. The module also provides the platform's VLM use case: synthetically generated scanned fiscal documents, processed end to end by a local vision-language model.

The VLM pipeline (Docling with the IBM Granite-Docling-258M model) runs end to end without errors and loads a real model with no paid credential required. In the test performed, extraction quality was low, with repeated text segments. The same framework's traditional OCR pipeline, by comparison, extracted the same document with high accuracy. The result is consistent with a known limitation of small, general-purpose VLMs on plain, structured text extraction tasks. Full technical write-up: [`docs/decisions/ADR-015-fiscal-tax-reform-extension.md`](docs/decisions/ADR-015-fiscal-tax-reform-extension.md).

---

## Tech Stack

| Category | Stack |
|---|---|
| Language | Python 3.10+ |
| Ingestion / Lake | Azure Data Factory, Azure Data Lake Storage Gen2, Azure Databricks, Delta Lake, PySpark, Unity Catalog |
| Data Quality | Custom pandas engine; Great Expectations (GX Core) documented as an alternative |
| MDM | Jellyfish (Jaro-Winkler), scikit-learn, NetworkX |
| Warehouse / Semantic Layer | Snowflake, dbt / MetricFlow, Unity Catalog Metric Views |
| BI | Power BI, Power BI MCP |
| ML / MLOps | scikit-learn, XGBoost, SHAP, MLflow |
| GenAI / Agents | LangGraph, Agno, Azure OpenAI, OpenAI, Gemini, DeepSeek, AWS Bedrock, MCP, A2A |
| Local RAG | Crawl4AI, Docling (text and VLM), ChromaDB, FAISS |
| API | FastAPI, GraphQL |
| Infrastructure | Terraform (Azure/Databricks/Snowflake), Kubernetes, Docker, GitHub Actions |
| Observability | OpenTelemetry, Prometheus, Grafana |
| Governance | Unity Catalog, Microsoft Purview, LGPD |

Full rationale per tool: [ARCHITECTURE.md §3](ARCHITECTURE.md#3-tech-stack-rationale).

---

## Results

Metrics measured in local execution against the synthetic datasets and the Olist dataset:

| Metric | Value |
|---|---|
| Data quality — overall platform score | 99.83% |
| Data quality — fiscal domain (isolated) | 99.64%, with 10/10 injected discrepancies correctly quarantined |
| MDM / Entity Resolution | Recall 1.0000 · Precision 0.9687 · F1 0.9841 against a known ground-truth benchmark |
| Churn (ML) | ROC-AUC 0.882 (Logistic Regression, champion among three compared models) |
| Segmentation | 5 segments, no collapse |
| DQ root-cause classifier | 75% held-out accuracy, macro F1 0.739 |
| Fiscal discrepancy classifier | 80% held-out accuracy, macro F1 0.822 |
| Terraform | 20/20 modules validated (`terraform validate`) across dev/staging/prod |

---

## Applications

The project covers, in practice, the technical requirements most commonly seen in:

- Data Engineering — ETL/ELT, Lakehouse, Data Warehouse, dimensional modeling;
- Data Governance / MDM — Golden Record, lineage, RBAC, LGPD;
- Data Science / MLOps — feature engineering, MLflow, SHAP, model lifecycle;
- AI Engineering / GenAI — multi-provider LLMs, autonomous agents, RAG, MCP, A2A, VLM, human-in-the-loop;
- Regulated contexts — the fiscal extension demonstrates the same traceability and governance discipline evaluated in tax/accounting data roles.

---

## Roadmap

Built across 16 sprints over 8 phases (Foundation → Data Engineering → MDM → Warehouse/BI → ML → GenAI/RAG → Agentic/MCP → Enterprise hardening), with epics, stories and acceptance criteria. Full breakdown: **[ROADMAP.md](ROADMAP.md)**.

### Next steps

- `terraform apply` against real Azure/Databricks/Snowflake accounts — today only `validate`/`plan` run, a deliberate decision to avoid cloud cost without explicit approval;
- Configuring real LLM keys (Azure OpenAI, OpenAI, Gemini, DeepSeek) so agents produce real LLM reasoning;
- Downloading the real Olist dataset via `make download-olist` (requires interactive Kaggle login; the platform already degrades correctly without it);
- Connecting real Power BI and Databricks Genie — the artifacts (semantic model, DAX, DDL) are already in place;
- Publishing a hosted demo and a short walkthrough video.

---

## Getting Started

```bash
git clone https://github.com/Yuri-Fernando/Argus.git
cd Argus
cp .env.example .env
make up        # docker-compose: MinIO, Postgres, MLflow, GX
make seed      # generates synthetic datasets and attempts to download Olist
make test      # unit + data tests
```

Cloud components (Azure, Databricks, Snowflake, Power BI, Cortex) are optional, configured via `terraform/environments/dev`, and are not required to explore the local pipeline. Full guide: [docs/deployment.md](docs/deployment.md).

---

## Repository Structure

```text
agents/            6 agents (orchestrator, quality, recommendation, monitoring,
                    knowledge ingestion, fiscal root-cause) + MCP/A2A + LLM Gateway
api/                FastAPI + GraphQL
data/               Synthetic generators + documents (RAG)
data_quality/       Rule engine + quarantine
dashboard/          Streamlit dashboard
dbt/                Semantic layer (dbt/MetricFlow)
docs/decisions/     ADRs — Architecture Decision Records
governance/         LGPD, AI security, policies
k8s/                Kubernetes manifests
lakehouse/          Bronze → Silver pipeline
mcp/                MCP server + tools
mdm/                Entity Resolution + Golden Record
ml/                 Features, churn, segmentation, reinforcement, explainability
notebooks/          9 executable notebooks, one per layer
powerbi/            Semantic model, DAX, dashboard
rag/                Cloud RAG (Cortex) + local-first (Crawl4AI/Docling/Chroma/FAISS)
snowflake/          DDL, semantic views, local runner (DuckDB)
terraform/          IaC — Azure/Databricks/Snowflake, 3 environments
tests/              Test pyramid (unit/integration/data/ml/ai)
```

Full annotated tree: [ARCHITECTURE.md §20](ARCHITECTURE.md#20-repository-structure).

---

## Documentation Index

| Doc | Content |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Full architecture, diagrams, tool rationale |
| [ROADMAP.md](ROADMAP.md) | Sprints, epics, stories, acceptance criteria |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [DATA_MODEL.md](DATA_MODEL.md) | Datasets, schemas, dimensional model |
| [docs/decisions/](docs/decisions/) | ADRs — 15 documented architecture decisions |
| [governance/](governance/) | Governance, LGPD, AI security |

---

## Author

**Yuri Fernando Dubbern**

Data Engineer · AI Engineer · Data Science · MLOps · Automation · Embedded Systems · Research & Development

[LinkedIn](https://www.linkedin.com/in/yuridubbern) · [GitHub](https://github.com/Yuri-Fernando) · [Lattes](http://lattes.cnpq.br/7151392692642166) · [Linktree](https://linktr.ee/yuri.f.dubbern)

---

## License

MIT — see [LICENSE](LICENSE). All data is either public/anonymized (Olist) or synthetically generated; no real personal data is used anywhere in this repository.
