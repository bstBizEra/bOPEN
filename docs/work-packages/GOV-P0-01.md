# GOV-P0-01 — Program Goal v0.2 Controlled Baseline and G0 Measurement Contract

**Status:** Proposed
**Owner:** Engineering Authority
**Authorization source:** User direction to proceed; BOPEN-BOOT-001 documentation-drafting authority
**Accepted by/at:** Pending
**Lifecycle:** Program governance draft; no gate passage
**Expires:** 2026-08-21
**Dependencies:** BOOT-P0-12/DEC-0007 authority review; Product/Architecture review of DEC-0010
**Governing artifacts:** BOPEN-BOOT-001; supplied Program Goal v0.2
**Maker:** Codex root plus bounded register/catalog makers
**Independent checker:** Pending exact-SHA assignment
**Worktree:** `C:\laragon\www\bopen-worktrees\gov-p0-01-program-goal-v02`
**Branch:** `codex/GOV-P0-01-program-goal-v02`
**Base commit:** `bc623b0d851f44713d9ba7cb7650f08bb4f072c5`

## Objective

Transform the supplied Program Goal v0.2 into a complete, reviewable, fail-closed draft control baseline without approving the goal or authorizing runtime implementation.

## In scope

- controlled goal and source-complete machine-readable requirement inventory;
- lifecycle namespace/crosswalk and proposed adoption decision;
- draft program authority baseline;
- draft goal, agent, module, skill, schedule, authority and technology registers;
- work-item, evidence and handoff template extensions;
- deterministic program-G0 readiness report and negative tests;
- evidence, manifest, status and traceability updates.

## Out of scope

Goal or gate approval; BOOT-B7 decision; research gate changes; technology selection; production code, migrations or infrastructure activation; active agent/skill registration; module certification; release or merge authorization.

## Allowed paths

`docs/`, `contracts/governance/`, `tools/report_program_g0.py`, `tools/validate_program_controls.py`, `tests/governance/test_program_*`, `artifacts/validation/program-g0-readiness.md`, and package/CI command surfaces only if required for validation.

## Prohibited paths

`apps/`, `services/`, `packages/`, `infrastructure/`, `research/upstream/`, research execution evidence, migrations and runtime secrets.

## Deliverables

1. BOPEN-GOAL-001 and BOPEN-GOV-001 drafts.
2. DEC-0010 and lifecycle crosswalk.
3. Complete requirement catalog and seven fail-closed registers.
4. Program-control validator and PG-G0 report.
5. Template extensions, tests, EVD-GOV-001 and generated artifacts.

## Acceptance criteria

- every supplied goal clause has a stable inventory ID and preserved target;
- ambiguous bare lifecycle status IDs are rejected;
- incomplete, empty, expired or self-reviewed records fail closed;
- all eight module-certification prerequisites are required;
- a zero/unknown denominator cannot produce a successful rate;
- current report returns `NOT_READY` and production authorization `false`;
- a different checker accepts an exact final SHA;
- existing repository, contract, security, clean-room and supply-chain checks remain green.

## Required checks and evidence

`pnpm validate`; full Python tests; program-control validator; deterministic report; document manifest; `git diff --check`; EVD-GOV-001 with source hash, base/head SHA, commands, results and checker verdict.

## Risks and rollback

Risk: lifecycle aliases are mistaken for approved renames or draft registers for active controls. Control: explicit Draft/Proposed statuses and fail-closed report. Rollback: revert the isolated candidate commit; no runtime state or data is touched.

## Completion record

Pending maker completion, exact-SHA checker verdict and human acceptance. This proposed record does not accept itself.
