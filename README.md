# Meridian Payments — GCP Delivery Architect POC

**Candidate:** Svetoslav Silkov  
**Organization:** `svetoslav-silkov-org`  
**Project:** `meridian-poc-ss-260913` · **Region:** `europe-west1`

## Deployed vs repository HEAD

| Identity | Value |
|----------|--------|
| **Deployed application source** | `910c929fbb101a6bcb8d5b012b21a460cec75cbc` (`910c929`) |
| **Repository HEAD** | See latest commit on `main` (docs/workflow cleanup may be newer than the deployed app SHA) |
| **Deployed image** | `europe-west1-docker.pkg.dev/meridian-poc-ss-260913/meridian-app/api@sha256:43c6dc4bd70fe3f25f3b29459e11333a0376f6498f78b40d0efcc73a36e5c678` |

Application and Terraform source trees under that deployed SHA remain the live workload. Later documentation-only commits intentionally do **not** trigger a redeploy.

## Architecture

Public **Cloud Run** HTTP API → **Direct VPC egress** (custom-mode VPC) → private **Cloud SQL** (PostgreSQL 15) and **Secret Manager**. Private Services Access for Cloud SQL. Terraform manages infrastructure; remote state in GCS.

**Networking notes:** custom-mode VPC + subnet + PSA. **No custom VPC firewall rules** were added for this POC. Direct VPC egress uses `PRIVATE_RANGES_ONLY` (no Serverless VPC Access connector).

This is an **AWS→GCP evaluation slice**: synthetic data only; no AWS CDC/cutover.

## Why Cloud Run

Stateless health API, managed scaling, Direct VPC egress to private SQL, fits a five-hour POC better than GKE.

## Private database

| Item | Value |
|------|--------|
| Engine | Cloud SQL PostgreSQL **15** |
| Network | **Private IP only**; `ipv4_enabled=false`; **no authorized networks** |
| Runtime DB identity | `app_user` (password via Secret Manager) |
| Migration DB identity | `meridian-migrator@meridian-poc-ss-260913.iam` (**Cloud SQL IAM DB authentication**) |
| Runtime connectivity | **Cloud SQL Python Connector**, `IPTypes.PRIVATE` |
| Migrations | Cloud Run Job `meridian-migrate`, invoked from the laptop via `gcloud run jobs execute` |

**Migration result (live POC):** first execution applied `001_init.sql`; second execution safely skipped it (idempotent).

## Secrets

Exactly **two** Secret Manager secrets (DB password, synthetic third-party token). Runtime SA performs **request-time** reads of **both** secrets at **version 1** on each `/health`. Values supplied at apply via ephemeral TF variables / write-only arguments (**no plaintext secret in Terraform state**).

## Live health

```text
https://meridian-api-rgi4x3jv2a-ew.a.run.app/health
```

Validated: **HTTP 200**; exactly five fields — `candidate`, `commit`, `region`, `db`, `secret` — with `db=ok` and `secret=ok` (`commit=910c929`).

```bash
curl -sS https://meridian-api-rgi4x3jv2a-ew.a.run.app/health
# Migration (already executed for this POC; re-run is idempotent):
gcloud run jobs execute meridian-migrate --region=europe-west1 --project=meridian-poc-ss-260913 --wait
```

## CI / WIF

| Workflow | Status |
|----------|--------|
| `.github/workflows/ci.yml` | **Implemented** — push/PR to `main`; `contents: read`; unit tests; `terraform fmt` + `validate`; linux/amd64 image build **without** push; **no** GCP credentials; **no** apply |
| Authenticated Terraform PR plan (OIDC/WIF) | **NOT IMPLEMENTED** — bonus deferred due to time priority |

Do **not** treat WIF as operational. Design intent (plan-only SA, no JSON keys) remains documented in `DECISIONS.md` / `ASSUMPTIONS.md` as future work.

## Time spent

Active exercise time is tracked privately. Figures in working notes are **current / subject to final reconciliation** at submission close — total is **not** finalized in this README yet.

## With more time

WIF plan-only PR workflow, HA Cloud SQL, secret rotation automation, full deploy pipeline, VPC-SC, monitoring SLOs, restore drill, narrower production migration DB privileges.
