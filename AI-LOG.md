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


### 11. Verbatim publication vs personal-identity exclusion

| Field | Detail |
|-------|--------|
| **AI / prompt contradiction** | An earlier instruction required both a verbatim useful-prompt quote and exclusion of personal identity material from the public tree |
| **Why wrong** | Publishing an unsanitized prompt that embeds personal Gmail-style identifiers cannot simultaneously satisfy a no-personal-email publication rule |
| **Correction** | Prompt 3 + 3A: sanitize all reachable history; place Prompt 3/3A (which contain no personal Gmail addresses) as the most useful prompt; add a CI publication-safety guard |
| **Evidence** | Expanded history rewrite; `scripts/check_publication_safety.py` |

## Something AI caught that I might have missed

Provider write-only arguments for both SQL user and Secret Manager versions remove the need for a split out-of-band secret bootstrap in the POC.

## Most useful prompt

The following sequence is quoted **verbatim**: Prompt 3 (final functional/reliability/publication closeout), immediately followed by Prompt 3A (expanded history-rewrite authorization).

Note: the original Prompt 3 two-commit rewrite boundary correctly **STOPPED** because personal Gmail-style identifiers also existed in earlier main history (first affected root commit). The user then explicitly authorized a narrow expanded rewrite of every main commit from that first affected commit through HEAD (`EXPANDED_REWRITE_AUTHORIZED=YES`, `ORPHAN_HISTORY_AUTHORIZED=NO`).

<pre>
CURSOR PROMPT 3 — FINAL FUNCTIONAL, RELIABILITY, AND PUBLICATION CLOSEOUT

AUTHORIZATION AND PRIORITY

HISTORY_REWRITE_AUTHORIZED=YES

The user explicitly authorizes:

- rewriting exactly the last two public commits currently reachable from main;
- one force-with-lease update of origin/main;
- rebuilding the container from the new clean source SHA;
- Terraform redeployment of the Cloud Run service and migration-job image;
- final migration, health, concurrency, IAM, drift, CI, and publication-safety validation.

Primary priority: produce a fully functional, defensible Delivery Architect POC as quickly and safely as possible.

Do not reconcile or finalize active minutes in this pass. Do not send any email.

OPERATING MODE

Work autonomously through the complete sequence unless a STOP condition below occurs.

Use evidence, not assumptions. Never print or publish:

- personal email addresses;
- active GCP login identity;
- secret payloads;
- Terraform-sensitive values;
- access tokens, credentials, cookies, ADC contents, private keys, or connection strings.

You may print only safe status such as ACCOUNT_MATCH=yes/no, counts, resource names already public, hashes, stages, exception classes, HTTP results, and elapsed durations.

Do not access Secret Manager payloads manually. The deployed application may read the two required secrets as part of its genuine request-time checks. Reuse already configured secure Terraform inputs without displaying them. If those inputs are unavailable, STOP and request them through an approved secure mechanism.

KNOWN SAFE ANCHORS

Repository:
https://github.com/svet1i0/commit-gcp-exercise

Branch:
main

Expected current public HEAD before rewrite:
6124c036d8060618ed13a91c780943f1f83a2c25

Its parent application/access commit:
2ef5b73638c6f9d0e517073e42791fc4d3c8a243

Last clean ancestor before those two commits:
3d519e379d71b1a338288886d8b9952f96555414

GCP project:
meridian-poc-ss-260913

Region:
europe-west1

Current deployed application source:
2ef5b73638c6f9d0e517073e42791fc4d3c8a243

Current image digest:
sha256:54835dd941d0ac456b62ebfab068730c3f2f4f774319bd2ea9fa1c9fe18c2260

Current serving revision:
meridian-api-00003-ssq

Health endpoint:
https://meridian-api-rgi4x3jv2a-ew.a.run.app/health

Reviewer binding that must remain unchanged:
group:gcp-devops@comm-it.cloud → roles/viewer

Reviewer principal type remains a documented working assumption, not a confirmed fact.

CURRENT PROVEN STATE

- The health remediation from Prompt 2 is deployed.
- Twelve sequential requests returned HTTP 200 with the exact five-field contract.
- The process-scoped Cloud SQL Connector repair eliminated the observed cold-start timeout.
- Terraform drift was zero after deployment.
- Reviewer Viewer IAM is in Terraform state and live IAM.
- Cloud SQL is private-only.
- Runtime reads both required secrets at request time.
- WIF is not implemented and remains out of scope.
- The current public AI-LOG reproduces personal email identifiers through the verbatim Prompt 2 block.
- Cloud Run has no explicit maximum request concurrency, while the application uses a four-worker dependency-check executor.
- Cloud Run’s default concurrency and the four-worker executor are not safely capacity-aligned.

