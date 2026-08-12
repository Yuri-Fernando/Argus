# Changelog

This file tracks the evolution of the **specification** (this repo's docs/architecture) through its design iterations, and will track **implementation** releases the same way once code lands, following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions (`Added / Changed / Deprecated / Removed / Fixed / Security`).

## [Unreleased]
Implementation has not started yet — sprints in [ROADMAP.md](ROADMAP.md) are all 🟢. This section will fill in as Sprint 0+ lands.

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
