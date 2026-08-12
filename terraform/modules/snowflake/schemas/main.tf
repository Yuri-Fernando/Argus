# modules/snowflake/schemas
#
# RAW/STAGING/CORE/ANALYTICS/SEMANTIC/AI — ARCHITECTURE.md §12. CORE holds
# the dimensional model (mirrors Databricks Gold); SEMANTIC holds Semantic
# View objects consumed by Cortex Analyst; AI holds Cortex Search /
# AI Function scaffolding (RAG indices, evaluation tables).

resource "snowflake_schema" "layers" {
  for_each = toset(["RAW", "STAGING", "CORE", "ANALYTICS", "SEMANTIC", "AI"])

  database = var.database_name
  name      = each.value
  comment    = "${each.value} schema — ARCHITECTURE.md §12"

  data_retention_time_in_days = each.value == "RAW" ? 1 : var.default_retention_days
}
