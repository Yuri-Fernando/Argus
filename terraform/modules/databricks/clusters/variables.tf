variable "environment" {
  type = string
}

variable "project" {
  type    = string
  default = "eci"
}

variable "spark_version" {
  description = "Databricks Runtime version (DBR), e.g. 15.4.x-scala2.12 (LTS)."
  type        = string
  default     = "15.4.x-scala2.12"
}

variable "allowed_node_types" {
  description = "Allowlisted node types for the job cluster policy — dev keeps this cheap."
  type        = list(string)
  default     = ["Standard_DS3_v2"]
}

variable "min_workers" {
  type    = number
  default = 1
}

variable "max_workers" {
  type    = number
  default = 4
}
