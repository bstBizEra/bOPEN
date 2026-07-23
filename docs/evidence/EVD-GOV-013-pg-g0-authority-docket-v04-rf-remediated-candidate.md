# EVD-GOV-013 - PG-G0 Authority Docket v0.4 Rebuild Remediation

**Evidence ID:** EVD-GOV-013
**Timestamp:** 2026-07-23T12:00:00+07:00
**Agent ID:** BST-Codex-Motor
**Work package:** GOV-P0-04
**Base:** `8a0987070efa4108e7f9ada716a8fb533fa47e42`
**Prerequisite reject:** EVD-GOV-014 at `0aedc26b6309c69f54b3b7bf19270fd742eb9af8`
**Evidence status:** `REMEDIATED_CANDIDATE`; independent exact-SHA review pending

## Remediation result

The v0.4 docket, inventory, five B8 approvals, B9 pending surface and readiness are unchanged. The 33-item RF-001 disposition table is retained in `docs/work-packages/GOV-P0-04.md`. The GOV-P0-03 Progress_Log entry is appended after the pre-existing final entry, and its package manifest is regenerated in the same commit. DELEGATED is no longer accepted by schema or validator; a DIRECT-only negative test covers the boundary. The order-stability test operates on a temporary package fixture.

EVD-GOV-014 remains an immutable reject. Claude must issue a new receipt against the final exact SHA; no signed outcome or B9 decision is changed.
