variable "database_name" {
  description = "From modules/snowflake/databases.database_name."
  type        = string
}

variable "schema_names" {
  description = "From modules/snowflake/schemas.schema_names."
  type        = map(string)
}

variable "role_names" {
  description = "From modules/snowflake/roles.role_names."
  type        = map(string)
}
