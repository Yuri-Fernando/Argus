# Roadmap

16 sprints across 8 phases. Each sprint is a real, demoable increment — never build two layers half-finished in parallel. Every sprint lists **what "done" looks like** so this can't quietly turn into an endless architecture doc.

Legend: 🟢 not started · 🟡 in progress · ✅ done — update as you go, this file is meant to be a living tracker, not just a plan.

---

## Phase 0 — Foundation

### Sprint 0 — Repo & local dev environment 🟢
**Goal:** anyone can clone the repo and have the local stack running in under 10 minutes.
- [ ] `docker-compose up` brings up MinIO, Postgres, MLflow, Prometheus, Grafana
- [ ] `make seed` downloads Olist + generates all synthetic data
- [ ] `pytest` runs (even if trivially, against `tests/data/test_no_real_pii.py`)
- [ ] CI (`ci.yml`) runs lint + tests on every PR
- **Acceptance criteria:** fresh clone → `make install && make up && make seed && make test` succeeds with zero manual steps.

### Sprint 1 — Data Lake & ingestion 🟢
**Goal:** raw data lands, untouched, in a structured lake.
- [ ] `ingestion/olist/` loads Olist CSVs into `adls/raw/olist/` (local: MinIO)
- [ ] `ingestion/api/` + synthetic generators load CRM/Marketing/Support/Web/Finance into `adls/raw/*`
- [ ] Landing → Raw promotion is idempotent (safe to re-run)
- [ ] Terraform `modules/azure/adls` provisions the real ADLS Gen2 container (cloud, optional at this stage)
- **Acceptance criteria:** `adls/raw/` contains all 6 sources with a manifest file recording row counts and ingestion timestamp.

---

## Phase 1 — Data Engineering (Lakehouse)

### Sprint 2 — Bronze & Silver (Databricks + PySpark) 🟢
**Goal:** Medallion Bronze/Silver implemented and Unity-Catalog-registered.
- [ ] `lakehouse/bronze/` — Delta tables, one notebook/job per source, minimal transform
- [ ] `lakehouse/silver/` — dedup (structural), casting, standardization, schema enforcement
- [ ] Unity Catalog: `customer_intelligence.bronze.*` / `.silver.*` registered with column comments
- [ ] Databricks Asset Bundle (`databricks/workflows/`) deploys the Bronze→Silver job declaratively
- **Acceptance criteria:** `silver.customer`, `silver.order`, `silver.web_event` etc. queryable in Databricks SQL with row counts matching raw ± dedup.

### Sprint 3 — Data Quality framework 🟢
**Goal:** the platform measures its own trustworthiness.
- [ ] GX Core suites for every Silver table (`data_quality/expectations/`)
- [ ] Checkpoints wired into the Databricks job (fail/quarantine on breach)
- [ ] `dq_score` computed per dataset + overall, published as GX Data Docs
- [ ] `data_quality.yml` CI workflow runs the suite on every PR touching `lakehouse/`
- **Acceptance criteria:** intentionally corrupting a field in the synthetic generator causes the Checkpoint to fail and the row to land in `quarantine/`.

---

## Phase 2 — MDM & Trusted Customer Data

### Sprint 4 — Entity Resolution (deterministic + fuzzy) 🟢
**Goal:** exact and near-duplicate customers are linked.
- [ ] `mdm/matching/deterministic.py` — email/phone/document_hash exact match
- [ ] `mdm/matching/fuzzy.py` — Jaro-Winkler + Levenshtein similarity scoring
- [ ] Benchmarked against `crm_customers_ground_truth.csv` (precision/recall/F1 reported)
- **Acceptance criteria:** fuzzy matcher recall ≥ 0.85 on the synthetic ground truth at a documented precision floor.

### Sprint 5 — ML-based matching + Golden Record 🟢
**Goal:** `gold.dim_customer` exists with a `master_customer_id` and full survivorship audit trail.
- [ ] `mdm/matching/ml_model.py` — Random Forest/XGBoost classifier over similarity features, tracked in MLflow
- [ ] `mdm/golden_record/` — survivorship rules (DATA_MODEL.md §4) + `survivorship_log/`
- [ ] `mdm/entity_resolution/evaluation/` — final match-quality report vs. ground truth
- **Acceptance criteria:** ML matcher F1 beats the fuzzy-only baseline from Sprint 4 on the same benchmark; every merge has a survivorship log entry.

### Sprint 6 — Customer Graph 🟢
**Goal:** relationship structure surfaces what row-by-row matching misses.
- [ ] `graph/networkx/build_graph.py` — Customer/Email/Phone/Address/Order/Product/Seller nodes
- [ ] `graph/algorithms/` — centrality, connected components, community detection
- [ ] Cross-check: does the graph flag any duplicate cluster the ML matcher missed?
- **Acceptance criteria:** at least one report (`graph/queries/duplicate_clusters.md`) showing clusters found via graph analysis alone.

