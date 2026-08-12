# modules/databricks/workspace
#
# Provisions the Azure Databricks workspace itself via azurerm (the
# workspace resource is an azurerm_* resource even though everything
# downstream of it — clusters, Unity Catalog, permissions — uses the
# databricks provider pointed at this workspace's URL). VNet-injected
# using the subnets from modules/azure/networking for secure cluster
# connectivity (no public IPs on cluster nodes).

resource "azurerm_databricks_workspace" "this" {
  name                        = "${var.project}-${var.environment}-dbx-${var.location_short}"
  location                    = var.location
  resource_group_name         = var.resource_group_name
  sku                          = var.sku
  managed_resource_group_name = "${var.project}-${var.environment}-dbx-managed-rg"

  custom_parameters {
    no_public_ip        = true
    virtual_network_id    = var.vnet_id
    public_subnet_name     = "snet-databricks-public"
    private_subnet_name    = "snet-databricks-private"
    # Names must match modules/azure/networking's delegated subnets exactly;
    # passed as *_id below for validation, names above for the parameter.
  }

  tags = var.tags
}
