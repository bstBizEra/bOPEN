# BOOT-P0-01 — Repository initialization and protections

**Status:** External review pending
**Owner:** Engineering Authority
**Authorization:** `BOPEN-BOOT-001` (approved for bootstrap execution)
**Phase:** Bootstrap P0
**Dependencies:** See register

## Objective

Create repository structure, protected governance files and branch-control evidence.

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

`docs/evidence/EVD-BOOT-004-source-control-start.md`, `docs/evidence/EVD-BOOT-009-bootstrap-self-review.md`, and `docs/evidence/EVD-BOOT-011-bgitea-protected-review-activation.md`.

## Residual activation

The private bGitea repository, credential-free `origin`, fenced teams, runner, and initial protected branch settings are observed. Completion still requires the first Gitea pull-request workflow, required status context activation, Reviewer approval, and protected merge evidence.
