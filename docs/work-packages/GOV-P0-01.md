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
**Independent checker:** Codex kernel-readiness checker; accepted maker SHA `f27b2fe60f12bd9bcc26794c740a1e83ecdc0b9e`
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

Maker repair and independent exact-SHA technical verification are complete. Human Engineering Authority acceptance remains pending. This proposed record does not accept itself.

## Evidence-completion note — 2026-07-21

Post-candidate audit found that the deterministic readiness report was locally generated but ignored by Git. The bounded maker repair requires that report to be tracked and reproducible from a fresh archive, adds a fail-closed equality check to both CI surfaces, and preserves `PG-G0 NOT_READY`. Exact-SHA checker review and human acceptance remain pending.

## Append-only completion clarification — 2026-07-21

Reason: the preceding evidence-completion note retained its pre-review pending sentence after exact-SHA technical review completed. Benefit of the old phase: it accurately preserved the state before review. Expected outcome: distinguish completed technical verification from still-pending human acceptance without rewriting the historical entry.

The exact-SHA checker accepted maker SHA `f27b2fe60f12bd9bcc26794c740a1e83ecdc0b9e` and receipt SHA `c59c87472c5d515e0e586e3a6fcbdb19943705d9`. This clarification does not change `Status: Proposed` or `Accepted by/at: Pending`; GOV-P0-01, DEC-0010, BOPEN-GOAL-001, BOPEN-GOV-001 and `PG-G0` remain ineffective pending attributable human authority decisions.

The PG-G0 authority-docket checker subsequently accepted append-only normalization maker SHA `034ead332450da61a1518ffa76645b59e94704dd`. This technical receipt removes only the obsolete evidence-marker blocker; it does not accept this work package or change any human authority disposition.
