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

Mandatory: `gcp-devops@comm-it.cloud` → project `roles/viewer`. Source does **not** specify principal type (user vs group).

**Working assumption (not customer-confirmed):** `group:gcp-devops@comm-it.cloud` via `reviewer_member` → additive `google_project_iam_member.human_access`. Reason: functional team address + group-first access practice. Successful IAM apply does **not** prove group membership or reviewer login.

This project does **not** create or administer the Google Group. Switching to `user:` would be an input-only change if Commit directs.

See [ACCESS-MODEL.md](ACCESS-MODEL.md).

## Group-first human access model (D-023)

**Decision:**

- POC reviewer grant uses documented `group:` working assumption for the exercise email.
- Production access is **group-first** (Level 2); identity membership managed outside project IAM.
- **Workforce Identity Federation** is the preferred larger-scale evolution for external enterprise identities (Level 3) — **NOT IMPLEMENTED**.
- Workload Identity Federation (GitHub → SA) remains separate from human federation — **NOT IMPLEMENTED**.

**Rationale:** scalable onboarding/offboarding; stable IAM policies; auditability; separation of identity lifecycle from cloud resource deployment; least privilege; multi-company support.

**Alternatives rejected:** individual IAM grants for every employee/vendor; broad organization-level roles; creating Google accounts manually for every external user; conflating human Workforce federation with workload WIF; inventing confirmation of principal type.
