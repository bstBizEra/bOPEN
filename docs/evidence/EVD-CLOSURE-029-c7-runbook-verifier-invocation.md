# EVD-CLOSURE-029 - Maker evidence: C7 runbook verifier invocation (supersedes EVD-CLOSURE-012 C7)

**Version:** 0.1
**Status:** Maker-authored runbook correction (advisory; NOT an independent-checker receipt).
**Class:** PG-P0 closure-repair, remediation cycle 7. Append-only supersession of one step.
**Maker:** Claude Opus 5 (BST-SA Motor worker agent), sole maker.
**Authorizes nothing.** This is a procedure correction, not an authorization to execute C6-C8.

## What is superseded, and what is not

`EVD-CLOSURE-012` ("The proven, ordered C6-C8 procedure") remains the procedure of record for
C6.2-C6.6 and C8. **Only its C7 line is superseded**, which currently reads:

> **C7:** docket --check + both manifest --check + VERIFY-P0-01 (real envelope/trust root)
> VERIFIED_EXACT + PG-P1-drift negative + full unittest 189 OK.

`EVD-CLOSURE-012` is not edited (extend-only); this record is the correction. Everything else in
it -- including its material finding about the `tests/governance/test_program_control_validation.py`
delta -- stands unchanged.

## Why the bare invocation is no longer sufficient

Under cycle 7 (`EVD-CLOSURE-028`) closure binding is required by default, so a bare invocation now
fails closed rather than passing silently. That is the desired direction, but it means the runbook
must state which of the two legitimate invocations applies, or an operator will hit a rejection at
C7 and be tempted to "fix" it with whatever flag makes it pass -- the precise failure mode
`bopen-windows-toolchain` and `bopen-phase-closure` both name as a stop condition (a `--check`
failure must never be resolved by weakening the check).

## The two legitimate C7 invocations

**(a) Verifying the already-signed legacy mandate `PG-P0-CLOSURE-001`.** It was signed before
`closure_binding` existed and cannot acquire one without invalidating the signature. Its decision id
must be named explicitly:

```
python tools/verify_phase_transition.py \
  --predecessor       docs/00-governance/registers/SCHEDULE-REGISTER.json \
  --successor         <proposed successor register> \
  --mandate           docs/00-governance/signing/PG-P0-CLOSURE-MANDATE.dsse.json \
  --trust-root        docs/00-governance/signing/PG-P0-COMPLETION-TRUST-ROOT-CANDIDATE.json \
  --identity-register docs/00-governance/registers/AUTHORITY-IDENTITY-REGISTER.json \
  --verification-time 2026-07-27T00:00:00+07:00 \
  --consumed          docs/00-governance/signing/PG-P0-CONSUMED-DECISIONS.json \
  --revocations       docs/00-governance/signing/PG-P0-REVOCATIONS.json \
  --closure-manifest  docs/00-governance/signing/PG-P0-CLOSURE-MANIFEST.json \
  --allow-unbound-legacy-mandate PG-P0-CLOSURE-001
```

Expected: `rc == 0` **AND** stdout contains `VERIFIED_EXACT`. Stdout will also carry
`(UNBOUND_LEGACY_EXEMPTION: PG-P0-CLOSURE-001)`. **That suffix is not noise and must be recorded in
the C7 evidence**: it is the standing disclosure that this verification did not include closure
binding, and therefore that the binding controls (manifest digest, permitted-effects digest,
successor blobs, tree scope, revocation and consumed state) were **not** exercised on this path.

**(b) Verifying a bound mandate (`PG-P0-CLOSURE-002` or any successor).** No exemption flag. The
binding inputs become mandatory:

```
  ... --closure-manifest <manifest> --execution-root <execution bytes> --repository <git dir>
```

Expected: `rc == 0` AND stdout contains `VERIFIED_EXACT` with **no** `UNBOUND_LEGACY_EXEMPTION`
suffix. If the suffix appears here, the run used the legacy path and the C7 gate has NOT been met.

## Gating rule (unchanged in spirit, restated because it is load-bearing)

Gate on **`rc == 0` AND stdout containing `VERIFIED_EXACT`** -- never on `rc` alone
(`EVD-CLOSURE-016` H2: a bit-flipped signature passed twelve validators and 189 tests; only this
verifier rejected it). Cycle 7 adds one clause: **if `UNBOUND_LEGACY_EXEMPTION` appears, record it
and treat the closure-binding controls as unexercised.**

## Prohibited resolutions at C7

- Adding `--allow-unbound-legacy-mandate` to make a *bound* mandate's rejection go away. If a
  mandate that should carry a binding is rejected, the binding or the execution bytes are wrong;
  fix those, escalate, or stop.
- Naming a decision id in the hatch other than a genuinely legacy, pre-`closure_binding` mandate.
- Any use of `--require-closure-binding` as though it still changes behaviour. It is retained only
  so existing scripts do not break; binding is required regardless.

## Status effect

None. A procedure correction only. `PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production not authorized.
The C6-C8 execution bytes remain the human-only blocker (`EVD-CLOSURE-023`), so neither invocation
above can yet be run against real execution bytes.
