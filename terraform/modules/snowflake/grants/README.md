# modules/snowflake/grants

Ties `modules/snowflake/roles` to `modules/snowflake/schemas` using `snowflake_grant_privileges_to_role` (the modern unified grant resource, replacing the deprecated per-privilege-type grant resources): `ECI_LOADER` gets DML on `CORE`, `ECI_TRANSFORMER` gets DDL on `ANALYTICS`, `ECI_BI_READER` gets read-only on `SEMANTIC`, `ECI_AI_AGENT` gets scoped read-only on `SEMANTIC`+`AI` — enforcing the least-privilege model from [ARCHITECTURE.md §16](../../../../ARCHITECTURE.md#16-layer-13--governance--security).

**Provider:** `snowflakedb/snowflake` (primary) — `snowflake_grant_privileges_to_role` is fully covered. See [ADR-008](../../../../docs/decisions/ADR-008-terraform-providers.md).

Built in **Sprint 7** ([ROADMAP.md](../../../../ROADMAP.md)), extended with row-access/masking policies in **Sprint 16**.
