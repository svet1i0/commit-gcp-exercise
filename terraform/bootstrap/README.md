# Terraform bootstrap

Creates the GCS remote-state bucket for this exercise.

## Resources

- `google_project_service` for `storage.googleapis.com`, `serviceusage.googleapis.com`
- `google_storage_bucket` named `{project_id}-tfstate` in `europe-west1`
  - uniform bucket-level access
  - public access prevention enforced
  - versioning enabled
  - `force_destroy=true` for short-lived POC teardown

## Existing Meridian POC

Bootstrap **has already been applied**. State bucket: `gs://meridian-poc-ss-260913-tfstate`. Do not re-apply or re-migrate state for routine POC updates — use `terraform/poc` with the existing remote backend.

## Fresh environment only

1. `terraform init` (local state)
2. `terraform apply` (explicit authorization required)
3. Copy `backend.tf.example` → `backend.tf` with bucket name
4. `terraform init -migrate-state`

No application infrastructure here.
