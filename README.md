# Meridian Payments — GCP Delivery Architect POC

**Candidate:** Svetoslav Silkov · **Org:** `svetoslav-silkov-org` · **Project:** `meridian-poc-ss-260913` · **Region:** `europe-west1`

## Architecture

Public **Cloud Run** API → Direct VPC egress → private Cloud SQL PostgreSQL 15 + Secret Manager. Terraform + GCS remote state. Runtime DB via Cloud SQL Connector (`PRIVATE`). Migrator: IAM DB user (Cloud Run Job). Exactly two secrets; request-time Secret Manager reads (version 1). Cloud Run `max_instance_request_concurrency=2` (aligned with a four-worker in-process dependency executor). WIF: **NOT IMPLEMENTED**.

## Repository and run

| Item | Value |
|------|--------|
| Public repo | https://github.com/svet1i0/commit-gcp-exercise |
| Branch | `main` |
| Health | https://meridian-api-rgi4x3jv2a-ew.a.run.app/health |
| Deployed source SHA | *(set after Prompt 3 redeploy)* |
| Image digest | *(set after Prompt 3 redeploy)* |
| Serving revision | *(set after Prompt 3 redeploy)* |

```bash
curl -sS https://meridian-api-rgi4x3jv2a-ew.a.run.app/health
```

Post-deployment validation will be recorded after the reliability redeploy (sequential + concurrent). Not a claim of permanent cold-start immunity.

## Human access

Viewer for `gcp-devops@comm-it.cloud`. Principal type **unconfirmed**. **Working assumption:** `group:gcp-devops@comm-it.cloud` → `roles/viewer`. See [ACCESS-MODEL.md](ACCESS-MODEL.md). Login not claimed.

## Time spent

**Final active minutes: outstanding.** Do not invent totals.

## With more time

WIF plan workflow, HA SQL, secret rotation, VPC-SC, SLOs, measured min-instances trade-off.
