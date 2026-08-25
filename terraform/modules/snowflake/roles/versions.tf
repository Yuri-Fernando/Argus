# Explicit provider source so `terraform init` doesn't default the implied
# local name "snowflake" to the legacy registry.terraform.io/hashicorp/snowflake
# namespace — this module uses the primary provider per ADR-008
# (docs/decisions/ADR-008-terraform-providers.md), published as
# snowflakedb/snowflake and declared with that source in
# environments/dev/main.tf's required_providers.
terraform {
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 1.0"
    }
  }
}
