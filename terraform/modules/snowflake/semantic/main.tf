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
# VIEW DDL via `snowflake_execute` on the FALLBACK Snowflake-Labs/snowflake
# provider. NOTE: this resource was `snowflake_unsafe_execute` (behind
# `preview_features_enabled`) in older provider releases; the pinned
# provider version (confirmed via `terraform providers schema`) renamed it
# to the now-stable `snowflake_execute` and no longer gates it as preview.
#
# Revisit this module every sprint that touches terraform/modules/snowflake
# — migrate to a native resource the moment either provider ships one.

resource "snowflake_execute" "customer_semantic_view" {
  # Resource type is "snowflake_execute" (the provider's own type name,
  # unrelated to our local provider alias) — `provider = snowflakelabs`
  # disambiguates which of the two configured Snowflake providers
  # (snowflake vs snowflakelabs local names, both source-address-different)
  # this resource actually uses, since the type prefix "snowflake_" would
  # otherwise default-associate with the primary `snowflake` provider.
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
