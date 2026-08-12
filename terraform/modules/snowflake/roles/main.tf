# modules/snowflake/roles
#
# Functional roles, not just Snowflake's default SYSADMIN/ACCOUNTADMIN —
# ARCHITECTURE.md §16 RBAC. Each maps to a real consumer: the Databricks
# Streams/Tasks sync job, dbt/MetricFlow, Power BI, and Cortex Agents.

resource "snowflake_role" "loader" {
  name    = "ECI_LOADER"
  comment = "Used by the Databricks Gold -> Snowflake CORE Streams/Tasks sync job."
}

resource "snowflake_role" "transformer" {
  name    = "ECI_TRANSFORMER"
  comment = "Used by dbt/MetricFlow to build ANALYTICS/SEMANTIC objects from CORE."
}

resource "snowflake_role" "bi_reader" {
  name    = "ECI_BI_READER"
  comment = "Used by Power BI Semantic Model connections — read-only on Semantic Views."
}

resource "snowflake_role" "ai_agent" {
  name    = "ECI_AI_AGENT"
  comment = "Used by Cortex Agents / the custom MCP server's query_snowflake tool — scoped to SEMANTIC/AI schemas only."
}