OBJECTIVES

Complete all of the following in one controlled cycle:

1. Remove personal email identifiers from the current public tree and from the rewritten last-two-commit main history.
2. Add a privacy-safe CI publication check preventing recurrence.
3. Align Cloud Run concurrency with the application’s dependency-check capacity.
4. Start DB and Secret Manager checks concurrently under a common bounded wall-clock budget.
5. Add explicit Secret Manager RPC deadlines.
6. Preserve genuine request-time checks, exact response contract, private SQL, least privilege, and safe diagnostics.
7. Rebuild from the new clean source SHA and deploy by immutable digest.
8. Execute the final migration-job image and prove idempotent success.
9. Validate sequential and concurrent live health behavior.
10. Prove final Terraform drift zero, CI green, and published reachable history clean.
11. Update public evidence without inventing time, reviewer login proof, WIF, HA, or permanent reliability claims.

STRICT NON-GOALS

Do not:

- change reviewer_member from group: to user:;
- add a second reviewer binding;
- create or administer a Google Group;
- implement Workload or Workforce Identity Federation;
- add service-account keys;
- set Cloud SQL public IP or authorized networks;
- create another secret;
- retrieve or print secret payloads manually;
- change database credentials;
- change VPC, PSA ranges, SQL tier, SQL edition, database version, backup settings, IAM DB identities, or runtime/migrator privilege model;
- set min_instance_count to 1;
- implement HA, DR, multi-region, NAT, load balancers, budgets, monitoring stacks, or unrelated production controls;
- execute destructive Terraform actions;
- rerun old migrations by changing migration files;
- delete the GitHub repository;
- use git push --mirror or an unrestricted force push;
- rewrite history before the stated clean ancestor;
- send the final submission email;
- finalize TIMELOG or active-minute totals.

PHASE 1 — READ-ONLY PREFLIGHT

Before editing or rewriting anything:

1. Locate the actual repository and inspect repository instructions.
2. Confirm the working tree is clean.
3. Fetch origin without modifying local work.
4. Confirm:
   - current branch is main;
   - HEAD equals origin/main;
   - origin/main equals the expected pre-rewrite SHA;
   - the preceding two commits and clean ancestor match the anchors above.
5. Confirm the Git author remains the already configured GitHub noreply identity. Do not print any personal alternative.
6. Confirm the active gcloud identity is the same identity privately verified in Prompt 2, but output only ACCOUNT_MATCH=yes/no.
7. Confirm the active GCP project is the expected project.
8. Confirm Terraform/provider versions and backend configuration are unchanged.
9. Run a read-only Terraform drift plan. It must return zero before this pass.
10. Check the remote repository for:
    - open pull requests;
    - forks;
    - tags or branches that contain either affected commit;
    - remote main movement;
    - branch protection preventing the authorized force-with-lease operation.
11. Scan all published reachable commits, commit messages, tags, and tracked blobs for actual personal Gmail-style email addresses using a private/non-echoing scan. Do not display matched values.
12. Establish whether every prohibited occurrence was introduced only within the two authorized commits.

Report only counts and affected commit/file paths, never the matched address.

STOP before mutation if:

- repository, branch, project, account, or SHA anchors differ;
- the worktree has unexpected changes;
- origin/main moved;
- affected content predates the clean ancestor;
- another public branch, tag, PR reference, or fork requires a wider rewrite;
- there are collaborators’ unmerged changes at risk;
- initial Terraform drift is non-zero;
- the history rewrite cannot be limited to the authorized segment.

PHASE 2 — RECOVERABLE BACKUP

Before rewriting:

1. Create a complete Git bundle or equivalent recoverable backup outside the repository and outside all public/tracked paths.
2. Store it under the existing private working area.
3. Record:
   - backup path;
   - original main SHA;
   - clean ancestor SHA;
   - remote refs checked.
4. Verify the backup can list its refs.
5. Never commit, upload, or publish the backup.

Do not proceed unless the backup verification succeeds.

PHASE 3 — NARROW HISTORY CLEANUP

Rewrite only the ancestry segment after:

3d519e379d71b1a338288886d8b9952f96555414

The two existing public commits must be recreated with their legitimate code, Terraform, documentation, and commit purposes preserved.

Requirements:

1. Replace every actual personal Gmail-style email occurrence in the rewritten versions with:

   [redacted-personal-email]

