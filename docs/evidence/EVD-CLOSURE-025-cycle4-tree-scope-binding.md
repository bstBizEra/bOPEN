# EVD-CLOSURE-025 - Maker evidence: cycle-4 tree-scope binding

**Version:** 0.1
**Status:** Maker-authored remediation evidence (advisory; NOT an independent-checker receipt).
**Class:** PG-P0 closure repair, remediation cycle 4. Additive commit on
`claude/PG-P0-closure-repair-c8-v2`; no governed history rewritten.
**Maker:** Claude Opus 5 (BST-SA Motor worker agent), sole maker.
**Authorizes nothing.**

## The defect: an independent attack defeated cycle 3

Codex's cycle-3 assurance conflict resolved fail-closed to HOLD after an independent attack **added
an undeclared file under the execution root and verification still accepted**.

The cause was structural, not a coding slip. Cycle 3 verified the seven *declared* paths thoroughly -
key-set equality, 40-hex ids, runtime byte comparison - but it never enumerated *anything else*. A
path that appeared in neither the permitted-effects list nor the `successor_blobs` map was simply
never looked at. Per-path verification, however strict, cannot establish scope: **scope has to be
established from the complete change**.

## Correction

`closure_binding` gains a required `successor_tree` (40-hex git tree object id; the current proposal
carries `UNRESOLVED` and therefore rejects). Closure-execution verification now:

1. **requires a bounded `--repository`** git object source (`REPOSITORY_REQUIRED`);
2. **requires both trees to be real git tree objects** - `assert_tree_object` runs `cat-file -t`, so a
   blob id, a commit id, or an unknown 40-hex string is `TREE_OBJECT_INVALID`;
3. **enumerates the complete `predecessor_tree -> successor_tree` diff** and rejects **any** touched
   path outside the permitted seven (`TREE_SCOPE_VIOLATION`). `--no-renames -M0` is deliberate: a
   rename decomposes into a delete of the old path plus an add of the new one, so **both** sides are
   enumerated and a rename cannot hide behind a single similarity-matched record. `-z` removes path
   quoting ambiguity;
4. **requires each bound blob to exist in `successor_tree` as a regular-file blob** and match the
   bound id (`SUCCESSOR_TREE_ENTRY_INVALID`, `SUCCESSOR_TREE_BLOB_MISMATCH`);
5. **requires the execution root to BE the successor tree exactly** - no extra file, no missing file,
   no differing byte (`EXECUTION_ROOT_MISMATCH`).

### Two findings surfaced while building this

- **Untracked bytes are invisible to a tree diff.** A tree diff compares two committed trees; a file
  written into the working tree but never added appears in neither. So the tree diff alone would
  *not* have caught Codex's attack if the undeclared file were untracked. Control 5 exists for that
  reason: the execution root is compared against the successor tree in full, both directions, with
  every file's bytes re-hashed. `test_extra_untracked_file_in_execution_root_rejects` proves it.
- **A symlink is also a blob in git.** Checking `type == "blob"` therefore does *not* prevent a
  permitted path being type-changed into a symlink pointing anywhere. This was caught by
  `test_permitted_path_type_changed_to_symlink_rejects` failing to raise. Entry **mode** is now
  allow-listed to `100644`/`100755` (`REGULAR_FILE_MODES`).

## Dependency change, disclosed

Tree-scope verification needs a real git object database, so these helpers shell out to the `git`
binary via `subprocess`. Everything above that section remains pure standard library. This mirrors
`tools/validate_pg_g0_authority_docket.py`, which already reads git state the same way. git is
invoked **read-only**: `cat-file`, `ls-tree`, `diff`, `rev-parse` - nothing that writes an object,
moves a ref, or mutates state. Tests that need git skip cleanly when the binary is absent.

## Attack pack (18 tree-scope tests, all rejecting)

| Attack | Reason code |
|---|---|
| undeclared **added** path (the cycle-3 escape) | `TREE_SCOPE_VIOLATION` |
| undeclared **modified** path | `TREE_SCOPE_VIOLATION` |
| undeclared **deleted** path | `TREE_SCOPE_VIOLATION` |
| undeclared **renamed** path | `TREE_SCOPE_VIOLATION` |
| undeclared **mode change** (`--chmod=+x`) | `TREE_SCOPE_VIOLATION` |
| undeclared **type change** to symlink | `TREE_SCOPE_VIOLATION` |
| in-scope path type-changed to symlink | `SUCCESSOR_TREE_ENTRY_INVALID` |
| `successor_tree` unresolved | `SUCCESSOR_TREE_UNRESOLVED` |
| blob id supplied as `successor_tree` | `TREE_OBJECT_INVALID` |
| nonexistent tree id | `TREE_OBJECT_INVALID` |
| wrong `predecessor_tree` | `TREE_OBJECT_INVALID` |
| no `--repository` | `REPOSITORY_REQUIRED` |
| bound blob disagrees with tree | `SUCCESSOR_TREE_BLOB_MISMATCH` / `SUCCESSOR_BLOB_MISMATCH` |
| **extra untracked file** in execution root | `EXECUTION_ROOT_MISMATCH` |
| missing file in execution root | `EXECUTION_ROOT_MISMATCH` |
| dirty permitted file in execution root | `EXECUTION_ROOT_MISMATCH` / `SUCCESSOR_BLOB_MISMATCH` |

Where two codes are listed, either is a correct fail-closed rejection from an independent control;
the tests accept either rather than asserting a brittle ordering.

## Preserved from earlier cycles

Frozen signed artifacts byte-identical to base: `PG-P0-CLOSURE-MANIFEST.json`
(`7417cc6a7bdffc6cac0b3707be293fb01ec17434f848d831c2383f374cafb33a`), `PG-P0-CLOSURE-MANDATE.md`,
`PG-P0-CLOSURE-MANDATE.dsse.json`, `SCHEDULE-REGISTER.json`, `EVD-CLOSURE-014`. Blocked status
(`DRAFT_NOT_SIGNABLE` / `BLOCKED_PENDING_EXECUTION_BYTES`) unchanged. Revocation scaffold still scoped
to `PG-P0-CLOSURE-002` and `PENDING_HUMAN_ATTESTATION`. Backdated verification guidance still
withdrawn. No Graphify artifacts.

## Status effect

None. The shipped proposal remains correctly rejected in closure mode. `PG-P0 ACTIVE`;
`PG-P1 NOT_READY`; production not authorized. The C6-C8 execution bytes remain a human-only blocker
(`EVD-CLOSURE-023`), now additionally blocking `successor_tree`.
