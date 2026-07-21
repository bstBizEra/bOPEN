# BOOT-P0-08 — Ownership and review governance

**Status:** Execution complete
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

`docs/evidence/EVD-BOOT-009-bootstrap-self-review.md` and `docs/evidence/EVD-BOOT-011-bgitea-protected-review-activation.md` plus the protected Gitea PR #1 merge receipt.

## External-control reconciliation

Gitea owner identities, separated role teams, CODEOWNERS paths, required Reviewer approval, merge restriction, direct-push denial, exact required governance context, and protected PR #1 merge are configured and observed in EVD-BOOT-011. BOOT-P0-08 execution is complete. B7 remains a separate bOPEN Architecture Authority decision.
