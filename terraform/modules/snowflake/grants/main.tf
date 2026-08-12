# modules/snowflake/grants
#
# Privilege grants tying modules/snowflake/roles to
# modules/snowflake/{databases,schemas}. Uses the modern
# snowflake_grant_privileges_to_role resource (replaces the deprecated
# per-privilege grant resources in the old Snowflake-Labs provider).

resource "snowflake_grant_privileges_to_role" "loader_core" {
  role_name  = var.role_names["LOADER"]
  privileges = ["USAGE"]

  on_schema {
    schema_name = "\"${var.database_name}\".\"${var.schema_names["CORE"]}\""
  }
}

resource "snowflake_grant_privileges_to_role" "loader_core_tables" {
  role_name  = var.role_names["LOADER"]
  privileges = ["INSERT", "UPDATE", "DELETE", "SELECT"]

  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_schema           = "\"${var.database_name}\".\"${var.schema_names["CORE"]}\""
    }
  }
}

resource "snowflake_grant_privileges_to_role" "transformer_analytics" {
  role_name  = var.role_names["TRANSFORMER"]
  privileges = ["USAGE", "CREATE_TABLE", "CREATE_VIEW"]

  on_schema {
    schema_name = "\"${var.database_name}\".\"${var.schema_names["ANALYTICS"]}\""
  }
}

resource "snowflake_grant_privileges_to_role" "bi_reader_semantic" {
  role_name  = var.role_names["BI_READER"]
  privileges = ["USAGE"]

  on_schema {
    schema_name = "\"${var.database_name}\".\"${var.schema_names["SEMANTIC"]}\""
  }
}

resource "snowflake_grant_privileges_to_role" "ai_agent_semantic_and_ai" {
  for_each = toset([var.schema_names["SEMANTIC"], var.schema_names["AI"]])

  role_name  = var.role_names["AI_AGENT"]
  privileges = ["USAGE", "SELECT"]

  on_schema {
    schema_name = "\"${var.database_name}\".\"${each.value}\""
  }
}
