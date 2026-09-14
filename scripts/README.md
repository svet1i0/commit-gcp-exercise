# Scripts

Repeatable local validation helpers. Do not embed credentials, secret values, or customer correspondence.

## `check_publication_safety.py`

Scans the repository for accidental publication of credentials, private keys, Terraform state, and similar sensitive patterns. Used by local CI (`.github/workflows/ci.yml` job `publication-safety`).

```bash
python3 scripts/check_publication_safety.py
```

Exit code 0 means the scan found no matching issues.