2. This includes occurrences embedded in the old verbatim Prompt 2 block.
3. Do not remove the historical explanation that an identity correction occurred.
4. Do not expose the removed values in:
   - commands shown to the user;
   - shell output;
   - patches;
   - commit messages;
   - reports;
   - temporary tracked files.
5. Keep the business reviewer address unchanged.
6. Preserve all unrelated content from the two commits.
7. Do not rewrite any commit at or before the clean ancestor.
8. Do not push yet.
9. Ensure no local backup/original ref will later be pushed accidentally.
10. Record the new sanitized equivalents of the two rewritten commits.

Use the safest narrow history-rewrite technique available. Do not use a repository-wide rewrite when a two-commit rewrite is sufficient.

PHASE 4 — APPLICATION RELIABILITY HARDENING

Review the current app/main.py implementation and implement the smallest correct design satisfying all requirements below.

A. Parallel independent dependency checks

- Submit check_database and check_secrets before waiting for either result.
- Both checks must therefore be attempted for every /health request.
- Use the existing process-scoped executor.
- Keep the executor at four workers.
- Do not create a ThreadPoolExecutor per request.
- Worker functions must not recursively submit work to the same executor.
- Evaluate results against absolute deadlines measured from the same request start.
- The request’s dependency-check wall time must be bounded approximately by the larger configured budget, not the sum of DB and secret budgets.
- On timeout, return error for only the affected dependency.
- Attempt to cancel queued timed-out futures.
- Running operations must have their own lower-level bounded timeouts.

B. Cloud Run capacity alignment

In google_cloud_run_v2_service.api set:

max_instance_request_concurrency = 2

Keep:

- min_instance_count = 0;
- max_instance_count = 2;
- CPU and memory unchanged;
- ingress and public invoker unchanged;
- Direct VPC egress unchanged.

This explicitly aligns two concurrent requests with two dependency tasks per request and four executor workers.

C. Secret Manager client and deadlines

- Reuse a process-scoped Secret Manager client if compatible with the pinned library.
- Cache only the client, never a secret payload.
- Both configured secrets must still be read from Secret Manager on every health request.
- Keep secret version 1 semantics.
- Pass an explicit timeout to every access_secret_version RPC.
- For the two-read secret check, calculate remaining time from one common secret-check deadline so two RPC calls cannot each consume the entire overall budget.
- The DB-password read inside check_database must also have an explicit bounded RPC timeout.
- Close process resources safely at shutdown when supported.
- Never log payloads, response objects, exception messages, secret resource names, or credential material.

D. Database behavior

Preserve:

- one process-scoped Cloud SQL Connector;
- lazy refresh;
- PRIVATE IP;
- a new short-lived database connection for every request;
- request-time DB-password retrieval;
- real SELECT 1;
- cursor and connection closure on success and failure;
- HTTP db=ok only after the query returns the expected row.

Maintain connector and driver timeouts. Ensure a timed-out background task cannot remain unbounded.

E. Structured diagnostics

Use safe structured health_diag events containing only:

- event;
- stage;
- outcome;
- actual elapsed_ms;
- timeout_sec where applicable;
- exception_class.

Add accurate Secret Manager stages and real elapsed duration. Never use an artificial elapsed_ms=0 for an operation that was actually attempted.

F. HTTP contract

Preserve exactly these response keys and no others:

- candidate
- commit
- region
- db
- secret

Preserve:

- candidate = Svetoslav Silkov;
- commit = first seven characters of the deployed source SHA;
- region = europe-west1;
- HTTP 200 only when db and secret are both ok;
- HTTP 503 otherwise;
- HTTP 404 JSON for non-health paths;
- no exception detail or secret material in responses.

PHASE 5 — TESTS

Extend the tests to prove at least:

1. Exact successful five-field response.
2. DB-only failure.
3. Secret-only failure.
4. Both failures.
5. DB timeout.
6. Secret timeout.
7. Both dependency functions are started before either result is awaited.
8. Total timeout behavior uses the common wall-clock budget rather than serially adding both budgets.
9. Two simultaneous health requests complete without executor starvation.
10. Every health request performs the required request-time secret reads.
11. Secret Manager calls receive explicit positive RPC timeouts.
12. The Secret Manager client may be reused but payloads are not cached.
13. Connector is process-scoped while DB connections remain request-scoped.
14. Cursor and DB connection close on query failure.
15. Timed-out/failed operations do not expose messages or payloads.
16. Structured logs contain stage, outcome, elapsed time, and exception class where applicable.
17. Non-health route remains 404.
18. Migration configuration still uses the distinct IAM database identity without a password.

