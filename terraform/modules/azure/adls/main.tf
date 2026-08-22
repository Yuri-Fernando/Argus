# modules/azure/adls
#
# ADLS Gen2 (hierarchical namespace enabled) with the container structure
# from ARCHITECTURE.md §5: landing/raw/bronze/silver/gold/quarantine/
# checkpoints/archive. Local-dev equivalent is MinIO exposing the same
# prefix structure (see docker-compose.yml).

resource "azurerm_storage_account" "this" {
  # Storage account names: lowercase, no hyphens, <= 24 chars.
  name                     = "${var.project}${var.environment}adls${var.location_short}"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = var.replication_type
  account_kind             = "StorageV2"

  is_hns_enabled = true # hierarchical namespace = ADLS Gen2, not flat Blob

  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false

  tags = var.tags
}

# One container per medallion/lifecycle stage — ARCHITECTURE.md §5.
resource "azurerm_storage_container" "layers" {
  for_each = toset([
    "landing",
    "raw",
    "bronze",
    "silver",
    "gold",
    "quarantine",
    "checkpoints",
    "archive",
  ])

  name                  = each.value
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
}
