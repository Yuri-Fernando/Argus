# modules/databricks/jobs
#
# NOTE: actual job DEFINITIONS (tasks, schedules, dependencies for the
# Bronze->Silver->Gold pipeline) are declarative via Databricks Asset
# Bundles in databricks/workflows/databricks.yml, deployed with
# `databricks bundle deploy` from CI — not via Terraform. Encoding job
# bodies in both Terraform and DABs would duplicate ownership and drift.
#
# This module only provisions the workspace-level resources jobs depend
# on: a dedicated instance pool (faster, cheaper job-cluster starts) and
# a service principal jobs run as, so job identity is managed as code.

resource "databricks_instance_pool" "job_pool" {
  instance_pool_name = "${var.environment}-job-pool"
  node_type_id       = var.node_type_id

  min_idle_instances = 0
  max_capacity       = var.max_capacity

  idle_instance_autotermination_minutes = 15

  azure_attributes {
    availability = "ON_DEMAND_AZURE"
  }
}

resource "databricks_service_principal" "jobs_runner" {
  display_name = "${var.environment}-jobs-runner"
  active       = true
}
