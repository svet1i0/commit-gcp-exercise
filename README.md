# Meridian Payments — GCP Delivery Architect POC

**Candidate:** Svetoslav Silkov · **Org:** `svetoslav-silkov-org` · **Project:** `meridian-poc-ss-260913` · **Region:** `europe-west1`

## Architecture

Public **Cloud Run** API → Direct VPC egress (custom VPC, no custom firewall rules) → private Cloud SQL PostgreSQL 15 + Secret Manager. Terraform + GCS remote state. Runtime DB: `app_user` via Cloud SQL Connector (`PRIVATE`). Migrator: IAM DB user `meridian-migrator@….iam` (Cloud Run Job). Exactly two secrets, request-time SM reads (version 1).

## Deployed anchors

| Item | Value |
|------|--------|
| Health | https://meridian-api-rgi4x3jv2a-ew.a.run.app/health |
| Deployed source SHA | *(set after health redeploy; see tip of validated image)* |
| Repository HEAD | tip of `main` (may differ from deployed app SHA for docs-only commits) |

```bash
curl -sS https://meridian-api-rgi4x3jv2a-ew.a.run.app/health
```

Post-deployment validation status will be recorded after the health repair redeploy (do not assume permanent 200 under all cold-start conditions until measured).

## Human access

Exercise requires Viewer for `gcp-devops@comm-it.cloud`. Principal type **unconfirmed**. **Working assumption:** `group:gcp-devops@comm-it.cloud` → `roles/viewer` (group-first practice; not Commit-confirmed). See [ACCESS-MODEL.md](ACCESS-MODEL.md). WIF / Workforce federation: **NOT IMPLEMENTED**.

## CI

Static `.github/workflows/ci.yml` only (tests, fmt, validate, amd64 build no push). Authenticated TF PR plan: **NOT IMPLEMENTED**.

## Time spent

**Final active minutes: outstanding** (`FINAL_CONFIRMED_ACTIVE_MINUTES` unset). Private TIMELOG exists; total not finalized here.

## With more time

WIF plan workflow, HA SQL, secret rotation, VPC-SC, SLOs, narrower migrator privileges, cold-start min-instances trade-off.
