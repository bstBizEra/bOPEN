# PG-G0-AUTH-001 — PG-G0 Authority Docket

**Version:** 0.1.0-draft
**Status:** Draft
**Owner:** Engineering Authority
**Issued:** 2026-07-21
**Work package:** GOV-P0-02 (Proposed; not accepted)
**Decision reference:** DEC-0012 (Proposed)
**Machine contract:** `contracts/governance/pg-g0-authority-docket.schema.json`
**Machine instance:** `docs/00-governance/authority-dockets/PG-G0-AUTH-001.json`

## Purpose

Route attributable human decisions for PG-G0 while proving that technical validation, CI success, PR approval and merge are not gate authority.

## Current decision requests

| ID | Live action | Subject | Final authority | Required concurrence | Current disposition |
|---|---|---|---|---|---|
| PG-G0-DEC-001 | APPROVE_ARCHITECTURE | DEC-0007 / BOOT-B7 | Architecture Authority | Security, Data | Pending |
| PG-G0-DEC-002 | ACCEPT_WORK_ITEM | GOV-P0-01 | Engineering Authority | Machine matrix says none; prose conflict unresolved | Pending |
| PG-G0-DEC-003 | APPROVE_ARCHITECTURE | DEC-0010 lifecycle decision | Architecture Authority | Security, Data | Pending |
| PG-G0-DEC-004 | APPROVE_GOAL | BOPEN-GOAL-001 v0.2 | Product Authority | Architecture, Security, Data | Pending |
| PG-G0-DEC-005 | ACCEPT_EVIDENCE | EVD-GOV-001 | Engineering Authority | None in draft matrix | Pending |

## Missing authority actions

The live machine authority matrix contains no action for approving BOPEN-GOV-001, approving the seven program registers, or passing PG-G0. This draft does not invent those actions. An approved successor authority matrix and gate contract must define them before PG-G0 can become ready for a human gate decision.

## Human identity rule

Final decision and concurrence actors must be humans bound to stable identity and authority-role evidence. Agents may prepare and independently check, but an agent, role label, CI result, PR review request or unsigned JSON value cannot exercise human authority.

## Exact-path conflict

`Roadmap.md`, `Master_Standards.md`, `Progress_Log.md`, `Backlog.md` and `Recap_Today.md` do not exist at the bound base. `docs/01-product/roadmap.md` is not treated as an equivalent without DEC-0012 disposition.

## Decision sequence

1. Human Engineering Authority accepts or rejects GOV-P0-02 for draft work only.
2. Product, Architecture and Engineering authorities dispose DEC-0012, with Security/Data concurrence where affected.
3. Architecture Authority disposes DEC-0007/BOOT-B7.
4. Engineering Authority disposes GOV-P0-01.
5. Architecture, Security and Data authorities supply required DEC-0010/BOPEN-GOAL-001 concurrences.
6. Product Authority disposes BOPEN-GOAL-001.
7. An approved successor authority model defines governance, register and PG-G0 actions.
8. Technology decisions receive real checkers and due dates.
9. Independent evidence is accepted by the accountable human authority.
10. A separately named human gate authority records the PG-G0 decision.

## Current result

`NOT_READY`. PG-G0, merge, release, runtime activation, module certification, skill promotion and production implementation are all false and unauthorized.

## Extend-only change note

Reason: current draft controls cannot authenticate human authority or express all PG-G0 actions. Benefit of the old phase: the draft authority matrix preserves the initial separation model. Expected outcome: an attributable human decision can approve a successor without rewriting this historical proposal.

## Append-only v0.2 preparation note — 2026-07-23

Operator Batch 1 is frozen at commit `26bea090c0aca14f1337c4be1a146fd48bb1f626`, tree `8789c5e70c2ce87298928d4d02add7ffe5867402`. The machine docket has been prepared as v0.2 with state `PENDING_HUMAN_DECISIONS`; its binding inventory records the immutable post-signing substrate rather than attempting to hash its own successor commit.

The v0.2 candidate adopts the contents of `AUTHORITY-MATRIX-0.2.0-PROPOSAL.json` into the bound matrix as a draft successor and exposes 13 Batch 2 disposition surfaces: BOPEN-GOV-001, authority matrix v0.2, DEC-0013, the remaining six program registers, GOV-P0-01, GOV-P0-04, DEC-0007/BOOT-B7 and the atomic five-ledger activation event. All 13 dispositions are pending, unsigned and ineffective. The original five `PG-G0-DEC-001..005` requests remain pending.

The root-control schema and validator now recognize only a complete, identically timestamped, Signing Pass 2 B6 activation across all five root ledgers. Zero events is valid Draft/Inactive state; one through four events, malformed events, mismatched timestamps or missing signing evidence fail closed. No activation event is present in this candidate.

Current result remains `NOT_READY`. Independent exact-SHA review, operator dispositions, root-ledger activation, B8 decision receipts and B9 PG-G0 disposition remain future controls. Merge, release, deployment and production implementation are unauthorized.
