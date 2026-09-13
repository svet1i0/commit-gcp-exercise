# Terraform POC

Stage A (`enable_workloads=false`): APIs, VPC, PSA, Cloud SQL, secrets, IAM, Artifact Registry, optional WIF.

Stage B (`enable_workloads=true` + `container_image` digest): Cloud Run service + migration job.

## Secret boundary

Supply at apply (not in git):

```bash
export TF_VAR_db_password='…'          # ephemeral
export TF_VAR_third_party_api_token='…' # ephemeral
```

Uses `password_wo` / `secret_data_wo`. Do not use `password` / `secret_data` attributes.

## Backend

After bootstrap: `backend.tf` from `backend.tf.example`, prefix `poc`.