Avoid timing-fragile tests. Use Events, barriers, mocks, and small deterministic deadlines.

PHASE 6 — PUBLICATION-SAFETY GUARD

Add a small dependency-free script under scripts/ that scans tracked public files.

It must:

- detect actual personal Gmail-style email addresses with a case-insensitive pattern equivalent to:
  [a-z0-9._%+-]+@gmail[.]com
- ignore Git metadata because it is not a tracked file;
- allow the configured GitHub noreply author identity;
- not print matched values;
- report only file path, line number, and violation class;
- exit non-zero on a violation.

Add this script to CI as a separate publication-safety step.

The script must scan the full tracked working tree, including AI-LOG.md.

Do not put the actual removed addresses in:

- source;
- test fixtures;
- allowlists;
- denylists;
- comments;
- documentation;
- the CI workflow.

Run the existing broader sensitive-data scan as well, without printing matched secret material.

PHASE 7 — DOCUMENTATION BEFORE CODE COMMIT

Update the documentation truthfully:

AI-LOG.md:

- Make this Prompt 3 the most useful prompt.
- Include this entire Prompt 3 verbatim.
- Remove the current full Prompt 2 from the “most useful prompt” position.
- It may remain represented historically only in sanitized/redacted form.
- Add the discovered publication contradiction as a genuine corrected AI proposal:
  an earlier instruction required both verbatim publication and exclusion of a personal identity, which was internally inconsistent.
- Explain that Prompt 3 corrected both publication safety and concurrency alignment.
- Do not include personal GCP identities.
- Keep the AI-generated-code percentage honest.

README.md:

- Keep it approximately one page.
- Do not yet invent final deployment anchors.
- Document explicit Cloud Run concurrency 2.
- Keep WIF clearly NOT IMPLEMENTED.
- Keep reviewer principal type unconfirmed.
- Keep active minutes outstanding; do not finalize them.
- Do not claim permanent cold-start immunity or production-level availability.

DECISIONS.md and ASSUMPTIONS.md:

- Record concurrency 2 as a deliberate POC capacity boundary aligned with the four-worker dependency executor.
- Record that DB and secret checks start concurrently and share bounded request-time behavior.
- Record process-scoped clients but request-time payload/query operations.
- Keep POC versus production distinctions accurate.

Do not expand ACCESS-MODEL.md unless a factual correction is necessary.

PHASE 8 — LOCAL VERIFICATION AND CODE COMMIT

Run:

- all application unit tests;
- any new publication-safety tests;
- publication-safety scan;
- broader sensitive scan;
- terraform fmt -check;
- terraform init -backend=false and validate for bootstrap and POC;
- a local container build;
- a review of the complete staged diff.

Confirm:

- no secret payload;
- no personal Gmail-style address;
- no state, plan, ADC, working, source, backup, or tool files are tracked;
- only intended application, test, Terraform, CI, script, and documentation changes exist.

Create one new functional hardening commit on top of the two rewritten sanitized commits.

Use the configured GitHub noreply author identity.

Record:

- sanitized rewritten commit SHAs;
- new functional source commit SHA;
- exact file list.

PHASE 9 — SINGLE AUTHORIZED FORCE-WITH-LEASE PUSH

Immediately before pushing:

1. Fetch/check origin/main without merging.
2. Confirm origin/main still equals:
   6124c036d8060618ed13a91c780943f1f83a2c25
3. Confirm the local branch contains:
   - exactly the two sanitized replacement commits;
   - the new functional hardening commit;
   - no unrelated history rewrite.
4. Confirm the public-safety scan is clean.

Then perform exactly one:

git push --force-with-lease=refs/heads/main:6124c036d8060618ed13a91c780943f1f83a2c25 origin main

Do not use plain --force.
Do not push backup refs.
Do not push --mirror.

If the lease fails, STOP. Do not override it.

After the push:

- confirm remote main equals the new functional source commit;
- wait for CI;
- require all jobs to succeed before building/deploying;
- record the new CI URL.

PHASE 10 — BUILD IMMUTABLE IMAGE

Build from the exact new functional source commit.

Requirements:

- tag with its short SHA;
- push to the existing Artifact Registry repository;
- resolve the immutable sha256 digest;
- verify the digest corresponds to the built source;
- do not use a mutable tag in Terraform;
- do not alter or delete prior images.

Record the full new source SHA and digest.

PHASE 11 — TERRAFORM PLAN AND APPLY

Reuse the existing secure ephemeral Terraform inputs without printing them.

Update only the required deployment variables:

