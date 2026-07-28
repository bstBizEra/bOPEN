# EVD-CLOSURE-030 - Maker evidence: cycle 8 removes the unbound-legacy exemption

**Version:** 0.1
**Status:** Maker-authored remediation evidence (advisory; NOT an independent-checker receipt).
Requires independent-checker review before any weight beyond advisory.
**Class:** PG-P0 closure-repair, remediation cycle 8.
**Maker:** Claude Opus 5 (BST-SA Motor worker agent), sole maker.
**Predecessor:** cycle-7 candidate `1756bad2cea88298a094bcfe20e01d7efd9c8473`.
**Authorizes nothing.** No register mutated, no mandate signed or consumed, no ref moved, no phase completed.

## Provenance of the finding this remediates - read first

The cycle-7 verdict `REJECT_EXACT_SHA` was **relayed to the maker by the operator**. At the time of
writing it is **not persisted anywhere in this repository**: no commit message, no file, and no
reference to `1756bad2cea88298a094bcfe20e01d7efd9c8473` exists on any of the 126 refs.

The maker has therefore **not read the checker's report** and does not certify it. This document
records what was changed and why; it does not attest that the verdict was issued, nor reproduce its
reasoning as though the maker had verified it. Persisting the verdict verbatim as a durable receipt
remains an open control, and it is not something the maker can close.

## The defect

Cycle 7 inverted the closure-binding default so an absent binding became fatal, and kept a
decision-scoped escape hatch for `PG-P0-CLOSURE-001`, a mandate signed before `closure_binding`
existed. The hatch was narrow: it matched one decision id, could not be repurposed into a blanket
bypass, and annotated its receipt and stdout.

It was still a path on which the verifier returned **exit 0 with a `VERIFIED_EXACT` verdict for a
mandate carrying no closure binding at all** - a green result for precisely the condition the control
exists to stop. A narrower fail-open is still a fail-open; the annotation makes it auditable after the
fact but does not stop an apply gate that reads rc and a verdict string.

## Root cause, which is why the hatch appeared necessary

The removed `required` parameter conflated two independent questions:

1. must the mandate **carry** a binding?
2. how **deeply** is the declared execution verified?

Because one flag answered both, exempting a legacy mandate from (1) also silently relaxed (2), and
the only way to verify anything about `PG-P0-CLOSURE-001` was to switch both off together. Splitting
them removes the motivation for an exemption entirely.

## What changed

**`tools/verify_phase_transition.py`**

- Deleted `closure_binding_required`. There is no longer any function that can answer "no" to "is a
  binding required".
- Deleted the `allow_unbound_legacy_decision` parameter from `verify_transition` and the `required`
  parameter from `enforce_closure_binding`.
- Deleted the `--allow-unbound-legacy-mandate` CLI flag. An invocation written against it now fails
  at argument parsing with exit 2 rather than quietly verifying something weaker than it claims.
- Deleted the `legacy_unbound_exemption` receipt field. No receipt can express "verified, but
  exempted", because no such state exists.
- An absent binding, or absent manifest / revocation / consumed bytes, is now an unconditional
  `CLOSURE_BINDING_REQUIRED` rejection.
- Verification **depth** now follows from the evidence supplied: an execution root and/or repository
  verifies successor blobs and tree against real bytes; supplying neither validates the binding
  structurally and records `closure_execution_verification: false` in the receipt.
- The CLI **refuses** a structural-only result (exit 1, `EXECUTION_ROOT_REQUIRED`) so no operator
  invocation can report a closure whose execution was never compared to real bytes.

**`tests/governance/test_phase_transition_verify.py`**

- Fixtures are **bound by default**. A test that wants an unbound mandate calls
  `_mandate(..., bound=False)`, so the exemption is explicit at the call site instead of being
  applied silently by the shared helper - which is how cycle 7's blanket default hid the weaker path
  from most of the suite.
- The helper supplies matching manifest / revocation / consumed bytes by default; a test that wants
  to withhold them passes `None` explicitly.
- The exemption tests are replaced by their inverses: the legacy decision id is not special, a
  substituted unbound mandate is still rejected, the receipt carries no exemption field, and the
  removed predicate is asserted absent so the default cannot be restored by re-wiring a caller.

