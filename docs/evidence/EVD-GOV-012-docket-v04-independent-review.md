# EVD-GOV-012 — Independent Exact-SHA Review of the PG-G0 Authority Docket v0.4 B8-Signed Candidate

**Version:** 0.1
**Status:** Draft technical evidence
**Work package:** GOV-P0-04 (accepted)
**Generated:** 2026-07-23
**Maker under review:** BST-Codex-Motor (v0.4 B8 encoder; EVD-GOV-011)
**Independent checker:** Claude (BST-SA Motor worker agent; claude-fable-5 session)
**Checker independence:** Different agent vendor, runtime and session; the checker authored none of the reviewed commit. The reviewed delta `7834c48..8a09870` is entirely Codex-authored.
**Candidate commit SHA:** `8a0987070efa4108e7f9ada716a8fb533fa47e42`
**Candidate tree SHA:** `8d649e24f970d2d0edb38cd2e8ee51c17bb596cb` (the handoff message listed the parent SHA in its Tree field; the correct tree is recorded here)
**Parent (operator B8 signing record):** `7834c48f84c01be8a03cf00380dd06f2bdea0b81`
**Branch:** `codex/GOV-P0-04-docket-v04`
**Worktree state:** clean at the exact candidate SHA throughout the review
**Verdict:** `REJECT` (exact-SHA technical receipt)

## What passes (preserved for the corrective candidate)

- `npm run validate` — exit 0 (all validators, reports, manifest, clean-room, secrets, supply-chain).
- Full test discovery in the checker environment — 143/143 passed (the maker-disclosed order-sensitive failure did not reproduce).
- **B8 encoding fidelity — perfect.** All five decisions carry `APPROVE` with `decided_at 2026-07-23T09:14:00+07:00`, final-authority actor blocks bound to `HUMAN-OPERATOR-001` through the identity register, the SIGNING-PASS-3 decision ref, and byte-identical subject bindings (SHA-256 values unchanged from the v0.3 docket). No signed outcome was altered.
- **B9 boundary correct.** `PG-G0-DEC-006` (`PASS_PG_G0`) is present, `PENDING`, actor-free, and fail-closed behind a fresh independent conformance receipt.
- **Readiness:** `READY_FOR_HUMAN_GATE_DECISION` with zero validation errors; remaining blockers are exactly B9, this technical review, the standing authorization boundary and the solo-operator disclosure.

## Reject findings

### GOV-P0-04-V04-RF-001 — Undocumented, unapproved removal of docket test coverage

`tests/governance/test_pg_g0_authority_docket.py` shrinks by 852 lines (44 tests to 11; full-suite count drops from 182 at the parent to 143). The removed fixture-based negative coverage includes identity-registry drift, role-binding digest mutation, delegation-grantor guards, append-only marker enforcement, state-machine transition and expiry-window cases — validator behaviors that still exist in the v0.4 validator and are now untested. Some removed tests were genuinely obsoleted by the pending-state redesign, but EVD-GOV-011 does not mention the removal at all.

AGENTS.md §11: "Never delete, skip or weaken a failing test without documenting the reason and obtaining approval." Applying the program's own precedent (EVD-GOV-005 rejected a candidate for a single stale manifest), an undocumented 75% reduction of the docket suite cannot be accepted.

**Required correction:** for each removed test, either restore it, supersede it with an equivalent-or-stronger v0.4-semantics test, or document why it is obsolete — in the work package and evidence, as an itemized append-only record. The B8 encoding itself needs no change.

### GOV-P0-04-V04-RF-002 — Undiagnosed nondeterministic test claim (minor)

The maker evidence reports "142/143; one order-sensitive stale-manifest failure" that does not reproduce in the checker environment (143/143). A candidate's evidence should not carry an unexplained failing run: either reproduce and fix the ordering dependency, or record the diagnosis and its environmental trigger in the evidence.

## Decision boundary

This is independent technical evidence only. The `REJECT` applies to the immutable candidate SHA; the corrective candidate carries a new SHA and requires a new receipt. The operator's B8 signature (SIGNING-PASS-3) is unaffected and must be re-encoded unchanged. B9 remains exclusively with the operator.

## Self-certification

```yaml
self_certification:
  agent_id: Claude BST-SA Motor (claude-fable-5)
  peer_agent_id: BST-Codex-Motor
  certification_scope: advisory_only
  execution_authority: false
  approval_authority: false
  candidate_verdict: REJECT
  ready_for_maker_correction: true
```
