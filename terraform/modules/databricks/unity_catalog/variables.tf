variable "catalog_name" {
  description = "Maps to DATABRICKS_CATALOG in .env.example."
  type        = string
  default     = "customer_intelligence"
}

variable "adls_storage_account" {
  description = "From modules/azure/adls.storage_account_name."
  type        = string
}

variable "adls_container" {
  description = "Container backing the catalog's storage root — typically the 'gold' container from modules/azure/adls.container_names."
  type        = string
}

variable "access_connector_id" {
  description = "Azure Databricks Access Connector resource ID, granting the workspace managed-identity access to ADLS. Provisioned alongside modules/databricks/workspace in a full deployment (azurerm_databricks_access_connector), passed in here to keep this module focused on Unity Catalog objects only."
  type        = string
  default     = null
}

variable "databricks_workspace_id" {
  description = "From modules/databricks/workspace.workspace_id — used for explicit dependency ordering, not referenced directly in resources."
  type        = string
  default     = null
}
