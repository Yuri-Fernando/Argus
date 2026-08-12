# modules/snowflake/roles

Provisions four functional Snowflake roles — `ECI_LOADER` (Databricks→Snowflake sync), `ECI_TRANSFORMER` (dbt/MetricFlow), `ECI_BI_READER` (Power BI), `ECI_AI_AGENT` (Cortex Agents / MCP `query_snowflake` tool) — instead of relying on the built-in `SYSADMIN`/`ACCOUNTADMIN` roles for application access, per the least-privilege RBAC model in [ARCHITECTURE.md §16](../../../../ARCHITECTURE.md#16-layer-13--governance--security). Actual privilege grants live in `modules/snowflake/grants`, which consumes `role_names` from this module.

**Provider:** `snowflakedb/snowflake` (primary) — `snowflake_role` is fully covered. See [ADR-008](../../../../docs/decisions/ADR-008-terraform-providers.md).

Built in **Sprint 7** ([ROADMAP.md](../../../../ROADMAP.md)), scoped further in **Sprint 16**.
