# Evidence Index

| Evidence ID | Work package | Description | Path | Status |
|---|---|---|---|---|
| EVD-BOOT-001 | BOOT-P0-02 | AGENTS hierarchy validation | `artifacts/validation/agents-validation.txt` | Generated |
| EVD-BOOT-002 | BOOT-P0-03 | Document manifest validation | `artifacts/validation/document-validation.txt` | Generated |
| EVD-BOOT-003 | BOOT-P0-05 | Local bootstrap validation and governance test result | `docs/evidence/EVD-BOOT-003-local-prep.md` | Generated |
| EVD-BOOT-004 | BOOT-P0-09/BOOT-P0-01 | Local bGitea and GitHub stable source-control baseline | `docs/evidence/EVD-BOOT-004-source-control-start.md` | Generated |
| EVD-BOOT-005 | BOOT-P0-10 | First coding move: contract validation harness | `docs/evidence/EVD-BOOT-005-contract-validation-harness.md` | Generated |
| EVD-BOOT-006 | BOOT-P0-11 | First vertical-slice acceptance fixtures and tests | `docs/evidence/EVD-BOOT-006-first-vertical-slice-fixtures.md` | Generated |
| EVD-BOOT-007 | BOOT-P0-12 | Bootstrap exit-gate readiness report | `docs/evidence/EVD-BOOT-007-bootstrap-gate-readiness.md` | Generated |
| EVD-BOOT-008 | BOOT-P0-02/BOOT-P0-03/BOOT-P0-12 | Missing bootstrap validation evidence closure | `docs/evidence/EVD-BOOT-008-missing-bootstrap-evidence-closure.md` | Generated |
| EVD-BOOT-009 | BOOT-P0-01 through BOOT-P0-12 | Requirement-by-requirement bootstrap completion self-review | `docs/evidence/EVD-BOOT-009-bootstrap-self-review.md` | Generated |
| EVD-BOOT-010 | BOOT-P0-01/BOOT-P0-08 | Approved GitHub history reconciliation branch | `docs/evidence/EVD-BOOT-010-github-reconciliation.md` | Generated |
| EVD-BOOT-011 | BOOT-P0-01/BOOT-P0-08 | Private bGitea repository, fenced teams, runner, protected `main`, and protected PR #1 merge | `docs/evidence/EVD-BOOT-011-bgitea-protected-review-activation.md` | External controls verified; B7 authority review pending |
| EVD-DEV-001 | DEV-P0-01 | Multi-tenant membership, context, ownership, and cross-tenant denial contract validation | `docs/evidence/EVD-DEV-001-multitenant-readiness.md` | Generated; authority review pending |
| EVD-RES-001 | RES-P0-02 | BoxyHQ provenance and license | BOPEN-RES-001 resources | Existing baseline |
| EVD-RES-002 | RES-P0-01/02/03 | R0 workspace, provenance, license and two-operator reproduction | `docs/evidence/EVD-RES-002-r0-control-establishment.md` | G0-G2 pass with conditions |
| EVD-GOV-001 | GOV-P0-01 | Program Goal v0.2 source-completeness, draft registers and fail-closed PG-G0 readiness | `docs/evidence/EVD-GOV-001-program-g0-controls.md` | Draft; checker pending; PG-G0 NOT_READY |
| EVD-GOV-002 | GOV-P0-02 | Draft human-authority docket, exact bindings and fail-closed negative tests | `docs/evidence/EVD-GOV-002-pg-g0-authority-docket.md` | Draft maker evidence; exact-SHA checker and human acceptance pending |
| EVD-GOV-005 | GOV-P0-04 | Independent exact-SHA review, fixture repair verification and v0.2 rebinding-plan evidence | `docs/evidence/EVD-GOV-005-gov-p0-04-independent-review.md` | REJECT for `203ed05`; maker correction required |

| EVD-GOV-006 | GOV-P0-04 | Independent exact-SHA review of the corrective authority-identity candidate | `docs/evidence/EVD-GOV-006-gov-p0-04-corrective-candidate-review.md` | `ACCEPT_EXACT_SHA` for `d7d8699`; human authority review pending |
| EVD-GOV-007 | GOV-P0-04 | Maker evidence for the exact-substrate PG-G0 authority docket v0.2 Batch 2 candidate | `docs/evidence/EVD-GOV-007-pg-g0-authority-docket-v02-candidate.md` | Candidate preparation; independent review and human dispositions pending |

## Append-only EVD-GOV-001 status supersession — 2026-07-21

Reason: the original index row preserves its pre-review checker-pending state. Benefit of the old phase: it accurately recorded the first indexed state. Expected outcome: this appended note records that exact-SHA technical checks exist through GOV-P0-01 head `c893062c197e74c15214e5ce1c425b9e9ed8002f`, while Human Engineering, Product and Architecture dispositions and PG-G0 remain pending. The historical row is not rewritten.

## Append-only signed-state evidence entries — 2026-07-23

| Evidence ID | Work package | Description | Path | Status |
|---|---|---|---|---|
| EVD-GOV-008 | GOV-P0-04 | Independent exact-SHA review of the docket v0.2 Batch 2 candidate | `docs/evidence/EVD-GOV-008-docket-v02-independent-review.md` | `ACCEPT_EXACT_SHA` for `b929821`; technical evidence only |
| EVD-GOV-009 | GOV-P0-04 | Maker evidence for the v0.3 mechanical encoding of all signed Batch 2 outcomes | `docs/evidence/EVD-GOV-009-pg-g0-authority-docket-v03-signed-state-candidate.md` | Signed-state candidate; new independent exact-SHA review pending |

Reason: index the prerequisite receipt and its non-self-referential signed-state successor evidence. Benefit of the old phase: the original rows preserve the preparation-time status. Expected outcome: reviewers can distinguish the accepted v0.2 candidate from the separately reviewable v0.3 encoding; neither evidence record decides B8 or B9.

## Append-only RF remediation candidate - 2026-07-23

| Evidence ID | Work package | Description | Path | Status |
|---|---|---|---|---|
| EVD-GOV-013 | GOV-P0-04 | RF-001 itemized test-coverage disposition and RF-002 manifest-order remediation for v0.4 | `docs/evidence/EVD-GOV-013-pg-g0-authority-docket-v04-rf-remediated-candidate.md` | Remediated candidate; independent exact-SHA review pending |

## Append-only v0.4 B8 signed-state entry - 2026-07-23

| Evidence ID | Work package | Description | Path | Status |
|---|---|---|---|---|
| EVD-GOV-011 | GOV-P0-04 | Maker evidence for v0.4 encoding of all five Signing Pass 3 B8 approvals and B9 pending surface | `docs/evidence/EVD-GOV-011-pg-g0-authority-docket-v04-b8-signed-candidate.md` | Signed-state candidate; new independent exact-SHA review pending |

Reason: record the next mechanical successor without upgrading EVD-GOV-010 or pre-signing B9. Benefit of the old phase: EVD-GOV-009 remains a stable v0.3 audit trail. Expected outcome: Claude reviews one exact v0.4 SHA while the human B9 decision remains pending.
