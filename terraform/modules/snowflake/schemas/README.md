# modules/snowflake/schemas

Provisions the six schemas inside `CUSTOMER_INTELLIGENCE` — `RAW`, `STAGING`, `CORE`, `ANALYTICS`, `SEMANTIC`, `AI` — matching [ARCHITECTURE.md §12](../../../../ARCHITECTURE.md#12-layer-9--snowflake-enterprise-dwh--cortex). `CORE` holds the dimensional model mirroring Databricks Gold; `SEMANTIC` holds the Semantic View objects Cortex Analyst queries directly (see `modules/snowflake/semantic`); `AI` holds Cortex Search/AI Function scaffolding for the RAG layer.

**Provider:** `snowflakedb/snowflake` (primary) — `snowflake_schema` is fully covered. See [ADR-008](../../../../docs/decisions/ADR-008-terraform-providers.md).

Built in **Sprint 7** ([ROADMAP.md](../../../../ROADMAP.md)); `SEMANTIC`/`AI` schemas are populated starting **Sprint 8** and **Sprint 12** respectively.
