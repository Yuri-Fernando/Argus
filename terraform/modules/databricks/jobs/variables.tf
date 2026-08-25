variable "environment" {
  type = string
}

variable "node_type_id" {
  type    = string
  default = "Standard_DS3_v2"
}

variable "max_capacity" {
  type    = number
  default = 4
}
