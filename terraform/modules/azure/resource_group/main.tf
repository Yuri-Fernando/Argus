# modules/azure/resource_group
#
# The container every other Azure module in this environment deploys into.
# Kept as its own module so environments/{dev,staging,prod} can each own
# exactly one resource group without repeating the naming logic.

resource "azurerm_resource_group" "this" {
  name     = "${var.project}-${var.environment}-rg-${var.location_short}"
  location = var.location

  tags = var.tags
}
