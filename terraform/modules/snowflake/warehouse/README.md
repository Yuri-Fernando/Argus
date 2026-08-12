# modules/snowflake/warehouse

Provisions the `CUSTOMER_INTELLIGENCE_WH` virtual warehouse — Snowflake's cost boundary and compute unit ([ARCHITECTURE.md §16](../../../../ARCHITECTURE.md#16-layer-13--governance--security)). Sized `XSMALL` with `auto_suspend = 60s` by default to keep credits low on a personal-budget sandbox; `warehouse_size`/`max_cluster_count` are exposed so `staging`/`prod` `.tfvars` can scale up without touching the module.

**Provider:** `snowflakedb/snowflake` (primary) — `snowflake_warehouse` is fully covered, no fallback needed. See [ADR-008](../../../../docs/decisions/ADR-008-terraform-providers.md).

Built in **Sprint 7** ([ROADMAP.md](../../../../ROADMAP.md)), alongside `databases`/`schemas`/`roles`.
