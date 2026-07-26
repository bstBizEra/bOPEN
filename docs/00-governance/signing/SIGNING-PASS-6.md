# PG-P0 Signing Pass 6 — Skeleton-Boundary Scope Decision + Work-Item Acceptances

**Version:** 0.1
**Status:** Signed operator record; integration/register-binding pending
**Operator:** `HUMAN-OPERATOR-001` (identity register `PG-REG-IDENTITY-001`, approved 2026-07-22)
**Signed at:** 2026-07-25T00:00:00+07:00
**Recorded by:** Claude (BST-SA Motor worker agent; `claude-opus-4-8`)
**Source:** explicit operator confirmation in the current Claude Code session, 2026-07-25 — "Adopt
skeleton-boundary and accept the reviewed candidates", confirmed against the exact SHA set below.
**Predecessor substrate:** accepted head `73912e483cc9f4b5bc107f84564b955c9a335ca4`

## Prerequisites satisfied

- Each accepted candidate below is a sole-Claude work item off the accepted head `73912e4` and
  carries an **independent BST-Codex-Motor `ACCEPT_EXACT_SHA`** receipt (technical evidence only).
- `PG-P0-GATE-001` (draft) surfaced the scope-boundary decision as unresolved; this record resolves it.
- `DEC-0014` records the completion mechanism (verifier + human apply) for adoption.

## Signed decision 1 — Scope boundary (Architecture Authority)

The operator **adopts skeleton-boundary completion** for program phase **PG-P0 ("Platform
Skeleton")**, as Architecture Authority under the approved solo-operator independence disclosure.
The PG-P0 completion criteria are satisfied by the accepted skeleton, draft contract shells and
test-harness scaffolding; the eight normative artifacts and BOPEN-RES-001 gates G3–G7 are
**PG-P1 entry conditions, not PG-P0 exit conditions**. This resolves the unresolved scope-boundary
decision recorded in `PG-P0-GATE-001`.

## Signed decision 2 — Work-item acceptances (Engineering / Architecture Authority)

The operator records `ACCEPT_WORK_ITEM` for each of the following at its exact reviewed SHA and
tree. Attestation: *"As HUMAN-OPERATOR-001, holding all five authority roles under the approved
solo-operator independence disclosure, I ACCEPT_WORK_ITEM each work item at the exact SHA below and
adopt DEC-0014. I have reviewed the independent evidence and take accountability for these
acceptances."*

| Work item | Accepted exact SHA | Tree | Meaning |
|---|---|---|---|
| VERIFY-P0-01 | `3946e94631419abe54521f073c4f4843e62c8217` | `e7eca010f94b01f27eb1c8b299240b59385ad63c` | Accept the transition verifier (the valid apply-proof path). |
| GATE-P0-01 | `f552da302b6df6f446c1d6351e144c9ac2acbeb2` | `b10f6c12e52be04383a436f1f71ebee3cee313d6` | Accept the work item. The `PG-P0-GATE-CONTRACT` **remains draft**; it becomes effective only via a separate approved successor incorporating the skeleton-boundary decision. |
| DEC-0014 | `8b8b79ed8a3da2b04ba07c21bbe7f33ab4596cff` | `37342aa98d1a5b44836436847748adc7b31662e9` | Adopt the completion mechanism: verifier + human apply. |
| SKEL-P0-01 (status reconciliation) | `11329bbaef7ef838d0d03145a762cead14245004` | `56bf494c3099ebfee2f8072af7de94ac52ea8eb3` | Accept the F-1 status-surface legibility reconciliation. |

## Explicitly held / not accepted

- **ENCODER-P0-02** `3c384c81fabbedb3cdb984ebe4949b1606bcfb82` (tree
  `38c9d994c5934e2a6f94e92dffbb2d26e230958c`) remains **HELD / ineligible** under the adopted
  verifier + human-apply mechanism (DEC-0014). It is not accepted; it may be reconsidered only if
  the Architecture Authority explicitly revises the mechanism to tool-performed authoritative apply.

## Boundary — what this record does NOT do

This is a signed acceptance decision only. It does **not**:

- merge any candidate to `main` (still `a908bbea1975ffc52a636765cd9f823dfeb978eb`), or integrate
  the accepted branches into a successor lineage (integration is a separate encoding step);
- mutate any signed register (`SCHEDULE-REGISTER.json` binding of the accepted work items into
  `PG-P0.work_item_refs` is a separate `APPROVE_PROGRAM_REGISTERS` act);
- complete the PG-P0 **phase** (`PG-P0` remains `ACTIVE`; completion is a separate signed schedule
  transition requiring the effective gate contract, the `COMPLETE_PHASE` authority action, a trust
  root, a signed Stage-1 mandate, and independent exact-SHA evidence);
- open `PG-P1` (`NOT_READY`), authorize BOPEN-RES-001 G3–G7 research, or authorize production
  implementation.

## Execution note

A Claude-authored successor encodes this record append-only and must pass the canonical validate
gate; an independent BST-Codex-Motor exact-SHA review must confirm the encoding binds to the exact
SHAs/trees above and introduces no signed-register mutation. The maker of the accepted candidates
does not self-certify this acceptance encoding.
