# modules/azure/key_vault
#
# Identity and secrets — ARCHITECTURE.md §16 (Governance & Security):
# no credentials in code/config ever. Data Factory, Databricks, and CI/CD
# service principals are all granted scoped access policies against this
# vault rather than embedding secrets anywhere.

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "this" {
  name                       = "${var.project}-${var.environment}-kv-${var.location_short}"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  tenant_id                  = var.tenant_id
  sku_name                   = "standard"
  purge_protection_enabled   = false # portfolio: allow `terraform destroy` to fully clean up
  rbac_authorization_enabled = true  # RBAC over legacy access policies (azurerm v5 renamed enable_rbac_authorization -> rbac_authorization_enabled)

  tags = var.tags
}

# The Terraform/CI service principal gets Key Vault Administrator so it can
# manage secrets used by other modules (Data Factory, Databricks, Snowflake
# credentials mirrored for break-glass access).
resource "azurerm_role_assignment" "terraform_admin" {
  scope                = azurerm_key_vault.this.id
  role_definition_name = "Key Vault Administrator"
  principal_id         = data.azurerm_client_config.current.object_id
}
