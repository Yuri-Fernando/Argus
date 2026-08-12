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

variable "tenant_id" {
  description = "Entra ID tenant ID. Maps to AZURE_TENANT_ID in .env.example."
  type        = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
