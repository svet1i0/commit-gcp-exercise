# Meridian Payments — GCP Delivery Architect POC

**Candidate:** Svetoslav Silkov · **Org:** `svetoslav-silkov-org` · **Project:** `meridian-poc-ss-260913` · **Region:** `europe-west1`

## Architecture

Public **Cloud Run** API → Direct VPC egress → private Cloud SQL PostgreSQL 15 + Secret Manager. Terraform + GCS remote state (`gs://meridian-poc-ss-260913-tfstate`). Runtime DB via Cloud SQL Connector (`PRIVATE`). Migrator: IAM DB user (Cloud Run Job). Exactly two secrets; request-time Secret Manager reads (version 1). Cloud Run `max_instance_request_concurrency=2` (aligned with a four-worker dependency executor). Parallel DB + secret health checks share a common wall-clock budget. WIF: **NOT IMPLEMENTED**.

**Why Cloud Run:** managed HTTPS public endpoint, scale-to-zero POC cost, and Direct VPC egress to private SQL without operating GKE/VMs for a single health API.

## Repository and run

| Item | Value |
|------|--------|
| Public repo | https://github.com/svet1i0/commit-gcp-exercise |
| Branch | `main` |
| Health | https://meridian-api-rgi4x3jv2a-ew.a.run.app/health |
| Deployed source SHA | `690d81cc175ef52533319a966c0e03cf669aa9b3` (short `690d81c` in `/health`) |
| Image digest | `sha256:48a8d15530e8be04ef9e11790e761bb1195d0802127ae2123920f0095bf70d98` |
| Serving revision | `meridian-api-00005-v7m` (100% traffic; concurrency 2) |
| Repository HEAD | tip of `main` (docs-only commits may follow the deployed functional SHA) |

```bash
curl -sS https://meridian-api-rgi4x3jv2a-ew.a.run.app/health

# Local validation
cd app
python -m unittest discover -s tests -v

# Schema migration: initiated from the laptop; executes remotely in GCP as Cloud Run Job
# meridian-migrate (SA meridian-migrator + IAM DB user). The human caller needs permission
# to execute that Job — no developer group is claimed as already granted.
gcloud run jobs execute meridian-migrate \
  --project meridian-poc-ss-260913 \
  --region europe-west1 \
  --wait
```

CI is validation-only (tests, publication-safety, `terraform fmt`/`validate`, Docker build without push). Bonus WIF / authenticated PR `terraform plan` is disabled, not deployed, not tested, and not implemented (`wif.tf` is a design skeleton only).

**Measured (2026-09-14):** after health-timeout remediation deploy, sequential `/health` **5/5** and concurrent **6/6** HTTP 200 (`db=ok`, `secret=ok`, five fields, commit `690d81c`) at **09:30:11Z**. Unknown route returns 404. Prior 2026-09-13 burst evidence remains historical.

## Human access and data migration

Viewer for `gcp-devops@comm-it.cloud` → `roles/viewer` (deployed). **Principal-type conflict:** Commit confirmed this address as an individual Google/Cloud Identity **user**, but the Cloud IAM API rejects `user:gcp-devops@comm-it.cloud` with HTTP 400 (“Principal … is of type group”; requires `group:`). Live binding therefore remains **`group:gcp-devops@comm-it.cloud`**. Interactive login is **not** claimed from our side. Group-first access remains the recommended production model for developer and operational teams. Cloud SQL Studio, VPN/local connectivity, large dump import, and DMS are **documented only — not deployed** ([ACCESS-MODEL.md](ACCESS-MODEL.md), [DATABASE-MIGRATION.md](DATABASE-MIGRATION.md)).

## Time spent

**Time spent: 04:09 (249 minutes).** Remaining under the five-hour hard stop: **51 minutes**. `FINAL_ACTIVE_MINUTES=249`. Bonus WIF / authenticated Terraform PR plan is disabled, not deployed, not tested, and not implemented.

## With more time

WIF plan workflow, HA SQL, secret rotation, VPC-SC, SLOs, measured min-instances trade-off.
