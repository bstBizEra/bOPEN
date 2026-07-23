# EVD-GOV-015 — Independent Exact-SHA Acceptance of the Rebuilt v0.4 Remediation Candidate

**Version:** 0.1
**Status:** Draft technical evidence
**Work package:** GOV-P0-04 (accepted)
**Generated:** 2026-07-24
**Maker under review:** BST-Codex-Motor (rebuilt RF remediation)
**Independent checker:** Claude (BST-SA Motor worker agent; claude-fable-5 session)
**Checker independence:** Different agent vendor, runtime and session; the checker authored none of the reviewed commit.
**Candidate commit SHA:** `ba44642e64b6bc19f891abc83b6002f497a644de`
**Candidate tree SHA:** `ec53505ed911abb37094953a60d3c93b000bcf79`
**Parent:** `8a0987070efa4108e7f9ada716a8fb533fa47e42` (the prefix-rewriting lineage `71f5ce2..c99f587` is abandoned, as EVD-GOV-014 required)
**Worktree state:** clean at the exact candidate SHA throughout the review
**Verdict:** `ACCEPT_EXACT_SHA` (technical evidence only)

## Commands and results (at the exact candidate SHA)

- `python -m unittest discover -s tests -p 'test_*.py'` — 145/145 passed.
- `npm run validate` — exit 0 (all validators, reports, manifest, clean-room, secrets, supply-chain).
- Root-control surface validation including full append-only git-history walk — zero errors.
- `git diff --check` — clean.
- Readiness: `READY_FOR_HUMAN_GATE_DECISION`, zero validation errors, `ready_for_human_gate_decision: true`.

## Finding-by-finding verification (EVD-GOV-012 and EVD-GOV-014)

1. **EVD-GOV-014 REM-RF-001 (ledger prefix rewrite) — fixed by rebuild.** All five root ledgers are byte-prefix supersets of their `8a09870` state; the remediation entry is appended after the final v0.4 entry (+475 bytes at end of `Progress_Log.md`) and the GOV-P0-03 package manifest is rebound in the same commit. The violating lineage is not an ancestor of this candidate.
2. **EVD-GOV-014 REM-RF-002 (live untested DELEGATED path) — fixed.** `authority_mode` is `const: "DIRECT"` in the docket schema, the validator contains zero `DELEGATED` references, a new negative test (`test_delegated_authority_mode_fails_closed`) proves rejection, and disposition items 26–29/31 now state the accurate ground ("DELEGATED is rejected").
3. **EVD-GOV-014 REM-RF-003 (state-asserting ordering test) — fixed.** The repeatability test now copies the package fixture into a temporary root, builds its manifest there, and validates twice with the git-history walk disabled — a genuine order-stability property.
4. **EVD-GOV-012 RF-001 (itemized test disposition) — retained.** The 33-item disposition table stands with corrected wording; suite is 145 tests.
5. **B8 immutability — verified.** The docket instance and V0.4 binding inventory are byte-identical to `8a09870`; the only contract change is the delegation-branch removal. The inventory's docket-schema record binds the frozen substrate bytes at `7834c48` by design (predecessor semantics), which this review confirmed hash-exact.

## Conformance statement for B9

This receipt is a fresh independent exact-SHA conformance verification of the complete signed-state candidate at `ba44642e64b6bc19f891abc83b6002f497a644de`. All five B8 decisions are encoded faithfully to SIGNING-PASS-3; `PG-G0-DEC-006` (`PASS_PG_G0`) is `PENDING`, actor-free, and its prerequisite for a fresh independent conformance receipt is satisfied by this document at this SHA. The `PASS_PG_G0` disposition itself remains exclusively a human operator decision.

## Decision boundary

Technical evidence only. This receipt does not sign B9, pass PG-G0, or authorize merge, release, runtime or production implementation.

## Self-certification

```yaml
self_certification:
  agent_id: Claude BST-SA Motor (claude-fable-5)
  peer_agent_id: BST-Codex-Motor
  certification_scope: advisory_only
  execution_authority: false
  approval_authority: false
  candidate_verdict: ACCEPT_EXACT_SHA
  ready_for_operator_review: true
```
