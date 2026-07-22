# EVD-GOV-007 — PG-G0 Authority Docket v0.2 Candidate

**Evidence ID:** EVD-GOV-007
**Timestamp:** 2026-07-23T00:05:19+07:00
**Agent ID:** BST-Codex-Motor
**Source:** Operator-authorized Batch 2 preparation following signed Operator Batch 1
**Work package:** GOV-P0-04 (human acceptance pending)
**Branch:** `codex/GOV-P0-04-docket-v02`
**Substrate commit:** `26bea090c0aca14f1337c4be1a146fd48bb1f626`
**Substrate tree:** `8789c5e70c2ce87298928d4d02add7ffe5867402`
**Evidence status:** MAKER_CANDIDATE; independent exact-SHA review pending

## Scope and atomic unit

This candidate moves the authority matrix/schema, BOPEN-GOV-001 and seven-register approval surfaces, GOV-P0-01/GOV-P0-04 acceptance surfaces, DEC-0007/BOOT-B7 surface, root-ledger activation contract/validator/tests and PG-G0-AUTH-001 v0.2 binding as one review unit. The immutable binding inventory proves the post-signing substrate without creating a self-referential successor hash.

The docket contains 13 `PENDING` prepared dispositions and preserves `PG-G0-DEC-001..005` as pending. Every disposition effect and every merge, release, deployment, runtime, production and PG-G0 authority flag is false.

## Fail-closed controls

- The bound matrix is `0.2.0-draft`; approval actor, time and evidence are null.
- Matrix entries must exactly match the proposal stored at the signed substrate.
- The inventory verifies each artifact path, SHA-256 and byte count using `git show` at the bound commit.
- Root activation is valid only when all five ledgers append the exact Signing Pass 2 B6 event with one timestamp. Partial, malformed or unbound activation fails.
- The readiness report remains `NOT_READY`; this evidence cannot change that status.

## Validation record

The final validation transcript is the command output produced immediately before candidate commit. Required checks are:

| Check | Required outcome |
|---|---|
| Focused docket tests | Pass |
| Focused root-control tests | Pass |
| Full governance unittest discovery | Pass |
| `pnpm validate` | Exit 0 |
| `git diff --check` | Exit 0 |
| Docket readiness report | `NOT_READY`, zero validation errors |

Candidate verification completed with these observed outcomes:

- `python -m unittest tests.governance.test_pg_g0_authority_docket tests.governance.test_root_control_surfaces`: the combined focused set passed after its deterministic report and package manifest were refreshed (49 docket cases and 15 root-control cases in the final suite composition).
- `pnpm test:governance`: 139/139 tests passed.
- `python tools/validate_root_control_surfaces.py --check`: exit 0.
- `python tools/validate_pg_g0_authority_docket.py --check`: exit 0; committed report current.
- `artifacts/validation/program-g0-authority-readiness.json`: `status: NOT_READY`, `validation_errors: []`.

- `pnpm validate`: exit 0 across repository, contract, program-control, identity-register, readiness-report, document-manifest, clean-room, secret and supply-chain checks.

The versioned document manifest is regenerated after this evidence append, then checked again before commit. The resulting candidate SHA is intentionally not self-asserted inside the commit; an independent reviewer must bind its receipt to the actual committed SHA and tree.

## Threat and rollback notes

Primary threats are mistaken draft activation, fabricated authority identity, partial root-ledger activation, stale/self-referential artifact binding and treating technical evidence as a gate decision. The status/provenance coupling, exact substrate reads, atomic root event and explicit non-authority flags mitigate these threats. The residual solo-operator concentration and lack of independent technical review remain disclosed.

Before any operator signature or merge, rollback is deletion of this isolated branch/worktree. After a candidate commit, an independent checker must review that exact SHA; corrections require a new SHA and receipt.

## Outcome

`PENDING_HUMAN_DECISIONS`. This maker evidence does not approve BOPEN-GOV-001, any register or matrix; does not accept GOV-P0-01 or GOV-P0-04; does not accept DEC-0007/BOOT-B7; does not activate root ledgers; and does not pass PG-G0 or authorize merge, release, deployment or production implementation.
