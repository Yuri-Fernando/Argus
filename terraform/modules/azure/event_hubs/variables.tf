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

variable "sku" {
  description = "Standard is sufficient for dev; consider Premium for prod isolation."
  type        = string
  default     = "Standard"
}

variable "throughput_units" {
  type    = number
  default = 1
}

variable "partition_count" {
  type    = number
  default = 2
}

variable "tags" {
  type    = map(string)
  default = {}
}
