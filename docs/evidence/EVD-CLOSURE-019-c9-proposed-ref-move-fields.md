# EVD-CLOSURE-019 - Maker evidence: explicit proposed C9 target-ref and expected-old CAS fields

**Version:** 0.1
**Status:** Maker-authored preparation evidence (advisory; NOT an independent-checker receipt).
Requires independent-checker review before any weight beyond advisory.
**Class:** PG-P0 closure-repair candidate, item 5.
**Persisted:** by Claude (BST-SA Motor, sole maker this session), on isolated candidate branch
`codex/PG-P0-closure-repair-c8`, worktree base commit `042dda535be70927b73cd1a131b2545349729643`.
**Authorizes nothing. Moves no ref.**

## Gap audited

`PG-P0-CLOSURE-MANIFEST.json`'s `prohibited_effects` names the C9 act ("any move of an
authoritative ref by an agent (C9 is the operator expected-old CAS commit)") but never states,
anywhere in the frozen closure record, which ref C9 moves or what its expected-old value is. Every
other CAS in this lineage (the schedule-register predecessor digest, the docket validator
expected-state) is bound to an exact value in the manifest; the C9 ref-level CAS was the one
exception - an operator arriving at C9 would have had to reconstruct `target_ref`/`expected_old`
from narrative prose scattered across `PG-P0-CLOSURE-MANDATE.md` ("main a908bbe") rather than a
single explicit field.

## Fields added (`PG-P0-CLOSURE-MANIFEST.json`, this branch, new `c9_proposed_ref_move` block)

```json
{
  "target_ref": "refs/heads/main",
  "expected_old": "a908bbea1975ffc52a636765cd9f823dfeb978eb",
  "expected_old_as_of": "2026-07-27T17:06:16+07:00",
  "proposed_command": "git update-ref refs/heads/main <new_C8_commit_sha> a908bbea1975ffc52a636765cd9f823dfeb978eb"
}
```

- `target_ref`: `refs/heads/main`. This is the ref every closure evidence record has been binding
  status against throughout the lineage ("main a908bbe" - `PG-P0-CLOSURE-MANDATE.md`;
  "`main` remained `a908bbea1975ffc52a636765cd9f823dfeb978eb`" - `EVD-CLOSURE-015`), i.e. it is
  where the C8 execution commit is intended to land, not the `pg-p0-closure-lineage` staging
  branch this closure-repair candidate itself is built on top of.
- `expected_old`: `a908bbea1975ffc52a636765cd9f823dfeb978eb` - `main`'s tip as independently
  confirmed this session (`git rev-parse HEAD` on the dirty main checkout, matching every prior
  evidence record's citation).
- **Explicit staleness caveat (`expected_old_note`):** this is a *proposal snapshot*, not a live
  value. It goes stale the instant `main` advances. The operator's real C9 command MUST re-read
  `main`'s actual tip immediately before executing the compare-and-swap; this field only removes
  the ambiguity about *which* ref and *which* field name the C9 CAS uses, matching the pattern
  already proven fail-closed for the schedule-register CAS (`EVD-CLOSURE-015` case 6, "Wrong parent
  / CAS" - rejected: `cannot lock ref ...: is at <x> but expected <y>`).
- No distinction is smuggled between `predecessor.source_commit`
  (`dab84c06f4f78d7f285f462d869969f156542079`, the schedule-register blob lineage on
  `pg-p0-closure-lineage`) and the C9 target (`refs/heads/main` at `a908bbe`) - they are two
  different CAS operations at two different layers (schedule-register content vs. `main`'s tip),
  and the manifest's new `expected_old_note` field says so explicitly to prevent that conflation.

## Non-effect

This is a proposal field, not an execution. No `git update-ref` was run against any real ref. No
commit was created on `main` or `pg-p0-closure-lineage`. `main` remains `a908bbe` (independently
re-confirmed this session). `PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production not authorized.
