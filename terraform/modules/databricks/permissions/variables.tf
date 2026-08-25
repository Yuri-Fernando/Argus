variable "catalog_name" {
  description = "From modules/databricks/unity_catalog.catalog_name."
  type        = string
}

variable "cluster_id" {
  description = "Cluster policy ID from modules/databricks/clusters.job_cluster_policy_id."
  type        = string
}
