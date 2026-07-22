# PG-G0 Signing Pass 1 — Operator Dispositions and Prepared Confirmations

**Version:** 0.1
**Status:** Draft (partially disposed; remaining items pending explicit operator confirmation)
**Prepared by:** Claude (BST-SA Motor worker agent)
**Operator:** `HUMAN-OPERATOR-001` (ounkhamvilay@gmail.com)
**Issued:** 2026-07-22
**Branch:** `operator/PG-G0-signing-pass-1` (base `d7d8699326345bb1a2f027e4027fb90d18649022`)

## Part A — Dispositions recorded in this commit (operator-selected 2026-07-22)

These two selections were made explicitly by the operator in the current session and are recorded with provenance, following the DEC-0012 option-1 user-instruction precedent:

| # | Disposition | Artifact | Effect |
|---|---|---|---|
| A1 | DEC-0012 manifest option: **immutable versioned snapshots** | Recorded **here** (see A1 record below) | Convention selected; DEC-0012 itself remains Proposed |
| A2 | Independent checker **BST-Codex-Motor**, due **2026-08-21**, for DEC-0004, DEC-0005, ADR-0005, ADR-0009 | `registers/TECHNOLOGY-DECISION-ASSIGNMENTS.json` (entries → `READY_FOR_REVIEW`), `docs/adr/ADR-0005.md`, `docs/adr/ADR-0009.md` (appended) | Review controls named; no decision taken |

Neither disposition approves a register, accepts a work package, passes a gate or grants implementation authority.

### A1 disposition record (held here; DEC-0012 is byte-frozen)

`docs/decisions/DEC-0012.md` is bound byte-exactly by `docs/manifests/GOV-P0-03-PACKAGE-MANIFEST.json` pending GOV-P0-03 review, so this disposition is recorded here instead of appended there, and must be appended to DEC-0012 in the same commit that accepts GOV-P0-03 (item B6).

**Source:** explicit operator selection recorded in the current Claude Code session (AskUserQuestion response, 2026-07-22).
**Disposition:** manifest option 2 — immutable versioned snapshots under `docs/manifests/` with an index; the root `docs/DOCUMENT-MANIFEST.json` is frozen as a historical bootstrap record with a freeze note to follow.
Reason: deterministic replacement conflicted with literal append-only wording and left the root manifest permanently stale. Benefit of the old phase: both options stayed open until an attributable human choice existed. Expected outcome: one auditable manifest convention without silent rewriting of prior evidence.
This selects a convention only; it approves nothing and passes no gate.

### Fixture note

`tests/governance/test_program_control_validation.py::test_self_approval_and_unassigned_technology_review_fail_closed` previously relied on the live register's empty checker/due fields when flipping an entry to `READY_FOR_REVIEW`. A2 filled those fields, so the fixture now blanks `checker_authorities`/`due_at` explicitly. The assertion is unchanged; the negative case is made explicit instead of inherited from register state.

## Part B — Prepared confirmations (NOT signed; each requires your explicit confirmation)

Confirm items individually or as numbered groups ("I confirm B1–B4"). On confirmation the prepared edit is applied, attributed to `HUMAN-OPERATOR-001` with the confirmation timestamp, and committed append-only.

### Founding acts (trust root; sign only after Codex ACCEPTs `d7d8699`)

- **B1 — Approve the authority identity register**: `AUTHORITY-IDENTITY-REGISTER-DRAFT.json` → status `approved`, version `0.1.0`, provenance filled, entry `HUMAN-OPERATOR-001` → `approved`; move to `registers/AUTHORITY-IDENTITY-REGISTER.json` (after Codex's fixture repair lands).
- **B2 — Adopt authority matrix v0.2 and approve BOPEN-GOV-001** (DEC-0013 option 1): proposal content replaces `registers/AUTHORITY-MATRIX.json` with status `approved` + provenance; matrix schema contract bumped in the same change.

### Register approvals (action `APPROVE_PROGRAM_REGISTERS` once B2 is effective)

- **B3 — Approve the seven program registers**: GOAL, AGENT, MODULE, SKILL, SCHEDULE, AUTHORITY-MATRIX (via B2), TECHNOLOGY-DECISION-ASSIGNMENTS — each status `approved`, non-draft version, provenance filled. Clears all 28 `program-g0-readiness` blockers.

### Acceptances and gate records

- **B4 — Accept work packages GOV-P0-01, GOV-P0-02, GOV-P0-03** (all independently checker-accepted) and, after its ACCEPT receipt, **GOV-P0-04**.
- **B5 — BOOT-B7 / DEC-0007 bootstrap exit acceptance.**
- **B6 — Activate the five root control ledgers** (Roadmap, Master_Standards, Progress_Log, Backlog, Recap_Today: Draft/Inactive → Active) as part of accepting GOV-P0-03.
- **B7 — Research G0 (BOPEN-RES-001 exit gate)**: sponsor and research lead = operator; security and license reviewers = operator (with BST-Codex-Motor and Claude as non-authoritative technical reviewers); isolated workspace = `research/` zones per clean-room policy. Recorded in `docs/resources/open-source-research/BOPEN-RES-001/02-execution/exit-gates.md`.

### Docket decisions (after Codex's docket v0.2 rebinding)

- **B8 — Sign PG-G0-DEC-001…005** (DEC-0007, GOV-P0-01, DEC-0010, BOPEN-GOAL-001 v0.2, EVD-GOV-001) as final authority with all concurrences, in the rebound docket.
- **B9 — PASS_PG_G0** once the readiness report returns `ready_for_human_gate_decision: true`, with a fresh independent conformance receipt.

## Boundary

This document prepares and records dispositions. It cannot approve its own Part B items; prepared values are ineffective until the operator's explicit confirmation is recorded. PG-G0 remains `NOT_READY`. Production kernel implementation remains separately gated regardless of PG-G0 passage.
