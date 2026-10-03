# bOPEN Schema Diff Skill

**Canonical ID:** `io.bizera.bopen.database.schema-diff`  
**Version:** `0.1.0`  
**Lifecycle:** `VALIDATED` candidate  
**Execution boundary:** PostgreSQL analysis and evidence only; no production mutation

This package provides a governed Agent Skill for PostgreSQL schema comparison, migration-risk review, drift detection, bOPEN tenant-isolation conformance, RLS analysis, normalized findings, and evidence generation.

## Architecture

```text
Schema source A + Schema source B
              ↓
      deterministic engines
        Atlas / pg-schema-diff
              ↓
      canonical change model
              ↓
 migration safety + RLS + tenancy
              ↓
      risk verdict and evidence
              ↓
 separate authorized deployment workflow
```

## Included capabilities

- SQL migration static analysis
- Atlas and `pg-schema-diff` safe wrappers
- canonical diff normalization
- bOPEN `tenant_id`, RLS, privilege, and constraint checks
- migration risk and compatibility classification
- JSON and Markdown evidence generation
- deterministic evaluation suite
- JSON Schemas, policy files, CI examples, SBOM, provenance placeholder, checksums, and release tooling

## Quick start

```bash
python -m pip install -r requirements.txt
python scripts/validate_package.py
python -m unittest discover -s tests -v
python scripts/run_static_evals.py
python scripts/analyze_sql.py fixtures/sql/safe_tenant_table.sql --json /tmp/report.json --markdown /tmp/report.md
```

See `docs/INSTALL.md`, `docs/USAGE.md`, and `docs/GOVERNANCE.md`.
