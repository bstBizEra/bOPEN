# BOOT-P0-04 — Control templates and registers

**Status:** Execution complete
**Owner:** BST Codex Motor
**Authorization:** `BOPEN-BOOT-001` (approved for bootstrap execution)
**Phase:** Bootstrap P0
**Dependencies:** See register

## Objective

Install ADR, decision, risk, evidence, exception and work-package controls.

## In scope

Repository/bootstrap controls directly required by this work package.

## Out of scope

Production platform business logic and unapproved architecture decisions.

## Deliverables

- governed files/configuration;
- validation or review evidence;
- updated document and traceability registers;
- residual risk record.

## Acceptance criteria

1. Deliverables exist and follow applicable `AGENTS.md` instructions.
2. `python tools/validate_repository.py` passes.
3. Documentation and evidence are linked.
4. No clean-room or production implementation gate is bypassed.

## Required evidence

`docs/evidence/EVD-BOOT-009-bootstrap-self-review.md`.
