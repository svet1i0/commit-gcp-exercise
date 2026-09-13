# ASSUMPTIONS

| ID | Assumption | Reason | Impact if false | Status |
|----|------------|--------|-----------------|---------|
| A-001 | Cloud Run acceptable for POC API | Stateless health service | Rework compute | DOCUMENTED |
| A-002 | Custom VPC + PSA (not default VPC) | Private SQL; brief default-VPC rejected | Network redesign | DOCUMENTED |
| A-003 | Direct VPC egress for service and job | Provider schema verified | Connector fallback | DOCUMENTED |
| A-004 | Cloud Run Job for developer migrations | Private DB; laptop has no route | Alternate path | DOCUMENTED |
| A-005 | Single region `europe-west1` | Meridian EU constraint | Relocate | DOCUMENTED |
| A-006 | Single-zone Cloud SQL `db-f1-micro` | Cost/time POC | Upsize if quota/API rejects | DOCUMENTED |
| A-007 | HTTP 503 + five fields on dependency failure | Brief silent on errors | Change contract | DOCUMENTED |
| A-008 | Ephemeral vars + `password_wo` / `secret_data_wo` | Avoid state persistence | Out-of-band secrets | DOCUMENTED |
| A-009 | Runtime `app_user` password auth; migrator uses Cloud SQL IAM DB user | Separate migration identity without a third secret | Change identities | DOCUMENTED |
| A-010 | Synthetic data and token only | No customer production data | Change data handling | DOCUMENTED |
| A-011 | Org parent `626616300793` | Created during Free Trial/Cloud Identity | — | DOCUMENTED |
| A-012 | EU residency = configurable data resources in `europe-west1` | Not all control-plane metadata | Wording | DOCUMENTED |
| A-013 | Reviewer principal type unresolved; **working assumption** `group:gcp-devops@comm-it.cloud` (not confirmed as a Google Group) | Exercise lists functional team email only; group-first access is more maintainable; Q34 unanswered | Switch input to `user:` only if Commit directs | DOCUMENTED |
| A-014 | Initial apply via local ADC; WIF plan-only Actions intended but **NOT IMPLEMENTED** | Org policy bans SA keys; time priority deferred bonus | Add WIF later | DOCUMENTED |
| A-015 | Public `/health` with dependency checks | Exercise requirement | Split in production | DOCUMENTED |
| A-016 | Production group names / Workforce Identity Federation are recommendations only — **not implemented**; POC may bind an **externally managed** group email without creating/administering that group | Time-boxed POC; no customer identity directory control | Create groups/federation later | DOCUMENTED |
| A-017 | External group membership depends on identity provider + organization policy (`allowedPolicyMemberDomains` etc.); IAM apply ≠ login proof | Org allows broad domains in this Free Trial org | External reviewers blocked if policy tightens or membership empty | DOCUMENTED |
| A-018 | Final active minutes remain outstanding until `FINAL_CONFIRMED_ACTIVE_MINUTES` is provided | Time tracking paused; do not invent totals | Submission time claim blocked | DOCUMENTED |

## Unanswered Meridian questions (Q1–Q34)

Treated as architect decisions except confirmed constraints: private DB; EU data. See internal customer-answer matrix (not published).
