output "id" {
  value = azurerm_data_factory.this.id
}

output "name" {
  value = azurerm_data_factory.this.name
}

output "identity_principal_id" {
  description = "System-assigned managed identity principal ID — grant this Storage Blob Data Contributor on ADLS and a Key Vault access policy."
  value       = azurerm_data_factory.this.identity[0].principal_id
}
