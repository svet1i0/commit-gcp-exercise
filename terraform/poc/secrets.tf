resource "google_secret_manager_secret" "db_password" {
  project   = var.project_id
  secret_id = "${var.name_prefix}-db-password"

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret" "third_party_token" {
  project   = var.project_id
  secret_id = "${var.name_prefix}-third-party-token"

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret                 = google_secret_manager_secret.db_password.id
  secret_data_wo         = var.db_password
  secret_data_wo_version = var.db_secret_data_wo_version
}

resource "google_secret_manager_secret_version" "third_party_token" {
  secret                 = google_secret_manager_secret.third_party_token.id
  secret_data_wo         = var.third_party_api_token
  secret_data_wo_version = var.third_party_secret_data_wo_version
}
