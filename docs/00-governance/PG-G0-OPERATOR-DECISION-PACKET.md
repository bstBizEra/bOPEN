# PG-G0 Operator Decision Packet

**Version:** 0.1
**Status:** Draft (advisory; grants nothing by itself)
**Work package:** GOV-P0-04 (Proposed; not accepted)
**Prepared by:** Claude (BST-SA Motor worker agent)
**Issued:** 2026-07-22
**Operator identity (proposed):** `HUM-OPR-001` — ounkhamvilay@gmail.com, sole holder of Product, Architecture, Security, Data and Engineering Authorities (see `registers/AUTHORITY-IDENTITY-REGISTER.json`)

## Purpose

Every remaining PG-G0 blocker requires an attributable human decision. This packet lists all of them once, in dependency order, with the exact bound artifacts. Signing a step means: record your identity, an ISO-8601 timestamp and a decision reference in the named artifact, in an append-only commit.

The five docket decisions (Step 6) bind subjects at commit `c893062c197e74c15214e5ce1c425b9e9ed8002f` (tree `f336976981c9b7e95c96ec8289589e53c1ac506c`).

## Step 1 — Approve the authority identity register

**File:** `docs/00-governance/AUTHORITY-IDENTITY-REGISTER-DRAFT.json`
**Action:** set register `status: "approved"`, fill `approved_by/approved_at/approval_ref`, set entry `HUM-OPR-001` `status: "approved"`, then move the file to the validator-bound path `docs/00-governance/registers/AUTHORITY-IDENTITY-REGISTER.json` (the docket test fixtures must be repaired first — see handoff notes). Confirm the `independence_disclosure` (all five roles collapse to you).
**Clears:** "attributable … human authority identities are absent"; "approved authority identity registry … is absent".

## Step 2 — Adopt authority matrix v0.2 and approve the governance baseline

**Files:** `docs/00-governance/AUTHORITY-MATRIX-0.2.0-PROPOSAL.json` → `docs/00-governance/registers/AUTHORITY-MATRIX.json`; `docs/00-governance/BOPEN-GOV-001-DRAFT.md`; `docs/decisions/DEC-0013.md`
**Action:** dispose DEC-0013 (recommended: Option 1); adopt matrix v0.2 with `status: "approved"` and approval provenance; approve BOPEN-GOV-001 (new action `APPROVE_GOVERNANCE_BASELINE`); bump `contracts/governance/authority-matrix.schema.json` in the same change.
**Clears:** "authority matrix … draft and ineffective"; the three "matrix has no action for …" blockers; "prose and machine … conflict on ACCEPT_WORK_ITEM"; "authority source is not effective".

## Step 3 — Approve the seven program registers

**Files:** `docs/00-governance/registers/` — GOAL, AGENT, MODULE, SKILL, SCHEDULE, AUTHORITY-MATRIX (Step 2), TECHNOLOGY-DECISION-ASSIGNMENTS
**Action:** for each register set `status: "approved"` and fill `approved_by/approved_at/approval_ref` (action `APPROVE_PROGRAM_REGISTERS`).
**Clears:** all 28 blockers in `artifacts/validation/program-g0-readiness.md`.

## Step 4 — Assign named checkers and due dates

**Files:** `docs/00-governance/registers/TECHNOLOGY-DECISION-ASSIGNMENTS.json` (TECH-001/DEC-0004, TECH-002/DEC-0005 and the ADR-0005/ADR-0009 assignments), `docs/adr/ADR-0005.md`, `docs/adr/ADR-0009.md`
**Action:** fill `checker_authorities` and `due_at` for each assignment (clearing each entry's recorded blocker) and append the named checker and due date to the two ADRs.
**Clears:** "DEC-0004, DEC-0005, ADR-0005 and ADR-0009 lack named checkers and due dates".

## Step 5 — Dispose open decisions

- **DEC-0012** (manifest handling): root-path option 1 is already user-disposed; the manifest option is still open. Recommended: immutable versioned snapshots (`docs/manifests/`), matching current GOV-P0-02/03 practice; the stale root `docs/DOCUMENT-MANIFEST.json` then needs a final freeze note. See disclosed observation in `docs/evidence/EVD-GOV-004-gov-p0-03-independent-verification.md`.
- **BOOT-B7 / DEC-0007**: bootstrap exit acceptance.
- **Work packages GOV-P0-01…04**: record `Accepted by/at` (action `ACCEPT_WORK_ITEM`, Owning Artifact Authority concurrence per matrix v0.2).
- **GOV-P0-03 root surfaces**: acceptance decides whether the five root ledgers move Draft/Inactive → Active.

## Step 6 — Sign the five docket decisions

**File:** revised authority docket (docket v0.2 rebinding required — Codex follow-up; the current `PG-G0-AUTH-001.json` binds pre-identity-register state).
For each decision fill `final_authority_actor`, concurrence actors, dispositions and timestamps:

| Decision | Action | Subject | Final authority | Concurrence |
|---|---|---|---|---|
| PG-G0-DEC-001 | APPROVE_ARCHITECTURE | DEC-0007 | Architecture | Security, Data |
| PG-G0-DEC-002 | ACCEPT_WORK_ITEM | GOV-P0-01 | Engineering | Product (owning artifact authority) |
| PG-G0-DEC-003 | APPROVE_ARCHITECTURE | DEC-0010 | Architecture | Product, Security, Data |
| PG-G0-DEC-004 | APPROVE_GOAL | BOPEN-GOAL-001 v0.2 | Product | Architecture, Security, Data |
| PG-G0-DEC-005 | ACCEPT_EVIDENCE | EVD-GOV-001 | Engineering | — |

## Step 7 — Pass PG-G0

**Action:** with Steps 1–6 committed, regenerate the readiness reports; when `ready_for_human_gate_decision: true`, record the `PASS_PG_G0` decision (Engineering Authority final, all four concurrences) with a fresh independent conformance receipt.
**Note:** PG-G0 passage still does **not** authorize production kernel implementation; that remains separately gated (BOPEN-RES-001 G7 and later program gates).

## Handoff notes

- Codex follow-up needed: docket v0.2 rebinding governing artifacts (incl. the approved identity register) to the post-approval commit, plus validator/blocker-list updates as steps land.
- Codex follow-up needed: `tests/governance/test_pg_g0_authority_docket.py` `committed_file` mock prefers `ROOT / relative` over the temp fixture root; once a real register exists at `docs/00-governance/registers/AUTHORITY-IDENTITY-REGISTER.json`, five negative tests fail spuriously. The mock should resolve the temp root first.
- Claude deliverables in GOV-P0-04 are drafts; nothing here is effective until you sign it.
