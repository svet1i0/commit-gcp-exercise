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
| **Instead** | Local ADC for apply; design for GitHub OIDC/WIF plan-only (**WIF not implemented** in this submission — time priority) |
| **Evidence** | Exercise PDF; org policy |

### 7. Default VPC

| Field | Detail |
|-------|--------|
| **Customer brief** | Put everything in default VPC |
| **Why wrong** | Misleading for private SQL; poor isolation |
| **Instead** | Custom-mode VPC + PSA |
| **Evidence** | Meridian authorized proper design; Cloud SQL private IP docs |

### 8. Privacy-safe Git history before publish

| Field | Detail |
|-------|--------|
| **Issue** | Early local commits used a personal author/committer email unsuitable for a public repository |
| **Correction** | Rewrote author/committer metadata to the verified GitHub noreply address `75417040+svet1i0@users.noreply.github.com` (tree preserved), then redacted remaining personal-email text in `AI-LOG.md` to `[redacted-personal-gmail]` |
| **Deploy impact** | Application/Terraform trees stayed byte-identical; Cloud Run was reconciled to public SHA `910c929` / image digest `sha256:43c6dc4b…` without schema/migration changes |
| **Evidence** | Private working traceability; live `/health` `commit=910c929` |

### 9. Direct-user-only reviewer access vs scalable human access

| Field | Detail |
|-------|--------|
| **Earlier reasoning** | Focused on granting the exercise reviewer as a direct IAM principal |
| **Why incomplete** | Direct-user-only IAM does not scale for global / multi-company environments (lifecycle, audit, offboarding) |
| **Correction** | Retain direct reviewer grant **only** for the POC requirement (`reviewer_member`); adopt **group-first** production recommendation; identify **Workforce Identity Federation** as future external-identity model |
| **Not claimed** | Groups and Workforce Identity Federation were **not** implemented in this POC |
| **Evidence** | `ACCESS-MODEL.md`; Terraform `human_access_bindings` + `reviewer_member` |

### 10. Per-request Cloud SQL Connector + timeout wrapper

| Field | Detail |
|-------|--------|
| **AI-assisted design** | Create/close a new Cloud SQL Python Connector on every `/health` request; wrap checks in a per-request `ThreadPoolExecutor` context manager with a short timeout |
| **Why wrong/risky** | Cold-start Connector refresh often exceeded ~5.5s; executor `with` exit waited on timed-out workers; logs only said “health check timed out” without stage; intermittent HTTP 503 with `db=error` / `secret=ok` |
| **Instead** | Process-scoped Connector (`refresh_strategy=lazy`) + short-lived DB connections; connector/driver `timeout`; process-scoped executor; structured stage diagnostics without secret payloads; default overall DB budget ~15s as secondary tolerance |
| **Evidence** | Prompt 1 log correlation; `app/main.py` repair |

## Something AI caught that I might have missed

Provider write-only arguments for both SQL user and Secret Manager versions remove the need for a split out-of-band secret bootstrap in the POC.

## Most useful prompt

The following prompt is quoted **verbatim** (PROMPT 2 — targeted health remediation, controlled deployment, reviewer access, and final evidence), as used for this remediation pass:

<pre>
# PROMPT 2 — TARGETED HEALTH REMEDIATION, CONTROLLED DEPLOYMENT, REVIEWER ACCESS, AND FINAL EVIDENCE

Use the completed PROMPT 1 report as the current source of truth.

The user explicitly authorizes the following reviewer binding as a documented working assumption:

group:gcp-devops@comm-it.cloud -&gt; roles/viewer

The exercise specifies the email address but does not confirm its principal type. Treat `group:` as a reasoned working assumption because it is a functional team address and group-based human access is the more maintainable model. Do not state that Commit confirmed it as a Google Group.

This prompt authorizes:

- careful modification of the existing application, tests, Terraform and public documentation;
- preservation and completion of the existing local human-access refactor;
- non-destructive validation;
- commit and push to the existing `main` branch;
- building a new immutable application image;
- a narrowly scoped Terraform apply for the Cloud Run application repair;
- creation of exactly one additive project Viewer binding for the reviewer group specified below.

It does NOT authorize:

