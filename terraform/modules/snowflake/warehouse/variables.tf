variable "warehouse_name" {
  description = "Maps to SNOWFLAKE_WAREHOUSE in .env.example."
  type        = string
  default     = "CUSTOMER_INTELLIGENCE_WH"
}

variable "warehouse_size" {
  type    = string
  default = "XSMALL"
}

variable "auto_suspend_seconds" {
  type    = number
  default = 60
}

variable "max_cluster_count" {
  type    = number
  default = 1
}