- container_image = new immutable digest reference;
- commit_sha = new functional source SHA.

The expected plan is:

- Cloud Run service update:
  - new image digest;
  - new COMMIT_SHA;
  - max_instance_request_concurrency = 2;
- Cloud Run migration job image update to the same digest;
- zero creates;
- zero destroys;
- no reviewer IAM change;
- no SQL, VPC, PSA, secrets, service-account, role, WIF, or state-backend change.

The exact plan count may group the service changes differently, but the semantic resource scope must match the list above.

STOP before apply if the plan includes:

- any create or destroy;
- any IAM mutation;
- reviewer principal change;
- SQL/network/secret mutation;
- public database exposure;
- service-account key or WIF resource;
- resource replacement;
- any unrelated change.

Save no public plan file.

Apply only the reviewed plan.

Do not execute the migration job as part of Terraform apply.

PHASE 12 — LIVE DEPLOYMENT VERIFICATION

Confirm:

- new Cloud Run revision is Ready;
- 100% traffic targets it;
- runtime service account unchanged;
- image digest matches;
- COMMIT_SHA matches the new functional source commit;
- live concurrency is 2;
- min instances remains 0;
- max instances remains 2;
- Direct VPC egress remains PRIVATE_RANGES_ONLY;
- VPC and subnet unchanged;
- Cloud SQL remains private-only with ipv4Enabled=false;
- no authorized networks exist;
- exactly two application secrets exist;
- runtime secret IAM remains secret-scoped;
- runtime and migrator identities remain separate;
- USER_MANAGED service-account key count remains zero;
- no WIF pool was created;
- reviewer group binding remains in live IAM and Terraform state.

Do not access secret payloads while performing these checks.

PHASE 13 — FINAL MIGRATION-JOB SMOKE TEST

Execute the newly deployed migration job once and wait for completion.

Expected result:

- successful execution;
- existing 001 migration reported as skipped/already applied;
- no schema change;
- no new migration record;
- IAM database authentication used;
- no password supplied;
- no secret payload logged.

If the job attempts an unexpected schema change or fails, STOP and diagnose before continuing.

PHASE 14 — LIVE HEALTH VALIDATION

Use an explicit validation start timestamp.

A. Sequential validation

Run twelve sequential requests.

For every response verify:

- HTTP 200;
- exactly five keys;
- candidate is correct;
- commit equals the first seven characters of the new functional source SHA;
- region is europe-west1;
- db=ok;
- secret=ok;
- no additional fields;
- record UTC timestamp and duration.

B. Concurrent validation

Run at least one burst of eight simultaneous requests against the public endpoint.

For every response verify the same contract and HTTP 200.

Record:

- success count;
- failure count;
- minimum, median, p95, and maximum duration;
- observed revision/instance evidence where available.

Do not call a failed run successful. If any 429, 5xx, malformed response, wrong SHA, or timeout occurs:

1. correlate logs;
2. identify the exact stage;
3. make the smallest in-scope correction;
4. rerun tests, CI/build/deploy as required;
5. repeat the full validation.

C. Negative route

Verify:

/nope → HTTP 404 with {&quot;error&quot;:&quot;not_found&quot;}

D. Logs

Inspect logs from the validation start timestamp.

Require:

- no health_timeout events;
- no outcome=error for validated successful requests;
- no unhandled exception;
- no connector lifecycle failure;
- stage and elapsed diagnostics present;
- no secret payload, credential, connection string, or exception message;
- evidence that both DB and secret checks ran;
- evidence that request-time DB query and both required secret reads occurred.

A new-revision startup request is valid cold/new-instance evidence. Do not call it a proven scale-from-zero idle cold start unless the evidence supports that exact claim.

PHASE 15 — FINAL DOCUMENTATION COMMIT

After measured deployment validation:

Update README.md with:

- new deployed source SHA;
- new image digest;
- new serving revision;
- concurrency 2;
- measured sequential result;
- measured concurrent-burst result;
- final migration-job smoke-test result;
- accurate caveat about what was and was not proven.

Keep:

- repository and health links;
- WIF NOT IMPLEMENTED;
- reviewer principal type unconfirmed;
- login proof not claimed;
- active minutes outstanding;
- approximately one-page length.

Update AI-LOG.md with the actual Prompt 3 outcome and safe evidence.

Update DECISIONS/ASSUMPTIONS only if required by measured facts.

Create one docs-only evidence commit and push it normally, without force.

Wait for and require green CI.

The final repository HEAD will be the docs commit, while the deployed source SHA will be the preceding functional commit. State this explicitly.