- public Cloud SQL;
- authorized networks;
- accessing or printing secret payloads;
- additional secrets;
- service-account keys;
- broad IAM roles;
- WIF implementation;
- budgets, HA, multi-region or other bonus work;
- rewriting Git history;
- sending email.

## USER-CONTROLLED PARAMETERS

APPLY_HEALTH_DEPLOYMENT = YES

REVIEWER_MEMBER = group:gcp-devops@comm-it.cloud

REVIEWER_ROLE = roles/viewer

# Set only from confirmed time records or explicit user input.
# Never infer active work time from unattended wall-clock gaps.
FINAL_CONFIRMED_ACTIVE_MINUTES = UNSET

SEND_EMAIL = NO

## FIXED IDENTITY AND PROJECT ANCHORS

Expected GCP account:

[redacted-personal-email]

Forbidden old GCP identity:

[redacted-personal-email]

Expected project:

meridian-poc-ss-260913

Expected project number:

559006006849

Expected organization:

626616300793

Expected GitHub account:

svet1i0

Expected repository:

svet1i0/commit-gcp-exercise

Expected branch:

main

Expected repository Git identity:

Svetoslav Silkov
75417040+svet1i0@users.noreply.github.com

Expected Terraform:

1.16.2

Expected Google provider:

8.2.0

Expected region:

europe-west1

Public health endpoint:

https://meridian-api-rgi4x3jv2a-ew.a.run.app/health

## NON-NEGOTIABLE FUNCTIONAL CONTRACT

`GET /health` must remain public and return exactly these five fields:

- candidate
- commit
- region
- db
- secret

Required values and semantics:

- `candidate = "Svetoslav Silkov"`
- `commit` = short SHA of the source actually built and deployed
- `region = "europe-west1"`
- `db = "ok"` only after a real `SELECT 1` succeeds during that request
- `secret = "ok"` only after both required Secret Manager secrets are successfully read during that request
- no cached health result
- no secret values in responses or logs
- DB and secret checks must still be attempted independently
- return HTTP 503 with the same five fields when either dependency check fails

## PHASE 0 — PREFLIGHT AND CHANGE PRESERVATION

Before changing anything:

1. Read every applicable `AGENTS.md`.
2. Confirm all identities and anchors above.
3. Confirm local HEAD and `origin/main` relationship.
4. Record the complete existing dirty-tree file list.
5. Inspect all local diffs before editing.
6. Preserve the user’s existing human-access refactor and documentation work.
7. Do not overwrite unrelated local changes.
8. Confirm that no secret, credential, ADC content or old personal Gmail address would be published.

Stop immediately if:

- the active GCP or GitHub identity is wrong;
- the project or repository is wrong;
- `origin/main` advanced unexpectedly;
- an existing local modification cannot be safely reconciled.

Do not print tokens or credential content.

## PHASE 1 — REPAIR THE HEALTH-CHECK IMPLEMENTATION

Inspect the current application and tests before choosing the exact implementation.

The repair must satisfy all of the following requirements.

### 1. Connector lifecycle

- Do not create and close a new Cloud SQL Python Connector for every health request.
- Use one process-scoped Connector instance.
- Keep `refresh_strategy="lazy"` because this is Cloud Run.
- Keep private IP connectivity.
- Close the Connector safely when the application process terminates.
- A DB connection may still be opened and closed for each health request.
- Every request must still execute a genuine `SELECT 1`.
- Do not cache DB health results.

Do not add SQLAlchemy solely for this repair unless the existing dependency model or measured behavior clearly justifies it.

A process-scoped Connector with a fresh short-lived DB connection for each request is acceptable for this POC.

### 2. Real timeout behavior

Inspect the exact current `_run_with_timeout` implementation.

Do not use a per-request `ThreadPoolExecutor` context manager whose exit waits for the timed-out worker.

Use supported Connector and database-driver timeout facilities wherever possible. Verify parameter support against the installed package versions before adding keyword arguments. Do not guess driver parameters.

If an executor remains necessary:

- make its lifecycle process-scoped;
- keep its worker count bounded;
- do not assume `future.cancel()` terminates a running I/O operation;
- ensure underlying connector or driver operations have their own timeout;
- prevent unbounded accumulation of timed-out DB tasks;
- ensure the HTTP request can return after the declared overall health timeout.

