variable "database_name" {
  description = "From modules/snowflake/databases.database_name."
  type        = string
}

variable "schema_name" {
  description = "From modules/snowflake/schemas.schema_names[\"SEMANTIC\"]."
  type        = string
}
