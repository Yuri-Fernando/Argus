output "job_cluster_policy_id" {
  value = databricks_cluster_policy.job_policy.id
}

output "shared_interactive_cluster_id" {
  value = databricks_cluster.shared_interactive.id
}
