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

variable "log_retention_days" {
  type    = number
  default = 30
}

variable "diagnostic_targets" {
  description = "Map of {label => resource_id} to attach diagnostic settings to (e.g. { adls = module.adls.storage_account_id })."
  type        = map(string)
  default     = {}
}

variable "tags" {
  type    = map(string)
  default = {}
}
