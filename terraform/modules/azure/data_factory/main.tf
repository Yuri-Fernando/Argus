# modules/azure/data_factory
#
# ADF handles scheduled batch pulls (CRM/Marketing/Support exports, Olist
# CSV drop) that land raw, untouched, in adls/landing/ — ARCHITECTURE.md §4.
# Pipeline definitions themselves live in ingestion/api/ (exported as ADF
# ARM templates) and are deployed via CI, not authored inline here.

resource "azurerm_data_factory" "this" {
  name                = "${var.project}-${var.environment}-adf-${var.location_short}"
  location            = var.location
  resource_group_name = var.resource_group_name

  identity {
    type = "SystemAssigned" # used to grant ADF read/write on ADLS + Key Vault access
  }

  tags = var.tags
}

# Linked service pointing ADF at the ADLS Gen2 account so pipelines can
# read/write landing/ and raw/ containers directly.
resource "azurerm_data_factory_linked_service_data_lake_storage_gen2" "adls" {
  name                = "ls_adls_${var.environment}"
  data_factory_id     = azurerm_data_factory.this.id
  use_managed_identity = true
  url                  = "https://${var.adls_storage_account}.dfs.core.windows.net"
}

# Linked service granting ADF access to Key Vault-stored secrets (source
# system credentials for CRM/Marketing/Support exports) without embedding
# any secret in pipeline JSON.
resource "azurerm_data_factory_linked_service_key_vault" "kv" {
  name            = "ls_keyvault_${var.environment}"
  data_factory_id = azurerm_data_factory.this.id
  key_vault_id    = var.key_vault_id
}
