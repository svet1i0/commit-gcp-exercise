# AI-LOG

## Tools used

| Tool | Purpose |
|------|---------|
| Cursor (Composer) | Clarification drafting, Phase 2–4 reconciliation, local implementation |
| Terraform CLI 1.16.2 | fmt, init -backend=false, validate, provider schema |
| Google Cloud SDK 584 | Auth, project create (authorized), read-only discovery |
| GitHub CLI | Auth as `svet1i0` |
| Python 3.12/3.14 unittest | Application unit tests |

## Rejected or corrected AI proposals

### 1. Overly long clarification email to Meridian

| Field | Detail |
|-------|--------|
| **AI proposal** | Comprehensive 34-question discovery email |
| **Why wrong** | Meridian: email “far too long”; did not read; not GCP people |
| **Instead** | Extract two hard constraints; architect decisions for the rest; concise future client communication |
| **Evidence** | `sources/Meridian-Response.md` |

### 2. Out-of-band secret bootstrap as primary path

| Field | Detail |
|-------|--------|
| **AI proposal** | If write-only unverified, populate secrets out-of-band |
| **Why risky** | Premature fallback before checking provider |
| **Instead** | Pin google 8.2.0; use ephemeral + `password_wo` / `secret_data_wo` |
| **Evidence** | Phase 3 schema verification |

### 3. Uncertainty on Cloud Run Job Direct VPC (GCP guide omits Terraform for jobs)

| Field | Detail |
|-------|--------|
| **AI proposal** | Leave job Direct VPC unconfirmed because Console/gcloud-only in GCP guide |
| **Why wrong** | Provider schema confirms job `network_interfaces` |
| **Instead** | Keep Direct VPC for service and job |
| **Evidence** | Provider v8.2.0 docs/schema |

### 4. Expired / wrong GCP identity and billing

| Field | Detail |
|-------|--------|
| **AI / early state** | Work proceeded against `[redacted-personal-gmail]` and a closed billing account |
| **Why wrong** | Free Trial and org live under `[redacted-personal-email]` / open billing `012DF5-…A3C3` |
| **Instead** | Re-auth; create `meridian-poc-ss-260913` under org; never use prior projects |
| **Evidence** | Phase 4 verification |

### 5. “No organization” assumption

| Field | Detail |
|-------|--------|
| **AI / early assumption** | Free Trial with no org parent |
| **Why wrong** | Org `626616300793` (`svetoslav-silkov-org`) exists |
| **Instead** | Parent project under organization; document in ASSUMPTIONS |
| **Evidence** | `gcloud organizations list` |

### 6. Service-account JSON key (customer brief + AI temptation)

| Field | Detail |
|-------|--------|
| **Proposal** | Store SA JSON key in GitHub Secrets for Terraform |
| **Why wrong** | Exercise forbids long-lived credentials; org policy `disableServiceAccountKeyCreation` / upload |
| **Instead** | Local ADC for apply; GitHub OIDC/WIF for plan-only |
| **Evidence** | Exercise PDF; org policy |

### 7. Default VPC

| Field | Detail |
|-------|--------|
| **Customer brief** | Put everything in default VPC |
| **Why wrong** | Misleading for private SQL; poor isolation |
| **Instead** | Custom-mode VPC + PSA |
| **Evidence** | Meridian authorized proper design; Cloud SQL private IP docs |

## Something AI caught that I might have missed

Provider write-only arguments for both SQL user and Secret Manager versions remove the need for a split out-of-band secret bootstrap in the POC.

## Most useful prompt

> Cursor prompt — Phase 3 capability verification and version lock … Verify … google_secret_manager_secret_version.secret_data_wo … google_sql_user.password_wo …

(Phase 3 master prompt — locked the secret and Direct VPC boundaries before implementation.)

## Estimate of AI-generated code

Roughly **70–85%** of repository file text was AI-drafted in Cursor; all Terraform and health-contract behavior reviewed and adjusted by Svetoslav before apply/publish.
