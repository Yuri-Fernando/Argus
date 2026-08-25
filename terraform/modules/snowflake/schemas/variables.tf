variable "database_name" {
  description = "From modules/snowflake/databases.database_name."
  type        = string
}

variable "default_retention_days" {
  type    = number
  default = 1
}
