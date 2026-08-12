# snowflake/

Enterprise Data Warehouse + Cortex AI serving layer — ARCHITECTURE.md §12, built in **Sprint 7** (DWH) through **Sprint 15** (Cortex Agents comparison). See [ADR-002](../docs/decisions/ADR-002-lakehouse-vs-warehouse.md) for why this exists alongside Databricks, not instead of it.

```
snowflake/
├── databases/ schemas/ warehouses/ roles/ grants/   # human-readable SQL DDL mirrors of terraform/modules/snowflake/
├── tables/               # CORE dimensional model DDL (mirrors lakehouse/gold/, see DATA_MODEL.md §3)
├── views/
├── semantic_views/        # Sprint 8 — one of the three semantic layer implementations, see ADR-005
├── cortex/
│   ├── analyst/            # Semantic View bindings consumed by Cortex Analyst
│   ├── search/               # Cortex Search index config over rag/ output
│   ├── agents/                 # Cortex Agents config (Analyst + Search orchestration)
│   └── functions/               # AI_PARSE_DOCUMENT / AI_EXTRACT / AI_SENTIMENT / AI_EMBED / AI_REDACT usage
└── evaluations/                  # golden-question harness: questions.csv, ground_truth.sql, results/, metrics/
                                   # (SQL correctness, answer correctness, latency, regression — ARCHITECTURE.md §12)
```

## Status (Aug/2026 research — see IMPROVEMENTS_AND_RESEARCH.md)

Cortex Analyst and Cortex Agents are **GA** (Nov/2025); Semantic View SQL querying is **GA** (Mar/2026); Cortex AI Guardrails are **GA** (May/2026). This layer is treated as core/production-like, not experimental.
