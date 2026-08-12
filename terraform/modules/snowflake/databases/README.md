# modules/snowflake/databases

Provisions the `CUSTOMER_INTELLIGENCE` database — the Enterprise DWH described in [ARCHITECTURE.md §12](../../../../ARCHITECTURE.md#12-layer-9--snowflake-enterprise-dwh--cortex). Per [ADR-002](../../../../docs/decisions/ADR-002-lakehouse-vs-warehouse.md), this database is a **derived data product**, synced incrementally from Databricks Gold via Streams + Tasks — never the origin of truth.

**Provider:** `snowflakedb/snowflake` (primary) — `snowflake_database` is fully covered. See [ADR-008](../../../../docs/decisions/ADR-008-terraform-providers.md).

Built in **Sprint 7** ([ROADMAP.md](../../../../ROADMAP.md)).
