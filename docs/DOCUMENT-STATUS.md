# Document Status Register

| Artifact | Status | Implementation authority | Next action |
|---|---|---:|---|
| BOPEN-RES-001 | R0 executed; G0-G2 pass with conditions | Research only | Execute RES-P0-04 through RES-P0-07 and gather G3 evidence |
| BOPEN-RES-001 R1 update | Static lifecycle trace executed; G3 open | Research only | Build and review isolated synthetic G3 runtime evidence pack |
| BOPEN-BOOT-001 | Approved for bootstrap execution; B0-B6 evidenced | Repository/docs/tooling only | Submit BOOT-P0-12 and DEC-0007 for B7 authority review |
| BOPEN-REQ-001 | Draft shell | No | Product authority review |
| BOPEN-ARCH-001 | Draft shell | No | Architecture synthesis |
| BOPEN-TENANT-001 | Draft contract baseline | No | Authority review of DEV-P0-01 membership, context, ownership and isolation inputs |
| BOPEN-AUTHZ-001 | Draft shell | No | Define authorization and delegation |
| BOPEN-ENT-001 | Draft shell | No | Define entitlement and usage model |
| BOPEN-MOD-001 | Draft shell | No | Define capability/module contracts |
| BOPEN-PARTY-001 | Draft shell | No | Define common party model |
| BOPEN-SEC-001 | Draft shell | No | Threat model and security baseline |
| BOPEN-GOAL-001 | Draft v0.2 controlled intake | No | Product/Architecture review through DEC-0010 |
| BOPEN-GOV-001 | Draft program-control baseline | No | Engineering/Product/Architecture review; PG-G0 remains NOT_READY |
| PG-G0-AUTH-001 | Draft authority docket; all decision requests pending | No | Human Engineering acceptance of GOV-P0-02, then attributable authority routing |
| PG-G0-GATE-001 | Draft gate-decision contract; ineffective | No | Approved successor authority matrix must name governance/register/gate actions |
| DEC-0012 | Proposed instruction-surface and manifest decision | No | Product/Architecture/Engineering disposition with applicable Security/Data concurrence |

## Instruction-surface reconciliation note — 2026-07-21

Reason: replacement instructions require five exact root control paths that do not exist at the bound base. Benefit of the old phase: the existing `docs/` hierarchy preserves stable bootstrap IDs and Git evidence. Expected outcome: DEC-0012 designates approved equivalents or authorizes exact-path creation. Until then, alignment remains `UNRESOLVED`, not passed.

## Append-only Batch 2 signed-state supersession — 2026-07-23

The operator's Signing Pass 2 record makes BOPEN-GOV-001 and DEC-0013 effective, approves the authority matrix plus six program registers, accepts GOV-P0-01/GOV-P0-04 and DEC-0007/BOOT-B7, and activates GOV-P0-03 through the atomic five-ledger B6 event. PG-G0-AUTH-001 v0.3 is a `TECHNICAL_REVIEW` candidate for that exact state. The five B8 requests and B9 remain pending; no merge, release, deployment, runtime or production implementation authority is created.

Reason: preserve historical status rows while exposing the signed successor state. Benefit of the old phase: proposed controls made missing authority explicit. Expected outcome: document consumers use the v0.3 docket and EVD-GOV-009 pending a new exact-SHA receipt.

## Append-only v0.4 status - 2026-07-23

PG-G0-AUTH-001 v0.4 is a `PENDING_HUMAN_DECISIONS` signed-state candidate. B8 dispositions 001-005 are effective approvals from Signing Pass 3; readiness is `READY_FOR_HUMAN_GATE_DECISION` and `ready_for_pg_g0_gate_decision: true`. B9/DEC-006 remains pending and requires fresh independent conformance plus separate human disposition. Independent exact-SHA review is pending.

## Append-only v0.5 terminal gate-passed status - 2026-07-24

PG-G0-AUTH-001 v0.5 is terminal `DISPOSED`/`gate_passed`. PG-G0-DEC-006 is the operator-signed `PASS_PG_G0` approval from Signing Pass 4, with EVD-GOV-015 as its independent-conformance prerequisite. Readiness reports `PG_G0_PASSED`; PG-P0 is opened as `READY_FOR_AUTHORITY_REVIEW`. Production implementation, merge, release, deployment and runtime activation remain false and unauthorized. Final independent exact-SHA review is pending.

## Append-only PG-P0 preparation status - 2026-07-24

Signing Pass 5 transitions PG-P0 from `READY_FOR_AUTHORITY_REVIEW` to `ACTIVE` preparation at the exact operator-signed substrate. SKEL-P0-01 remains proposed and unaccepted; only preparation and independent review are in scope. Production implementation, migrations, merge, release, deployment and runtime activation remain false and unauthorized.

## Append-only SKEL-P0-01 sole-maker candidate status - 2026-07-24

SKEL-P0-01 has a sole-Claude-maker candidate prepared on the governed PG-P0 `ACTIVE` substrate (base `29949f46`): draft contract shells, typed package roots, fail-closed test tiers with recursive guards, and a re-authored `tools/validate_skeleton.py`. Every byte is authored by Claude so the designated checker BST-Codex-Motor is fully independent (resolving the prior checker-independence block on `8927b258`). Evidence: `docs/evidence/EVD-SKEL-002-skeleton-maker-candidate.md`. Work package remains `Proposed; not accepted`; production, migration, merge, release, deployment and runtime remain unauthorized.