**Ledgers.** `Progress_Log.md`, `Backlog.md` and `Recap_Today.md` each gain the `-0006` triple that
cycle 7 omitted (recorded retrospectively, and labelled as such) and the `-0007` triple for this
cycle. The series is now unbroken from `0001` to `0007`.

**Manifests.** `GOV-P0-02-DOCUMENT-MANIFEST.json` then `DOCUMENT-MANIFEST.json`, regenerated in that
order.

## Consequence the reviewer must weigh

**`PG-P0-CLOSURE-001` is now unverifiable by this tool, by design.** It carries no closure binding and
cannot acquire one without invalidating its signature. Completing the PG-P0 closure therefore requires
a **newly issued and operator-signed mandate that carries the binding**. That is the intended reading
of "require a newly bound mandate": the remedy is a new mandate, not a verifier that accepts the old
one.

This is a deliberate loss of capability. Any runbook step, evidence document or plan that assumed
`PG-P0-CLOSURE-001` could be verified is invalidated by this commit.

## Verification performed

- Full suite: **267 tests, OK**.
- No residual reference to the removed hatch anywhere in the tool: `allow_unbound`,
  `legacy_unbound`, `closure_binding_required`, `UNBOUND_LEGACY` all return zero matches.
- Ledger files written LF-only.

## Not done, and why

- The cycle-7 verdict is **not persisted** as a durable receipt. The maker cannot persist a verdict
  it has not read; doing so would fabricate independent evidence.
- No new mandate has been drafted or signed. Issuance and signature are operator acts.
- `EVD-CLOSURE-016` H4/H5 (duplicate keyid ingest, small-order keys, lexical time comparison) are
  **untouched** and remain open. They are a separate finding and folding them in would put two
  unrelated changes under one review.

---

## Append-only amendment - 2026-07-29 - maker self-audit findings and their remediation

Before independent review began, the maker ran two adversarial passes over its own candidate
`fdf0434bfee6ff5370a133b5c1b3419649a588f9`. Both are maker-side and carry no independence. They did
not refute the central claim - no input produced a VERIFIED verdict for an unbound mandate - but they
found four defects in the maker's own work, three of which are fixed in the successor commit.

**A1 - `--execution-root ""` silently meant the current working directory. FIXED.**
`main()` passed the argument through unchecked, and `Path("")` is `.`, so an empty string counted as
"supplied" and resolved to the process CWD. Demonstrated: `--execution-root "" --repository ""` with
the CWD set to a fixture repository returned `rc=0 VERIFIED: VERIFIED_EXACT`. Real bytes were
compared, so the literal claim held - but against a tree the operator never named, which in a runbook
is one unset shell variable (`--execution-root "$VAR"`) away from a green result describing the wrong
repository. Cycle 8 made both roots mandatory, which made this the sole path to `rc=0` and therefore
raised its exposure. Both options now reject an empty or whitespace-only value.

**A2 - the exemption-removal test was VACUOUS. FIXED, and this is the most serious of the four.**
`test_exemption_parameter_no_longer_exists` called the test file's own `_verify(...)` helper, so the
`TypeError` it asserted came from the helper's signature and production was never entered. Proven by
mutation: re-adding a working `allow_unbound_legacy_decision` parameter to `verify_transition` left
the test passing. Worse, a functioning opt-in exemption re-introduced under a *different* parameter
name failed **0 of 105** tests. The test now asserts against `inspect.signature(v.verify_transition)`
and calls production directly, and a new test sweeps every optional parameter of `verify_transition`
with truthy probes to prove none of them can tolerate an absent binding.

The regression this cycle exists to prevent was never unguarded: restoring cycle 7's default-ON
behaviour does fail `test_the_legacy_decision_id_is_not_special`. Only the opt-in-under-a-new-name
variant was unguarded.

**A3 - the new CLI refusal shipped with zero tests. FIXED.**
This commit's argument that a structural-only library mode is safe rests on `main()` refusing it, and
nothing in the repository invoked `main()`. Five subprocess tests now exercise the real entrypoint:
structural-only is refused, the removed flag exits 2, an empty execution root or repository is
refused, and an unbound mandate is refused end to end. Each asserts on rc **and** stdout, because an
apply gate reads both (EVD-CLOSURE-016 H2).

