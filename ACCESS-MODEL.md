# Human access model

This document separates **POC implementation** from **production recommendations**.

Google Groups, Cloud Identity groups, and **Workforce Identity Federation are NOT IMPLEMENTED** in this exercise. They are documented architecture only.

**Workload** identity (GitHub **Workload** Identity Federation → service accounts; Cloud Run runtime/migrator SAs) is separate from **human** access and must not be conflated with Workforce Identity Federation.

---

## Mandatory POC requirement (unchanged)

| Item | Value |
|------|--------|
| Address | `gcp-devops@comm-it.cloud` |
| Role | `roles/viewer` |
| Scope | project `meridian-poc-ss-260913` |
| Source type | **Unspecified** (not user / group / service account) |
| Working assumption | `group:gcp-devops@comm-it.cloud` |

Rationale for the working assumption: a single functional team email is supplied; principal type was not confirmed; group-first access is more maintainable for a team reviewer identity. **Not** “confirmed Google Group.” Successful IAM apply does not prove membership or login. This POC does not create or administer the group.

Terraform input `reviewer_member` can switch `user:` → `group:` without redesigning the IAM layer.

---

## Target architecture (conceptual)

```text
HUMAN / REVIEWER ACCESS
        |
        +-- direct user principal      (POC / exceptional cases)
        |
        +-- Google / Cloud Identity group
        |      |
        |      +-- internal members
        |      +-- external members where organization policy permits
        |
        +-- future Workforce Identity Federation principal/group
               |
               +-- enterprise IdP
               +-- partner IdP
               +-- contractor IdP

        -> project (or folder) IAM roles

WORKLOAD IDENTITIES (separate)
  GitHub Actions  -> Workload Identity Federation -> service account
  Cloud Run       -> dedicated runtime service account
  Migration Job   -> dedicated migration service account
```

---

## Three levels of human access

### Level 1 — Direct user IAM (exception / switchable)

Appropriate for emergency/time-limited access or when principal type is confirmed as a user.

Example alternate input (only if directed): `user:gcp-devops@comm-it.cloud` → `roles/viewer`

This POC’s exercise grant uses the **group:** working assumption below (Level 2 style), not a confirmed user principal.

Limitations of direct-user grants: poor lifecycle scalability; IAM policy grows with users; harder offboarding and audit.

### Level 2 — Access groups (recommended default)

Where identities can participate in Cloud Identity / Google Groups, grant IAM roles to **groups**, not individuals.

Example concept: `group:gcp-external-reviewers@company.example` → `roles/viewer`

Membership may include approved external identities if organization policy permits. GCP IAM stays stable while group membership changes.

**Suggested example group names only** (not created in this POC):

| Example group | Intended audience |
|---------------|-------------------|
| `gcp-viewers` | auditors, reviewers, read-only support |
| `gcp-developers` | application development (roles by workload need) |
| `gcp-devops` | platform / infrastructure operations (least privilege) |
| `gcp-security-auditors` | security and logging visibility |
| `gcp-external-reviewers` | short-lived partners/vendors; read-only by default |

Do **not** assign broad production role bundles without requirements. Prefer least privilege.

Operating principles:

- IAM roles are granted to access groups.
- Users are added/removed from groups.
- GCP IAM policies do not need to change for every joiner/leaver.
- Group membership is the identity lifecycle boundary.
- Group ownership should have multiple administrators.
- Membership should be periodically reviewed.
- External membership must be governed by organization policy.
- Privileged groups need stronger controls than read-only groups.
- Direct user IAM grants are exceptions, not the default production pattern.

### Level 3 — Workforce Identity Federation

**RECOMMENDED PRODUCTION EVOLUTION — NOT IMPLEMENTED**

For large global / multi-company environments where employees, contractors, partners, and vendors remain in existing enterprise IdPs (e.g. Microsoft Entra ID, Okta, compatible SAML/OIDC).

```text
External/Corporate IdP
       |
       +-- Developers group
       +-- DevOps group
       +-- Reviewers group
       |
Workforce Identity Federation
       |
group/attribute based authorization
       |
GCP IAM
```

Benefits: no Google account for every external person; joiner/mover/leaver stays with the identity owner; attribute/group authorization; cleaner cross-company access.

Exact Workforce principal / `principalSet` IAM member syntax is an extension to verify from current Google documentation before use — not invented in this POC variable validation.

---

## Environment / scope model (future)

Bind access groups at the **narrowest useful scope**:

```text
organization
  |
  +-- folder / environment
  |     |
  |     +-- prod
  |     +-- nonprod
  |
  +-- project
```

Prefer project/folder-level access appropriate to responsibility. Avoid organization-wide roles unless necessary.

Possible future group naming (not created here): `prod-viewers`, `prod-devops`, `nonprod-developers`, `security-auditors`, `external-reviewers`.

---

## Terraform interface (this repository)

| Input | Purpose |
|-------|---------|
| `reviewer_member` | Exercise grant gate → folds into generic human IAM as `exercise_reviewer` / `roles/viewer` |
| `human_access_bindings` | Optional additional named bindings (`role` + `members` set); default `{}` |

Both use additive `google_project_iam_member` resources (stable `for_each` keys). No authoritative project IAM policy.
