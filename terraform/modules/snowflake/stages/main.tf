# modules/snowflake/stages
#
# External stage over the ADLS Gen2 gold/ container, used by the
# Streams+Tasks sync job (ADR-002) to COPY INTO CORE tables incrementally,
# and by rag/ to stage parsed-document output for AI_EMBED. Requires a
# storage integration so Snowflake can assume access to ADLS without
# embedding a SAS token in the stage definition.

resource "snowflake_storage_integration" "adls" {
  name    = "ECI_ADLS_INTEGRATION"
  comment = "Storage integration for the Databricks Gold -> Snowflake CORE sync (ADR-002)."

  storage_provider          = "AZURE"
  enabled                   = true
  azure_tenant_id           = var.azure_tenant_id
  storage_allowed_locations = ["azure://${var.adls_storage_account}.blob.core.windows.net/${var.adls_container}/"]
}

resource "snowflake_stage" "gold_external" {
  name                = "GOLD_EXTERNAL_STAGE"
  database            = var.database_name
  schema              = var.raw_schema_name
  url                 = "azure://${var.adls_storage_account}.blob.core.windows.net/${var.adls_container}/"
  storage_integration = snowflake_storage_integration.adls.name
  comment             = "Source for the Databricks Gold -> Snowflake CORE incremental sync."
}
