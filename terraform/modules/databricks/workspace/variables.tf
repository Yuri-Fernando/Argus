variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "location" {
  type = string
}

variable "location_short" {
  type    = string
  default = "brs"
}

variable "resource_group_name" {
  type = string
}

variable "vnet_id" {
  description = "From modules/azure/networking.vnet_id."
  type        = string
}

variable "public_subnet_id" {
  description = "From modules/azure/networking.public_subnet_id (unused directly by azurerm_databricks_workspace, kept for explicit dependency ordering)."
  type        = string
}

variable "private_subnet_id" {
  description = "From modules/azure/networking.private_subnet_id."
  type        = string
}

variable "sku" {
  type    = string
  default = "premium" # required for Unity Catalog + VNet injection
}

variable "tags" {
  type    = map(string)
  default = {}
}