---

## Phase 3 — Warehouse, Semantics & BI

### Sprint 7 — Gold dimensional model + Snowflake DWH 🟢
**Goal:** `fact_orders`/`dim_customer` etc. live in both Delta Gold and Snowflake CORE.
- [ ] `lakehouse/gold/` — dimensional model build (DATA_MODEL.md §3)
- [ ] `terraform/modules/snowflake/` provisions database/schemas/warehouse/roles
- [ ] `snowflake/tables/` DDL + Streams/Tasks for incremental Databricks→Snowflake sync
- **Acceptance criteria:** a row inserted in Databricks Gold appears in Snowflake CORE within one Task cycle, values matching exactly.

### Sprint 8 — Semantic Layer (dbt/MetricFlow + UC Metric Views + Snowflake Semantic Views) 🟢
**Goal:** one metric, one definition, in three consumable forms.
- [ ] `docs/semantic-dictionary.md` — canonical definitions (Revenue, AOV, Churn, CLV, NPS, Delivery SLA...)
- [ ] `dbt/models/marts/` + MetricFlow semantic models
- [ ] Unity Catalog Metric View equivalents
- [ ] Snowflake Semantic View equivalents
- **Acceptance criteria:** the same question ("What was Revenue last month?") returns the identical number from all three implementations — this is an actual automated test (`tests/data/test_metric_parity.py`), not a manual check.

### Sprint 9 — Power BI 🟢
**Goal:** 5 report pages live, sourced only from the semantic layer.
- [ ] `powerbi/semantic_model/` connects to Snowflake Semantic Views
- [ ] Executive Overview, Customer Intelligence, Operations, Data Quality, Platform Observability pages
- **Acceptance criteria:** every visual's tooltip/data-source trace leads back to a semantic-layer object, never a raw table.

---

## Phase 4 — Data Science / ML

### Sprint 10 — Feature engineering + Churn model 🟢
**Goal:** a tracked, explainable churn model.
- [ ] `ml/features/` — RFM, engagement, support, graph-derived features
- [ ] `ml/churn/` — Logistic Regression, Random Forest, Gradient Boosting compared on ROC-AUC/F1/PR-AUC/calibration
- [ ] `ml/explainability/` — SHAP values attached to every prediction
- [ ] MLflow Model Registry entry, promoted to `Staging`
- **Acceptance criteria:** champion model registered, its SHAP explanation demoable for at least 3 example customers.

### Sprint 11 — Segmentation 🟢
**Goal:** every customer has a segment.
- [ ] `ml/segmentation/` — KMeans over RFM/engagement, `VIP/Loyal/Potential/At Risk/Inactive`
- **Acceptance criteria:** segment distribution reported and sane (no >90%-in-one-bucket collapse).

---

## Phase 5 — GenAI / RAG

### Sprint 12 — Document Intelligence + RAG 🟢
**Goal:** the platform can answer policy questions grounded in real documents.
- [ ] `rag/parsing/` — `AI_PARSE_DOCUMENT`/`AI_EXTRACT` over the 4 synthetic policy docs
- [ ] `rag/embeddings/` + Cortex Search index
- [ ] `rag/evaluation/` — golden Q&A set, retrieval precision measured
- [ ] `rag/local_stack/` — local-first equivalent (Crawl4AI ingestion + Docling parsing + ChromaDB/FAISS index, [ADR-011](docs/decisions/ADR-011-local-rag-stack.md)) mirroring the Snowflake pipeline stage-for-stage
- [ ] `agents/knowledge_ingestion/agent.py` — Agno-based Knowledge Ingestion Agent choosing Crawl4AI vs. Docling vs. static read per source, writing into `rag/local_stack/vector_store.py`
- [ ] ChromaDB vs. FAISS retrieval precision@k compared and recorded, same golden set as the Cortex Search path
- **Acceptance criteria:** retrieval precision@3 ≥ 0.8 on the golden set.

---

## Phase 6 — Agentic AI / MCP

### Sprint 13 — Custom MCP server 🟢
**Goal:** a working MCP server exposing platform data as tools.
- [ ] `mcp/server/` — implements the tool list in ARCHITECTURE.md §15
- [ ] Connected and tested from Claude Desktop / Claude Code
- **Acceptance criteria:** `get_customer_churn(customer_id)` and `get_data_quality()` return correct live data end-to-end through MCP.

