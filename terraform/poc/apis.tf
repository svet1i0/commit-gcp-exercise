# Stage A APIs only. Cloud Run / WIF APIs added when those stages are enabled.
locals {
  stage_a_apis = toset([
    "compute.googleapis.com",              # VPC, subnet, PSA address
    "servicenetworking.googleapis.com",    # PSA connection for private Cloud SQL
    "sqladmin.googleapis.com",             # Cloud SQL
    "artifactregistry.googleapis.com",     # container registry
    "secretmanager.googleapis.com",        # two exercise secrets
    "iam.googleapis.com",                  # service accounts + IAM bindings
    "cloudresourcemanager.googleapis.com", # project IAM
  ])

  stage_b_apis = var.enable_workloads ? toset([
    "run.googleapis.com", # Cloud Run service + job
  ]) : toset([])

  wif_apis = var.enable_wif ? toset([
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
  ]) : toset([])

  apis = setunion(local.stage_a_apis, local.stage_b_apis, local.wif_apis)
}

resource "google_project_service" "required" {
  for_each = local.apis

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}
