# modules/snowflake/databases
#
# The single CUSTOMER_INTELLIGENCE database — ARCHITECTURE.md §12. Schemas
# (RAW/STAGING/CORE/ANALYTICS/SEMANTIC/AI) are provisioned by the sibling
# modules/snowflake/schemas module to keep database vs. schema lifecycle
# independently manageable.

resource "snowflake_database" "this" {
  name    = var.database_name
  comment = "Enterprise DWH — mirrors Databricks Gold via Streams/Tasks. See ADR-002."

  data_retention_time_in_days = var.data_retention_days
}
