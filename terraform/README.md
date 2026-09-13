# Terraform

Infrastructure as code for the Meridian Payments GCP exercise.

## Layout

| Directory | Purpose |
|-----------|---------|
| `bootstrap/` | Creates GCS bucket and supporting resources for remote Terraform state |
| `poc/` | Exercise infrastructure (network, database, compute, IAM, secrets) |

## Intended flow

1. Apply `bootstrap/` with local state.
2. Migrate bootstrap state to the GCS backend it creates.
3. Apply `poc/` using remote state in GCS.

## Status

Exact resources, provider versions, and module structure remain **pending**:

- Meridian customer response (Q1–Q34)
- Official documentation verification
- Locked assumptions and blockers

Do not create `.tf` files until Phase 5–6 entry conditions are met.
