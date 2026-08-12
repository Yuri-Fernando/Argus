output "data_engineers_group_id" {
  value = databricks_group.data_engineers.id
}

output "data_analysts_group_id" {
  value = databricks_group.data_analysts.id
}

output "ml_engineers_group_id" {
  value = databricks_group.ml_engineers.id
}
