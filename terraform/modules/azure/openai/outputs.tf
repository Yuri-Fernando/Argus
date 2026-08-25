output "endpoint" {
  description = "Maps to AZURE_OPENAI_ENDPOINT in .env.example."
  value       = azurerm_cognitive_account.openai.endpoint
}

output "id" {
  value = azurerm_cognitive_account.openai.id
}

output "primary_access_key" {
  description = "Maps to AZURE_OPENAI_API_KEY in .env.example. Prefer Entra ID auth over this key where the client supports it."
  value       = azurerm_cognitive_account.openai.primary_access_key
  sensitive   = true
}

output "deployment_name" {
  value = azurerm_cognitive_deployment.chat.name
}
