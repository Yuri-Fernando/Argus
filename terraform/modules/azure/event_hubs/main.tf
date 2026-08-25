# modules/azure/event_hubs
#
# Simulates the web events clickstream (~1M synthetic events, ARCHITECTURE.md
# §4) as a real streaming source, landing in adls/landing/ via the
# ingestion/streaming/ consumer.

resource "azurerm_eventhub_namespace" "this" {
  name                = "${var.project}-${var.environment}-evh-${var.location_short}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = var.sku
  capacity            = var.throughput_units

  tags = var.tags
}

resource "azurerm_eventhub" "web_events" {
  name              = "web-events"
  namespace_id      = azurerm_eventhub_namespace.this.id
  partition_count   = var.partition_count
  message_retention = 1 # days — dev keeps cost minimal; raise for staging/prod
}

resource "azurerm_eventhub_consumer_group" "streaming_ingestion" {
  name                = "streaming-ingestion"
  eventhub_name       = azurerm_eventhub.web_events.name
  namespace_name      = azurerm_eventhub_namespace.this.name
  resource_group_name = var.resource_group_name
}