PHASE 16 — FINAL PUBLICATION AND HISTORY AUDIT

Use a fresh temporary clone of the public remote after the final docs commit.

Verify all remote-published reachable refs without displaying sensitive matches:

1. No actual personal Gmail-style address exists in:
   - current tracked files;
   - reachable historical blobs;
   - reachable commit messages;
   - reachable tag messages.
2. The business reviewer address remains correctly documented.
3. No secrets, private keys, ADC, state, plans, backups, sources, working files, or tool directories are tracked.
4. The new publication-safety CI check passes.
5. HEAD equals origin/main.
6. Worktree is clean.
7. Both final CI runs are green.
8. Public GitHub file contents match the local final tree.

Do not claim that unreachable cached SHA views, third-party clones, or forks were cryptographically erased. Report only what was verified:

- current public tree clean;
- remote-published reachable history clean;
- known PR/fork/ref status;
- GitHub cache limitation, if applicable.

If an unexpected fork or external reference exists, report it without exposing the removed value.

PHASE 17 — FINAL TERRAFORM DRIFT CHECK

Run terraform plan -detailed-exitcode with the deployed functional SHA and digest.

Required result:

exit code 0 — no changes.

Also reconfirm:

- reviewer Viewer binding in state and live IAM;
- principal type remains an assumption;
- reviewer login remains externally unverified;
- private SQL and identity boundaries unchanged.

FINAL REPORT FORMAT

Return one evidence-based report with these sections:

A. Preflight and STOP-gate results
B. Backup and recovery anchor
C. Narrow history rewrite
D. Publication-safety correction
E. Reliability/concurrency implementation
F. Test and local validation results
G. Rewritten commits, functional commit, docs commit, push, and CI
H. Image digest and deployment anchors
I. Migration-job smoke test
J. Sequential health table
K. Concurrent health statistics
L. Log correlation
M. Reviewer IAM and private-infrastructure verification
N. Final Terraform drift
O. Fresh-clone publication/history audit
P. Mandatory requirement status
Q. Remaining external assumptions or administrative items
R. Exact mutations performed
S. STOP confirmation

The report must include:

- full safe commit SHAs;
- image digest;
- revision;
- CI URLs;
- Terraform plan/apply resource scope;
- migration execution result;
- sequential and concurrent health evidence;
- publication scan counts;
- backup location without its contents;
- final functional-ready assessment.

Never include:

- personal email addresses;
- active GCP account;
- secret payloads;
- Terraform-sensitive inputs;
- credentials;
- exception messages containing infrastructure details.

SUCCESS CRITERIA

Do not call the implementation functionally complete unless all are true:

- authorized history rewrite completed with force-with-lease;
- current public tree contains no personal Gmail-style address;
- remote-published reachable history contains no such address;
- CI publication guard exists and passes;
- all unit tests pass;
- Terraform fmt and validate pass;
- both CI runs are green;
- image was built from the new functional source SHA;
- deployment uses the matching immutable digest and SHA;
- Cloud Run concurrency is 2;
- migration job succeeds idempotently from the final image;
- twelve sequential health checks pass;
- eight simultaneous health checks pass;
- exact five-field response contract is preserved;
- log review is clean;
- Cloud SQL remains private-only;
- both secrets are read at request time;
- no service-account keys exist;
- reviewer Viewer binding remains applied;
- final Terraform drift is zero;
- final repository is clean and synchronized.

When all work and reporting are complete, STOP.

Do not send email.
Do not finalize active minutes.

CURSOR PROMPT 3A — EXPANDED HISTORY-REWRITE AUTHORIZATION

HISTORY_REWRITE_AUTHORIZED=YES
EXPANDED_REWRITE_AUTHORIZED=YES
ORPHAN_HISTORY_AUTHORIZED=NO

The user explicitly authorizes:

- rewriting every main-branch commit from the first affected commit identified as 83c9f4e4eae3, inclusive, through the current main HEAD;
- changing every descendant SHA required by that narrow cleanup;
- one force-with-lease update of origin/main against the expected remote HEAD:
  6124c036d8060618ed13a91c780943f1f83a2c25
- continuing with all reliability hardening, build, Terraform deployment, migration smoke testing, live validation, documentation, and final audits defined in Prompt 3.

This authorization supersedes only these Prompt 3 restrictions:

- “rewrite exactly the last two public commits”;
- “rewrite only the ancestry segment after 3d519e3…”;
- the STOP condition triggered solely because an affected occurrence predates that former boundary;
- any phase text assuming that only two replacement commits will exist.

