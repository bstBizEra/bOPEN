# EVD-CLOSURE-022 - Maker evidence: cycle-2 remediation and superseding reconciliation

**Version:** 0.1
**Status:** Maker-authored remediation evidence (advisory; NOT an independent-checker receipt).
Requires independent-checker review before any weight beyond advisory.
**Class:** PG-P0 closure-repair, remediation cycle 2, on branch `claude/PG-P0-closure-repair-c8-v2`
from exact base `042dda535be70927b73cd1a131b2545349729643`.
**Maker:** Claude Opus 5 (BST-SA Motor worker agent), sole maker.
**Authorizes nothing.** Signs nothing, applies nothing, moves no ref, consumes no decision.

## Predecessor candidate: REJECTED

Candidate `2134ea2d53f78b79522b476e78f4b33022595615` (branch `codex/PG-P0-closure-repair-c8`)
received `REJECT_EXACT_SHA` from the independent Codex checker. This cycle is built **from base**,
not atop the rejected candidate, and no commit from that branch is inherited. Evidence identifiers
`EVD-CLOSURE-017` through `EVD-CLOSURE-021` were consumed by that rejected candidate and are **not**
carried into this lineage; cycle 2 numbering starts at `EVD-CLOSURE-022`.

## Correction 1 - fail-closed closure-execution verification (was: insecure optional binding)

**Defect:** cycle 1 added an *optional* `closure_manifest_digest` and, worse, shipped a test
(`test_mandate_without_closure_manifest_digest_is_not_contradicted`) asserting that a mandate with
no binding is "not contradicted". That test encoded the vulnerability as a requirement: an attacker
supplying a mandate with no binding would silently receive a `VERIFIED` verdict.

**Correction (`tools/verify_phase_transition.py`):**

- Six new reason codes: `CLOSURE_BINDING_REQUIRED`, `CLOSURE_BINDING_MALFORMED`,
  `CLOSURE_MANIFEST_MISMATCH`, `PERMITTED_EFFECTS_MISMATCH`, `REVOCATION_STATE_MISMATCH`,
  `CONSUMED_STATE_MISMATCH`.
- New `closure_binding` mandate object with a **closed** required-key set: `closure_manifest_digest`,
  `permitted_effects_digest`, `predecessor_commit`, `predecessor_tree`, `target_ref`, `expected_old`,
  `revocation_state_digest`, `consumed_state_digest`, `successor_blobs`.
- New `require_closure_binding` mode (CLI `--require-closure-binding`). When set, **absence,
  malformation, or mismatch of any binding element is a hard rejection.** Absent manifest bytes,
  absent revocation bytes and absent consumed bytes are each independently fatal.
- Enforcement runs **before** authority resolution and before any digest comparison, so no later
  check can produce a `VERIFIED`-looking verdict on an unbound closure.
- A binding that is *present* is fully enforced even outside closure mode; only its absence is
  tolerated there. The insecure "not contradicted" test is **deleted and not replaced**.
- `permitted_effects_digest` is an independent second control: a manifest legitimately accretes
  free-text revision notes, so the effects list carries its own RFC 8785 digest. An attacker who
  alters *what may be written* is caught even if the whole-file digest were re-issued for an
  unrelated editorial reason.

**Semantic attacker negative test (`test_attacker_altered_permitted_effects_rejects`):** the attacker
widens permitted effects to include a write to `AUTHORITY-MATRIX.json` ("grant self approval") while
leaving the schedule transform, the signature, and every other input untouched. The test asserts the
transform is byte-identical to the unmodified mandate's transform, proving this is purely an
effects-scope attack that transform-level checks cannot see. Result: `CLOSURE_MANIFEST_MISMATCH`.

**Second attacker test (`test_permitted_effects_digest_is_an_independent_control`):** the mandate
binds the *attacker's* whole-file digest but the *original* effects digest, so only the effects
control can fire. Result: `PERMITTED_EFFECTS_MISMATCH`.

**Test count:** 49 (27 inherited + 22 new), all passing.

## Correction 2 - frozen signed artifacts preserved append-only (was: manifest mutated in place)

