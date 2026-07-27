# EVD-CLOSURE-027 - Maker evidence: cycle-6 expected_old anchor

**Version:** 0.1
**Status:** Maker-authored remediation evidence (advisory; NOT an independent-checker receipt).
**Class:** PG-P0 closure repair, remediation cycle 6. Additive commit on
`claude/PG-P0-closure-repair-c8-v2`; no governed history rewritten.
**Maker:** Claude Opus 5 (BST-SA Motor worker agent), sole maker.
**Authorizes nothing.**

## Predecessor candidate

`d4cd5d594d9b9e25fed8634ef0def5dea18c354a` (cycle 5) returned one blocker on Codex's fail-closed
review. Reproduced before fixing; it was real.

## The defect

`closure_binding` carries two commit-shaped fields that mean different things:

- `predecessor_commit` - the baseline the entire verification diffs **from**;
- `expected_old` - the value the human's C9 compare-and-swap will publish **on top of**.

Nothing ever compared them. Both are 40-hex-validated, so `expected_old = "f" * 40` is
structurally well-formed and passed every check while `predecessor_commit` and `predecessor_tree`
remained entirely genuine. Reproduced against cycle-5 code:

```
expected_old = ffffffffffffffffffffffffffffffffffffffff   predecessor_commit = 896803e47406...
RESULT -> ACCEPTED   <-- expected_old never compared
```

The consequence is that **the transition proven is not the transition applied**. Verification would
attest a change anchored at `predecessor_commit`, while the compare-and-swap would succeed only
against a different ref state entirely - or, with an unresolvable value, be crafted to fail or to
target something the proof never examined. Every downstream control in cycles 3-5 (tree scope,
execution-root equality, blob binding) is anchored to `predecessor_commit` and therefore inherits
this divergence silently.

## Correction

`validate_closure_binding()` now requires `expected_old == predecessor_commit`, raising the new
stable reason code **`EXPECTED_OLD_MISMATCH`**.

Placement is deliberate and is itself part of the fix. The check lives in the **structural**
validator, not in `validate_successor_tree`, so it:

- runs in **both** closure mode and reporting mode;
- runs **before any repository, tree or diff work**, satisfying the "before tree/diff verification"
  requirement by construction rather than by ordering convention;
- **cannot be skipped** by a caller that omits `--repository` or `--execution-root`. This is proven
  directly by `test_expected_old_enforced_before_any_repository_work`, which calls
  `validate_closure_binding()` alone, with no repository at all, and asserts the rejection.

It needs no I/O: both fields are inside the signed payload, so their mutual consistency is a pure
property of the binding.

## Tests (5)

| Case | Expectation |
|---|---|
| `expected_old == predecessor_commit` | **ACCEPTED** (positive equality test) |
| `expected_old = "f" * 40`, commit/tree genuine | `EXPECTED_OLD_MISMATCH` (the reported attack) |
| `expected_old` names a **different real commit** | `EXPECTED_OLD_MISMATCH` |
| `predecessor_commit` moved forward, `expected_old` keeps the true baseline | `EXPECTED_OLD_MISMATCH` |
| structural check with **no repository supplied** | `EXPECTED_OLD_MISMATCH` |

The two-real-commit cases are the substantive ones: every field resolves, every object exists, and
only the mutual-consistency requirement separates them. Independent probe on corrected code:

```
expected_old == predecessor_commit (positive)  -> ACCEPTED
expected_old all-f (the reported attack)       -> REJECTED EXPECTED_OLD_MISMATCH
expected_old = different REAL commit           -> REJECTED EXPECTED_OLD_MISMATCH
predecessor_commit moved forward, old kept     -> REJECTED EXPECTED_OLD_MISMATCH
```

## Fixture consistency (disclosed)

The new check invalidated three fixtures that had bound `expected_old` to a placeholder (`"0" * 40`,
and a base-repo commit id absent from throwaway repositories); they now bind the fixture's real base
commit, matching `predecessor_commit`. Two cycle-5 tests that deliberately override
`predecessor_commit` (`test_tree_oid_supplied_as_predecessor_commit_rejects`,
`test_nonexistent_predecessor_commit_rejects`) now also override `expected_old` to match, so they
still reach and assert their originally intended reason codes rather than being short-circuited by
the earlier check. No control was weakened to accommodate any fixture.

## Preserved

All controls from cycles 3-5 retained unchanged: complete-tree-diff scope with rename decomposition,
execution-root-equals-successor-tree, regular-file mode allow-list, real-tree-object checks,
predecessor-commit-binds-tree anchor, bounded `--repository`, successor-blob binding, fail-closed
absent/malformed/mismatched handling. Frozen signed artifacts byte-identical to base
(`PG-P0-CLOSURE-MANIFEST.json` `7417cc6a7bdffc6cac0b3707be293fb01ec17434f848d831c2383f374cafb33a`,
`PG-P0-CLOSURE-MANDATE.md`, `PG-P0-CLOSURE-MANDATE.dsse.json`, `SCHEDULE-REGISTER.json`,
`EVD-CLOSURE-014`). The unsigned proposal remains `DRAFT_NOT_SIGNABLE` /
`BLOCKED_PENDING_EXECUTION_BYTES` and still rejects in closure mode; its `expected_old` and
`predecessor_commit` are both `042dda535be70927b73cd1a131b2545349729643` and therefore already
satisfy the new check. Revocation scaffold still scoped to `PG-P0-CLOSURE-002` and
`PENDING_HUMAN_ATTESTATION`. Backdated verification guidance still withdrawn. No Graphify artifacts.

## Status effect

None. `PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production not authorized. The C6-C8 execution bytes remain
a human-only blocker (`EVD-CLOSURE-023`), still blocking `successor_tree` and six blob ids.
