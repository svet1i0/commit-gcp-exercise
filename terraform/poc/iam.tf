# Runtime SA: used by Cloud Run service (Stage B). Created in Stage A so IAM is ready.
resource "google_service_account" "runtime" {
  project      = var.project_id
  account_id   = "${var.name_prefix}-runtime"
  display_name = "Meridian POC Cloud Run runtime"
}

# Migrator SA: used by Cloud Run Job (Stage B). Separate GCP identity from runtime;
# shares the single POC DB user (Design B) — SQL-user separation is a prod improvement.
resource "google_service_account" "migrator" {
  project      = var.project_id
  account_id   = "${var.name_prefix}-migrator"
  display_name = "Meridian POC migration job"
}

# No roles/cloudsql.client: app and migrator use pg8000 TCP to the private IP
# with DB user/password (Direct VPC egress). They do not use Cloud SQL Connector.

# Secret access is secret-scoped, not project-wide.

resource "google_secret_manager_secret_iam_member" "runtime_db_secret" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.db_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "runtime_token_secret" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.third_party_token.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "migrator_db_secret" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.db_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.migrator.email}"
}

# WIF plan SA — only when enable_wif=true (not Stage A)
resource "google_service_account" "tf_plan" {
  count = var.enable_wif ? 1 : 0

  project      = var.project_id
  account_id   = "${var.name_prefix}-tf-plan"
  display_name = "Meridian POC GitHub Actions Terraform plan (read-only)"
}

resource "google_project_iam_member" "tf_plan_viewer" {
  count = var.enable_wif ? 1 : 0

  project = var.project_id
  role    = "roles/viewer"
  member  = "serviceAccount:${google_service_account.tf_plan[0].email}"
}

resource "google_storage_bucket_iam_member" "tf_plan_state_reader" {
  count = var.enable_wif ? 1 : 0

  bucket = "${var.project_id}-tfstate"
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.tf_plan[0].email}"
}

# Reviewer Viewer — only when reviewer_member is set (grant gate)
resource "google_project_iam_member" "reviewer_viewer" {
  count = var.reviewer_member == "" ? 0 : 1

  project = var.project_id
  role    = "roles/viewer"
  member  = var.reviewer_member
}
