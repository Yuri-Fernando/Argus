# environments/dev/main.tf
#
# Wires together every module (azure/databricks/snowflake) for the "dev"
# environment. See terraform/README.md for the overall provider strategy
# and docs/decisions/ADR-008-terraform-providers.md for why Snowflake has
# two provider declarations.

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.0"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.55"
    }
    # Primary Snowflake provider — ADR-008: prefer this for every resource
    # it already covers (warehouse, database, schema, role, grant).
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 1.0"
    }
    # Fallback Snowflake provider — ADR-008: used only where the primary
    # provider does not yet expose a resource (e.g. Semantic Views), with
    # preview_features_enabled declared explicitly per-resource.
    snowflakelabs = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 1.0"
    }
  }

  # This is a portfolio project — no live remote backend is attached by
  # default so `terraform init` "just works" locally with state on disk
  # (terraform.tfstate, gitignored). To use a real Azure remote backend,
  # provision a storage account/container out-of-band (chicken-and-egg:
  # backends cannot be created by the same config that uses them) and
  # uncomment the block below with your own values, then re-run
  # `terraform init -migrate-state`.
  #
  # backend "azurerm" {
  #   resource_group_name  = "eci-tfstate-rg"
  #   storage_account_name = "ecitfstatebrs"
  #   container_name       = "tfstate"
  #   key                  = "dev.terraform.tfstate"
  # }
}

provider "azurerm" {
  subscription_id = var.azure_subscription_id
  tenant_id       = var.azure_tenant_id

  features {
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
    resource_group {
      prevent_deletion_if_contains_resources = false # portfolio: allow clean `terraform destroy`
    }
  }
}

provider "databricks" {
  host  = var.databricks_host
  token = var.databricks_token
}

provider "snowflake" {
  # NOTE: both the primary (snowflakedb/snowflake) and fallback
  # (Snowflake-Labs/snowflake) provider schemas replaced the old single
  # `account` argument with the pair `organization_name` + `account_name`
  # (both required together) and renamed `username` to `user` — confirmed
  # via `terraform providers schema` against the pinned provider versions.
  organization_name = var.snowflake_organization_name
  account_name      = var.snowflake_account
  user              = var.snowflake_user
  password          = var.snowflake_password
  role              = var.snowflake_role
  warehouse         = var.snowflake_warehouse
}

provider "snowflakelabs" {
  organization_name = var.snowflake_organization_name
  account_name      = var.snowflake_account
  user              = var.snowflake_user
  password          = var.snowflake_password
  role              = var.snowflake_role
  # NOTE: the CREATE SEMANTIC VIEW workaround (modules/snowflake/semantic)
  # now uses the stable `snowflake_execute` resource, not the older
  # preview-gated `snowflake_unsafe_execute` — `preview_features_enabled`
  # is no longer needed for it (see ADR-008 and modules/snowflake/semantic/main.tf).
}

locals {
  standard_tags = {
    project     = var.project
    environment = var.environment
    cost_center = var.cost_center
    managed_by  = "terraform"
  }
}

# ---------------------------------------------------------------------------
# Azure — Sprint 1 (ADLS), Sprint 16 (full hardening)
# ---------------------------------------------------------------------------

module "resource_group" {
  source      = "../../modules/azure/resource_group"
  project     = var.project
  environment = var.environment
  location    = var.azure_region
  tags        = local.standard_tags
}

module "networking" {
  source              = "../../modules/azure/networking"
  project             = var.project
  environment         = var.environment
  location            = var.azure_region
  resource_group_name = module.resource_group.name
  tags                = local.standard_tags
}

module "key_vault" {
  source              = "../../modules/azure/key_vault"
  project             = var.project
  environment         = var.environment
  location            = var.azure_region
  resource_group_name = module.resource_group.name
  tenant_id           = var.azure_tenant_id
  tags                = local.standard_tags
}

module "adls" {
  source              = "../../modules/azure/adls"
  project             = var.project
  environment         = var.environment
  location            = var.azure_region
  resource_group_name = module.resource_group.name
  tags                = local.standard_tags
}

module "data_factory" {
  source               = "../../modules/azure/data_factory"
  project              = var.project
  environment          = var.environment
  location             = var.azure_region
  resource_group_name  = module.resource_group.name
  adls_storage_account = module.adls.storage_account_name
  key_vault_id         = module.key_vault.id
  tags                 = local.standard_tags
}

