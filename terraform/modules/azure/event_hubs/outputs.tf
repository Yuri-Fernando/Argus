output "namespace_id" {
  value = azurerm_eventhub_namespace.this.id
}

output "namespace_name" {
  value = azurerm_eventhub_namespace.this.name
}

output "web_events_eventhub_name" {
  value = azurerm_eventhub.web_events.name
}

output "consumer_group_name" {
  value = azurerm_eventhub_consumer_group.streaming_ingestion.name
}
