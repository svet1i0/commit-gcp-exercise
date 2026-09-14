# Database migration paths

This document separates **implemented POC capabilities** from **planned production evolution**. Nothing here creates GCS buckets, DMS jobs, Storage Transfer resources, or import automation unless explicitly marked as implemented.

**Implemented schema migrations** remain the Cloud Run Job workflow (`meridian-migrate`). Cloud SQL Studio is optional for lightweight inspection; it is **not** the versioned migration engine.

---

## Decision table

| Need | Path | Status |
|------|------|--------|
| Controlled schema change (DDL, versioned SQL) | Cloud Run Job `meridian-migrate` | **IMPLEMENTED** |
| Small sanitized sample data | Controlled import or migration Job, depending on content | **PLANNED — case-by-case** |
| Large offline SQL dump with acceptable downtime | Dedicated private GCS bucket + Cloud SQL import | **PLANNED — NOT IMPLEMENTED** |
| Low-downtime full database move / ongoing replication | Database Migration Service (DMS) / CDC | **PLANNED — SOURCE DETAILS AND CUSTOMER APPROVAL REQUIRED** |

---

## A. Versioned schema migrations — IMPLEMENTED

**Purpose:** controlled, repeatable schema evolution — not bulk production data loads.

| Item | Detail |
|------|--------|
| SQL artifacts | Versioned files in `app/migrations/` (e.g. `001_init.sql`) |
| Initiation | Developer runs from laptop (requires permission to execute the Job) |
| Execution | Remote inside GCP on private network path |
| Identity | GCP SA `meridian-migrator`; PostgreSQL IAM DB user `meridian-migrator@meridian-poc-ss-260913.iam` |
| Evidence | Job execution history + Cloud Logging |

```bash
gcloud run jobs execute meridian-migrate \
  --project meridian-poc-ss-260913 \
  --region europe-west1 \
  --wait
```

Inspect result:

```bash
gcloud run jobs executions list --job=meridian-migrate \
  --project meridian-poc-ss-260913 --region europe-west1
```

**POC note:** migrator holds `cloudsqlsuperuser` for deterministic DDL within the time budget. Production would replace that with a custom PostgreSQL role limited to required schema operations.

---

## B. One-off large SQL dump — PLANNED, NOT IMPLEMENTED

Future conceptual path when a full or large PostgreSQL dump must move from AWS (RDS/Aurora) or another source with acceptable import downtime:

```text
AWS PostgreSQL / RDS / Aurora
  -> pg_dump-compatible .sql or .sql.gz
  -> dedicated private GCS migration-staging bucket
  -> Cloud SQL import (gs:// URI)
  -> validation
  -> controlled deletion / lifecycle expiry
```

### Required controls (design only — none deployed by this POC)

- **Never** commit real database dumps to Git.
- **Never** store dumps in the application container image or the Terraform state bucket (`…-tfstate`).
- Use a **dedicated** bucket with uniform bucket-level access and public access prevention.
- Use **immutable object names** (timestamp + source identifier); no wildcards in import URIs.
- Apply **short lifecycle retention** only after business and audit requirements are confirmed.
- Import URI must be an exact `gs://bucket/object.sql` or `gs://bucket/object.sql.gz` — **no wildcards**.
- Grant the **Cloud SQL managed service account** only verified bucket-level object read/list permissions required for import.
- The **human or import automation identity** separately needs Cloud SQL import permission (`roles/cloudsql.admin` or a narrower custom role after review).
- Verify dump compatibility before import: PostgreSQL major version, extensions, ownership/`ALTER OWNER` statements, encoding, and locale.
- Perform row count, schema, and application reconciliation after import.
- Delete or expire staging objects after successful validation.

**Status:** no migration-staging bucket, import helper, or dump pipeline exists in this repository or project.

Large-data transfer method depends on unresolved customer questions (internal matrix Q9–Q11) and source constraints.

---

## C. Database Migration Service / CDC — PLANNED, DETAILS REQUIRED

Use **DMS** when low downtime or continuous replication is required instead of a single offline import.

**Status:** `PLANNED — SOURCE DETAILS AND CUSTOMER APPROVAL REQUIRED`

Do **not** create DMS connectivity profiles, replication jobs, Storage Transfer Service jobs, or AWS federation resources in this POC.

### Prerequisites before any DMS design is finalized

| Area | Must be confirmed |
|------|-------------------|
| Source engine | Exact engine and version (e.g. Aurora PostgreSQL x.y) |
| Connectivity | Approved path from DMS to source (VPN, private connectivity, allowlists) |
| Replication | Logical decoding / replication settings; slot impact on source storage and I/O |
| Identity | Approved migration service account and least-privilege source credentials |
| Compatibility | Extensions, features, data types, generated columns, partitioning |
| Schema objects | Tables without primary keys, large LOBs, unsupported types |
| Cutover | Acceptable downtime, write freeze strategy, DNS/application switch owner |
| Validation | Row counts, checksums, application smoke tests — named owner |
| Rollback | Strategy if cutover fails; post-cutover write direction |

DMS is the path for **full database migration with minimal downtime**, not day-to-day schema DDL. Day-to-day schema changes remain path **A** (Cloud Run Job).

---

## Relationship to developer access

Schema migrations (path A) do **not** require developers to hold PostgreSQL superuser or direct laptop TCP connectivity to Cloud SQL. Developers need permission to **execute** the migration Job; the Job uses the dedicated migrator identity inside the VPC.

Optional Cloud SQL Studio access for inspection is documented in [ACCESS-MODEL.md](ACCESS-MODEL.md). Studio does not replace path A for versioned migrations.
