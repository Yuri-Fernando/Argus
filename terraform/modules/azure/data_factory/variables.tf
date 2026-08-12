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

variable "adls_storage_account" {
  description = "Storage account name from modules/azure/adls."
  type        = string
}

variable "key_vault_id" {
  description = "Key Vault resource ID from modules/azure/key_vault."
  type        = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
