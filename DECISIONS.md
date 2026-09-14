# DECISIONS

## Compute: Cloud Run (not GKE)

GKE adds cluster ops cost and time. Cloud Run fits a single stateless HTTP API with Direct VPC egress.

## Network: custom VPC (not default)

Customer brief suggested default VPC. Incorrect simplification for PSA/private SQL. Dedicated custom-mode VPC with an explicit subnet and Private Services Access.

**Firewall:** no custom VPC firewall rule was required for this POC path (Cloud Run Direct VPC egress + private Cloud SQL / PSA). Production hardening may still add explicit deny/allow rules.

## Database: Cloud SQL PostgreSQL, private only

Exercise requires Cloud SQL. Meridian: not internet-reachable. Implementation: PostgreSQL 15, private IP, `ipv4_enabled=false`, no `authorized_networks`, PSA peering.

## Connectivity: Direct VPC egress + Cloud SQL Connector

No Serverless VPC Access connector. Confirmed for service and job in provider google 8.2.0.

Application and migration code use the **Cloud SQL Python Connector** with **`IPTypes.PRIVATE`** (not raw host/password TCP to a private IP env var).

## Secrets: Secret Manager + write-only Terraform

Two secrets. Ephemeral sensitive variables feed `password_wo` and `secret_data_wo` so payloads are not stored in plan/state. Org policy also forbids SA JSON keys. Runtime reads both secrets at request time (version 1).

## Auth to GCP from GitHub: WIF/OIDC (design) — NOT IMPLEMENTED

Rejected long-lived JSON keys (exercise + `disableServiceAccountKeyCreation`). Intended pattern: plan-only SA via GitHub OIDC/WIF; local ADC for apply.

**Status:** authenticated Terraform PR plan / WIF is **NOT IMPLEMENTED** (bonus deferred due to time priority). Static local CI (`ci.yml`) is the delivered automation.

## Migrations: Cloud Run Job + separate IAM database identity

Developers trigger from laptop via `gcloud run jobs execute`. The job runs as GCP SA `meridian-migrator` and authenticates to Cloud SQL as a distinct PostgreSQL IAM database user:

`meridian-migrator@meridian-poc-ss-260913.iam`

(Cloud SQL PostgreSQL truncates `.gserviceaccount.com` from the SA email.)

Runtime uses built-in `app_user` with the existing DB-password secret. No third Secret Manager secret.

**POC privilege note:** `cloudsqlsuperuser` is granted **only** to the migration IAM DB identity so schema migrations are deterministic within the time budget. The runtime `app_user` must **not** receive `cloudsqlsuperuser` or schema-owner privileges (DML grants only after migrate). **Production would narrow migration DB privileges** (replace `cloudsqlsuperuser` with a custom role limited to required schema operations).

Live result: first job run applied `001_init.sql`; second run safely skipped it.

## POC vs production

Single-zone, no HA/DR demo, no multi-region, no AWS CDC. Production would add HA, rotation, VPC-SC, private health diagnostics, stronger CI/CD, and narrower migrator privileges.

## AWS → GCP framing

POC proves the **target** GCP pattern Meridian would evaluate; source AWS remains out of scope for implementation.

## Staging apply

Stage A: APIs, network, SQL, secrets, IAM, Artifact Registry (`enable_workloads=false`).  
Stage B: push image by digest, set `enable_workloads=true`.

## Reviewer (POC)

Mandatory: `gcp-devops@comm-it.cloud` → project `roles/viewer`.

**Commit confirmation:** address is an individual Google/Cloud Identity user (not intended as a team Google Group).

**Google Cloud IAM fact (verified on apply):** requesting `user:gcp-devops@comm-it.cloud` returns HTTP 400 — principal is of type **group** and must be granted as `group:gcp-devops@comm-it.cloud`. The attempted `user:` binding was **not** created. The temporary removal of `group:` was restored so Viewer access was not left broken.

**Deployed:** `group:gcp-devops@comm-it.cloud` → `roles/viewer` via `reviewer_member`. Do not retain a failed `user:` binding. Successful IAM apply does **not** prove interactive reviewer login.

**Production direction (unchanged):** group-first access for developer and operational teams (see D-023). Treat any true individual-user grant as an exception only after Google IAM accepts `user:` for that principal.

See [ACCESS-MODEL.md](ACCESS-MODEL.md).

## Group-first human access model (D-023)

**Decision:**

- POC exercise reviewer Viewer grant is deployed as **`group:gcp-devops@comm-it.cloud`** because that is the only principal type Google IAM accepts for this email, despite Commit’s individual-user confirmation.
- Production access remains **group-first** (Level 2); identity membership managed outside project IAM.
- **Workforce Identity Federation** is the preferred larger-scale evolution for external enterprise identities (Level 3) — **NOT IMPLEMENTED**.
- Workload Identity Federation (GitHub → SA) remains separate from human federation — **NOT IMPLEMENTED**.

**Rationale:** scalable onboarding/offboarding for teams; stable IAM policies; auditability; least privilege. The exercise email’s Google-side principal type must match the IAM member prefix or the grant fails.

**Alternatives rejected:** forcing `user:` after API rejection (breaks apply); leaving the project with no Viewer grant after a failed switch; inventing interactive login proof.

## Developer database access (group-first) — DOCUMENTED ONLY

- Production direction: grant IAM to **customer-confirmed Google Groups**, not individual users.
- Four layers apply independently: identity membership → GCP IAM → network connectivity → PostgreSQL GRANTs.
- Proposed Studio role: `roles/cloudsql.studioUser` (do not add redundant `roles/cloudsql.instanceUser`).
- Local tools require an approved private network path; Auth Proxy alone is insufficient.
- **No developer group IAM or PostgreSQL privileges are deployed in this POC.**

See [ACCESS-MODEL.md](ACCESS-MODEL.md).

## Data migration paths — schema vs bulk vs DMS

| Path | Mechanism | Status |
|------|-----------|--------|
| Versioned schema DDL | Cloud Run Job `meridian-migrate` | **IMPLEMENTED** |
| Large SQL dump import | Dedicated private GCS + Cloud SQL import | **PLANNED — NOT IMPLEMENTED** |
| Low-downtime / CDC | Database Migration Service | **PLANNED — SOURCE DETAILS AND CUSTOMER APPROVAL REQUIRED** |

Large-data method depends on Q9–Q11 and source constraints. No migration-staging bucket or DMS resources exist.

See [DATABASE-MIGRATION.md](DATABASE-MIGRATION.md).

## Health reliability and concurrency (POC)

- Process-scoped Cloud SQL Connector (`lazy`) + process-scoped Secret Manager client; short-lived DB connections and request-time secret payload reads every `/health`.
- DB and secret checks **start concurrently** on a four-worker process-scoped executor; wall-clock budget ≈ max(DB, secret), not the serial sum.
- Cloud Run `max_instance_request_concurrency = 2` deliberately aligns with 2 concurrent requests × 2 dependency tasks = 4 workers.
- `min_instance_count` remains 0 (no permanent warm capacity claim).

