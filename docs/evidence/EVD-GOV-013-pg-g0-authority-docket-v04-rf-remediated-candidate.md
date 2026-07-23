# EVD-GOV-013 - PG-G0 Authority Docket v0.4 RF-001/RF-002 Remediated Candidate

**Evidence ID:** EVD-GOV-013
**Timestamp:** 2026-07-23T11:00:00+07:00
**Agent ID:** BST-Codex-Motor
**Work package:** GOV-P0-04
**Base:** rejected v0.4 candidate `8a0987070efa4108e7f9ada716a8fb533fa47e42`
**Prerequisite reject:** EVD-GOV-012 at `269a8b2c444e3ec0de159177308f63ba51660dfa`
**Evidence status:** `REMEDIATED_CANDIDATE`; exact final SHA intentionally left for independent review binding

## Scope

This candidate leaves the v0.4 docket, all five B8 approvals, B9 pending surface, readiness result and signed provenance unchanged. RF-001 is closed by an append-only itemized disposition of all 33 removed predecessor tests in the work package and this evidence, plus maintained v0.4 controls. RF-002 is closed by a repeatability/order-stability regression test and a clean-checkout reproduction: full discovery passes 144/144 and repeated root-manifest validation passes with no stale-manifest error.

`pnpm validate`, the PG-G0 validator, root-control validator and `git diff --check` are required before commit. Claude must independently review the final exact SHA and issue a new receipt; EVD-GOV-012 remains an immutable reject and cannot be upgraded.
