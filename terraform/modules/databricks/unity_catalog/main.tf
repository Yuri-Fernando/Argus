# modules/databricks/unity_catalog
#
# The `customer_intelligence` catalog and its five schemas
# (bronze/silver/gold/ml/monitoring) — ARCHITECTURE.md §6 — backed by an
# external location on the ADLS Gen2 `gold` container via a storage
# credential using the workspace's managed identity.

resource "databricks_storage_credential" "adls" {
  name = "${var.catalog_name}-adls-credential"

  azure_managed_identity {
    access_connector_id = var.access_connector_id
  }
}

resource "databricks_external_location" "gold" {
  name            = "${var.catalog_name}-gold-external-location"
  url             = "abfss://${var.adls_container}@${var.adls_storage_account}.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.adls.id
}

resource "databricks_catalog" "this" {
  name         = var.catalog_name
  comment      = "Customer Intelligence lakehouse catalog — ARCHITECTURE.md §6"
  storage_root = databricks_external_location.gold.url
}

resource "databricks_schema" "layers" {
  for_each = toset(["bronze", "silver", "gold", "ml", "monitoring"])

  catalog_name = databricks_catalog.this.name
  name         = each.value
  comment      = "${each.value} layer — see ARCHITECTURE.md §6 / DATA_MODEL.md"
}
