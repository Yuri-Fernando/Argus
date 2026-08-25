output "storage_integration_name" {
  value = snowflake_storage_integration.adls.name
}

output "stage_name" {
  value = snowflake_stage.gold_external.name
}

# After apply, run DESCRIBE STORAGE INTEGRATION ECI_ADLS_INTEGRATION in
# Snowflake to get the AZURE_CONSENT_URL / AZURE_MULTI_TENANT_APP_NAME
# needed to grant Snowflake's service principal access on the Azure side —
# this is an unavoidable manual step in the real Snowflake<->Azure trust
# handshake, not something Terraform can automate away.
