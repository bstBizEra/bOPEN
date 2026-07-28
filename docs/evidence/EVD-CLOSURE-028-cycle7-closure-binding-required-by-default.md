# EVD-CLOSURE-028 - Maker evidence: cycle-7 closure binding required by default

**Version:** 0.1
**Status:** Maker-authored remediation evidence (advisory; NOT an independent-checker receipt).
Requires independent-checker review before any weight beyond advisory.
**Class:** PG-P0 closure-repair, remediation cycle 7, on branch
`claude/PG-P0-closure-binding-default-cycle7` from exact base
`2a18ed5352930f7603543cdab00fe397e6b11dc4` (cycle 6 tip).
**Maker:** Claude Opus 5 (BST-SA Motor worker agent), sole maker.
**Authorizes nothing.** Signs nothing, applies nothing, moves no ref, consumes no decision.

## Maker independence caveat (read first)

The defect corrected here was found by this maker while reviewing cycle 2-6, and cycle 2-6 exists
because this maker's own earlier candidate (`2134ea2`, cycles 1) was rejected. This maker is
therefore **not disinterested** about the cycle-2 design. The finding below is stated as a
reproducible command sequence precisely so an independent checker can confirm or refute it without
relying on the maker's judgement.

## Defect: the fail-closed control defaulted to off

Cycle 2 (`EVD-CLOSURE-022`) correctly identified that cycle 1 had made closure binding optional and
had shipped a test asserting an unbound mandate is "not contradicted". Cycle 2 built a genuine
fail-closed control: a closed-key `closure_binding` object, six reason codes, enforcement before
authority resolution. That work is sound and is retained unchanged here.

But cycle 2 defaulted `require_closure_binding=False`, engaging the control only when a caller
opted in with `--require-closure-binding`. Empirically, against the real signed mandate at the
cycle-6 tip:

```
$ python tools/verify_phase_transition.py <real inputs>
VERIFIED: VERIFIED_EXACT                       rc=0      # control silently inert

$ python tools/verify_phase_transition.py <real inputs> --require-closure-binding
REJECTED: CLOSURE_BINDING_REQUIRED             rc=1      # control engaged
```

The vulnerability class from cycle 1 was therefore not eliminated, only relocated: from "always
open" to "open unless the caller remembers a flag". Three facts made that materially dangerous:

1. **No validator, docket check, or test enforced the flag.** Only the verifier CLI accepted it.
   (`grep -rln require_closure_binding tools/` matched the verifier alone.)
2. **The operative C7 apply runbook did not pass it.** `EVD-CLOSURE-012`, inherited unchanged and
   still the procedure of record, specifies "VERIFY-P0-01 ... VERIFIED_EXACT" with no flag. An
   operator following it would have received a clean `VERIFIED_EXACT` on an unbound mandate while
   the evidence trail read as though closure binding was enforced.
3. **This repository already learned this exact lesson once.** `EVD-CLOSURE-016` H2: a bit-flipped
   signature passed all twelve validators and all 189 tests because a single gate checked `rc`
   alone. A control that must be switched on is a control that will eventually be left off.

## Correction

**`tools/verify_phase_transition.py`:**

- New predicate `closure_binding_required(mandate, allow_unbound_legacy_decision)`. Binding is
  required by **default**; absence is fatal unless the caller names the specific legacy decision.
- `verify_transition(...)`'s `require_closure_binding=False` parameter is **replaced** by
  `allow_unbound_legacy_decision=None`. The public function's own default is now fail-closed, so a
  caller who omits the argument entirely gets the safe behaviour (pinned by
  `test_library_default_argument_is_fail_closed`).
- CLI: new `--allow-unbound-legacy-mandate DECISION_ID`.
  `--require-closure-binding` is retained as an accepted, documented no-op so existing invocations
  (including the one written into `PG-P0-CLOSURE-MANDATE-V2-PROPOSAL.md`) keep working unchanged.

**The hatch is scoped to a decision id, never a boolean off-switch.** `PG-P0-CLOSURE-001` was
signed before `closure_binding` existed and cannot acquire one without invalidating the signature,
so an escape hatch is genuinely necessary. But a blanket `--allow-unbound` would equally wave
through an attacker-substituted unbound mandate carrying a different decision id. Matching on the
id confines the hatch to the one historical artifact it was opened for:

```
$ ... --allow-unbound-legacy-mandate PG-P0-CLOSURE-001
VERIFIED: VERIFIED_EXACT (UNBOUND_LEGACY_EXEMPTION: PG-P0-CLOSURE-001)   rc=0

$ ... --allow-unbound-legacy-mandate SOME-OTHER-DECISION
REJECTED: CLOSURE_BINDING_REQUIRED                                        rc=1
```

**The weaker mode is never invisible.** The receipt carries
`legacy_unbound_exemption: <decision_id>` (`null` on the fully bound path) and
`closure_execution_verification: false`, and stdout appends `(UNBOUND_LEGACY_EXEMPTION: ...)`.
Because the apply gate reads stdout as well as `rc` (`EVD-CLOSURE-016` H2), an exempted run cannot
be mistaken for a fully bound one at either layer. A present-but-malformed binding is still
rejected even when the decision is exempted -- the hatch tolerates **absence only**
(`test_exemption_never_weakens_a_present_binding`).

## Runbook correction (the gap that made this reachable)

`EVD-CLOSURE-012`'s C7 step is superseded on this branch by
`docs/evidence/EVD-CLOSURE-029-c7-runbook-verifier-invocation.md`, which states the exact verifier
invocation the apply must use and why the bare invocation is no longer sufficient. Fixing the
default without fixing the runbook would have left the same class of latent gap for the next
control added.

## Tests

`tests/governance/test_phase_transition_verify.py`: **103 pass** (was 96; 7 added). New
`ClosureBindingRequiredByDefaultTests` pins: rejection by default; the *public function signature's*
own default being fail-closed; the named exemption working; the exemption **not** covering a
different decision id; the receipt recording the exemption; the hatch not
weakening a present binding; and direct predicate semantics so the default cannot be flipped back
without a failure here.

Pre-existing tests are unchanged in intent: the shared `_verify` helper exempts this file's own
legacy-shaped fixture decision id, so tests written to exercise canonicalization, authority and
replay keep exercising exactly those things. Tests asserting the new default pass
`allow_unbound_legacy_decision=None` explicitly.

## Status effect

None. `PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production not authorized; `main` unchanged at
`a908bbea1975ffc52a636765cd9f823dfeb978eb`. The C6-C8 execution bytes remain the human-only blocker
recorded in `EVD-CLOSURE-023`; nothing here changes that. `PG-P0-CLOSURE-002` remains unsigned and
`DRAFT_NOT_SIGNABLE`.