A default overall DB health timeout around 15 seconds may be used as secondary cold-start tolerance, but increasing the timeout alone is not an acceptable fix.

Do not set Cloud Run minimum instances to 1 during the first repair.

### 3. Safe diagnostic logging

Add structured, privacy-safe diagnostics for the DB check.

Log only fields such as:

- event
- stage
- elapsed_ms
- timeout_sec
- exception_class
- outcome

Distinguish at least these stages where the implementation permits:

- db_password_read
- connector_initialization
- connector_acquisition
- database_connect
- select_1
- connection_close
- overall_db_check

Never log:

- secret values;
- tokens;
- passwords;
- full connection strings;
- credential objects;
- Authorization headers;
- raw ADC content.

Avoid raw exception messages if they could contain connection, credential or identity details. Exception class and sanitized stage information are sufficient.

### 4. Preserve secret behavior

Both required secrets must continue to be read during every `/health` request.

The DB-password secret read and third-party-token secret read must remain genuine runtime operations.

Do not:

- add a third secret;
- cache secret payloads for the health result;
- return payloads;
- log payloads.

### 5. Tests

Extend the existing tests to cover:

- successful five-field response;
- DB failure while secret succeeds;
- secret failure while DB succeeds;
- timeout behavior;
- exact response-key set;
- correct HTTP 200 and HTTP 503 behavior;
- process-scoped Connector reuse;
- DB connection close on success;
- DB connection close on failure;
- absence of sensitive values in logs;
- deployed commit value behavior.

Use a temporary virtual environment or the project’s documented dependency installation method.

The previous bare-system-Python `google` import error is not a product failure.

Run the same checks used by CI, including formatting, linting and tests.

Do not continue to deployment if tests fail.

## PHASE 2 — RECONCILE TERRAFORM AND HUMAN ACCESS

Review the existing local-only files and modifications:

- `ACCESS-MODEL.md`
- `terraform/poc/human_access.tf`
- `terraform/poc/iam.tf`
- `terraform/poc/variables.tf`
- `terraform/poc/terraform.tfvars.example`
- `README.md`
- `ASSUMPTIONS.md`
- `DECISIONS.md`
- `AI-LOG.md`

Keep the generic additive human-access model if it remains equivalent to the audited design:

- use `google_project_iam_member`;
- support explicit `user:` and `group:` principals;
- do not use an authoritative project IAM policy or binding;
- do not invent a Google Group;
- do not claim the group type was confirmed;
- do not implement Workforce Identity Federation;
- do not implement WIF resources;
- do not retain a duplicate reviewer resource.

Remove or replace the old unpublished `reviewer_viewer` definition so there is only one reviewer grant path.

Because neither reviewer Terraform resource address has ever been applied, do not add an unnecessary `moved` block.

Configure exactly this reviewer grant:

`group:gcp-devops@comm-it.cloud -&gt; roles/viewer`

The code and documentation must state that `group:` is a documented working assumption based on the functional team address and group-first access practice. It is not a customer-confirmed fact.

Use an additive IAM member resource only.

Do not create:

- a `user:gcp-devops@comm-it.cloud` binding;
- both `user:` and `group:` bindings;
- additional reviewer roles;
- project-level authoritative IAM resources.

Run:

- `terraform fmt -check`
- `terraform init` using the appropriate safe backend configuration
- `terraform validate`
- `terraform plan`

Use a temporary plan location outside the public repository.

The plan must contain:

- the expected Cloud Run revision/image/configuration update;
- exactly one additive reviewer `roles/viewer` member;
- no unexpected infrastructure changes.

Stop if the plan proposes unexpected changes to:

- Cloud SQL networking or public IP;
- secrets or secret versions;
- secret payloads;
- service accounts;
- service-account keys;
- VPC or Private Services Access;
- migration identity;
- unrelated APIs.

## PHASE 3 — DOCUMENTATION CORRECTIONS BEFORE PUBLICATION

### AI-LOG.md

The exercise requires the most useful AI prompt to be quoted verbatim.