All other Prompt 3 requirements, safety controls, STOP gates, non-goals, validation requirements, and reporting requirements remain active.

Do not create an orphan history.
Do not squash the repository into a new root.
Do not use plain --force.
Do not use push --mirror.
Do not send email.
Do not finalize active minutes.
Do not display personal email values.

UPDATED REWRITE BOUNDARY

1. Resolve 83c9f4e4eae3 to its unique full commit SHA.
2. Derive and record its direct parent as the new clean-history anchor.
3. Privately verify, without printing matched values, that:
   - the identified commit is the first main-history commit containing the prohibited personal email pattern;
   - its parent and all earlier reachable main commits are clean;
   - commit author, committer, commit-message, tag-message, and blob metadata have also been checked;
   - origin/main has not moved;
   - no PR, fork, tag, or additional branch expands the published rewrite scope.
4. Output only:
   - resolved first-affected SHA;
   - clean-parent SHA;
   - affected commit count;
   - affected blob/path counts;
   - ACCOUNT_MATCH=yes/no;
   - safe pass/fail statuses.

STOP if any prohibited occurrence exists before the derived clean parent or in another published ref not covered by this authorization.

BACKUP

Before rewriting:

- create and verify the complete private Git bundle required by Prompt 3;
- keep it outside the repository and all published paths;
- confirm it contains the original main ref;
- record its safe path without displaying contents.

EXPANDED SANITIZATION

Rewrite the main history beginning with the resolved 83c9f4e4eae3 commit, inclusive.

For every affected historical version:

- replace every actual personal Gmail-style address with:
  [redacted-personal-email]
- sanitize all affected AI-LOG.md blobs, including old verbatim prompts;
- preserve the meaning of the AI correction record;
- preserve every unrelated file, change, commit purpose, and clean ancestor;
- do not place the removed values in commands, output, patches, commit messages, fixtures, allowlists, denylists, or reports.

Use one generic non-echoing replacement rule rather than a tracked list of actual addresses.

After rewriting, verify locally that:

- no prohibited address exists in any reachable rewritten commit;
- the clean parent is unchanged;
- only the first affected commit and its descendants received new SHAs;
- all legitimate application, Terraform, documentation, IAM, and migration changes remain present.

Record a safe old-SHA → new-SHA mapping for every rewritten commit. Hashes are safe; do not include sensitive content.

CONTINUE PROMPT 3

Resume Prompt 3 from its backup/history-cleanup phase and complete every remaining phase.

Where Prompt 3 refers to:

- “the two rewritten commits”, interpret it as “the rewritten sanitized commit chain”;
- “the clean ancestor 3d519e3…”, use the newly derived clean parent;
- “the local branch contains exactly two sanitized replacement commits”, require instead that it contains the complete sanitized replacement chain plus the new functional hardening commit.

Maintain the one-push design:

1. Rewrite and sanitize the affected chain locally.
2. Implement the Prompt 3 reliability, concurrency, tests, CI guard, and documentation changes.
3. Create the new functional source commit.
4. Recheck origin/main equals 6124c036d8060618ed13a91c780943f1f83a2c25.
5. Perform exactly one force-with-lease push using that expected SHA.
6. Require green CI.
7. Build the immutable image from the new functional commit.
8. Deploy through the reviewed Terraform plan.
9. Run the final migration-job smoke test.
10. Run sequential and concurrent live validation.
11. Create and normally push the final docs-only evidence commit.
12. Require final green CI, zero Terraform drift, and a clean fresh-clone history audit.

AI-LOG REQUIREMENT

Treat Prompt 3 plus this Prompt 3A authorization extension as the complete most-useful prompt sequence.

AI-LOG.md must include:

- Prompt 3 verbatim;
- this Prompt 3A extension verbatim immediately after it;
- a clear note that the original two-commit boundary correctly triggered a STOP because the earlier history was also affected;
- the fact that the user explicitly authorized the narrow expanded rewrite;
- no personal email values.

FINAL HISTORY SUCCESS CRITERIA

Do not declare publication cleanup complete unless a fresh clone proves that all remote-published reachable refs are clean across:

- current tracked files;
- every reachable historical blob;
- commit messages;
- author and committer metadata;
- tag messages.

Report GitHub cache/unreachable-object limitations honestly. Do not claim deletion from third-party clones or cached direct-SHA views.

Proceed now through the remaining Prompt 3 phases and STOP only on a still-applicable safety, validation, lease, CI, deployment, or drift failure.
</pre>


## Prompt 3 / 3A measured outcome

