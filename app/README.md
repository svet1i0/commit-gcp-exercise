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
| `GCP_PROJECT` / `GOOGLE_CLOUD_PROJECT` | Project for Secret Manager |
| `DB_HOST` | Cloud SQL private IP |
| `DB_PORT` | Default `5432` |
| `DB_NAME` | Database name |
| `DB_USER` | Application DB user |
| `DB_PASSWORD` | Password (injected from Secret Manager at deploy) |
| `DB_PASSWORD_SECRET` | Secret resource/id for health secret check |
| `THIRD_PARTY_TOKEN_SECRET` | Second secret resource/id |

`/health` performs an independent SQL `SELECT 1` and independent Secret Manager reads of **both** secrets.

## Migrations

```bash
python3 migrations/migrate.py
```

Run via Cloud Run Job with migration identity (see repository README).
