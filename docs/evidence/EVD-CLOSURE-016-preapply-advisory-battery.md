# EVD-CLOSURE-016 - Advisory maker-side pre-apply battery (4 nodes)

**Version:** 0.1
**Status:** Advisory maker-side evidence. NOT independent-checker receipts (that class is
EVD-CLOSURE-001..008, 013, 014, 015). Produced by Claude worker sub-agents; authorizes nothing.
**Persisted:** 2026-07-27 by Claude (BST-SA Motor worker, maker).
**Runtime pointers (non-anchors):** ac5ca3ff (candidate), a5a017dc (guard), a224634858 (signature),
aee620a654 (abort/CAS).
**Subject:** the PG-P0 execution candidate and apply pipeline at parent
`01ddb750aa719e0b3faf935418a001e907fb9e37`. All mutating work used throwaway keys and disposable
clones/worktrees, all deleted; the operator's private key was never requested or used; no real ref was
created, moved or deleted.

## Node 1 - Execution candidate verification: EXECUTION_CANDIDATE_VALID

Patch applies cleanly (exactly 3 files); successor RFC-8785 digest ==
`1f8d183e4bbcd2acc82148b659d5e0b74e2ea48bfc6dc4c0ceccc69e2b3ff863`; PG-P0 COMPLETE with canonical sorted
evidence refs; **all other schedule entries byte-identical**; all 12 validators PASS; VERIFY-P0-01 against
the REAL signed envelope = `VERIFIED / VERIFIED_EXACT` (signer HUMAN-OPERATOR-001); 189 tests OK; scope
contained (no matrix/identity/contracts change). No blocking discrepancy. Advisory note: manifest
regeneration order (GOV-P0-02 first, default last) is load-bearing.

## Node 2 - Section 5 guard adversarial: GUARD_FAILS_CLOSED

Baseline passes; the guard is a verified NO-OP while PG-P0 is ACTIVE (cannot brick the live state) and
correctly EXCLUDES cryptographic verification (sha256 integrity binding only; DSSE/Ed25519 stays with
VERIFY-P0-01). Every tamper rejected with an element-naming error: empty closure record; missing
`APPROVE_GOVERNANCE_BASELINE` token; missing manifest SHA-256; **tampered manifest BYTES while the record
keeps the old SHA (proves content binding, not presence-only)**; deleted evidence file; altered
`planned_end` / `rebaseline_decision_ref` / `evidence_refs` ORDER; PG-P1 flipped to ACTIVE; signer
`expires_at` before completion. Case-sensitivity is fail-closed.

## Node 3 - Signature gate negative proof: SIGNATURE_GATE_FAILS_CLOSED

60 probes, zero critical. Rejected: signature bit-flips (R and S halves), a throwaway key signing the real
PAE, four payload substitutions, three successor smuggles, two predecessor drifts (including a single
trailing space in an unrelated entry), wrong/unknown/identity-unbound trust keys, four authority denials,
both validity-window ends, identity revocation, revoked decision id and revoked keyid, replay (two
variants), and six malformed envelopes. Beyond the brief it also proved: a validly-signed NON-CANONICAL
payload is rejected (`CANONICALIZATION_ERROR`); **a valid signature plus a mandate adding PG-P1 -> ACTIVE
with a matching successor is still rejected (`INVARIANT_VIOLATION`)**; signature malleability (S+L) is
rejected; an appended permissive duplicate identity cannot escalate; extra signatures grant nothing.
Conclusion: possession of the operator's genuine envelope confers NOTHING beyond the single authorized
transition.

## Node 4 - Abort-safety and compare-and-swap: ABORT_SAFE_AND_CAS_PROTECTED

No failing case ever produced a commit or moved a ref. Validator failure, signature failure and test
failure each abort with the branch unchanged and NO commit object. A concurrent ref move makes the CAS
refuse and the branch remains at the other actor's commit, leaving the execution commit orphaned
(unreferenced; `git fsck` clean). Wrong expected-old values refuse. The pre-flight guard refuses before any
work. **A re-run with the pre-flight guard bypassed is still refused by the CAS**, so double-apply is
impossible. `git apply` is atomic (a failed hunk leaves the tree completely clean). The single-commit shape
is load-bearing: the closure must not be split into incremental commits.

## Hardening findings (advisory; none blocks the apply; three changed the runbook)

- **H1 (medium, adopted): on any `--check` failure never run `--write` as remediation.** The docket/report
  `--check` failure message is non-diagnostic ("PG-G0 authority readiness report is stale") and the same
  tool's `--write` mode would regenerate the report to MATCH a tampered state, converting a genuine
  integrity failure into a pass. The runbook now forbids this; investigate instead.
- **H2 (medium, adopted): forged-signature detection is single-gated.** A bit-flipped signature passes all
  12 validators and all 189 tests; only VERIFY-P0-01 rejects it. The apply now gates on BOTH `rc == 0` AND
  stdout containing `VERIFIED_EXACT`.
- **H3 (low, adopted): destroy the worktree on the CAS-failure path**, not only on validation failure, so a
  validated-but-unauthorized orphan commit is not left reachable.
- **H4 (medium, post-closure): trust-root ingest hardening.** A duplicate `keyid` in a trust root is
  last-write-wins, and low-order/identity public keys are accepted at ingest. Neither affects this closure:
  the committed trust root has exactly one key entry, and the operator key was verified to lie in the
  prime-order subgroup (`8*A != identity`, `L*A == identity`). Recommend rejecting duplicate keyids and
  small-order points.
- **H5 (medium, post-closure): ISO-8601 offset handling.** Validity-window comparison is lexical and is
  correct only while all timestamps share one offset. This closure is safe (register and verification time
  are all `+07:00`), but a `Z`-suffixed time could misjudge the window. Recommend parsing to absolute
  instants. Independently found by two nodes.
- **H6 (low, informational): anti-replay is external state** - the verifier persists nothing. Structurally
  covered here by git CAS plus predecessor-digest binding.
- **H7 (low, informational): abort leaves modified files in the runner directory** - destroy the worktree,
  never retry in place.

```yaml
self_certification:
  agent_ids: [claude-motor, claude-immune]
  certification_scope: advisory_only
  independent_of_maker: false
  execution_authority: false
  approval_authority: false
  ready_for_operator_review: true
```

## Status effect

None. Pre-apply advisory evidence only. `PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production not authorized; the
apply remains the operator's act under DEC-0014.
