# modules/snowflake/semantic

Provisions the `CUSTOMER_INTELLIGENCE_SV` Semantic View — the object Cortex Analyst queries directly and, per [ARCHITECTURE.md §11](../../../../ARCHITECTURE.md#11-layer-8--semantic-layer-three-implementations-one-contract), one of the three implementations of the platform's single canonical metric contract (alongside dbt/MetricFlow and Unity Catalog Metric Views — all three must return the identical number, enforced by `tests/data/test_metric_parity.py`).

**Provider:** `Snowflake-Labs/snowflake` v1 (fallback), **not** the primary `snowflakedb/snowflake` provider. As documented in [ADR-008](../../../../docs/decisions/ADR-008-terraform-providers.md), neither provider ships a native `snowflake_semantic_view` resource as of this writing — Semantic Views are a newer object kind (GA Mar/2026) that provider coverage hasn't caught up with yet. The workaround used here is `snowflake_unsafe_execute` running the raw `CREATE SEMANTIC VIEW` DDL, which requires `preview_features_enabled` to be declared explicitly on the `snowflakelabs` provider block in `environments/dev/main.tf` — see the `# preview_features_enabled required — see ADR-008` comment in `main.tf`.

**Revisit every sprint that touches `terraform/modules/snowflake/`** — migrate to a native resource type the moment either provider ships one; the `snowflake_unsafe_execute` approach forfeits Terraform's usual plan-diff safety for this one resource.

Built in **Sprint 8** ([ROADMAP.md](../../../../ROADMAP.md)), when the semantic layer's three implementations are wired up together.