- Expanded history rewrite sanitized reachable main history (first affected was the repository root).
- Functional deploy SHA `b6a654e…`; image digest `sha256:9fcbf3d8…`; revision `meridian-api-00004-sgb`; concurrency 2.
- Migration execution succeeded with `001_init.sql` skipped.
- Live health: sequential 12/12 and concurrent 8/8 HTTP 200 with the five-field contract.
- Publication-safety CI guard added; personal Gmail-style addresses removed from published reachable history.
- `EARLIER_TECHNICAL_CLOSEOUT_BASELINE_MINUTES=212` (Prompt 3 / 3A technical closeout). Clarification email already sent earlier; not resent. Bonus WIF is disabled, not deployed, not tested, and not implemented.

## Group-ready access and data-migration documentation (post-closeout documentation refinement)

An earlier technical closeout baseline recorded **212 active minutes**. Before final delivery, an additional documentation refinement was completed. The documentation work is recorded as an **approved 20-minute estimate** because it was not directly measured, and the final reconciliation added **1 measured minute**, producing an intermediate published total of **233**. A further **2 user-reported** minutes cover subsequent review/diagnosis before the health-timeout remediation. The unapproved ~19-minute presentation estimate is **not** included. This remediation’s active work is included in **`FINAL_ACTIVE_MINUTES=244` (04:04)**. The **final submission email had not been sent** at the time of this documentation update.

| Item | Detail |
|------|--------|
| **Work** | Expanded [ACCESS-MODEL.md](ACCESS-MODEL.md) with four-layer developer access; created [DATABASE-MIGRATION.md](DATABASE-MIGRATION.md); minimal cross-links in README, DECISIONS, ASSUMPTIONS |
| **Infrastructure** | **None** — documentation only; no Terraform apply, IAM grants, buckets, DMS, or Job execution |
| **Rejected: staging bucket now** | AI suggested provisioning a migration-staging GCS bucket before dump size, retention, and audit requirements are confirmed — rejected as speculative cost and attack surface |
| **Rejected: broad developer DDL/DML GRANTs** | AI suggested example PostgreSQL privileges for a developer group before Meridian confirms developer duties — rejected; privileges must follow an approved access model |

WIF remains bonus, disabled, not deployed, not tested, and not implemented.

## Health timeout independence (final remediation)

| Item | Detail |
|------|--------|
| **Finding** | With equal DB/secret budgets, awaiting the timed-out check first caused `_await_future` to report the sibling as `error` after the waiter’s remaining budget hit zero — even when that sibling had already completed successfully within its own deadline. |
| **Evidence** | Local reproduction: equal 0.05–0.2s budgets, slow DB, immediate secret → HTTP 503 with `db=error` and incorrectly `secret=error`. |
| **Correction** | Submit checks with a completion timestamp; accept an on-time stamped result when retrieved after the waiter’s remaining budget; reject results that actually completed after their deadline. `cancel()` only affects queued work — it does not terminate a running thread. |
| **Tests** | Added equal-deadline regressions (both directions), both-timeout, late-stamped rejection, waiter-late acceptance, and exception independence. Full suite **31** tests. |
| **Deploy** | Functional source `690d81c…`; image `sha256:48a8d155…`; revision `meridian-api-00005-v7m` @ 100%. Previous revision `meridian-api-00004-sgb` / digest `sha256:9fcbf3d8…` retained for recovery. Migration Job image updated to the same digest; Job **not** executed. |
| **Final time** | `FINAL_ACTIVE_MINUTES=244` (04:04). Starting total before resume **235**; remediation **+9** measured/ceiled. Presentation estimate excluded. |

## Reviewer principal correction (user-confirmed intent; Google IAM conflict)

| Item | Detail |
|------|--------|
| **Commit confirmation** | `gcp-devops@comm-it.cloud` is an individual Google/Cloud Identity user |
| **Attempted IAM** | Remove `group:…` / add `user:…` → `roles/viewer` |
| **Google IAM result** | HTTP 400: principal is of type **group**; must use `group:gcp-devops@comm-it.cloud` |
| **Recovery** | Restored `group:gcp-devops@comm-it.cloud` → `roles/viewer` immediately after the failed `user:` create (group destroy had already succeeded) |
| **Deployed now** | `group:gcp-devops@comm-it.cloud` only — no dual binding |
| **Login** | Interactive reviewer login **not** claimed from our side |

## Estimate of AI-generated code

Roughly **70–85%** of repository file text was AI-drafted in Cursor; all Terraform and health-contract behavior reviewed and adjusted by Svetoslav before apply/publish.
