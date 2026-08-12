# modules/snowflake/semantic
#
# Snowflake Semantic Views (ARCHITECTURE.md §11/§12) feed Cortex Analyst
# directly and are the recommended grounding source for it as of 2026.
#
# ADR-008: as of this writing, neither snowflakedb/snowflake nor
# Snowflake-Labs/snowflake ships a first-class `snowflake_semantic_view`
# resource type — Semantic Views are a newer object kind (GA Mar/2026)
# that Terraform provider coverage hasn't fully caught up with. The
# documented workaround, per ADR-008, is to declare the CREATE SEMANTIC
# VIEW DDL via `snowflake_unsafe_execute` on the FALLBACK
# Snowflake-Labs/snowflake provider, which requires
# `preview_features_enabled` to be set explicitly (done in
# environments/dev/main.tf's `provider "snowflakelabs"` block).
#
# Revisit this module every sprint that touches terraform/modules/snowflake
# — migrate to a native resource the moment either provider ships one.

resource "snowflakelabs_unsafe_execute" "customer_semantic_view" {
  # preview_features_enabled required — see ADR-008
  provider = snowflakelabs

  execute = <<-SQL
    CREATE OR REPLACE SEMANTIC VIEW ${var.database_name}.${var.schema_name}.CUSTOMER_INTELLIGENCE_SV
      TABLES (
        customer AS ${var.database_name}.CORE.DIM_CUSTOMER PRIMARY KEY (master_customer_id),
        orders   AS ${var.database_name}.CORE.FACT_ORDERS   PRIMARY KEY (order_id)
      )
      RELATIONSHIPS (
        orders_to_customer AS orders (master_customer_id) REFERENCES customer (master_customer_id)
      )
      FACTS (
        orders.order_value AS order_value
      )
      METRICS (
        -- Canonical definition mirrored from docs/semantic-dictionary.md —
        -- must match the dbt/MetricFlow and Unity Catalog Metric View
        -- definitions exactly (tests/data/test_metric_parity.py).
        orders.revenue AS SUM(orders.order_value) COMMENT = 'Revenue — see docs/semantic-dictionary.md'
      )
  SQL

  revert = "DROP SEMANTIC VIEW IF EXISTS ${var.database_name}.${var.schema_name}.CUSTOMER_INTELLIGENCE_SV"

  query = "SHOW SEMANTIC VIEWS LIKE 'CUSTOMER_INTELLIGENCE_SV' IN SCHEMA ${var.database_name}.${var.schema_name}"
}
