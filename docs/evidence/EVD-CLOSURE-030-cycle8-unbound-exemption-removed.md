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
