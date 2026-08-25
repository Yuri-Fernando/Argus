# environments/dev/variables.tf
#
# Variable names mirror .env.example at the repo root so the same mental
# model (and, for local dev, the same values) applies whether you're
# running `make` targets or `terraform plan`.

# ---- Tagging / naming (policies/tagging.tf, policies/naming.md) ----

variable "project" {
  description = "Short project slug used in tags and resource names."
  type        = string
  default     = "eci"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "dev"
}

variable "cost_center" {
  description = "FinOps cost-center code (ARCHITECTURE.md §17)."
  type        = string
  default     = "portfolio-eci"
}

# ---- Azure (mirrors AZURE_* in .env.example) ----

variable "azure_subscription_id" {
  description = "Azure subscription ID. Maps to AZURE_SUBSCRIPTION_ID."
  type        = string
  sensitive   = true
}

variable "azure_tenant_id" {
  description = "Azure AD (Entra ID) tenant ID. Maps to AZURE_TENANT_ID."
  type        = string
  sensitive   = true
}

variable "azure_region" {
  description = "Primary Azure region for most resources."
  type        = string
  default     = "brazilsouth"
}

variable "azure_openai_region" {
  description = "Azure OpenAI is not available in every region; kept as a separate var."
  type        = string
  default     = "eastus2"
}

variable "azure_openai_deployment" {
  description = "Model deployment name. Maps to AZURE_OPENAI_DEPLOYMENT."
  type        = string
  default     = "gpt-4o"
}

# ---- Databricks (mirrors DATABRICKS_* in .env.example) ----

variable "databricks_host" {
  description = "Databricks workspace URL. Maps to DATABRICKS_HOST."
  type        = string
}

variable "databricks_token" {
  description = "Databricks PAT used only for the initial bootstrap; prefer Entra ID auth in staging/prod. Maps to DATABRICKS_TOKEN."
  type        = string
  sensitive   = true
  default     = null
}

variable "databricks_catalog" {
  description = "Unity Catalog catalog name. Maps to DATABRICKS_CATALOG."
  type        = string
  default     = "customer_intelligence"
}

# ---- Snowflake (mirrors SNOWFLAKE_* in .env.example) ----

variable "snowflake_organization_name" {
  description = "Snowflake organization name (the part before the account name in the org-account identifier). Required alongside snowflake_account by the snowflakedb/snowflake and Snowflake-Labs/snowflake provider schemas — see https://docs.snowflake.com/en/user-guide/organizations-gs."
  type        = string
}

variable "snowflake_account" {
  description = "Snowflake account name (account_name). Maps to SNOWFLAKE_ACCOUNT."
  type        = string
}

variable "snowflake_user" {
  description = "Snowflake service user for Terraform. Maps to SNOWFLAKE_USER."
  type        = string
}

variable "snowflake_password" {
  description = "Snowflake service user password/secret. Maps to SNOWFLAKE_PASSWORD. Prefer key-pair auth in staging/prod."
  type        = string
  sensitive   = true
}

variable "snowflake_role" {
  description = "Role Terraform assumes when applying. Maps to SNOWFLAKE_ROLE."
  type        = string
  default     = "SYSADMIN"
}

variable "snowflake_warehouse" {
  description = "Default warehouse name. Maps to SNOWFLAKE_WAREHOUSE."
  type        = string
  default     = "CUSTOMER_INTELLIGENCE_WH"
}

variable "snowflake_warehouse_size" {
  description = "Warehouse size — dev stays XSMALL to control cost."
  type        = string
  default     = "XSMALL"
}

variable "snowflake_database" {
  description = "Database name. Maps to SNOWFLAKE_DATABASE."
  type        = string
  default     = "CUSTOMER_INTELLIGENCE"
}
