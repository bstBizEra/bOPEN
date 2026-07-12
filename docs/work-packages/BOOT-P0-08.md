# BOOT-P0-08 — Ownership and review governance

**Status:** External activation pending
**Owner:** Engineering Authority
**Authorization:** `BOPEN-BOOT-001` (approved for bootstrap execution)
**Phase:** Bootstrap P0
**Dependencies:** See register

## Objective

Activate CODEOWNERS and required reviews.

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

`docs/evidence/EVD-BOOT-009-bootstrap-self-review.md` plus pending external branch-protection evidence.

## Residual activation

CODEOWNERS paths and branch policy are prepared. Actual owner identities, required reviews, protected branch settings, and CI enforcement must be configured and evidenced in local bGitea before completion.
