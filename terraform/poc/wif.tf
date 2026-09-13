# GitHub OIDC → Workload Identity Federation (design prepared; enable with enable_wif=true).
# Trust uses immutable repository and owner IDs, not mutable names alone.
# Org policy disableServiceAccountKeyCreation: no SA keys.

resource "google_iam_workload_identity_pool" "github" {
  count = var.enable_wif ? 1 : 0

  project                   = var.project_id
  workload_identity_pool_id = "${var.name_prefix}-github"
  display_name              = "GitHub Actions (Meridian POC)"
  description               = "OIDC pool for GitHub Actions plan-only workflow"

  depends_on = [google_project_service.required]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  count = var.enable_wif ? 1 : 0

  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github[0].workload_identity_pool_id
  workload_identity_pool_provider_id = "github-oidc"
  display_name                       = "GitHub OIDC"

  attribute_mapping = {
    "google.subject"          = "assertion.sub"
    "attribute.actor"         = "assertion.actor"
    "attribute.repository"    = "assertion.repository"
    "attribute.ref"           = "assertion.ref"
    "attribute.repository_id" = "assertion.repository_id"
    "attribute.owner_id"      = "assertion.repository_owner_id"
  }

  # Restrict to immutable IDs when provided; otherwise block until set.
  attribute_condition = var.github_repo_id == "" ? "assertion.repository_owner_id == '${var.github_owner_id}'" : "assertion.repository_id == '${var.github_repo_id}' && assertion.repository_owner_id == '${var.github_owner_id}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_member" "tf_plan_wif" {
  count = var.enable_wif ? 1 : 0

  service_account_id = google_service_account.tf_plan[0].name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github[0].name}/attribute.repository_owner_id/${var.github_owner_id}"
}
