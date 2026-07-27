# EVD-CLOSURE-020 - Maker evidence: revocation + consumed-decision state binding

**Version:** 0.1
**Status:** Maker-authored preparation evidence (advisory; NOT an independent-checker receipt).
Requires independent-checker review before any weight beyond advisory.
**Class:** PG-P0 closure-repair candidate, item 6 - plus a closing checkpoint on the manifest's
current content hash after this session's four additive revisions (EVD-CLOSURE-017..020).
**Persisted:** by Claude (BST-SA Motor, sole maker this session), on isolated candidate branch
`codex/PG-P0-closure-repair-c8`, worktree base commit `042dda535be70927b73cd1a131b2545349729643`.
**Authorizes nothing. Consumes nothing new. Revokes nothing.**

## Gap audited

`bopen-dsse-verification`: "Anti-replay is external state. `--consumed` is read and an updated
registry is returned in memory; the tool persists nothing. Single-use holds only if the caller
writes the registry back." and "Revocations are external too... honoured only when `--revocations`
is actually supplied." No such files existed anywhere in the lineage before this session, despite
`EVD-CLOSURE-014` having already produced a `VERIFIED_EXACT` result for `PG-P0-CLOSURE-001` - the
write-back never happened. This is exactly the documented stop condition: "`--consumed` or
`--revocations` is omitted and single-use or revocation is then claimed."

## Registries created (this branch)

- `docs/00-governance/signing/PG-P0-CONSUMED-DECISIONS.json` - flat `decision_id -> {predecessor_digest,
  successor_digest}` map, matching `verify_transition()`'s internal `consumed` shape exactly.
  Seeded from `EVD-CLOSURE-014`'s already-persisted `VERIFIED_EXACT` digests
  (`predecessor_digest e80f7b93...`, `successor_digest 1f8d183e...`) - no new verification was
  invented, this only durably records the one that already happened.
- `docs/00-governance/signing/PG-P0-REVOCATIONS.json` - empty scaffold (`revoked_keyids: []`,
  `revoked_decision_ids: []`); nothing in this lineage is revoked as of this session.
- `PG-P0-CLOSURE-MANIFEST.json`'s new `revocation_and_consumed_decision_state` block (EVD-CLOSURE-018/019
  edit) points to both files by path so a future verifier invocation does not have to rediscover
  them.

## Independent end-to-end re-verification performed this session

Ran the extended `tools/verify_phase_transition.py` against the real, currently-committed files
(predecessor register on disk, the real DSSE envelope, the real trust-root candidate, the real
identity register) plus the two new registries and the new `--closure-manifest` input:

```
VERIFIED: ALREADY_VERIFIED_EXACT   (rc=0)
```

Full receipt (abbreviated to the fields this repair changed):

```json
{
  "verdict": "VERIFIED",
  "outcome": "ALREADY_VERIFIED_EXACT",
  "decision_id": "PG-P0-CLOSURE-001",
  "predecessor_schedule_digest": "e80f7b9390d86a7627d6d14bd683296f2314189d145791971fb8aeb2a8d9f1cf",
  "authorized_successor_schedule_digest": "1f8d183e4bbcd2acc82148b659d5e0b74e2ea48bfc6dc4c0ceccc69e2b3ff863",
  "proposed_successor_schedule_digest": "1f8d183e4bbcd2acc82148b659d5e0b74e2ea48bfc6dc4c0ceccc69e2b3ff863",
  "closure_manifest_sha256": "8a3c14b65276a98241a4aece46f7e2b020189a44aef79e68fde209737eb81202",
  "permitted_effects_digest": "c867b7ff5287803af2e30c76fa05d72b226110f9f8de657136d564a712d59861"
}
```

The `ALREADY_VERIFIED_EXACT` outcome (rather than a fresh `VERIFIED_EXACT`) is the *correct* and
*expected* result now that the consumed-decisions registry is persisted and supplied - it proves
single-use replay protection is now structurally real rather than merely narrated, exactly as
`bopen-dsse-verification` requires ("Re-verifying the byte-identical transition is idempotent"). No
mandate was re-signed; no register was mutated; the successor was recomputed in memory only.
`predecessor.schedule_digest` and `authorized_successor_schedule_digest` are independently
reconfirmed unchanged from `EVD-CLOSURE-014`.

## Manifest content-hash checkpoint (closes EVD-CLOSURE-017/018/019/020)

`PG-P0-CLOSURE-MANIFEST.json`'s raw-bytes content SHA-256 has two distinct, correctly-distinguished
values that must never be conflated:

- **`7417cc6a7bdffc6cac0b3707be293fb01ec17434f848d831c2383f374cafb33a`** - the C3-frozen manifest as
  it stood when the operator's C4 signature was produced. This is the value
  `PG-P0-CLOSURE-MANDATE.md` cites ("Bound closure manifest... content SHA-256 = ..."), and it
  remains historically accurate and unedited - that document is not touched by this closure-repair
  candidate.
- **`8a3c14b65276a98241a4aece46f7e2b020189a44aef79e68fde209737eb81202`** - the manifest's content
  SHA-256 *after* this session's four additive revisions (EVD-CLOSURE-017's `_status`/`activation`
  correction, EVD-CLOSURE-018's labeling fix, EVD-CLOSURE-019's `c9_proposed_ref_move` block,
  EVD-CLOSURE-020's `revocation_and_consumed_decision_state` block). Independently recomputed twice
  this session (direct `hashlib.sha256` and via `tools/verify_phase_transition.py
  closure_manifest_sha256()`) - both agree.

Neither value is used as, or claimed to be, the DSSE-signed subject: `mandate.mandate_payload_b64`
/ `digest_rfc8785_sha256` (`0f34a306ad63bb3457c1fdda3d3c9185bd99636314dc3008f2dc6ebc9acaf92c`) /
`pae_sha256` (`bd5113a6...`) are independently re-verified byte-identical to their pre-session
values throughout this candidate (see EVD-CLOSURE-017/018). Only the manifest's own free-text and
advisory-field bytes changed; the signed mandate never did.

## Status effect

None. Pre-execution, additive evidence only. No register mutated, no ref moved, no mandate edited
or (re)signed, no decision newly consumed, no key revoked. `PG-P0 ACTIVE`; `PG-P1 NOT_READY`;
production not authorized; `main` unchanged at `a908bbea1975ffc52a636765cd9f823dfeb978eb`. Requires
independent-checker review (task 10, this session) before any weight beyond advisory.
