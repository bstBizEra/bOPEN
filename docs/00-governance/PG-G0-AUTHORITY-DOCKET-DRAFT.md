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
