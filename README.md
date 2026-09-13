# Meridian Payments — GCP Delivery Architect POC

**Candidate:** Svetoslav Silkov  
**Project:** `meridian-poc-ss-260913` · **Region:** `europe-west1`

## Architecture

Public Cloud Run HTTP API → Direct VPC egress → private Cloud SQL (PostgreSQL) and Secret Manager. Custom-mode VPC with Private Services Access. Terraform manages infrastructure; remote state in GCS. GitHub Actions uses OIDC/WIF (no SA JSON keys).

This is an **AWS→GCP evaluation slice**: synthetic data only; no AWS CDC/cutover.

## Why Cloud Run

Stateless health API, managed scaling, Direct VPC egress to private SQL, fits a five-hour POC better than GKE.

## Private database

Cloud SQL: private IP only, `ipv4_enabled=false`, no `authorized_networks`. PSA via Service Networking. Migrations: Cloud Run Job with separate `migrator` DB user, invoked from the laptop via `gcloud run jobs execute`.

## Secrets

Exactly two Secret Manager secrets (DB password, synthetic third-party token). Runtime SA reads both on each `/health`. Values supplied at apply via ephemeral TF variables / write-only arguments (not in state).

## Run (after deploy)

```bash
curl -sS "$HEALTH_URL/health"
# Migration:
gcloud run jobs execute meridian-migrate --region=europe-west1 --wait
```

## Time spent

See working time log; README updated at submission with final total.

## With more time

HA Cloud SQL, secret rotation automation, full deploy pipeline, VPC-SC, monitoring SLOs, restore drill.
