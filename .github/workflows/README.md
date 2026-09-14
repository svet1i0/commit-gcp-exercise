# GitHub Actions

## ci.yml (mandatory local CI)

Runs on push/PR to `main`:

- application unit tests
- publication-safety scan (`scripts/check_publication_safety.py`)
- `terraform fmt -check`
- `terraform validate` for bootstrap and poc (`-backend=false`)
- linux/amd64 container build without push

No GCP authentication. Minimal `contents: read`. Third-party Actions are pinned to full commit SHAs.

## Authenticated Terraform PR plan / WIF — NOT IMPLEMENTED

Bonus OIDC/WIF plan-only workflow is **not** published as an active workflow (would fail without WIF configured). Design intent remains:

- plan-only service account via Workload Identity Federation
- no SA JSON keys
- never `terraform apply` from Actions
- repository variables such as `WIF_PROVIDER`, `TF_PLAN_SERVICE_ACCOUNT`, `TF_STATE_BUCKET`, `GCP_PROJECT_ID`, `GCP_REGION`

Deferred due to remaining active-time priority after the privacy-safe deploy.
