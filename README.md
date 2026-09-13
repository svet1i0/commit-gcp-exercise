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
| Deployed source SHA | `b6a654efffd3a4922596e3fec24f806b381fbcfd` (short `b6a654e` in `/health`) |
| Image digest | `sha256:9fcbf3d808b78c4cd738acc02673cd0cfa5599ff2959ffffec0725f56d2e2908` |
| Serving revision | `meridian-api-00004-sgb` (100% traffic; concurrency 2) |
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

**Measured (2026-09-13):** sequential `/health` **12/12** HTTP 200 (`db=ok`, `secret=ok`, five fields) starting **15:44:38Z**. Concurrent burst **8/8** HTTP 200 (min 0.231s, median 2.319s, p95 4.387s, max 4.395s). Migration job `meridian-migrate-dwhvd` succeeded; `001_init.sql` skipped. New-revision evidence: `DEPLOYMENT_ROLLOUT` / `AUTOSCALING` startup logs — not claimed as a proven idle scale-from-zero cold start under all conditions.

## Human access

Viewer for `gcp-devops@comm-it.cloud`. Principal type **unconfirmed**. **Working assumption (deployed):** `group:gcp-devops@comm-it.cloud` → `roles/viewer`. Login not claimed.

## Time spent

**Final active time: 3 hours 32 minutes (212 minutes total).** Confirmed as `FINAL_ACTIVE_MINUTES=212`. Remaining under the five-hour hard stop: **1 hour 28 minutes (88 minutes)** for human review and demonstration prep. Bonus WIF / authenticated Terraform PR plan is disabled, not deployed, not tested, and not implemented.

## With more time

WIF plan workflow, HA SQL, secret rotation, VPC-SC, SLOs, measured min-instances trade-off.
