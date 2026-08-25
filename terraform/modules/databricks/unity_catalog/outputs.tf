output "catalog_name" {
  value = databricks_catalog.this.name
}

output "schema_names" {
  description = "Map of layer name -> fully qualified schema name, e.g. schema_names[\"gold\"]."
  value       = { for k, v in databricks_schema.layers : k => "${databricks_catalog.this.name}.${v.name}" }
}

output "external_location_url" {
  value = databricks_external_location.gold.url
}
