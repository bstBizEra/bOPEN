# Handoff - PG-P0 closure repair cycle 8 -> Codex independent review

> **REVIEW SUBJECT IS `a9f7d8de6efbd4208d60491a1e1476c539ecff3b`** - the third candidate. Two
> earlier ones (`fdf0434`, `c0abb2b`) were superseded before review began, each because a maker
> self-audit found defects in the one before it. Three audit rounds, three sets of findings, all in
> my own work. **Assume more remain.** Highlights you should not have to rediscover: my first
> empty-path fix closed one spelling and left `.`, `./`, `..` returning rc=0 VERIFIED_EXACT against
> the process CWD; and ten tests - including the entire CLI-gate remediation - never ran under
> `python <file>` because `unittest.main()` sat above their classes. I ran two adversarial passes over my own candidate before handing it to you. They
> could not refute the central claim, but they found four defects in my own work - including a test I
> wrote that asserted nothing about production. Three are fixed in the successor commit; the fourth is
> recorded. Details in the self-audit section below and in the EVD-CLOSURE-030 amendment. I did not
> amend `fdf0434`; it is preserved as the parent.

> Untracked coordination artifact in the repo working tree, matched by `.gitignore` line 40
> (`/HANDOFF-*-TO-CODEX.md`). Not part of the reviewed candidate. Do not `git add` it.

```yaml
handoff_id: HANDOFF-PG-P0-CLOSURE-CYCLE8-001
work_item_id: PG-P0 closure repair, remediation cycle 8
from_actor: Claude Opus 5 (BST-SA Motor worker agent), sole maker
to_actor: BST-Codex-Motor (independent checker)
role_completed: maker
repository: C:/laragon/www/bopen
branch: claude/PG-P0-closure-cycle8
worktree: C:/b-c8
base_commit: 1756bad2cea88298a094bcfe20e01d7efd9c8473   # cycle 7, REJECT_EXACT_SHA
head_commit: a9f7d8de6efbd4208d60491a1e1476c539ecff3b   # SUPERSEDES c0abb2b and fdf0434
superseded_candidates: [fdf0434bfee6ff5370a133b5c1b3419649a588f9, c0abb2b3e6444c36f16596674b843026931cb22e]

requirements:
  - Remove the green unbound-legacy C7 path: it must not return 0 with VERIFIED_EXACT.
  - Require a newly bound mandate.
  - Make test exemptions explicit.
  - Add the missing ledger events.
  - Regenerate manifests.
  - Publish one new exact SHA for review.

decisions:
  - Removed the hatch outright rather than narrowing it again. A hatch that produces a passing
    verdict is not a narrower control; it is the same fail-open behind a longer command line.
  - Fixed the ROOT CAUSE rather than the symptom. The `required` parameter conflated "must the
    mandate carry a binding" with "how deeply is execution verified", so exempting a legacy mandate
    from the first silently relaxed the second. Split into: binding always mandatory; depth follows
    from whether an execution root / repository is supplied.
  - The CLI now REFUSES a structural-only result rather than annotating it. Cycle 7 annotated the
    weaker mode in stdout; annotation still returns 0, and EVD-CLOSURE-016 H2 already showed a gate
    reading rc alone.
  - Did NOT keep the flag as an accepted no-op (the precedent cycle 7 set with
    --require-closure-binding). An invocation written against an exemption should break loudly, not
    appear to work.

changed_files:
  - tools/verify_phase_transition.py
  - tests/governance/test_phase_transition_verify.py
  - docs/evidence/EVD-CLOSURE-030-cycle8-unbound-exemption-removed.md   (new)
  - Progress_Log.md, Backlog.md, Recap_Today.md
  - docs/CHANGELOG.md
  - docs/manifests/GOV-P0-03-PACKAGE-MANIFEST.json
  - docs/manifests/GOV-P0-02-DOCUMENT-MANIFEST.json
  - docs/DOCUMENT-MANIFEST.json

verification_performed:
  - Full suite 273 tests OK, run twice: in the worktree and again from a FRESH `git clone --shared`
    checkout of c0abb2b (0 modified paths there, so the committed blobs are what was tested).
    fdf0434 measured 267 before the self-audit added 6.
  - 11 governance validators rc=0; root-control surfaces PASS; both document manifests --check
    current; docket --check rc=0.
  - `--allow-unbound-legacy-mandate` is absent from --help (0 matches) and any invocation using it
    exits 2. At library level `verify_transition(..., allow_unbound_legacy_decision=...)` raises
    TypeError, pinned by test_exemption_parameter_no_longer_exists - which in fdf0434 was VACUOUS and
    is rewritten in c0abb2b to assert against production (see A2).

authorization_required: >
  None granted or requested. This handoff authorizes nothing, signs nothing, moves no ref, consumes
  no decision. main unmoved at a908bbea1975ffc52a636765cd9f823dfeb978eb; PG-P0 ACTIVE;
  PG-P1 NOT_READY; production not authorized.

timestamp: 2026-07-29T00:00:00+07:00
```

## Read this first - a provenance limit on the whole cycle

**The cycle-7 verdict was relayed to me by the operator and is not persisted anywhere in this
repository.** I measured this across all 126 refs: no commit message, no file, and no reference to
`1756bad` in any tree. I have **not read your report**, and nothing in this commit certifies that it
was issued or reproduces its reasoning as though I had verified it.

That means two things for your review:

1. If I have misread the finding, the remediation may be aimed at the wrong thing. The instruction I
   worked from was: remove the green unbound-legacy path so it cannot return 0 with VERIFIED_EXACT,
   require a newly bound mandate, make test exemptions explicit, add the missing ledger events,
   regenerate manifests, publish one new exact SHA.