### Sprint 14 — Agents (LangGraph) + human-in-the-loop 🟢
**Goal:** the four agents from ARCHITECTURE.md §15 work and never auto-execute unsupervised.
- [ ] Customer Intelligence Agent, Data Quality Agent, Recommendation Agent, Monitoring Agent
- [ ] Human-in-the-loop approval gate on every write/recommendation action
- [ ] `agents/*/evaluation/` — golden question sets + LLM-as-judge scoring, including prompt-injection test cases
- [ ] `agents/llm_gateway/` — multi-model router (`complete(prompt, task_type)`) wired in as the LLM call path for at least one agent, with a documented cost/latency/quality comparison across Azure OpenAI/OpenAI/Gemini/DeepSeek ([ADR-012](docs/decisions/ADR-012-llm-gateway-multimodel.md))
- [ ] `agents/memory/` — short-term (per-thread) and long-term (per-customer, vector-store-backed, traceable) memory wired into the Customer Intelligence Agent ([ADR-013](docs/decisions/ADR-013-agent-memory.md))
- [ ] `ml/reinforcement/next_best_action.py` — contextual bandit extension, gated by the same approval queue as every other recommendation
- **Acceptance criteria:** the Recommendation Agent's suggestion queue requires explicit approval before any downstream action is logged as "executed."

### Sprint 15 — Databricks Managed MCP + Cortex Agents + Power BI MCP (experimental) 🟢
**Goal:** compare three ways of asking the same question.
- [ ] Databricks Genie MCP wired up (GA — production-like)
- [ ] Snowflake Cortex Agents wired up (GA — production-like), evaluated against the golden-question harness from ARCHITECTURE.md §12
- [ ] Power BI MCP wired up and clearly labeled experimental (Public Preview)
- **Acceptance criteria:** `benchmarks/` records latency + accuracy for the same 10 questions asked through all three paths.

---

## Phase 7 — Enterprise hardening

### Sprint 16 — Governance, Security, Observability, IaC, FinOps 🟢
**Goal:** the platform looks and behaves like an audited enterprise system.
- [ ] Unity Catalog RBAC + masking policies; Snowflake RBAC + row-access policies
- [ ] Microsoft Purview connected to Unity Catalog
- [ ] `governance/lgpd.md`, `governance/pii.md`, `governance/access_control.md` finalized
- [ ] OpenTelemetry traces across pipeline/ML/LLM/MCP, Prometheus + Grafana dashboards live
- [ ] FinOps dashboard (cost per 1M records, per agent request)
- [ ] `terraform/` fully applies dev environment end-to-end from scratch (destroy → apply round-trip tested)
- [ ] Threat model + prompt-injection defenses documented and tested (`governance/security.md`)
- [ ] `benchmarks/` complete for pipeline, DQ, ML, Cortex, agents, infra
- **Acceptance criteria:** `terraform destroy && terraform apply` on `environments/dev` succeeds unattended; Grafana shows live data from a real pipeline run; README production-readiness table reflects reality.

---

## What comes after Sprint 16

See [IMPROVEMENTS_AND_RESEARCH.md](IMPROVEMENTS_AND_RESEARCH.md) for a prioritized backlog beyond the MVP scope: hosted public demo, data contracts/CDC, DR strategy, SLA/SLO dashboard, Databricks Metric Views ↔ Genie deep integration, and cost-guardrails automation.

### Sprint 17 — market-requirements gap closure (tributario.txt + add2.txt addendum, 2026-08-21)

Not a core-scope sprint — closes concrete gaps surfaced by a second round of job-market
requirements. See [IMPROVEMENTS_AND_RESEARCH.md §5](IMPROVEMENTS_AND_RESEARCH.md#5-integração-dos-requisitos-de-tributariotxt--complemento-de-add2txt-agosto2026)
for the full gap analysis and rationale; status tracked live in [BUILD_LOG.md](BUILD_LOG.md).

- [x] `k8s/` — Kubernetes manifests (Deployment/Service) for `api/`, `mcp/server/`, `dashboard/`, validated with `kubectl apply --dry-run=client` (no cluster required — a live cluster was not available in this environment; see `k8s/README.md` for the manual YAML-schema sanity check run instead, and the honest record of the `kubectl` attempt)
- [x] `agents/a2a/` — Agent2Agent (A2A) protocol layer (AgentCard discovery + `tasks/send`) wrapping the existing agents, testable end-to-end locally, no external credentials needed
- [x] `agents/llm_gateway/` — AWS Bedrock provider adapter, same documented-stub pattern as the existing providers (works once real AWS credentials are configured)
- [x] `docs/decisions/ADR-014-hexagonal-architecture.md` — formalizes the Ports & Adapters pattern already implicit in `mcp/tools/`/`api/`
- **Acceptance criteria:** all four items runnable/testable locally without any new external credential; anything that *does* need a credential (AWS Bedrock, live A2A calls to a real second party) is stubbed exactly like the existing LLM Gateway providers, never silently skipped.
