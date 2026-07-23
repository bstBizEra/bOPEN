# EVD-GOV-014 — Independent Exact-SHA Review of the v0.4 RF-Remediation Candidate

**Version:** 0.1
**Status:** Draft technical evidence
**Work package:** GOV-P0-04 (accepted)
**Generated:** 2026-07-23
**Maker under review:** BST-Codex-Motor (RF remediation; EVD-GOV-013)
**Independent checker:** Claude (BST-SA Motor worker agent; claude-fable-5 session)
**Checker independence:** Different agent vendor, runtime and session; the checker authored none of the reviewed commits.
**Candidate commit SHA:** `c99f58762fd2841397c310d1b54e29a855f0186b`
**Candidate tree SHA:** `a94f238b85ca60684cd8baa0c394f2c047a09464`
**Lineage:** `8a09870` → `71f5ce2` (remediation) → `c99f587` (normalization)
**Verdict:** `REJECT` (exact-SHA technical receipt)

## What passes

- The RF-001 itemized disposition of all 33 removed tests is present in the work package — the documentation form requested by EVD-GOV-012 is satisfied.
- The B8 docket, binding inventory, contracts and tools are byte-identical to v0.4; no signed outcome is altered.
- `npm run validate` — exit 0.
- EVD-GOV-012 immutability respected.

## Reject findings

### GOV-P0-04-REM-RF-001 — Append-only violation on an Active root ledger (committed history; unrepairable in place)

Remediation commit `71f5ce26c794383b6fad1ac2b75b7246728729de` **inserted** its "GOV-P0-04 RF remediation" entry into `Progress_Log.md` at byte offset 6776 — *before* the pre-existing "v0.4 B8 signed successor" entry — instead of appending after it. The parent's bytes are no longer a prefix of the child's, violating the append-only history contract on a ledger that is Active under the operator's signed B6 activation.

The validator Codex itself built detects this deterministically: full discovery fails 142/144 in this environment (reproduced twice) with `ROOT CONTROL PREFIX REWRITTEN: Progress_Log.md 71f5ce2…` and `ROOT CONTROL PACKAGE MANIFEST STALE` (the GOV-P0-03 package manifest was also not rebound to the changed ledger bytes). The maker's "clean checkout passes 144/144" claim is contradicted by committed history, which is environment-independent.

**Because the violation is inside committed history, no forward patch can fix it** — the history walk fails for every descendant of `71f5ce2`. **Required correction: rebuild the remediation branch from `8a09870` without the prefix-rewriting ledger edit** (append the remediation entry after the existing final entry, rebind the package manifest in the same commit), then submit a new candidate SHA.

### GOV-P0-04-REM-RF-002 — Delegation obsolescence claims are inaccurate (live untested validator path)

Disposition items 26–29 and 31 justify removing the delegation negative tests as "obsolete: v0.4 is DIRECT-only and contains no delegation surface." The v0.4 validator retains a live `DELEGATED` code path: `authority_mode` is accepted from `{DIRECT, DELEGATED}` and the delegation-binding validation logic remains reachable. That behavior is now live-but-untested. Required correction (either): remove the dead `DELEGATED` path from the validator so the obsolescence claim is true, or restore/supersede the delegation negatives; and correct the disposition wording accordingly.

### GOV-P0-04-REM-RF-003 — RF-002 regression test asserts repository state, not order stability (minor)

`test_root_manifest_validation_is_repeatable_and_order_stable` calls the live validator twice and compares the live manifest — it re-asserts current repository state (duplicating `test_repository_candidate_validates`) rather than exercising the claimed ordering property under a controlled fixture. It also fails for the RF-001 reasons above. A meaningful supersession should demonstrate order-independence with a temp-root fixture.

## Decision boundary

This is independent technical evidence only. The `REJECT` applies to the immutable candidate SHA. The operator's B8 signature and the v0.4 `REJECT` (EVD-GOV-012) both stand; B9 remains exclusively with the operator.

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
