# Acceptance Contract Fixtures

Draft acceptance fixtures capture observable contract expectations before production implementation begins.

Files ending `.acceptance.json` are executable governance fixtures. They are not production seed data and must use synthetic identifiers.

- `first-vertical-slice.acceptance.json` covers the initial principal-to-audit chain.
- `multitenant-dev-readiness.acceptance.json` covers membership, active-context integrity, tenant ownership, and API/database cross-tenant denial for DEV-P0-01.
