resource "google_sql_database_instance" "poc" {
  name             = "${var.name_prefix}-pg"
  project          = var.project_id
  region           = var.region
  database_version = "POSTGRES_15"

  # POC: allow destroy after review without console steps
  deletion_protection = false

  settings {
    # Enterprise shared-core; valid for POSTGRES_15 in europe-west1 per Cloud SQL docs
    tier              = "db-f1-micro"
    edition           = "ENTERPRISE"
    availability_type = "ZONAL"
    disk_size         = 10
    disk_type         = "PD_SSD"

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.poc.id
      # intentionally no authorized_networks
      # enable_private_path_for_google_cloud_services omitted: not required for
      # Cloud Run Direct VPC egress → Cloud SQL private IP (no BigQuery/etc.).
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = false
      start_time                     = "03:00"
    }
  }

  depends_on = [google_service_networking_connection.psa]
}

resource "google_sql_database" "app" {
  name     = "meridian"
  project  = var.project_id
  instance = google_sql_database_instance.poc.name
}

# Design B: one POC database user. Separate migrator SQL user + credentials
# is a production improvement (documented), not fake dual users sharing one password.
resource "google_sql_user" "app" {
  name     = "app_user"
  project  = var.project_id
  instance = google_sql_database_instance.poc.name

  password_wo         = var.db_password
  password_wo_version = var.db_password_wo_version
}