**Defect:** cycle 1 edited `PG-P0-CLOSURE-MANIFEST.json` in place, moving its raw-bytes digest from
`7417cc6a7bdffc6cac0b3707be293fb01ec17434f848d831c2383f374cafb33a` to `8a3c14b6...`, and then
claimed the existing C4 signature still bound it. A signature is over exact bytes; it does not.

**Correction:** the frozen manifest is **byte-identical to base** in this candidate (independently
re-verified: `7417cc6a7bdffc6cac0b3707be293fb01ec17434f848d831c2383f374cafb33a`, 6613 bytes). All
corrections live in a new, separate, unsigned artifact
`docs/00-governance/signing/PG-P0-CLOSURE-MANIFEST-V2-PROPOSAL.json`, generated programmatically
from the frozen manifest so its seven `permitted_effects_at_execution_C8` entries are carried
structurally rather than re-typed. It carries a **new** `decision_id`
(`PG-P0-CLOSURE-002-PROPOSAL`) and states explicitly that it requires a **new** signature.
`PG-P0-CLOSURE-MANDATE.md` and `PG-P0-CLOSURE-MANDATE.dsse.json` are likewise untouched.

## Correction 3 - C9 target corrected (was: refs/heads/main, factually impossible)

**Defect:** cycle 1's `EVD-CLOSURE-019` proposed `target_ref refs/heads/main` with expected-old
`a908bbea1975ffc52a636765cd9f823dfeb978eb`.

**Independently verified this cycle:** `git merge-base a908bbe 042dda5` **exits 1** - no common
ancestor. `main`'s root commit is `a908bbe` itself (a single-commit orphan bootstrap history); the
closure lineage's root is `9a80f9d042f1ed176c9939bae57953443d0c5964`. The histories are **disjoint**,
so a C8 commit descending from `042dda5` could never fast-forward `main`. The earlier proposal was
not merely stale - it was impossible.

**Correction:** `target_ref refs/heads/pg-p0-closure-lineage`, `expected_old
042dda535be70927b73cd1a131b2545349729643` (verified to be that ref's exact current tip), with the
staleness caveat retained.

## Correction 4 - consumption and revocation state (was: maker-manufactured authority)

**Defect (consumption):** cycle 1 seeded `PG-P0-CONSUMED-DECISIONS.json` with `PG-P0-CLOSURE-001`
marked consumed, sourced from `EVD-CLOSURE-014`. That retroactively reclassified an **advisory
pre-execution C5 verification** as an execution. It also produced a misleading
`ALREADY_VERIFIED_EXACT` outcome that cycle 1 then cited as evidence the control was working.

**Correction:** the registry is **empty**. Consumption is recorded only by the human at or after the
real C8 execution. With no entry present, the first genuine verification correctly yields
`VERIFIED_EXACT`, not a spurious `ALREADY_VERIFIED_EXACT`.

**Defect (revocation):** cycle 1 presented an empty `PG-P0-REVOCATIONS.json` as settled state.

**Correction:** relabelled a maker-prepared scaffold that is explicitly **not authoritative**. An
empty list means "this maker recorded no revocation", never "the operator confirms none exists". The
operator must attest completeness at signing time. Both files' digests are bound into the unsigned
mandate proposal so the human signs over the exact external state in force.

## Correction 5 - truthful maker identity

The rejected candidate was committed as `SIM-EXEC-THROWAWAY`. This candidate is committed with
inline `user.name='Claude Opus 5 (BST-SA Motor sole maker)'` / `user.email='noreply@anthropic.com'`,
set per-commit only; no repository-wide git identity was changed.

## Scope boundaries observed

No signature generated or requested; no private key generated, received, or held; no C8 execution;
no C9 ref move; no governed ref moved; no merge; `PG-P1` untouched at `NOT_READY`; no deployment; no
production claim; no Graphify artifacts (base `042dda5` predates them and none were introduced); the
dirty `main` checkout was not modified; the rejected candidate branch was not built upon or amended.

## Status effect

None. Pre-execution, additive preparation only. `PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production not
authorized. Requires independent-checker review before any weight beyond advisory.
