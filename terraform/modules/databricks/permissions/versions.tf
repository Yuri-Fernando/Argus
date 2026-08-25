# Explicit provider source so `terraform init` doesn't default the implied
# local name "databricks" to the legacy registry.terraform.io/hashicorp/databricks
# namespace — the real provider is published as databricks/databricks and is
# declared with that source in environments/dev/main.tf's required_providers.
terraform {
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.55"
    }
  }
}
