# GATE-P0-01 — PG-P0 Completion Gate Contract + Completion-Action Proposal (draft)

**Version:** 0.1
**Status:** Proposed; not accepted
**Owner:** Architecture Authority
**Maker:** Claude (BST-SA Motor worker agent; `claude-opus-4-8`) — sole maker
**Independent checker:** BST-Codex-Motor (must review the exact final SHA)
**Base:** accepted head `73912e4`

## Why this exists

Independent research established that PG-P0 completion is blocked not by the (now independently
accepted) transition verifier `VERIFY-P0-01`, but by two missing governed definitions: there is
**no PG-P0 completion/exit-criteria contract**, and the authority matrix has **no phase-completion
action**. Without the first, "PG-P0 complete" is undefined; without the second, no completion
mandate can be authorized or verified. This work item supplies both as **draft, ineffective**
proposals for human decision, following the supersession template of `PG-G0-GATE-001`.

## In scope (additive; draft/ineffective; base `73912e4`)

1. `docs/00-governance/PG-P0-GATE-CONTRACT-DRAFT.md` — a Draft, ineffective PG-P0 completion gate
   contract defining candidate completion criteria, fail-closed dispositions, the unresolved
   **scope-boundary decision** (skeleton-boundary vs maturity-boundary) surfaced for the
   Architecture Authority, current-effectiveness statement, supersession rule, and explicit
   non-authorization.
2. `docs/00-governance/AUTHORITY-MATRIX-COMPLETE-PHASE-PROPOSAL.md` — a Draft proposal for the
   missing `COMPLETE_PHASE` authority action and its identity binding. It does **not** edit the
   live authority matrix or identity register.

## Out of scope

Editing the live authority matrix or any register; selecting the scope boundary; signing,
consuming, or applying any mandate; completing PG-P0; opening PG-P1; authorizing research or
production. Those are human-authority acts recorded append-only.

## Acceptance criteria

- Both artifacts are clearly marked Draft/ineffective and assert no authority.
- Additive only; existing `docs/00-governance/**` files byte-unchanged; full `pnpm validate`
  passes at the exact candidate SHA; the document manifest is regenerated with the date-invariant
  tool.
- Independent BST-Codex-Motor exact-SHA review, then Human Architecture Authority disposition of
  the scope boundary and the completion-action proposal.

## Completion record

Pending. This proposed record does not accept itself, and neither draft it introduces completes
or authorizes anything.
