output "vnet_id" {
  value = azurerm_virtual_network.this.id
}

output "vnet_name" {
  value = azurerm_virtual_network.this.name
}

output "public_subnet_id" {
  description = "Databricks-delegated public (host) subnet — consumed by modules/databricks/workspace."
  value       = azurerm_subnet.public.id
}

output "public_subnet_name" {
  value = azurerm_subnet.public.name
}

output "private_subnet_id" {
  description = "Databricks-delegated private (container) subnet — consumed by modules/databricks/workspace."
  value       = azurerm_subnet.private.id
}

output "private_subnet_name" {
  value = azurerm_subnet.private.name
}
