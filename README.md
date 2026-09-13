# Meridian Payments — GCP Delivery Architect POC

**Candidate:** Svetoslav Silkov · **Org:** `svetoslav-silkov-org` · **Project:** `meridian-poc-ss-260913` · **Region:** `europe-west1`

## Architecture

Public **Cloud Run** API → Direct VPC egress (custom VPC) → private Cloud SQL PostgreSQL 15 + Secret Manager. Terraform + GCS remote state. Runtime DB: `app_user` via Cloud SQL Connector (`PRIVATE`). Migrator: IAM DB user (Cloud Run Job). Exactly two secrets; request-time Secret Manager reads (version 1). WIF: **NOT IMPLEMENTED**.

## Repository and run

| Item | Value |
|------|--------|
| Public repo | https://github.com/svet1i0/commit-gcp-exercise |
| Branch | `main` |
| Health | https://meridian-api-rgi4x3jv2a-ew.a.run.app/health |
| Deployed source SHA | `2ef5b73638c6f9d0e517073e42791fc4d3c8a243` |
| Image digest | `sha256:54835dd941d0ac456b62ebfab068730c3f2f4f774319bd2ea9fa1c9fe18c2260` |
| Serving revision | `meridian-api-00003-ssq` (100% traffic) |

```bash
curl -sS https://meridian-api-rgi4x3jv2a-ew.a.run.app/health
```

Post-deployment validation: **12/12** requests returned HTTP 200 at **2026-09-13T15:10:41Z–15:10:50Z** (`db=ok`, `secret=ok`, five-field contract). One request aligned with revision startup (`DEPLOYMENT_ROLLOUT` / connector init). Not a claim of permanent health under all future cold starts.

## Human access

Exercise requires Viewer for `gcp-devops@comm-it.cloud`. Principal type **unconfirmed**. **Working assumption:** `group:gcp-devops@comm-it.cloud` → `roles/viewer` (group-first practice; not Commit-confirmed). See [ACCESS-MODEL.md](ACCESS-MODEL.md).

## Time spent

**Final active minutes: outstanding** (`FINAL_CONFIRMED_ACTIVE_MINUTES` unset). Submission blocked on confirmed active-time reconciliation.

## With more time

WIF plan workflow, HA SQL, secret rotation, VPC-SC, SLOs, narrower migrator privileges, measured min-instances trade-off for cold starts.
