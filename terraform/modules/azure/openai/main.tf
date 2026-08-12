# modules/azure/openai
#
# Backs the LangGraph agents (ARCHITECTURE.md §15) and any Azure-native
# LLM calls outside the Snowflake Cortex path. Deployed as a Cognitive
# Services account of kind "OpenAI" with a single model deployment — kept
# to one deployment for portfolio cost control.

resource "azurerm_cognitive_account" "openai" {
  name                = "${var.project}-${var.environment}-oai-${var.location_short}"
  location            = var.location
  resource_group_name = var.resource_group_name
  kind                = "OpenAI"
  sku_name             = "S0"

  custom_subdomain_name         = "${var.project}-${var.environment}-oai-${var.location_short}"
  public_network_access_enabled = true # portfolio: no private endpoint; document as a prod gap

  tags = var.tags
}

resource "azurerm_cognitive_deployment" "chat" {
  name                 = var.deployment_name
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = var.model_name
    version = var.model_version
  }

  sku {
    name     = "Standard"
    capacity = var.capacity_tpm
  }
}
