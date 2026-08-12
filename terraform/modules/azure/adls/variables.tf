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

variable "replication_type" {
  description = "LRS for dev to control cost; ZRS/GRS recommended for staging/prod."
  type        = string
  default     = "LRS"
}

variable "tags" {
  type    = map(string)
  default = {}
}
