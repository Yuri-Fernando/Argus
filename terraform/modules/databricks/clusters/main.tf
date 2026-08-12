# modules/databricks/clusters
#
# Workspace-level cluster policy + a shared interactive cluster for ad-hoc
# exploration (notebooks/). The job-triggered clusters used by the actual
# Bronze->Silver->Gold pipeline are defined declaratively inside the
# Databricks Asset Bundle at databricks/workflows/ (job_clusters block),
# not here — this module only owns the policy they must comply with.

resource "databricks_cluster_policy" "job_policy" {
  name = "${var.environment}-job-cluster-policy"

  definition = jsonencode({
    "spark_version" : {
      "type" : "fixed",
      "value" : var.spark_version
    },
    "node_type_id" : {
      "type" : "allowlist",
      "values" : var.allowed_node_types
    },
    "autotermination_minutes" : {
      "type" : "range",
      "maxValue" : 60
    },
    "custom_tags.project" : {
      "type" : "fixed",
      "value" : var.project
    }
  })
}

resource "databricks_cluster" "shared_interactive" {
  cluster_name            = "${var.environment}-shared-interactive"
  spark_version            = var.spark_version
  node_type_id              = var.allowed_node_types[0]
  autotermination_minutes  = 30
  num_workers               = var.min_workers

  autoscale {
    min_workers = var.min_workers
    max_workers = var.max_workers
  }

  spark_conf = {
    "spark.databricks.delta.preview.enabled" = "true"
  }
}
