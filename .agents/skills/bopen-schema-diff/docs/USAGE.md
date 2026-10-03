# Usage

## Local static migration review

```bash
python scripts/analyze_sql.py migrations/20260722_change.sql   --request-id BOPEN-DB-CHANGE-001   --json evidence/schema-review.json   --markdown evidence/schema-review.md
```

## Normalize an engine plan

```bash
python scripts/normalize_diff.py atlas-plan.sql --engine atlas --output canonical-changes.json
```

## Tenant invariant-only check

```bash
python scripts/check_bopen_invariants.py migrations/20260722_change.sql
```

## Exit codes

- `0`: PASS
- `1`: REVIEW
- `2`: BLOCK
- `127`: required external tool unavailable

A zero exit code is not deployment authorization. It only represents the scope of the checks performed.
