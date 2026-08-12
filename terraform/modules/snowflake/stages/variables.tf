variable "database_name" {
  description = "From modules/snowflake/databases.database_name."
  type        = string
}

variable "raw_schema_name" {
  description = "From modules/snowflake/schemas.schema_names[\"RAW\"]."
  type        = string
}

variable "adls_storage_account" {
  description = "From modules/azure/adls.storage_account_name."
  type        = string
}

variable "adls_container" {
  description = "Typically the 'gold' container from modules/azure/adls.container_names."
  type        = string
}

variable "azure_tenant_id" {
  description = "Maps to AZURE_TENANT_ID in .env.example."
  type        = string
}
