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
        name  = "INSTANCE_CONNECTION_NAME"
        value = google_sql_database_instance.poc.connection_name
      }
      env {
        name  = "DB_NAME"
        value = google_sql_database.app.name
      }
      env {
        name  = "DB_USER"
        value = google_sql_user.app.name
      }
      # Secret *identifiers* only — app performs request-time Secret Manager API reads.
      # Do NOT inject DB password via secret_key_ref (that is not a /health SM read).
      env {
        name  = "DB_PASSWORD_SECRET"
        value = google_secret_manager_secret.db_password.secret_id
      }
      env {
        name  = "THIRD_PARTY_TOKEN_SECRET"
        value = google_secret_manager_secret.third_party_token.secret_id
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
    google_project_iam_member.runtime_cloudsql_client,
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
          name  = "INSTANCE_CONNECTION_NAME"
          value = google_sql_database_instance.poc.connection_name
        }
        env {
          name  = "DB_NAME"
          value = google_sql_database.app.name
        }
        # Distinct IAM DB identity (not app_user). No password / no secret_key_ref.
        env {
          name  = "DB_USER"
          value = google_sql_user.migrator_iam.name
        }
        env {
          name  = "APP_DB_USER"
          value = google_sql_user.app.name
        }
      }
    }
  }

  depends_on = [
    google_project_service.required,
    google_sql_user.migrator_iam,
    google_project_iam_member.migrator_cloudsql_client,
    google_project_iam_member.migrator_cloudsql_instance_user,
  ]
}
