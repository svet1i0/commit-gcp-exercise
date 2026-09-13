# Meridian Payments POC API

Minimal Python HTTP service for the Commit GCP Delivery Architect exercise.

## Local unit tests

```bash
cd app
python3 -m unittest discover -s tests -v
```

## Runtime environment

| Variable | Purpose |
|----------|---------|
| `PORT` | Listen port (Cloud Run sets this) |
| `COMMIT_SHA` | Full or short Git SHA of deployed source |
| `GCP_REGION` | Deployment region (e.g. `europe-west1`) |
| `GCP_PROJECT` / `GOOGLE_CLOUD_PROJECT` | Project for Secret Manager and Connector |
| `INSTANCE_CONNECTION_NAME` | Cloud SQL instance connection name (`project:region:instance`) |
| `DB_NAME` | Database name |
| `DB_USER` / `APP_DB_USER` | Runtime DB user (`app_user`) |
| `DB_PASSWORD_SECRET` | Secret Manager secret id for the DB password (request-time read) |
| `THIRD_PARTY_TOKEN_SECRET` | Second secret id (synthetic third-party token) |

There is **no** `DB_HOST` / raw `DB_PASSWORD` environment injection for the live path. The app opens Cloud SQL via the **Cloud SQL Python Connector** with **`IPTypes.PRIVATE`**, using `INSTANCE_CONNECTION_NAME`. The DB password is retrieved from **Secret Manager at request time** (version **1**), not mounted as a plaintext env var from Terraform.

`/health` performs an independent SQL `SELECT 1` and independent Secret Manager reads of **both** secrets.

## Migrations

```bash
python3 migrations/migrate.py
```

Run via Cloud Run Job `meridian-migrate` as GCP SA `meridian-migrator`, authenticating to PostgreSQL as IAM DB user `meridian-migrator@meridian-poc-ss-260913.iam` (Cloud SQL IAM DB authentication + Connector / `PRIVATE`).
