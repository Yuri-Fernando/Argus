variable "database_name" {
  description = "Maps to SNOWFLAKE_DATABASE in .env.example."
  type        = string
  default     = "CUSTOMER_INTELLIGENCE"
}

variable "data_retention_days" {
  description = "Time Travel retention — Snowflake Standard edition caps this at 1 day; Enterprise+ allows up to 90."
  type        = number
  default     = 1
}
