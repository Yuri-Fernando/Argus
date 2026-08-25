output "granted_role_names" {
  description = "Pass-through of the role names this module granted privileges to — lets downstream modules (e.g. semantic) depend on grants completing first."
  value       = var.role_names
}
