# modules/azure/networking
#
# VNet injection for the Databricks workspace (secure cluster connectivity)
# and a baseline NSG. Kept minimal — this portfolio does not run a
# multi-region hub-spoke topology, but demonstrates the pattern a real
# enterprise deployment would require for Databricks VNet injection.

resource "azurerm_virtual_network" "this" {
  name                = "${var.project}-${var.environment}-vnet-${var.location_short}"
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space        = [var.vnet_cidr]

  tags = var.tags
}

# Databricks requires two dedicated subnets per injected workspace:
# "public" (host VMs) and "private" (container VMs), each delegated to
# Microsoft.Databricks/workspaces.
resource "azurerm_subnet" "public" {
  name                 = "snet-databricks-public"
  resource_group_name = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.this.name
  address_prefixes      = [var.public_subnet_cidr]

  delegation {
    name = "databricks-public-delegation"
    service_delegation {
      name    = "Microsoft.Databricks/workspaces"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

resource "azurerm_subnet" "private" {
  name                 = "snet-databricks-private"
  resource_group_name = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.this.name
  address_prefixes      = [var.private_subnet_cidr]

  delegation {
    name = "databricks-private-delegation"
    service_delegation {
      name    = "Microsoft.Databricks/workspaces"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

resource "azurerm_network_security_group" "this" {
  name                = "${var.project}-${var.environment}-nsg-${var.location_short}"
  location            = var.location
  resource_group_name = var.resource_group_name

  tags = var.tags
}

resource "azurerm_subnet_network_security_group_association" "public" {
  subnet_id                 = azurerm_subnet.public.id
  network_security_group_id = azurerm_network_security_group.this.id
}

resource "azurerm_subnet_network_security_group_association" "private" {
  subnet_id                 = azurerm_subnet.private.id
  network_security_group_id = azurerm_network_security_group.this.id
}
