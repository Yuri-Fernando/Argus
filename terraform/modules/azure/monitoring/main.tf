# modules/azure/monitoring
#
# Azure-native half of ARCHITECTURE.md §17 (Observability & FinOps).
# OpenTelemetry traces from pipeline/ML/LLM/MCP are exported to Prometheus/
# Grafana (self-hosted, see monitoring/) for the portable path, and
# mirrored here into Log Analytics/App Insights for the Azure-native path
# used by Data Factory/Databricks diagnostic settings.

resource "azurerm_log_analytics_workspace" "this" {
  name                = "${var.project}-${var.environment}-law-${var.location_short}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days    = var.log_retention_days

  tags = var.tags
}

resource "azurerm_application_insights" "this" {
  name                = "${var.project}-${var.environment}-appi-${var.location_short}"
  location            = var.location
  resource_group_name = var.resource_group_name
  workspace_id        = azurerm_log_analytics_workspace.this.id
  application_type     = "other" # data platform, not a classic web app

  tags = var.tags
}

# Example diagnostic setting wiring a monitored resource's platform logs
# into Log Analytics. Concrete `target_resource_id` values are passed in
# by the caller per resource (ADLS, ADF, Event Hubs, Key Vault) that needs
# audit/diagnostic logging enabled.
resource "azurerm_monitor_diagnostic_setting" "targets" {
  for_each = var.diagnostic_targets

  name                       = "diag-${each.key}"
  target_resource_id         = each.value
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id

  enabled_log {
    category_group = "allLogs"
  }

  metric {
    category = "AllMetrics"
  }
}
