# EVD-CLOSURE-010 - Advisory maker-side audit: C7 negative-control robustness battery

**Version:** 0.1
**Status:** Advisory robustness evidence (maker-side). NOT an independent-checker receipt.
**Class note:** Produced by a Claude worker sub-agent (motor lane), maker-side, using ONLY a throwaway
Ed25519 key. This is robustness evidence for the `PROVEN_MECHANISM` acceptance condition; it is NOT the
operator signature and NOT independent BST-Codex-Motor verification. It authorizes nothing.
**Persisted:** 2026-07-27 by Claude (BST-SA Motor worker, maker). **Runtime pointer (non-anchor):** afde589b.
**Subject:** the frozen PG-P0 closure mechanism at lineage HEAD `1f885049` (manifest PG-P0-CLOSURE-MANIFEST.json).

## Verdict: MECHANISM_ROBUST

Frozen-subject binding reproduced exactly: predecessor `e80f7b93...`, mandate `0f34a306...`, successor
`1f8d183e...`, PAE 1197 bytes `bd5113a6...`, payload RFC8785-canonical - all match the manifest.

### VERIFY-P0-01 tests (throwaway-key trust root)

| Test | Scenario | Result | Reason code |
|---|---|---|---|
| A | Happy path (exact pred + valid sig + recomputed successor) | VERIFIED | VERIFIED_EXACT |
| B | Wrong parent (tweaked predecessor) | reject | PREDECESSOR_MISMATCH |
| C | Smuggled change (flip PG-P1 -> ACTIVE in proposed successor) | reject | SUCCESSOR_MISMATCH |
| D | Corrupt one signature byte | reject | SIGNATURE_INVALID |
| E | Same keyid, different public key | reject | SIGNATURE_INVALID |
| E2 | Genuinely unknown keyid | reject | UNTRUSTED_KEY |
| F1 | verification_time after expires_at | reject | VALIDITY_EXPIRED |
| F2 | verification_time before valid_from | reject | VALIDITY_EXPIRED |
| G | revoked_decision_ids = [PG-P0-CLOSURE-001] | reject | REVOKED |
| H1 | Replay, same successor digest | VERIFIED | ALREADY_VERIFIED_EXACT |
| H2 | Replay, different successor digest | reject | REPLAY_DENIED |
| I1 | required_action = AUTHORIZE_RELEASE (not held) | reject | AUTHORITY_DENIED |
| I2 | required_role = Release Authority (not held) | reject | AUTHORITY_DENIED |

### Docket coordinated-change tests (scratch commits, removed)

| Sub-test | Action | Result |
|---|---|---|
| J1 | schedule PG-P0 -> COMPLETE mutation ONLY | FAIL (exit 1): "signed register transformation differs from signed outcome: SCHEDULE-REGISTER.json" |
| J2 | + validator expected-state extension (PG-P0 branch -> COMPLETE) | PASS (exit 0, PG_G0_PASSED) |
| J3 | + flip PG-P1 -> ACTIVE (drift) | FAIL (exit 1) |

**Key insight:** docket `--check` fails on non-empty `validation_errors` independently of report
staleness - you cannot launder a bad transition past `--check` by regenerating the readiness report.
The deterministic successor-recompute equality (test C) is a binding control on its own, not just the
signature. The closure therefore requires the register mutation and the validator expected-state
extension applied TOGETHER and EXACTLY; any extra drift re-fails.

Hard-block compliance: throwaway key `sha256(b"c7-tests")` only; the real key was never read; all
mutation confined to scratch worktree `C:/b-c7test` (removed); scratch commits unreferenced; real
branch `pg-p0-closure-lineage` re-verified unchanged at `1f885049`.

```yaml
self_certification:
  agent_id: claude-motor
  certification_scope: advisory_only
  independent_of_maker: false
  execution_authority: false
  approval_authority: false
  ready_for_operator_review: true
```

Status effect: none. This is `PROVEN_MECHANISM` robustness evidence only; the operator signature and the
real C0-C11 execution remain the sole authority. `PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production not authorized.
