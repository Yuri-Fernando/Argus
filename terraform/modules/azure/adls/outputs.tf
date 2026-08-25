output "storage_account_id" {
  value = azurerm_storage_account.this.id
}

output "storage_account_name" {
  value = azurerm_storage_account.this.name
}

output "primary_dfs_endpoint" {
  description = "abfss:// endpoint root, used by Databricks/Data Factory linked services."
  value       = azurerm_storage_account.this.primary_dfs_endpoint
}

output "container_names" {
  description = "Map of layer name -> container name, e.g. container_names[\"gold\"]."
  value       = { for k, v in azurerm_storage_container.layers : k => v.name }
}