Replace the abbreviated prompt containing an ellipsis with the full exact text of a prompt that was genuinely used.

Prefer the complete text of this PROMPT 2 if it is selected as the most useful prompt.

The quoted prompt must be genuinely verbatim:

- no ellipsis;
- no paraphrase;
- no omitted middle sections;
- no reconstructed wording.

If the exact prompt text cannot be obtained from the current conversation or input, stop this documentation item and report the blocker. Do not invent it.

Preserve:

- tools used;
- at least three genuine rejected or corrected AI proposals;
- AI-caught gaps;
- honest AI-generated-code percentage.

Add the discovered per-request Connector lifecycle and ineffective timeout-wrapper design as a genuine corrected AI-assisted finding if not already covered.

### README.md

Keep `README.md` under one page.

It must contain:

- architecture and compute choice;
- repository and run information;
- health URL;
- deployed source SHA;
- time spent;
- improvements with more time.

Do not claim universal or permanent health.

Before final validation, use provisional factual wording.

After successful validation, state only what was measured, for example:

`Post-deployment validation: 12/12 requests returned HTTP 200 at &lt;timestamp&gt;.`

If validation still shows failures, state that honestly and mark the project as not ready.

If `FINAL_CONFIRMED_ACTIVE_MINUTES=UNSET`:

- do not invent a total;
- do not derive it from unattended wall-clock time;
- keep time reconciliation explicitly outstanding;
- report that final submission remains blocked on confirmed active minutes.

### ASSUMPTIONS.md

Record explicitly:

- the exercise specifies `gcp-devops@comm-it.cloud`;
- the principal type was not confirmed;
- the implementation uses `group:gcp-devops@comm-it.cloud` as a documented working assumption;
- group-first access is preferred for a functional reviewer identity;
- successful IAM application does not prove group membership or reviewer login;
- confirmation by Commit remains the definitive validation.

### DECISIONS.md and ACCESS-MODEL.md

Reconcile them with the actual implementation.

Clearly separate:

- deployed;
- published but not deployed;
- local-only;
- production recommendation;
- not implemented.

Do not present WIF, Google Groups administration, Workforce Identity Federation, budgets, HA, multi-region or production DR as implemented.

The Terraform configuration may grant access to an externally managed Google Group, but this project does not create or administer that group.

Do not publish:

- `sources/`;
- `working/`;
- `.tools/`;
- state files;
- plan files;
- ADC;
- credentials.

## PHASE 4 — COMMIT, PUSH, BUILD, AND DEPLOY

Only continue if `APPLY_HEALTH_DEPLOYMENT=YES` and all local checks pass.

1. Review the complete diff.
2. Confirm publication safety.
3. Confirm repository-local Git author and noreply email.
4. Commit without amending or rewriting existing history.
5. Push to `origin/main`.
6. Wait for static CI to complete successfully.
7. Stop if CI fails.

Build the application image from the exact committed source.

Requirements:

- record the full source commit SHA;
- embed the correct short SHA in the application;
- obtain the immutable image digest;
- verify the built image corresponds to that source;
- never deploy a mutable tag as the final Terraform image reference.

Update and apply Terraform using the immutable image digest and correct deployed source SHA.

Before apply, review the final plan.

Allowed cloud changes:

- a new Cloud Run revision or configuration required by the health repair;
- exactly one additive reviewer binding:
  `group:gcp-devops@comm-it.cloud -&gt; roles/viewer`

No other infrastructure mutation is allowed.

If the plan contains anything else, stop before apply and report it.

After apply:

- verify the serving revision;
- verify 100% intended traffic;
- verify the runtime service account is unchanged;
- verify the private VPC attachment is unchanged;
- verify SQL remains private-only;
- verify the live image digest;
- verify the embedded deployed SHA;
- verify Terraform state contains the reviewer member.

Do not rerun schema migrations unless a concrete application change requires it. The existing two successful and idempotent executions are sufficient evidence.

## PHASE 5 — HEALTH VALIDATION

Validate the new revision without accessing secret payloads.

Perform:

1. One request correlated with a confirmed new-instance startup log, if possible.
2. At least 12 sequential public `GET /health` requests.
3. Record for each request:
   - UTC timestamp;
   - HTTP status;
   - duration;
   - candidate;
   - commit;
   - region;
   - db;
   - secret;
   - exact key count.
