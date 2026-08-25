output "job_pool_id" {
  value = databricks_instance_pool.job_pool.id
}

output "jobs_runner_application_id" {
  description = "Service principal application ID — reference from databricks/workflows/databricks.yml as the job's run_as identity."
  value       = databricks_service_principal.jobs_runner.application_id
}
