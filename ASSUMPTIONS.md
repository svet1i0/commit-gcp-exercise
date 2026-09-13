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
| A-009 | Password auth for app + migrator DB users | Understandable POC; exercise does not require IAM DB auth | Add IAM DB later | DOCUMENTED |
| A-010 | Synthetic data and token only | No customer production data | Change data handling | DOCUMENTED |
| A-011 | Org parent `626616300793` | Created during Free Trial/Cloud Identity | — | DOCUMENTED |
| A-012 | EU residency = configurable data resources in `europe-west1` | Not all control-plane metadata | Wording | DOCUMENTED |
| A-013 | Reviewer `user:gcp-devops@comm-it.cloud` until type confirmed | Brief lists email; org policy allows any domain | Switch to `group:` if needed | DOCUMENTED |
| A-014 | Initial apply via local ADC; WIF for plan-only Actions | Org policy bans SA keys | — | DOCUMENTED |
| A-015 | Public `/health` with dependency checks | Exercise requirement | Split in production | DOCUMENTED |

## Unanswered Meridian questions (Q1–Q34)

Treated as architect decisions except confirmed constraints: private DB; EU data. See internal customer-answer matrix (not published).