4. Confirm every response has exactly five fields.
5. Confirm no timeout or DB-failure warning appears in the corresponding sanitized logs.
6. Confirm a non-health route still returns the intended HTTP 404 behavior.

Success criteria:

- 12/12 HTTP 200;
- `db=ok` and `secret=ok` on every request;
- exact five-field contract on every request;
- correct candidate, commit and region;
- at least one validated cold or new-instance request if startup logs prove that classification;
- no correlated timeout warning.

Do not claim a cold-start test unless a new-instance or startup log proves it.

If any request fails:

- do not call the issue fixed;
- use the new stage timings to identify the exact slow stage;
- make at most one additional narrowly targeted correction;
- repeat tests, commit, CI, immutable build, Terraform plan/apply and validation;
- if failures persist, stop and report the blocker honestly.

Do not enable minimum instances automatically.

Do not increase timeouts repeatedly without stage evidence.

## PHASE 6 — REVIEWER IAM VERIFICATION

Apply exactly:

`group:gcp-devops@comm-it.cloud -&gt; roles/viewer`

Verify using a read-only IAM policy query after Terraform apply.

Report:

- exact member string;
- exact role;
- Terraform resource address;
- whether Terraform state contains the resource;
- whether the live project IAM policy contains the binding.

Do not claim that the principal type was externally confirmed.

Do not claim that the reviewer successfully logged in unless Commit verifies it.

If the `group:` principal is rejected:

- do not try `user:` automatically;
- do not create both bindings;
- do not use a service account;
- do not grant another role;
- report the sanitized error;
- request explicit user direction.

## PHASE 7 — FINAL DRIFT AND PUBLICATION VALIDATION

After all authorized changes:

- run Terraform plan with detailed exit code;
- require no unexpected drift;
- verify Git working-tree status;
- verify local HEAD equals `origin/main`;
- verify final CI is green;
- verify the public repository contains the intended files;
- verify forbidden private directories and files are absent;
- scan tracked content for credentials, private keys, secret payloads and the old personal Gmail address;
- do not print any matched sensitive content;
- verify runtime and migrator `USER_MANAGED` key counts remain zero;
- verify no WIF resources exist;
- verify documentation states that WIF is not implemented.

If a final documentation-only commit is needed after live validation:

- commit and push it normally;
- wait for CI again;
- do not rebuild the application solely because documentation changed;
- clearly distinguish repository HEAD from deployed source SHA.

## PHASE 8 — TIME AND SUBMISSION

If `FINAL_CONFIRMED_ACTIVE_MINUTES` is set:

- reconcile it with `TIMELOG.md`;
- show the arithmetic;
- ensure the total is not fabricated;
- update README with the confirmed total;
- state honestly if the 300-minute limit was exceeded.

If it is `UNSET`:

- do not finalize the time claim;
- report it as a mandatory remaining item.

Do not send an email.

Prepare only a proposed submission summary containing:

- public repository URL;
- live health URL;
- GCP project ID;
- deployed source SHA;
- immutable image digest;
- reviewer access status;
- reviewer principal-type assumption;
- confirmed active time or explicit pending status;
- remaining limitations.

## REQUIRED FINAL REPORT

Return:

A. Preflight result  
B. Preserved local changes  
C. Application root cause and exact repair  
D. Test results  
E. Terraform plan summary  
F. Git commit, push and CI evidence  
G. Image and deployment anchors  
H. Health validation table  
I. Reviewer IAM result  
J. Terraform drift result  
K. Documentation and publication-safety result  
L. Time reconciliation status  
M. Mandatory requirements status  
N. Remaining blockers  
O. Proposed submission summary  

Explicitly list every mutation performed.

Then STOP.

Do not send email.
Do not implement WIF.
Do not access or print secret payloads.
Do not fall back from `group:` to `user:` automatically.
</pre>

## Estimate of AI-generated code

Roughly **70–85%** of repository file text was AI-drafted in Cursor; all Terraform and health-contract behavior reviewed and adjusted by Svetoslav before apply/publish.
