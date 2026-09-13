output "project_id" {
  value = var.project_id
}

output "region" {
  value = var.region
}

output "vpc_name" {
  value = google_compute_network.poc.name
}

output "cloud_sql_connection_name" {
  value = google_sql_database_instance.poc.connection_name
}

output "cloud_sql_private_ip" {
  value = google_sql_database_instance.poc.private_ip_address
}

output "artifact_registry_repository" {
  value = google_artifact_registry_repository.app.name
}

output "runtime_service_account" {
  value = google_service_account.runtime.email
}

output "migrator_service_account" {
  value = google_service_account.migrator.email
}

output "tf_plan_service_account" {
  value = try(google_service_account.tf_plan[0].email, "")
}

output "db_password_secret_id" {
  value = google_secret_manager_secret.db_password.secret_id
}

output "third_party_token_secret_id" {
  value = google_secret_manager_secret.third_party_token.secret_id
}

output "cloud_run_uri" {
  value = try(google_cloud_run_v2_service.api[0].uri, "")
}

output "migration_job_name" {
  value = try(google_cloud_run_v2_job.migrate[0].name, "")
}

output "wif_provider" {
  value = try(google_iam_workload_identity_pool_provider.github[0].name, "")
}
