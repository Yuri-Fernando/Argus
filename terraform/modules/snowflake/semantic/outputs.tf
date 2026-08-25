output "semantic_view_name" {
  description = "Fully qualified Semantic View name, consumed by Cortex Analyst and documented in docs/semantic-dictionary.md."
  value       = "${var.database_name}.${var.schema_name}.CUSTOMER_INTELLIGENCE_SV"
}
