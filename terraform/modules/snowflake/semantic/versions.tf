# modules/snowflake/semantic/versions.tf
#
# This module is passed the root's "snowflakelabs" provider configuration
# explicitly (environments/dev/main.tf: `providers = { snowflakelabs =
# snowflakelabs }`) because it uses the Snowflake-Labs/snowflake fallback
# provider per ADR-008 (docs/decisions/ADR-008-terraform-providers.md) —
# Semantic Views aren't yet covered by a native resource in either
# provider, so this module shells out via `snowflakelabs_unsafe_execute`.
#
# Terraform requires every module that receives a provider configuration
# under a local name to declare that name's source here, or `terraform
# init` fails with "Provider type mismatch" against the root's
# `Snowflake-Labs/snowflake` provider (confirmed via `terraform validate`
# against environments/dev).
terraform {
  required_providers {
    snowflakelabs = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 1.0"
    }
  }
}
