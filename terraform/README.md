# Terraform

Infrastructure as code for the Meridian Payments GCP exercise.

## Layout

| Directory | Purpose |
|-----------|---------|
| `bootstrap/` | GCS remote-state bucket (already applied for this POC) |
| `poc/` | Exercise infrastructure: network, Cloud SQL, Secret Manager, IAM, Artifact Registry, Cloud Run API + migration Job |

## Status

**IMPLEMENTED** for project `meridian-poc-ss-260913` in `europe-west1`. Provider pin and resource layout are in the `.tf` files under `bootstrap/` and `poc/`.

WIF resources remain **disabled / not implemented** (`enable_wif=false`; `wif.tf` is a design skeleton only).

Customer volume, traffic, recovery, and AWS→GCP bulk-migration parameters are **production design inputs**, not blockers for this POC. Confirmed Meridian constraints reflected in the deployment: private-only database; EU data location for configurable resources.

## Intended flow

### Existing deployment (this repository’s live POC)

Remote state already lives in `gs://meridian-poc-ss-260913-tfstate`. Work from `poc/` with the configured `backend.tf`. Do **not** re-run bootstrap or migrate state unless intentionally rebuilding.

```bash
cd terraform/poc
terraform init
terraform plan   # review before any apply
```

### Fresh environment (new project)

1. Apply `bootstrap/` with local state.
2. Copy `backend.tf.example` → `backend.tf` and migrate bootstrap state to the new bucket.
3. Apply `poc/` Stage A (`enable_workloads=false`), then Stage B with an image digest.

Do not embed credentials or secret payloads in Git.
