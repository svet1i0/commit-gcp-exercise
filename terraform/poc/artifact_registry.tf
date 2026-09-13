resource "google_artifact_registry_repository" "app" {
  project       = var.project_id
  location      = var.region
  repository_id = "${var.name_prefix}-app"
  description   = "Meridian POC container images"
  format        = "DOCKER"

  depends_on = [google_project_service.required]
}

# No repository IAM on runtime/migrator SAs.
# Cloud Run image pull uses the Cloud Run service agent (same project),
# not the workload runtime/migrator identities. Push/pull for deploy uses
# the operator (or future CI) identity, not these SAs.
