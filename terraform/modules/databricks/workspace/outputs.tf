output "workspace_id" {
  value = azurerm_databricks_workspace.this.workspace_id
}

output "workspace_url" {
  description = "Maps to DATABRICKS_HOST in .env.example (prefix with https://)."
  value       = azurerm_databricks_workspace.this.workspace_url
}

output "id" {
  value = azurerm_databricks_workspace.this.id
}