**A4 - `EVD-CLOSURE-029` still prescribes the deleted flag. NOT fixed here; recorded.**
`EVD-CLOSURE-029` is the operative record of procedure for step C7 and still specifies
`--allow-unbound-legacy-mandate PG-P0-CLOSURE-001` with an expected `rc == 0`. That invocation now
exits 2. The original text of this document acknowledged the invalidation only in generic prose; it
is stated explicitly here instead: **EVD-CLOSURE-029's C7 invocation is superseded and must not be
run.** `EVD-CLOSURE-029` is append-only evidence and has not been edited. A corrected runbook is a
separate work item and is not in this commit's scope.

### Known and deliberately not changed

**The `verdict` field still does not encode verification depth.** `verify_transition` returns
`VERIFIED` / `VERIFIED_EXACT` for a structural-only run; only the separate
`closure_execution_verification: false` records that execution was never checked. The CLI refuses
that combination, and no library importer exists in this repository today (`grep` finds only the test
file), so the risk is latent rather than live. Encoding depth in the verdict itself would change the
meaning of a value that appears in signed and reviewed evidence, so it is raised for the checker to
rule on rather than changed unilaterally.

**Pre-existing findings, unchanged and fail-closed:** the execution root must be a pristine checkout
(ignored files such as `__pycache__` trip `EXECUTION_ROOT_MISMATCH`); `ALREADY_VERIFIED_EXACT` is
unreachable in closure mode because `consumed_state_digest` is fixed at signing time; a missing
optional input reports `CLOSURE_BINDING_REQUIRED`, which reads as though the mandate were at fault;
and a manifest whose effects value is a non-iterable raises `TypeError` rather than a `VerifyError`,
which is ungraceful but not attacker-reachable and still non-zero.

### Verification after the amendment

111 tests in the verifier module (106 + 5 new CLI subprocess tests); full suite re-run; validators and
manifests re-checked. The maker self-audit is not independent review and does not reduce what the
checker should attempt.

---

## Append-only amendment 2 - 2026-07-29 - the A1 fix was incomplete; fixed at the enforcement point

A third maker self-audit found that the A1 remedy in the previous amendment **closed one spelling of
the hazard rather than the class it belongs to**. This is recorded in full because the first fix was
published and would have been reviewed as adequate.

**What was wrong with the A1 fix.** It rejected empty and whitespace-only values in `main()`. But
`Path("")` is `.` for exactly the same reason `.`, `./`, `..` and `docs/..` are - they all resolve
against the process working directory. Measured against the previous commit, with the CWD set to a
fixture repository, every one of these returned **`rc=0 VERIFIED: VERIFIED_EXACT`**:

    --execution-root .        --execution-root ./       --execution-root ..
    --execution-root docs/..  --execution-root "./$ROOT"  (ROOT unset)
    --execution-root "${ROOT:-.}"                         (ROOT unset)

The last two are the realistic runbook shapes of the very unset-variable mistake the guard's own
comment cited. Only the bare `"$ROOT"` spelling was caught.

**Two further gaps in that fix:**

- **It was CLI-only.** `verify_transition(execution_root="", repository="")` was never guarded and
  returned `VERIFIED_EXACT` with `closure_execution_verification: true`. The remedy sat at the
  outermost layer while the enforcement point went untouched.
- **The reason code was wrong for one option.** `--repository ""` reported
  `EXECUTION_ROOT_REQUIRED`, so the code and the option name contradicted each other in one line.
  The test written alongside it asserted only the substring `"empty value"`, so it could not catch
  that - a test shaped to pass rather than to constrain.

**The fix now applied.** A single validator, `require_named_directory`, is called from
`enforce_closure_binding` - the library enforcement point, so every caller is covered. It requires a
path that names one tree unambiguously: non-empty, **absolute**, and an existing **directory**. A
CWD-relative value is ambiguous by construction; the tree verified depends on where the process
happened to start, and that is not recorded in the verdict. For a control whose entire purpose is to
prove which bytes were verified, that ambiguity is the defect.

