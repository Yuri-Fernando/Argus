output "id" {
  value = azurerm_key_vault.this.id
}

output "name" {
  value = azurerm_key_vault.this.name
}

output "uri" {
  description = "Vault URI. Maps to AZURE_KEY_VAULT_URI in .env.example."
  value       = azurerm_key_vault.this.vault_uri
}
