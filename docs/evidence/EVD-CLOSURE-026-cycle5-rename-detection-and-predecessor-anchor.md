# EVD-CLOSURE-026 - Maker evidence: cycle-5 rename-detection and predecessor-anchor defects

**Version:** 0.1
**Status:** Maker-authored remediation evidence (advisory; NOT an independent-checker receipt).
**Class:** PG-P0 closure repair, remediation cycle 5. Additive commit on
`claude/PG-P0-closure-repair-c8-v2`; no governed history rewritten.
**Maker:** Claude Opus 5 (BST-SA Motor worker agent), sole maker.
**Authorizes nothing.**

## Predecessor candidate: REJECTED

Candidate `fc4960fcc99df3cf35aa3140e9a01bf215abfa91` received `REJECT_EXACT_SHA`. Two exact defects
were named; both were reproduced before being fixed, and both were real.

## Defect 1 - rename detection was never actually disabled

`tree_diff_paths` passed `--no-renames` and then `-M0`. git applies **last-option-wins**, so `-M0`
(rename detection with a zero similarity threshold) silently re-enabled what `--no-renames` had
turned off. Reproduced directly:

```
$ git diff --raw -z --no-renames -M0 <T1> <T2>     # cycle-4 order
:100644 100644 d95f3ad d95f3ad R100
a.txt
evil.txt

$ git diff --raw -z -M0 --no-renames <T1> <T2>     # corrected order
:100644 000000 d95f3ad 0000000 D
a.txt
:000000 100644 0000000 d95f3ad A
evil.txt
```

The consequence was worse than a cosmetic difference. A rename record carries **three**
NUL-separated fields (metadata, source, destination); every other status carries two. The parser
assumed two, so it recorded the **source** path and then advanced past the **destination**, which
- not starting with `:` - was skipped by the resynchronisation branch. Renaming a **permitted**
path (`docs/CHANGELOG.md`) to an **undeclared** destination (`evil.txt`) therefore enumerated only
the permitted source, read as an in-scope change, and passed the scope test entirely.

**Correction:** `--no-renames` is now the final rename-related flag, and the parser handles `R`/`C`
records explicitly by consuming and recording **both** paths. The flag order is defence in depth
with the parser, not a substitute for it: if a future git emits a rename despite the flag, scope is
still enforced correctly.

**Regression tests (3):**

- `test_permitted_source_renamed_to_undeclared_destination_rejects` - the exact named case. Asserts
  `evil.txt` **is enumerated**, asserts `validate_successor_tree` rejects specifically
  `TREE_SCOPE_VIOLATION` with `evil.txt` named in the message, and asserts full enforcement rejects.
- `test_rename_detection_is_actually_disabled` - pins the flag order: the rename must surface as a
  separate `D` on the source and `A` on the destination.
- `test_rename_between_two_permitted_paths_still_enumerates_both` - both sides enumerated even when
  both are in scope.

Independent probe on the corrected code: `{'docs/CHANGELOG.md': 'D', 'evil.txt': 'A'}` -
destination enumerated.

## Defect 2 - predecessor_commit and predecessor_tree floated free of each other

Both fields are inside the signed payload, but nothing ever proved them **mutually consistent**.
Cycle 4 checked that `predecessor_tree` was *a* real tree and never resolved `predecessor_commit` at
all. A mandate could therefore name the genuine signed base commit while pairing it with some
*other real tree*, and the diff, the scope test and every blob comparison would run against that
substituted baseline and pass.

**Correction:** `assert_predecessor_commit_binds_tree()` runs **before any tree diff**. It requires
`predecessor_commit` to be a real **commit** object (`PREDECESSOR_COMMIT_INVALID`) and requires
`rev-parse <predecessor_commit>^{tree}` to equal the signed `predecessor_tree` exactly
(`PREDECESSOR_TREE_MISMATCH`).

**Regression tests (4):**

- `test_substituted_real_but_wrong_predecessor_tree_rejects` - the named case: a **genuine, existing**
  tree object (the successor's `docs/` subtree) substituted for `predecessor_tree` while
  `predecessor_commit` names the real base. Not a nonexistent id.
- `test_predecessor_commit_and_tree_consistent_accepts` - the consistent pair still verifies.
- `test_tree_oid_supplied_as_predecessor_commit_rejects` - a tree id where a commit is required.
- `test_nonexistent_predecessor_commit_rejects` - unknown id.

Independent probe: consistent pair `ACCEPTED`; substituted real tree `REJECTED
PREDECESSOR_TREE_MISMATCH`; tree id as commit `REJECTED PREDECESSOR_COMMIT_INVALID`.

## Fixture consistency (disclosed)

Adding the predecessor anchor invalidated three test fixtures that had bound placeholder commits
(`"0"*40`, and a base-repo commit id that does not exist inside a throwaway temp repository). Rather
than weaken the check, `_make_git_execution_tree` now creates a real empty base commit whose tree
**is** the empty tree, and the fixtures bind that genuinely consistent pair. Two further fixture
bugs surfaced and were fixed in the tests, not the verifier: a rename-away left a bound path absent
from the successor tree (now tolerated in the fixture, since the scope layer is what those cases
assert), and `Path.rename()` refuses an existing destination on Windows (now `Path.replace()`).

## Preserved from earlier cycles

All cycle-4 controls retained unchanged: complete-tree-diff scope, execution-root-equals-successor-tree,
regular-file mode allow-list, real-tree-object checks, bounded `--repository`, successor-blob
binding. Frozen signed artifacts byte-identical to base (`PG-P0-CLOSURE-MANIFEST.json`
`7417cc6a7bdffc6cac0b3707be293fb01ec17434f848d831c2383f374cafb33a`, `PG-P0-CLOSURE-MANDATE.md`,
`PG-P0-CLOSURE-MANDATE.dsse.json`, `SCHEDULE-REGISTER.json`, `EVD-CLOSURE-014`). The unsigned
proposal remains `DRAFT_NOT_SIGNABLE` / `BLOCKED_PENDING_EXECUTION_BYTES` and still rejects in
closure mode. Revocation scaffold still scoped to `PG-P0-CLOSURE-002` and
`PENDING_HUMAN_ATTESTATION`. Backdated verification guidance still withdrawn. No Graphify artifacts.

## Status effect

None. `PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production not authorized. The C6-C8 execution bytes remain
a human-only blocker (`EVD-CLOSURE-023`), still blocking `successor_tree` and six blob ids.
