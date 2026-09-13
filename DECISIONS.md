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

## Migrations: Cloud Run Job + separate DB user

Developers trigger from laptop via gcloud; job uses private path; `migrator` user separate from `app_user`.

## POC vs production

Single-zone, no HA/DR demo, no multi-region, no AWS CDC. Production would add HA, rotation, VPC-SC, private health diagnostics, stronger CI/CD.

## AWS → GCP framing

POC proves the **target** GCP pattern Meridian would evaluate; source AWS remains out of scope for implementation.

## Staging apply

Stage A: APIs, network, SQL, secrets, IAM, Artifact Registry (`enable_workloads=false`).  
Stage B: push image by digest, set `enable_workloads=true`.

## Reviewer

Documented `gcp-devops@comm-it.cloud` → `roles/viewer` via `reviewer_member` (not granted until explicit gate).