Reason codes now match the option: `--execution-root` reports `EXECUTION_ROOT_REQUIRED`,
`--repository` reports `REPOSITORY_REQUIRED`.

**Deliberate behaviour change:** a legitimate *relative* execution root is now refused. That is a
real loss of convenience, accepted because a relative path cannot be audited from the verdict alone.

**The verdict line now names the verified tree.** Previously `main()` printed only the verdict and
outcome, so a gate reading rc and stdout could not distinguish `<REPO>` from `.` from `..`. It now
prints the resolved `execution_root` and `repository`. That is what made the bypass invisible.

**Uncaught tracebacks with empty stdout are gone.** Five required and three optional path options
previously raised `PermissionError: '.'` out of `_load()` - rc=1 with **empty stdout** and a message
about the current directory rather than the argument at fault. Every failure now prints a `REJECTED:`
line, which is the contract the CLI tests were written against. Supplying an unreadable path to an
optional option is also no longer silently equivalent to omitting it.

### Test-suite defects found in the same audit round, fixed here

A parallel mutation audit of the tests written in the previous commit found that they were not
vacuous - all seven were killed by at least one mutant reproducing the defect they claim to prevent -
but it found one blocking defect and two blind spots, all in the maker's own test code.

**T1 - BLOCKING: ten tests never ran under one of the two runners.** `if __name__ == "__main__":
unittest.main()` sat ABOVE `CommandLineRefusalTests` and `AmbiguousExecutionPathTests`, so
`python tests/governance/test_phase_transition_verify.py` executed `unittest.main()` before those
classes existed: **106 tests** that way versus **116** under `python -m unittest`. Verified by
mutation: deleting the structural-only refusal from `main()`, and restoring the empty-path bypass,
both reported OK under direct execution and FAILED only under `-m unittest`. The entire "untested CLI
gate" remediation was invisible to a plausible runner. This is the same class of defect as a test
that asserts against its own helper - the guard exists but is not wired in. The `__main__` block now
sits last, with a comment saying why. Both runners now report the same count.

**T2 - the exemption sweep was blind to magic-value exemptions.** It probed only
`("PG-P0-CLOSURE-001", True)` against a fixture whose decision id was the same string. Two mutants
survived all 111 tests: an exemption firing on `binding_policy == "GRANDFATHERED"`, and one scoped to
a decision-id allowlist hardcoded to the OTHER real legacy id. The sweep now iterates both real
decision ids and ten probe values including allowlist-shaped ones. Re-verified by rebuilding the
magic-value mutant: it now FAILS the suite where it previously passed.

**T3 - no CLI positive control.** A mutant making `main()` refuse unconditionally left four of the
five refusal tests passing; a tool incapable of ever returning 0 would have looked healthy. Added a
positive control that builds a real git execution tree and asserts `rc=0`, `VERIFIED_EXACT`, and that
the resolved root appears in stdout. Added a discriminator asserting the structural refusal does not
carry the empty-value message, since both refusals share a reason code.

**T4/T5 - minor, fixed.** The runtime clause of the removal test is one mutant wide (it catches only
a `**kwargs` catch-all, which `inspect` never reports as an optional parameter); that is now stated
rather than implied, and its probe uses the mandate's own decision id instead of a mismatched one. A
dead assertion (`exc.reason != v.VERIFIED` - a verdict is never a rejection reason, so it could never
fire) is removed, and the sweep's `except` no longer swallows `ValueError`/`AttributeError`/`OSError`,
which would have masked a future exemption path that raised one of them after accepting.

**Verification:** 280 tests in the full suite, 118 in this module, and both runners agree. New
`AmbiguousExecutionPathTests` covers the class - empty,
whitespace, `.`, `./`, `..`, `docs/..`, bare relative, nonexistent absolute, a file rather than a
directory, both options' reason codes, and the library-level call that the previous fix missed.

**Lesson recorded against the maker.** Two fixes in a row addressed the demonstrated instance rather
than the class: `git apply --check` earlier in this lineage, and now the empty string. The pattern is
fixing what was shown rather than asking what else reaches the same state. The remedy that held was
to move enforcement to the point every caller passes through, and to make the output name the thing
that was verified.
