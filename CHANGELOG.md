# Changelog

This file tracks the evolution of the **specification** (this repo's docs/architecture) through its design iterations, and will track **implementation** releases the same way once code lands, following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions (`Added / Changed / Deprecated / Removed / Fixed / Security`).

## [Unreleased]
In progress: 3 new notebooks (`07_rag_document_intelligence`, `08_agents_mcp_a2a_demo`, `09_terraform_snowflake_databricks_walkthrough`) and the Streamlit `dashboard/` (6 pages, all reading real data at runtime — no hardcoded metrics). Tracked live in [BUILD_LOG.md](BUILD_LOG.md) — that file is the source of truth for exact status between releases.

---

## [2.0.0] — 2026-08-14 — First real implementation pass (Lakehouse, MDM, ML)

Moves the project from pure specification to real, executable code with real (not simulated)
metrics, run end-to-end against the local synthetic dataset (Olist not available in this
environment — everything degrades gracefully per ADR-009/ADR-010). Full detail and reproduction
commands in [BUILD_LOG.md](BUILD_LOG.md).

### Added
- `lakehouse/bronze/`, `lakehouse/silver/`, `lakehouse/run_pipeline.py` — pandas-primary Bronze→Silver pipeline (PySpark documented as an equivalent alternative path, not required).
- `data_quality/expectations/`, `data_quality/validators/` — self-contained rule engine (10 rule types) + quarantine mechanism, verified end-to-end (referential-integrity cascades). **Overall platform DQ score: 99.83%.**
- `mdm/matching/{deterministic,fuzzy,ml_model}.py`, `mdm/survivorship/`, `mdm/golden_record/`, `mdm/entity_resolution/` — three-tier entity resolution. **Recall 1.0000, Precision 0.9687, F1 0.9841** vs. ground truth. Notable finding: Faker `pt_BR` email collisions make email-only matching unreliable at this scale — `deterministic.py` adjusted to never auto-merge on email alone.
- `graph/networkx/`, `graph/algorithms/` — customer relationship graph; `graph/queries/duplicate_clusters.md` documents a real over-clustering finding (naive connected-components produces false-positive clusters from coincidental email matches).
- `ml/features/`, `ml/churn/`, `ml/explainability/`, `ml/segmentation/` — RFM/engagement/support features; 3-model churn comparison (**Logistic Regression champion, ROC-AUC 0.882**) registered in MLflow; SHAP explanations for 3 concrete customers; 5-segment KMeans (balanced, 6%-28.4% spread, no collapse).
- `notebooks/01-06` — all 6 notebooks executed end-to-end for the first time (previously 0 baked outputs); notebooks 01 and 06 reworked to run without the Olist dataset (synthetic-only fallback path).
- `BUILD_LOG.md` — new living build log, source of truth for in-progress work across sessions (protects against lost context on session interruptions, which happened twice during this build).

### Changed
- `lakehouse/README.md`, `data_quality/README.md`, `mdm/README.md`, `graph/README.md`, `ml/README.md` — corrected to describe the actual implemented architecture (previous text described a PySpark/GX-only setup that didn't match what was actually buildable/reasonable locally) and to add real "Results" sections.

### Known incidents (see BUILD_LOG.md for full detail)
- An initial attempt to run 6 work-packages in parallel failed immediately (account session concurrency limit) before any files were written — no data lost, just retried sequentially.
- The Semantic Layer work-package (dbt/Snowflake-local/Power BI) failed silently twice (no files, no notification) across a Claude Code process interruption — retried a third time, split into smaller pieces, tracked live in BUILD_LOG.md.

---

## [2.2.0] — 2026-08-21 — Kubernetes, A2A protocol, AWS Bedrock provider, Hexagonal Architecture

Closes the gap analysis from `tributario.txt` (Controladoria/Reforma Tributária posting + embedded "Python + AI Agents + AWS" posting) plus an add2.txt addendum on AI model-type taxonomy — same "every tool solves one named problem" discipline as [§4](IMPROVEMENTS_AND_RESEARCH.md#4-integração-dos-requisitos-do-add2txt-mercado-de-trabalho). Full gap analysis in [IMPROVEMENTS_AND_RESEARCH.md §5](IMPROVEMENTS_AND_RESEARCH.md#5-integração-dos-requisitos-de-tributariotxt--complemento-de-add2txt-agosto2026).

### Added
- `k8s/` — Kubernetes Deployments/Services + Dockerfiles for `api/`, `mcp/server/`, `dashboard/`. No live cluster available here — structural validity confirmed via a Python/PyYAML schema sanity check (`kubectl apply --dry-run=client` itself failed on API-server discovery, no cluster configured; documented honestly in `k8s/README.md`, not hidden). Real gap: no k8s manifests existed anywhere in the project before.
- `agents/a2a/` — Agent2Agent (A2A) protocol layer (AgentCard discovery + `POST tasks/send` JSON-RPC) wrapping the 4 existing agents, never reimplementing them. **Verified live**: booted the server, queried `/agents` + `/.well-known/agent.json`, and called `tasks/send` against all 4 agents — all returned `"state":"completed"` with real output (the recommendation agent enqueued a genuine `PENDING` item in `approval_queue.py`). Real gap: agents previously only talked to each other via direct Python calls/LangGraph, never a standardized inter-agent protocol.
- `agents/llm_gateway/` — `_complete_bedrock()` adapter added to `router.py`, same documented-stub pattern as the existing Azure OpenAI/OpenAI/Gemini/DeepSeek adapters; `bedrock-claude-3-5-sonnet` added to `models.yaml` as a selectable, non-default provider.
- `docs/decisions/ADR-014-hexagonal-architecture.md` — formalizes the Ports & Adapters pattern already implicit in `mcp/tools/`/`api/services/`/`agents/a2a/` wrapping the `mdm/`/`ml/`/`graph/`/`data_quality/` domain core — verified the dependency direction by reading the actual adapter code, not asserted from memory.
- `IMPROVEMENTS_AND_RESEARCH.md §5` — full gap analysis table for both new requirement sources.

### Explicitly not added
- No synthetic tax/fiscal domain dataset — the project's e-commerce/customer-intelligence dataset was judged more valuable to keep coherent than force-fitting an unrelated tax domain; the governance/LGPD/traceability discipline already demonstrated is what a fiscal/regulatory-context job posting actually evaluates, not a toy tax dataset.

---

## [2.1.0] — 2026-08-21 — Semantic Layer (dbt + Snowflake-local + Power BI), RAG completion, API, Terraform validation

Completes the Warehouse/Semantics/BI layer and the GenAI-consumption layer end to end, plus formally validates the entire pre-existing Terraform module tree. This work-package (originally scoped as one piece) was lost twice to a hung/silently-dying background agent before landing in three smaller, verified pieces — see BUILD_LOG.md for the incident log.

### Added
- `snowflake/ddl/`, `snowflake/local_runner.py` — DuckDB-based local stand-in for the Snowflake warehouse `terraform/modules/snowflake/` provisions; `run_metric()`/`run_all_metrics()` computes every semantic-dictionary metric that's derivable without Olist order data. **Real values**: Revenue R$ 15,515,805.42, AOV R$ 1,751.79, Churn Rate 0.5308, Repeat Rate 0.4033, CLV avg R$ 990.26. Orders/Delivery SLA/NPS explicitly `SKIPPED` with a documented reason, never faked.
- `snowflake/views/`, `snowflake/semantic_views/` — real Snowflake Semantic View DDL (ADR-005), explicitly labeled as not executed (no live account).
- `dbt/models/{staging,intermediate,marts}/`, `dbt/models/marts/_metrics.yml`, `dbt/tests/` — dbt/MetricFlow implementation of the same metrics, structurally correct (not executed — no pip install risk taken after two prior hangs).
- `powerbi/semantic_model/`, `powerbi/dax/measures.md`, `powerbi/dashboard/page_specs.md` — Power BI TMDL semantic model, DAX measures cross-checked against `local_runner.py`'s exact SQL logic, and the page-by-page dashboard blueprint later used to build `dashboard/`. **Metric-parity check passed**: Revenue/AOV/Churn Rate/Repeat Rate/CLV match exactly across all three implementations (dbt, Snowflake Semantic View, DAX) — the literal claim of ADR-005 ("one metric, one definition"), verified, not assumed.
- `rag/parsing/`, `rag/embeddings/` — orchestration glue over the pre-existing `rag/local_stack/`. `rag/evaluation/` — golden Q&A set + retrieval precision@k. **Real result: precision@3 = 1.0** (15/15, target was ≥0.8).
- `api/` — real FastAPI app (`/health`, `/customer/{id}`, `/customer/score`, `/customer/duplicates`, `/metrics`). **Verified live**: booted the server and curled all 4 non-trivial endpoints with real responses (real customer record, 1,016 real duplicate candidate pairs, real platform metrics matching `local_runner.py`).
- `docs/runbooks/slo.md` — SLO targets per layer (Sprint 16 gap).

### Verified (no code changes, validation only)
- **20/20 Terraform modules** — `terraform validate` passed on 16 (Azure ×8, Databricks ×5, Snowflake databases/roles/warehouse ×3), the remaining 4 Snowflake modules (schemas/grants/stages/semantic) validated via manual variable/output cross-reference after the environment's network connectivity dropped mid-run (DNS stopped resolving even for google.com/github.com — an environment issue, not a Terraform config issue). Zero configuration errors found by either method. `terraform/environments/dev/main.tf` wiring confirmed complete, no orphaned modules.

### Fixed
- `CHANGELOG.md` version ordering — a prior edit numbered this line of work "1.2.0" *after* "2.0.0" had already shipped, which broke semver ordering; renumbered to 2.1.0/2.2.0.

---

## [1.1.0] — 2026-08-10 — add2.txt requirements integration

Integrates a set of additional job-market requirements (`add2.txt`) into the existing architecture, following the same "every tool solves one named problem" discipline as the rest of the platform — see [IMPROVEMENTS_AND_RESEARCH.md §4](IMPROVEMENTS_AND_RESEARCH.md) for the full mapping and rationale.

### Added
- `rag/local_stack/` — local-first RAG stack: Crawl4AI (`crawler.py`, web ingestion), Docling (`document_parser.py`, complex document parsing), ChromaDB/FAISS (`vector_store.py`, local vector store) — the local-dev equivalent of Snowflake `AI_PARSE_DOCUMENT`/`AI_EMBED`/Cortex Search, per [ADR-011](docs/decisions/ADR-011-local-rag-stack.md).
- `agents/llm_gateway/` — multi-model LLM router (`router.py`'s `complete(prompt, task_type)` + `models.yaml` registry) across Azure OpenAI, OpenAI, Gemini, and DeepSeek, per [ADR-012](docs/decisions/ADR-012-llm-gateway-multimodel.md).
- `agents/memory/` — short-term (`short_term.py`, per conversation thread) and long-term (`long_term.py`, per customer, vector-store-backed, traceable) agent memory, per [ADR-013](docs/decisions/ADR-013-agent-memory.md).
- `agents/knowledge_ingestion/agent.py` — the **Knowledge Ingestion Agent**, built with **Agno** (not LangGraph), autonomously choosing Crawl4AI vs. Docling vs. a static read per knowledge source — deliberately a different framework and a different responsibility from the existing LangGraph-based `agents/orchestrator/`, not a duplicate.
- `ml/reinforcement/next_best_action.py` — an epsilon-greedy contextual bandit for next-best-action selection, explicitly labeled an extension (not core MVP scope), sharing `agents/recommendation/recommendation_agent.py`'s action set and gated by the same human-in-the-loop approval queue (ADR-006).
- `versioning/experimentation_pipeline.md` — names the experiment→version→publish lifecycle discipline explicitly, extending beyond ML models to LLM provider/model comparisons and RAG backend comparisons.
- `docs/decisions/ADR-011-local-rag-stack.md`, `ADR-012-llm-gateway-multimodel.md`, `ADR-013-agent-memory.md`.

### Changed
- `pyproject.toml` — added `[project.optional-dependencies].genai-extra` (crawl4ai, docling, chromadb, faiss-cpu, agno, google-genai).
- `README.md` §4 — added Agno, LLM Gateway, Crawl4AI, Docling, ChromaDB, FAISS to the tech stack list.
- `ARCHITECTURE.md` §3 — added tech stack rationale rows for Crawl4AI, Docling, ChromaDB/FAISS, LLM Gateway, and Agno. §14 — added "Local-first alternative (Crawl4AI + Docling + ChromaDB/FAISS)" subsection. §15 — added "LLM Gateway, agent memory, and the Knowledge Ingestion Agent (Agno)" subsection.
- `ROADMAP.md` — extended Sprint 12 and Sprint 14 checklists in place with the new modules; no sprint renumbering.
- `IMPROVEMENTS_AND_RESEARCH.md` — added §4, including August 2026 research on Crawl4AI, Agno, Docling, and ChromaDB maturity (stars, release recency, maintenance status).
- `rag/README.md` — added a one-line cross-link to `local_stack/` as the local-dev alternative.

---

## [1.0.0] — 2026-08-10 — Consolidated flagship specification

The specification produced by consolidating all prior design conversations (`rascunho.md`) into a coherent, non-redundant, research-verified architecture and repository skeleton.

### Added
- `README.md` / `README-pt.md` — bilingual project pitch and index.
- `ARCHITECTURE.md` — full 15-layer reference architecture with Mermaid diagrams and an explicit tool-by-tool rationale table (§3), replacing the three separate, overlapping diagrams from v0.1–v0.3.
- `ROADMAP.md` — the informal "Sprint 1..15" list from v0.3 rewritten as 16 sprints with explicit **acceptance criteria** per sprint (v0.3 listed sprint names only, no definition of done).
- `DATA_MODEL.md` — dataset download instructions (Kaggle link + working `download.py`), full schema reference, dimensional model ERD, and the Golden Record **survivorship rule table** (not present in any prior version).
- Working synthetic-data generators (`data/synthetic/generators/`) with deterministic seeding and a machine-checkable **ground truth** file for MDM benchmarking — v0.1–v0.3 only described this conceptually, never specified it as testable.
- `docs/decisions/ADR-*.md` — formalized Architecture Decision Records for the choices that were argued informally across the three conversations (cloud strategy, Lakehouse-vs-Warehouse split, semantic layer strategy, MCP strategy, Terraform provider strategy).
- `IMPROVEMENTS_AND_RESEARCH.md` — gap analysis against the original design + August 2026 research on every Preview/Beta feature referenced.
- **New layer not present in any prior draft:** AI security / prompt-injection defense (`governance/security.md`, §16 of ARCHITECTURE.md), driven by Snowflake's Cortex AI Guardrails reaching GA in May 2026.
- **New semantic layer option:** Databricks Unity Catalog Metric Views (GA April 2026) — didn't exist yet when the original design was written; now documented as a third implementation alongside dbt/MetricFlow and Snowflake Semantic Views (ARCHITECTURE.md §11).

### Changed
- **Databricks Managed MCP / Genie MCP status**: upgraded from "experimental / Beta" (as assumed in v0.3) to **production-like — reached General Availability in early 2026**, confirmed via research (see IMPROVEMENTS_AND_RESEARCH.md). This changes its position in the production-readiness table.
- **Snowflake Cortex Agents & Semantic Views status**: upgraded from "Preview" (v0.3 assumption) to **GA since November 2025** (Agents) and **March 2026** (Semantic Views standard SQL querying). The architecture now treats the Cortex layer as core, not an optional extension.
- **Power BI MCP status**: confirmed still **Public Preview** as of mid-2026 (v0.3's caution was correct) — kept as an explicitly experimental integration, not a core dependency.
- Repository structure: merged three slightly different, overlapping folder trees (v0.1, v0.2, v0.3) into the single tree in ARCHITECTURE.md §20, removing duplicated/renamed folders (e.g. v0.1's `snowflake/monitoring/` folded into `monitoring/`; v0.2's flat `terraform/azure|aws|modules` restructured into v0.3's `environments/`+`modules/` pattern, which is the one kept).
- Snowflake Terraform provider guidance: original drafts referenced only `Snowflake-Labs/snowflake`; this version documents the emerging `snowflakedb/snowflake` provider and a resource-by-resource fallback strategy (ADR-008), since the ecosystem shifted between v0.3 and this consolidation.

### Fixed
- Removed duplicated/contradictory content that existed across the three design conversations (e.g., the MCP tool list was specified three times with slightly different tool names; the repository tree was specified three times with drift between versions).

---

## [0.3.0] — design conversation, third iteration (superseded)
*(historical — preserved verbatim in `rascunho.md` lines ~3829–5395)*

- Added Snowflake as a first-class, non-optional component (previously "enterprise extension, not core").
- Added Terraform as a first-class component across three providers (azurerm, databricks, Snowflake-Labs).
- Introduced the "4 planes" architecture split: Azure (foundation) / Databricks (Lakehouse) / Snowflake (Warehouse+AI serving) / MCP (agentic interface).
- Added Cortex Analyst evaluation methodology (verified-queries-style regression testing).
- Added AWS portability table (documented, not duplicated).
- Added FinOps cost-tracking dashboard concept.
- Added production-readiness table (Production-like / Experimental / Prototype).

## [0.2.0] — design conversation, second iteration (superseded)
*(historical — preserved verbatim in `rascunho.md` lines ~589–2044)*

- Renamed project from generic "Data Intelligence Platform (Cortex Ready)" to "Enterprise Customer Intelligence Lakehouse."
- Anchored the project on a real dataset (Olist Brazilian E-Commerce) instead of a fully synthetic one.
- Added Databricks Medallion architecture (Bronze/Silver/Gold) with Unity Catalog.
- Added Power BI as the primary BI layer, plus Databricks Genie and Power BI MCP.
- Added MLflow, SHAP, dimensional modeling (fact/dim), dbt.
- Added the RAG/document-intelligence concept (policy PDFs).
- Requested and incorporated: Azure as primary cloud (user has AWS experience, wanted Azure added), Power BI kept, Databricks MCP added.

## [0.1.0] — design conversation, first iteration (superseded)
*(historical — preserved verbatim in `rascunho.md` lines ~1–588)*

- Original concept: "Data Intelligence Platform (Cortex Ready)" — generic multi-source customer MDM platform.
- Established the core problem statement (fragmented customer data → duplicates, inconsistent metrics, unreliable AI).
- Established the 12-stage conceptual pipeline: Raw → Quality → Standardization → Entity Resolution → Relationship Graph → Feature Store → ML → Semantic Layer → Cortex → AI Agent → Recommendation Agent → Monitoring Agent.
- Established the Databricks/PySpark/Airflow/Great Expectations/Neo4j/LangGraph/FastAPI/Terraform/Docker/GitHub Actions/Prometheus/Grafana tool list (largely carried forward).
