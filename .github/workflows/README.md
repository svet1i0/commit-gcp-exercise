# GitHub Actions

## ci.yml (mandatory local CI)

Runs on push/PR to `main`:

- application unit tests
- `terraform fmt -check`
- `terraform validate` for bootstrap and poc (`-backend=false`)
- container build without push

No GCP authentication. Minimal `contents: read`.

## terraform-plan.yml (bonus)

PR plan against remote state via OIDC/WIF. Requires:

- Terraform `enable_wif=true` applied
- Repository variables: `WIF_PROVIDER`, `TF_PLAN_SERVICE_ACCOUNT`, `TF_STATE_BUCKET`, `GCP_PROJECT_ID`, `GCP_REGION`

Skips fork PRs. Never runs `terraform apply`. No SA JSON keys (org policy + exercise).

Third-party Actions are pinned to full commit SHAs.