2. Persisting your verdict verbatim as a durable receipt is still open, and it is not something I can
   close - a maker cannot manufacture independent evidence.

## The consequence you should push hardest on

**`PG-P0-CLOSURE-001` is now unverifiable by this tool, deliberately.** It carries no closure binding
and cannot acquire one without invalidating its signature. Completing the PG-P0 closure therefore
requires a newly issued and operator-signed mandate that carries a binding.

This is a real loss of capability, and it invalidates any runbook step, evidence document or plan
that assumed that mandate could still be verified - including the invocation recorded in
EVD-CLOSURE-029. I did not edit EVD-CLOSURE-029 (append-only); EVD-CLOSURE-030 records the
supersession instead. If you think that is the wrong instrument, say so.

## Suggested adversarial angles

1. **Is the removal complete?** `allow_unbound`, `legacy_unbound`, `closure_binding_required`,
   `UNBOUND_LEGACY` return zero matches in the tool - confirm independently, and check I did not
   leave an equivalent path reachable by another name.
2. **Did splitting `required` open a NEW soft path?** Depth is now inferred from
   `execution_root is not None or repository is not None`. Structural mode is a legitimate library
   mode for tests, and the CLI refuses it - but confirm the refusal cannot be bypassed, and that
   nothing else calls `verify_transition` and ignores `closure_execution_verification`.
3. **Are the test fixtures actually bound?** Fixtures are bound by default and `bound=False` is
   explicit. Verify the default fixture really exercises a bound path rather than a vacuous one, and
   that the count is not inflated by tests that no longer assert anything. I audited this myself and
   found exactly one vacuous test, now fixed - assume I missed others.
4. **Ledger `-0006` is retrospective.** I recorded cycle 7's omitted triple in this commit and
   labelled it as such. If backfilling a ledger event for an already-rejected cycle is the wrong
   call, that is a finding I would rather have now.
5. **`--write-manifest` was used** to rebind GOV-P0-03 after the ledger appends. I treated that as
   the documented same-commit rebind for authorized source changes, not as regenerating an attested
   artifact to clear a stale check. Confirm that reading.

## Self-audit findings on fdf0434, all fixed or recorded in c0abb2b

**A1 `--execution-root ""` meant the process CWD.** `Path("")` is `.`, so an empty string counted as
supplied. Demonstrated rc=0 VERIFIED_EXACT against a tree the operator never named. Both options now
reject empty/whitespace values. FIXED.

**A2 my exemption-removal test was VACUOUS - the worst of the four.** It called the test file's own
`_verify` helper, so its TypeError came from the helper's signature and production was never entered.
Mutation proof: re-adding a working `allow_unbound_legacy_decision` to `verify_transition` left it
passing, and an exemption re-introduced under a DIFFERENT name failed 0 of 105 tests. Now asserts on
`inspect.signature(v.verify_transition)`, calls production directly, and a new test sweeps every
optional parameter with truthy probes. FIXED. Note the cycle-7 default-ON regression was never
unguarded - only the opt-in-under-a-new-name variant was.

**A3 the CLI refusal had zero tests.** My own design argument rests on `main()` refusing the
structural path, and nothing invoked `main()`. Five subprocess tests now assert rc AND stdout. FIXED.

**A4 `EVD-CLOSURE-029` still prescribes the deleted flag** with expected rc == 0; it now exits 2. Now
stated explicitly as superseded in EVD-CLOSURE-030 rather than generic prose. 029 is append-only and
unedited. A corrected runbook is a separate work item. RECORDED, NOT FIXED.

**Known, deliberately unchanged:** the `verdict` field still does not encode verification depth, so a
library importer keying on `VERIFIED_EXACT` would get green for a structural-only run. The CLI refuses
it and no such importer exists here, so it is latent. Changing the meaning of a value that appears in
signed evidence is not a unilateral maker decision - please rule on it.

273 tests OK (was 267). Fresh-checkout verified at c0abb2b: 0 dirty paths, 273 OK, root-control PASS,
manifests current.

## Maker self-check on angle 2 - result, not a substitute for your review

I ran angle 2 myself because it is the risk I rate highest in my own change. Findings, all measured:

- **Only the tool calls the changed functions.** Across the tree, `verify_transition(` appears once
  outside tests (its own CLI, line 1289) and `enforce_closure_binding(` once (line 1163). No other
  production caller exists that could ignore the depth signal.
- **The CLI does consume it** (line 1311), and `enforce_closure_binding` now has exactly one `return`
  statement - the result dict. The former `return None` paths are gone, so the receipt's
  `.get("execution_verified")` cannot silently read from a None result.
- **Partial execution inputs do not open a soft path.** Measured on the committed tree:
  execution root only -> rejects; repository only -> rejects `EXECUTION_ROOT_REQUIRED`; neither ->
  structural with `execution_verified=False`, which the CLI then refuses. There is no combination
  that yields rc=0 with a verified-looking verdict on unverified execution.

This is a maker self-check. It narrows where you look; it does not stand in for independent review,
and I would rather you tried to break it than took the above on trust.

## Known-clean, so you do not re-derive it

The GOV-P0-03 package manifest was written with CRLF by `--write-manifest` on Windows; I normalised
it to LF before staging, so the working copy and the committed blob agree. All ten changed paths are
LF-only. The fresh-checkout run above is the evidence that this holds after checkout, not just in my
worktree.

## Out of scope, deliberately

EVD-CLOSURE-016 H4/H5 remain open and untouched: trust-root ingest still accepts duplicate keyids
(last entry silently wins), there is no small-order / subgroup public-key check, and validity windows
are still compared as ISO-8601 strings rather than absolute instants. I demonstrated the first and
third against the cycle-7 tool and can supply the probe. They are a separate finding; folding them in
would put two unrelated changes under one review.
