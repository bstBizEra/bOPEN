# EVD-CLOSURE-017 - Maker evidence: VERIFY-P0-01 closure-manifest binding + C5 digest correction

**Version:** 0.1
**Status:** Maker-authored preparation evidence (advisory; NOT an independent-checker receipt). Per
`bopen-phase-closure` ("the maker never self-certifies"), this artifact requires a separate
independent-checker exact-SHA review before it carries any weight beyond advisory.
**Class:** PG-P0 closure-repair candidate, item 1 (DSSE subject/verifier-input binding) and item 2
(C5 digest correction). Prepared under the BST-SA "Claude is maker, Codex is independent checker"
model; Codex has not yet reviewed this artifact.
**Persisted:** by Claude (BST-SA Motor, sole maker this session), on isolated candidate branch
`codex/PG-P0-closure-repair-c8`, worktree base commit `042dda535be70927b73cd1a131b2545349729643`.
**Runtime pointer (non-anchor):** not applicable - direct maker session, no swarm task id.
**Authorizes nothing.** Signs nothing, applies nothing, moves no ref, consumes no decision.

## Part A - closure-manifest and permitted-effects binding in the DSSE verifier

**Defect audited:** `tools/verify_phase_transition.py` (VERIFY-P0-01) verified only the schedule
register transform. It took no `--closure-manifest` input and the mandate schema had no field
referencing the closure manifest's content or its `permitted_effects_at_execution_C8` list. The
closure manifest's own binding to the mandate (`PG-P0-CLOSURE-MANDATE.md`'s "Bound closure
manifest... content SHA-256 = ...") was therefore a narrative assertion, never independently
tool-verified - and exactly this hand-transcription path is what produced the Part B defect below.

**Change (this branch, `tools/verify_phase_transition.py`):**

- New reason code `CLOSURE_MANIFEST_MISMATCH`.
- `closure_manifest_digest` added to `MANDATE_ALLOWED` (NOT `MANDATE_REQUIRED`) - optional and
  additive, so the already-signed `PG-P0-CLOSURE-001` mandate (which predates this field) remains
  valid and unedited. Adding it to the required set would retroactively invalidate a signed
  mandate, which the DSSE-verification stop conditions forbid ("a mandate is edited after signing,
  in any byte").
- `closure_manifest_sha256(raw_bytes)` - raw-bytes SHA-256 (not RFC 8785 canonical; the manifest is
  a plain committed JSON file, not a signed payload).
- `permitted_effects_digest(manifest_obj)` - RFC 8785 canonical digest of
  `permitted_effects_at_execution_C8` alone, independently re-verifiable without re-hashing the
  whole manifest.
- `verify_closure_manifest_binding(mandate, closure_manifest_bytes)` - recomputes both digests;
  raises `CLOSURE_MANIFEST_MISMATCH` only when the mandate *declares*
  `closure_manifest_digest` and it disagrees with the supplied bytes. A mandate that omits the
  field (every mandate signed to date) is not contradicted - the binding is then
  advisory/reporting-only for that mandate.
- `verify_transition(...)` gains an optional trailing `closure_manifest_bytes=None` parameter
  (backward compatible: all 27 pre-existing positional call sites are unaffected) and the receipt
  now always carries `closure_manifest_sha256` / `permitted_effects_digest` (`null` when no
  manifest was supplied).
- CLI gains `--closure-manifest <path>` (optional).

**Tests:** `tests/governance/test_phase_transition_verify.py`, new `ClosureManifestBindingTests`
(7 tests: digest reported + full 64 hex chars; absent-manifest fields are `None`; a mandate without
the optional field is not contradicted; declared-digest mismatch is rejected
(`CLOSURE_MANIFEST_MISMATCH`); declared-digest match is accepted; an unrelated unknown mandate
field is still `MANDATE_INVALID` (the allow-list stays closed); a helper test reproducing the exact
Part B defect shape). Full suite: 34/34 `OK` (was 27; see run transcript in the closure-repair test
evidence, task 9).

## Part B - C5 digest correction (append-only; EVD-CLOSURE-014 is NOT edited)

**Defect audited:** `docs/evidence/EVD-CLOSURE-014-c5-signed-mandate-verification.md`'s embedded
verbatim checker-receipt JSON carries:

```
"closure_manifest_sha256": "7417cc6a7bdffc6cac0b3707be293fb01ec17434f848d831c2383f374cafb33"
```

which is **63 hex characters** (a SHA-256 digest is 64). The file's own "Maker note
(transcription)" already flagged this at the time and gave the correct value, but no durable
superseding evidence was ever persisted to correct the record inside the actual verbatim JSON
block - only a footnote next to it.

**Independent recomputation performed this session** (both agree):

- `hashlib.sha256(open("docs/00-governance/signing/PG-P0-CLOSURE-MANIFEST.json","rb").read()).hexdigest()`
  = `7417cc6a7bdffc6cac0b3707be293fb01ec17434f848d831c2383f374cafb33a` (64 hex chars).
- `docs/00-governance/signing/PG-P0-CLOSURE-MANDATE.md` independently states the same 64-char
  value ("Bound closure manifest... content SHA-256 = 7417cc6a...fb33a").
- `tools/verify_phase_transition.py closure_manifest_sha256()` (Part A, this branch) recomputes the
  identical value when pointed at the tracked manifest file, closing the gap mechanically: this
  digest can no longer be produced by hand-transcription, only by running the tool.

**Correction (superseding, append-only):** the correct, full-length closure-manifest content
SHA-256 for the `PG-P0-CLOSURE-001` C5 verification is:

```
7417cc6a7bdffc6cac0b3707be293fb01ec17434f848d831c2383f374cafb33a
```

This EVD-CLOSURE-017 record is the durable superseding evidence for that one field.
`EVD-CLOSURE-014` itself is left byte-for-byte unmodified (extend-only principle); its verbatim
JSON block is preserved as historical record with this correction layered on top, exactly as
`PG-P0-CLOSURE-MANIFEST.json`'s own `_encoding`/`_status` fields already document prior
supersessions ("Supersedes the C3 draft at 7d13898b...", "Rev: permitted_effects corrected...").
No other field in EVD-CLOSURE-014's receipt is affected: `pae_sha256`, `mandate_sha256`,
`predecessor_schedule_digest`, `successor_schedule_digest`, `subject_commit`, `subject_tree`,
`parent_commit` are all already full-length and were independently re-verified unchanged this
session.

## Status effect

None. Pre-execution, additive evidence only. No register mutated, no ref moved, no mandate edited,
no signature requested or handled. `PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production not authorized;
`main` unchanged. Requires independent-checker review (task 10, this session) before any weight
beyond advisory.
