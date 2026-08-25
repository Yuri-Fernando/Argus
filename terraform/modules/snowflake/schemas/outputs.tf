output "schema_names" {
  description = "Map of schema name -> schema name, e.g. schema_names[\"CORE\"] — kept as a map for symmetry with modules/databricks/unity_catalog.schema_names."
  value       = { for k, v in snowflake_schema.layers : k => v.name }
}
