# modules/snowflake/stages

Provisions an Azure storage integration and external stage over the ADLS Gen2 `gold/` container, giving Snowflake governed, credential-less read access for the Streams+Tasks incremental sync described in [ADR-002](../../../../docs/decisions/ADR-002-lakehouse-vs-warehouse.md) — Databricks Gold is the source of truth, Snowflake `CORE` is the derived copy. Also used by `rag/` to stage `AI_PARSE_DOCUMENT` output ahead of `AI_EMBED`.

**Provider:** `snowflakedb/snowflake` (primary) — `snowflake_storage_integration` and `snowflake_stage` are fully covered. See [ADR-008](../../../../docs/decisions/ADR-008-terraform-providers.md).

Note: completing the Azure↔Snowflake trust relationship requires one manual step outside Terraform — after apply, `DESCRIBE STORAGE INTEGRATION` and grant the returned Snowflake Azure AD application `Storage Blob Data Reader` on the storage account (Snowflake does not expose this consent as an API call).

Built in **Sprint 7** ([ROADMAP.md](../../../../ROADMAP.md)).
