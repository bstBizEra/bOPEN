# PG-P0-CLOSURE-002 - resolved payload and execution bytes

**Status:** UNSIGNED candidate. Carries no signature and authorizes nothing.
**Prepared:** 2026-07-29 by Claude (BST-SA Motor worker, maker).
**Supersedes:** the two `UNRESOLVED` fields in `PG-P0-CLOSURE-MANDATE-V2-PROPOSAL.payload.json`.

## What this resolves

The V2 proposal was correctly blocked on `successor_tree` and `successor_blobs`
(`successor_blobs_status: BLOCKED_PENDING_EXECUTION_BYTES`): a binding cannot pin a tree
that has not been built. This reconstruction builds the execution bytes against the V2
manifest and fills both fields.

    successor_tree  70fb3929d6c3aa879d1c1dff7370c784df7eaec7

| permitted path | successor blob |
|---|---|
| `docs/00-governance/registers/SCHEDULE-REGISTER.json` | `bae4f0430523d7d0b94208c8adf003a644ec5979` |
| `docs/CHANGELOG.md` | `eac28f229c759113548c0e718e67a7801cec9627` |
| `docs/DOCUMENT-MANIFEST.json` | `47be3cb610eb768a9f637d31ce2e467539a365c8` |
| `docs/manifests/GOV-P0-02-DOCUMENT-MANIFEST.json` | `e15aaf0bd61b7f5fdc121826dce580d553bf5187` |
| `tests/governance/test_program_control_validation.py` | `56c12405d32747d69294b3bdb816eaeef743cb13` |
| `tools/validate_pg_g0_authority_docket.py` | `40b05311918b83d594441a336c99a368a2b97428` |

The seventh permitted path, `PG-P0-CLOSURE-MANDATE.md`, was created at C5 and is unchanged.

## Verified

- `validate_closure_binding` and `validate_mandate` both PASS against the cycle-8 verifier
  (`fdf0434`). They FAIL against the pre-cycle-2 verifier on the closure lineage, which does
  not know the `closure_binding` field at all - see Prerequisite below.
- The mutated register recomputes under RFC 8785 to
  `1f8d183e4bbcd2acc82148b659d5e0b74e2ea48bfc6dc4c0ceccc69e2b3ff863`, the authorized
  successor digest, exactly.
- Both document manifests are current (`--check` clean).
- Exactly six paths change; no prohibited effect is touched.

## Why three blobs differ from the earlier PG-P0-CLOSURE-001 execution

The three SOURCE effects are byte-identical to the earlier execution
(`bae4f043`, `56c12405`, `40b05311`) - they contain no reference to a manifest digest.

The three DERIVED effects differ. `docs/CHANGELOG.md` names the governing manifest, and the
V2 manifest digest is `2fd049b2...` where V1 was `7417cc6a...`. Both document manifests hash
`CHANGELOG.md`, so that one line propagates into all three blobs and into the tree.

**Consequence for the signer:** because `successor_tree` binds the whole tree, signing this
payload cryptographically fixes the exact wording of the CHANGELOG entry, which was authored
by an agent. Read `PG-P0-CLOSURE-002-execution.patch` before signing.

## Prerequisite - NOT met at time of writing

The closure lineage carried a verifier with zero occurrences of `closure_binding`. A mandate
bearing this field is rejected there as an unknown mandate field. **Cycle 8 (or another
binding-capable verifier) must be on the lineage before this payload is signed**, otherwise
the signed artifact cannot be validated by the governed tooling.

## Reproduction

1. Worktree at `042dda535be70927b73cd1a131b2545349729643`.
2. `git checkout 757f5a1 -- ` the three source paths (they are V2-independent).
3. Append the CHANGELOG entry naming manifest `2fd049b2...`.
4. Regenerate `GOV-P0-02-DOCUMENT-MANIFEST.json`, then `DOCUMENT-MANIFEST.json`, in that order.
5. `git add -A && git write-tree` -> `70fb3929...`.

`PG-P0-CLOSURE-002-execution.patch` (sha256
`e94ce4a41630793128ddacd47ab74a36669ff0dda600b7085e2910a1e12ffa42`) is that diff.

## Signing

The DSSE pre-authentication encoding is deterministic from the payload: payload type
`application/vnd.bopen.phase-completion-mandate+json`, RFC 8785 canonical payload, PAE per
DSSEv1. For the payload as committed here the PAE is 2409 bytes with sha256
`615431eb75d65808d85266c4d6066b816e289cb9bb3a0e389b9e00259a7b4b21`.

Signing is HUMAN-OPERATOR-001's act with the offline key. No agent may hold, receive, or
generate that key. This document and the payload beside it are unsigned inputs only.
