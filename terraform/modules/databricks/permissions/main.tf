# modules/databricks/permissions
#
# RBAC on Unity Catalog objects and workspace compute — ARCHITECTURE.md
# §16. Groups are the unit of access; individual users are never granted
# permissions directly, matching the least-privilege pattern used by the
# custom MCP server's tool-scoped Unity Catalog access (ARCHITECTURE.md
# §15).

resource "databricks_group" "data_engineers" {
  display_name = "data-engineers"
}

resource "databricks_group" "data_analysts" {
  display_name = "data-analysts"
}

resource "databricks_group" "ml_engineers" {
  display_name = "ml-engineers"
}

# Data engineers get full USE/CREATE/MODIFY on the catalog.
resource "databricks_grants" "catalog_engineers" {
  catalog = var.catalog_name

  grant {
    principal  = databricks_group.data_engineers.display_name
    privileges = ["USE_CATALOG", "USE_SCHEMA", "CREATE_TABLE", "MODIFY", "SELECT"]
  }

  grant {
    principal  = databricks_group.ml_engineers.display_name
    privileges = ["USE_CATALOG", "USE_SCHEMA", "SELECT"]
  }

  grant {
    principal  = databricks_group.data_analysts.display_name
    privileges = ["USE_CATALOG", "USE_SCHEMA", "SELECT"]
  }
}

# Job cluster policy: only data engineers may create clusters against it.
resource "databricks_permissions" "job_cluster_policy" {
  cluster_policy_id = var.cluster_id

  access_control {
    group_name       = databricks_group.data_engineers.display_name
    permission_level = "CAN_USE"
  }
}
