# modules/snowflake/warehouse
#
# ADR-008: warehouses are well-covered by the primary snowflakedb/snowflake
# provider — no fallback needed here. Sized XSMALL by default (dev/cost
# control) with aggressive auto-suspend, since Snowflake credits are a
# FinOps line item tracked in ARCHITECTURE.md §17.

resource "snowflake_warehouse" "this" {
  name           = var.warehouse_name
  warehouse_size = var.warehouse_size

  auto_suspend        = var.auto_suspend_seconds
  auto_resume          = true
  initially_suspended = true

  min_cluster_count = 1
  max_cluster_count = var.max_cluster_count
  scaling_policy     = "STANDARD"

  comment = "Customer Intelligence DWH warehouse — cost boundary per ARCHITECTURE.md §16"
}
