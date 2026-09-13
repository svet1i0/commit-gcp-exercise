# Creates the GCS remote-state bucket only.
# Apply with local state first, then migrate into this bucket.
#
# Required APIs for bootstrap (enable via google_project_service below):
# - storage.googleapis.com (often already on new projects)
# - serviceusage.googleapis.com (to manage services)

resource "google_project_service" "storage" {
  project            = var.project_id
  service            = "storage.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "serviceusage" {
  project            = var.project_id
  service            = "serviceusage.googleapis.com"
  disable_on_destroy = false
}

locals {
  # Deterministic, globally unique bucket name from project id
  state_bucket_name = "${var.project_id}-tfstate"
}

resource "google_storage_bucket" "tfstate" {
  name                        = local.state_bucket_name
  project                     = var.project_id
  location                    = var.region
  force_destroy               = true # short-lived POC; destroy after review
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning {
    enabled = true
  }

  labels = {
    purpose  = "terraform-state"
    exercise = "meridian-poc"
  }

  depends_on = [
    google_project_service.storage,
    google_project_service.serviceusage,
  ]
}

output "state_bucket_name" {
  description = "GCS bucket for Terraform remote state."
  value       = google_storage_bucket.tfstate.name
}

output "state_bucket_url" {
  description = "gs:// URL for the state bucket."
  value       = google_storage_bucket.tfstate.url
}
