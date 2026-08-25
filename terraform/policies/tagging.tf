# Standard tag set applied across every taggable resource in every module.
# Modules under modules/azure/** accept a `tags` input and merge it with
# resource-specific tags; modules/dev/main.tf (and staging/prod) pass
# `local.standard_tags` down to every module invocation so no resource ever
# ships untagged. See naming.md for the companion naming convention.

variable "project" {
  description = "Short project slug used in tags and resource names."
  type        = string
  default     = "eci" # Enterprise Customer Intelligence
}

variable "environment" {
  description = "Deployment environment: dev | staging | prod."
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "cost_center" {
  description = "FinOps cost-center code this environment rolls up to (ARCHITECTURE.md §17)."
  type        = string
  default     = "portfolio-eci"
}

locals {
  standard_tags = {
    project     = var.project
    environment = var.environment
    cost_center = var.cost_center
    managed_by  = "terraform"
  }
}

output "standard_tags" {
  description = "Merge this into every resource's tags map alongside resource-specific tags."
  value       = local.standard_tags
}
