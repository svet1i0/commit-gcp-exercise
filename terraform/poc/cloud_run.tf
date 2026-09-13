locals {
  short_sha = substr(var.commit_sha, 0, 7)
  image_ok  = var.enable_workloads && var.container_image != ""
}

resource "google_cloud_run_v2_service" "api" {
  count = local.image_ok ? 1 : 0

  name     = "${var.name_prefix}-api"
  project  = var.project_id
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.runtime.email

    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    vpc_access {
      egress = "PRIVATE_RANGES_ONLY"
      network_interfaces {
        network    = google_compute_network.poc.id
        subnetwork = google_compute_subnetwork.app.id
      }
    }

    containers {
      image = var.container_image

      env {
        name  = "COMMIT_SHA"
        value = var.commit_sha
      }
      env {
        name  = "GCP_REGION"
        value = var.region
      }
      env {
        name  = "GCP_PROJECT"
        value = var.project_id
      }
      env {
        name  = "DB_HOST"
        value = google_sql_database_instance.poc.private_ip_address
      }
      env {
        name  = "DB_PORT"
        value = "5432"
      }
      env {
        name  = "DB_NAME"
        value = google_sql_database.app.name
      }
      env {
        name  = "DB_USER"
        value = google_sql_user.app.name
      }
      env {
        name  = "DB_PASSWORD_SECRET"
        value = google_secret_manager_secret.db_password.secret_id
      }
      env {
        name  = "THIRD_PARTY_TOKEN_SECRET"
        value = google_secret_manager_secret.third_party_token.secret_id
      }

      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_password.secret_id
            version = "1"
          }
        }
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }
  }

  depends_on = [
    google_project_service.required,
    google_secret_manager_secret_version.db_password,
    google_secret_manager_secret_version.third_party_token,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  count = local.image_ok ? 1 : 0

  project  = var.project_id
  location = google_cloud_run_v2_service.api[0].location
  name     = google_cloud_run_v2_service.api[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_job" "migrate" {
  count = local.image_ok ? 1 : 0

  name     = "${var.name_prefix}-migrate"
  project  = var.project_id
  location = var.region

  template {
    template {
      service_account = google_service_account.migrator.email
      timeout         = "600s"
      max_retries     = 1

      vpc_access {
        egress = "PRIVATE_RANGES_ONLY"
        network_interfaces {
          network    = google_compute_network.poc.id
          subnetwork = google_compute_subnetwork.app.id
        }
      }

      containers {
        image   = var.container_image
        command = ["python", "-u", "migrations/migrate.py"]

        env {
          name  = "DB_HOST"
          value = google_sql_database_instance.poc.private_ip_address
        }
        env {
          name  = "DB_PORT"
          value = "5432"
        }
        env {
          name  = "DB_NAME"
          value = google_sql_database.app.name
        }
        env {
          name  = "DB_USER"
          value = google_sql_user.app.name
        }
        env {
          name = "DB_PASSWORD"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.db_password.secret_id
              version = "1"
            }
          }
        }
      }
    }
  }

  depends_on = [
    google_project_service.required,
    google_secret_manager_secret_version.db_password,
  ]
}