module "event_hubs" {
  source              = "../../modules/azure/event_hubs"
  project             = var.project
  environment         = var.environment
  location            = var.azure_region
  resource_group_name = module.resource_group.name
  tags                = local.standard_tags
}

module "monitoring" {
  source              = "../../modules/azure/monitoring"
  project             = var.project
  environment         = var.environment
  location            = var.azure_region
  resource_group_name = module.resource_group.name
  tags                = local.standard_tags
}

module "openai" {
  source              = "../../modules/azure/openai"
  project             = var.project
  environment         = var.environment
  location            = var.azure_openai_region
  resource_group_name = module.resource_group.name
  deployment_name     = var.azure_openai_deployment
  tags                = local.standard_tags
}

# ---------------------------------------------------------------------------
# Databricks — Sprint 2 (Bronze/Silver), Sprint 7 (Gold), Sprint 16 (RBAC)
# ---------------------------------------------------------------------------

module "databricks_workspace" {
  source              = "../../modules/databricks/workspace"
  project             = var.project
  environment         = var.environment
  location            = var.azure_region
  resource_group_name = module.resource_group.name
  vnet_id             = module.networking.vnet_id
  public_subnet_id    = module.networking.public_subnet_id
  private_subnet_id   = module.networking.private_subnet_id
  tags                = local.standard_tags
}

module "databricks_unity_catalog" {
  source                  = "../../modules/databricks/unity_catalog"
  catalog_name            = var.databricks_catalog
  adls_storage_account    = module.adls.storage_account_name
  adls_container          = module.adls.container_names["gold"]
  databricks_workspace_id = module.databricks_workspace.workspace_id

  depends_on = [module.databricks_workspace]
}

module "databricks_clusters" {
  source      = "../../modules/databricks/clusters"
  environment = var.environment

  depends_on = [module.databricks_workspace]
}

module "databricks_jobs" {
  source      = "../../modules/databricks/jobs"
  environment = var.environment

  depends_on = [module.databricks_workspace]
}

module "databricks_permissions" {
  source       = "../../modules/databricks/permissions"
  cluster_id   = module.databricks_clusters.job_cluster_policy_id
  catalog_name = module.databricks_unity_catalog.catalog_name

  depends_on = [module.databricks_unity_catalog, module.databricks_clusters]
}

# ---------------------------------------------------------------------------
# Snowflake — Sprint 7 (Gold sync), Sprint 8 (Semantic Views), Sprint 16 (RBAC)
# ---------------------------------------------------------------------------

module "snowflake_warehouse" {
  source         = "../../modules/snowflake/warehouse"
  warehouse_name = var.snowflake_warehouse
  warehouse_size = var.snowflake_warehouse_size
}

module "snowflake_databases" {
  source        = "../../modules/snowflake/databases"
  database_name = var.snowflake_database
}

module "snowflake_schemas" {
  source        = "../../modules/snowflake/schemas"
  database_name = module.snowflake_databases.database_name

  depends_on = [module.snowflake_databases]
}

module "snowflake_roles" {
  source = "../../modules/snowflake/roles"
}

module "snowflake_grants" {
  source        = "../../modules/snowflake/grants"
  database_name = module.snowflake_databases.database_name
  schema_names  = module.snowflake_schemas.schema_names
  role_names    = module.snowflake_roles.role_names

  depends_on = [module.snowflake_schemas, module.snowflake_roles]
}

module "snowflake_stages" {
  source               = "../../modules/snowflake/stages"
  database_name        = module.snowflake_databases.database_name
  raw_schema_name      = module.snowflake_schemas.schema_names["RAW"]
  adls_storage_account = module.adls.storage_account_name
  adls_container       = module.adls.container_names["gold"]
  azure_tenant_id      = var.azure_tenant_id

  depends_on = [module.snowflake_schemas]
}

module "snowflake_semantic" {
  source        = "../../modules/snowflake/semantic"
  database_name = module.snowflake_databases.database_name
  schema_name   = module.snowflake_schemas.schema_names["SEMANTIC"]

  providers = {
    snowflakelabs = snowflakelabs
  }

  depends_on = [module.snowflake_schemas, module.snowflake_grants]
}
