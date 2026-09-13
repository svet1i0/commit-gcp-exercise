# DECISIONS

## Compute: Cloud Run (not GKE)

GKE adds cluster ops cost and time. Cloud Run fits a single stateless HTTP API with Direct VPC egress.

## Network: custom VPC (not default)

Customer brief suggested default VPC. Incorrect simplification for PSA/private SQL. Dedicated custom-mode VPC with explicit subnet and firewall.

## Database: Cloud SQL PostgreSQL, private only

Exercise requires Cloud SQL. Meridian: not internet-reachable. Implementation: private IP, `ipv4_enabled=false`, no `authorized_networks`, PSA peering.

## Connectivity: Direct VPC egress

No Serverless VPC Access connector. Confirmed for service and job in provider google 8.2.0.

## Secrets: Secret Manager + write-only Terraform

Two secrets. Ephemeral sensitive variables feed `password_wo` and `secret_data_wo` so payloads are not stored in plan/state. Org policy also forbids SA JSON keys.

## Auth to GCP from GitHub: WIF/OIDC

Rejected long-lived JSON keys (exercise + `disableServiceAccountKeyCreation`). Plan-only SA; local ADC for apply.

## Migrations: Cloud Run Job + separate IAM database identity

Developers trigger from laptop via `gcloud run jobs execute`. The job runs as GCP SA `meridian-migrator` and authenticates to Cloud SQL as a distinct PostgreSQL IAM database user:

`meridian-migrator@meridian-poc-ss-260913.iam`

(Cloud SQL PostgreSQL truncates `.gserviceaccount.com` from the SA email.)

Runtime uses built-in `app_user` with the existing DB-password secret. No third Secret Manager secret.

**POC privilege note:** `cloudsqlsuperuser` is granted **only** to the migration IAM DB identity so schema migrations are deterministic within the time budget. The runtime `app_user` must **not** receive `cloudsqlsuperuser` or schema-owner privileges (DML grants only after migrate). Production should replace `cloudsqlsuperuser` with a narrower custom migration role limited to required database/schema privileges.

Connectivity: Cloud SQL Python Connector with `PRIVATE` IP (Direct VPC egress), not raw unauthenticated TCP.

## POC vs production

Single-zone, no HA/DR demo, no multi-region, no AWS CDC. Production would add HA, rotation, VPC-SC, private health diagnostics, stronger CI/CD.

## AWS → GCP framing

POC proves the **target** GCP pattern Meridian would evaluate; source AWS remains out of scope for implementation.

## Staging apply

Stage A: APIs, network, SQL, secrets, IAM, Artifact Registry (`enable_workloads=false`).  
Stage B: push image by digest, set `enable_workloads=true`.

## Reviewer

Documented `gcp-devops@comm-it.cloud` → `roles/viewer` via `reviewer_member` (not granted until explicit gate).
