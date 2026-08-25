# modules/databricks/workspace

Provisions the Azure Databricks workspace (`azurerm_databricks_workspace`, Premium SKU — required for Unity Catalog), VNet-injected into the subnets from `modules/azure/networking`. This is the one `databricks/*` module that uses the `azurerm` provider rather than the `databricks` provider, because the workspace itself is an Azure resource; every other module in this directory (`clusters`, `jobs`, `unity_catalog`, `permissions`) uses the `databricks` provider authenticated against this workspace's URL/token.

Built in **Sprint 2** ([ROADMAP.md](../../../../ROADMAP.md)), when Bronze/Silver processing first needs a real workspace. See [ARCHITECTURE.md §6](../../../../ARCHITECTURE.md#6-layer-3--lakehouse-azure-databricks).
