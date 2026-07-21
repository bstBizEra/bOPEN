# Documentation Changelog

## 2026-07-21 - GOV-P0-01 Program Goal v0.2 controlled draft

- Converted the supplied Program Goal v0.2 into BOPEN-GOAL-001 with a source hash and explicit non-authorizing status.
- Added BOPEN-GOV-001, DEC-0010 and namespaced program/roadmap/bootstrap/research lifecycle aliases to prevent gate-status leakage.
- Established draft program registers, a source-complete requirement catalog and fail-closed program-control validation.
- Extended work-item, evidence and handoff templates with maker/checker, session, worktree, SHA, scope and authority separation fields.
- Kept PG-G0 NOT_READY, B7/DEC-0007 pending, RES-G3-G7 open and production implementation unauthorized.

## 2026-07-21 - BOOT-P0-12 external-control reconciliation

- Reconciled BOOT-P0-01 and BOOT-P0-08 with the protected Gitea PR #1 merge and current `main` protection observation.
- Updated EVD-BOOT-011 without changing the historical activation record.
- Moved deterministic bootstrap readiness to `ready_for_authority_review` while preserving B7 as pending and production implementation authority as false.
- Kept DEC-0007 proposed for the bOPEN Architecture Authority.

## 2026-07-21 - G3 synthetic runtime design

- Added a non-executing G3 design contract for the missing identity, tenant/membership and invitation runtime evidence.
- Added fail-closed authority, isolation, immutable dependency, synthetic-data, secure-oracle, evidence-retention and cleanup requirements.
- Added DEC-0011 as a proposed, ineffective runtime authorization decision.
- Added EVD-RES-004 and deterministic validation/report controls while preserving G3 as open and production implementation as unauthorized.

## 2026-07-13 - research R0 control establishment

- Approved DEC-0009 to keep physical upstream clones and raw evidence outside the bOPEN worktree.
- Assigned the R0 SARCHI/ARCHI/ENGIN/REV responsibilities and SecB license/compliance ownership.
- Consolidated the BoxyHQ source ID and expected pin, license and lock checksums.
- Hardened the Windows clone and verification scripts against ambient credential prompting, wrong origins, attached branches, missing locks and checksum drift.
- Added a recorded baseline runner and reproduced the exact result in separate ENGIN and REV workspaces.
- Recorded npm 10.9.2 as the R0 compatibility requirement, npm 11 lock rejection, the pinned upstream format failure, and passing lint/types/unit/build outcomes.
- Added EVD-RES-002 and marked G0-G2 `PASS WITH CONDITIONS`; G3-G7 and production implementation remain closed.

## 2026-07-13 - multi-tenant DEV readiness

- Accepted DEV-P0-01 for contract, fixture, validator, and test execution only.
- Added draft membership, active-context, and tenant-ownership schemas.
- Added seven synthetic multi-tenant readiness scenarios with API and database cross-tenant denial.
- Extended contract validation and focused tests for membership separation, trusted context, tenant ownership, deny-by-default behavior, and audit correlation.
- Added EVD-DEV-001 while keeping G7, normative approval, and production implementation gates closed.

## 2026-07-13 - bGitea protected review activation

- Created and verified the private `bst-sa/bopen` local source-of-truth repository and configured credential-free `origin`.
- Added separated Gitea Architect, Engineer, and Reviewer teams with repository-only membership.
- Installed the checksum-verified repository-scoped Gitea Runner 2.0.1 over rootless Podman.
- Protected `main` against direct/force pushes and administrator bypass, with Reviewer-only approval and merge authority.
- Added Gitea CODEOWNERS and governance workflow controls plus EVD-BOOT-011.
- Observed successful Actions run 17/job 33 and required the exact `Bootstrap Governance / validate (pull_request)` context.
- Recorded RSK-012 for rootless WSL host job networking required by the unavailable `/dev/net/tun` device.
- Applied independent review findings by making the Gitea workflow token read-only, pinning external actions to full commits, and validating both GitHub and Gitea workflows.
- Reported the Gitea hardening incident and residual host decisions to SecB and bstSA SARCHI without credential values.

## 2026-07-13 - GitHub draft review activation

- Published the reconciliation branch and opened draft GitHub PR #1.
- Recorded the passing Bootstrap Governance workflow result.
- Replaced placeholder CODEOWNERS teams with verified repository administrator `@bstBizEra`.
- Recorded DEC-0008 and RSK-011 after GitHub rejected private-repository branch protection under the current account plan.
- Approved DEC-0008 option 2, preserving private bGitea as the protected working source and GitHub as the stable review/publication surface.

## 2026-07-13 - approved GitHub reconciliation

- Recorded sponsor approval of DEC-0006 option 1.
- Rebuilt the BOOT-P0 history on a reconciliation branch from existing GitHub `main`.
- Preserved the GitHub root commit and resolved the one-line README conflict with the governed bootstrap README.
- Added EVD-BOOT-010 and kept direct or force publication to `main` prohibited.

## 2026-07-13 - BOOT-P0 completion self-review

- Audited all BOOT-P0-01 through BOOT-P0-12 outcomes against current evidence.
- Added executable secret and supply-chain checks with tests and full CI/pre-commit coverage.
- Added the missing exception register and formal DEC-0006/DEC-0007 decision requests.
- Classified ten packages as execution-complete, two as external-activation-pending, and BOOT-P0-12 as authority-review-pending.
- Recorded EVD-BOOT-009 without retaining local bGitea credentials.

## 2026-07-13 - missing bootstrap evidence

- Generated EVD-BOOT-001 AGENTS hierarchy validation evidence.
- Generated EVD-BOOT-002 document manifest validation evidence.
- Updated BOOTSTRAP-GATES B2/B3 status to evidence generated.
- Refreshed the bootstrap gate readiness report so pending evidence is no longer listed.

## 2026-07-13 - bootstrap gate readiness

- Added a deterministic bootstrap gate readiness report tool for BOOT-P0-12.
- Generated `artifacts/validation/bootstrap-gate-readiness.md`.
- Added governance tests for the report and EVD-BOOT-007 evidence.
- Confirmed B7 remains review-required and production implementation remains unauthorized.

## 2026-07-13 - vertical-slice fixtures

- Added the first vertical-slice acceptance fixture for BOOT-P0-11.
- Added a draft authorization audit-event schema.
- Extended contract validation to check `.acceptance.json` fixtures and correlation consistency.
- Added contract tests covering the seven first-slice acceptance scenarios.
- Added EVD-BOOT-006 evidence.

## 2026-07-13 - first coding move

- Added a standard-library contract validation harness for Phase 0 machine-readable contracts.
- Added contract validator tests and package scripts.
- Marked existing draft JSON schemas with top-level draft status metadata.
- Added EVD-BOOT-005 evidence for BOOT-P0-10.

## 2026-07-13 - roadmap build start

- Started the roadmap-safe Phase 0 build lane through BOOT-P0-09/BOOT-P0-01.
- Documented the local bGitea working remote and GitHub stable publication model.
- Added EVD-BOOT-004 source-control baseline evidence and traceability.
- Recorded DEC-0006/RSK-009 for the unrelated local bootstrap and GitHub `main` histories.
- Verified local bGitea service at `http://localhost:3030/` and recorded RSK-010 for the unverified local `origin` repository path.

## 2026-07-13 - local preparation

- Prepared downloaded BOPEN-BOOT-001 full pack for local version control.
- Fixed `pnpm test:governance` quoting so unittest discovery works in Windows PowerShell.
- Added local bootstrap validation evidence for BOOT-P0-05.

## 2026-07-12 — v1.0

- Created BOPEN-BOOT-001 full AGENTS.md and documentation bootstrap pack.

## Append-only entry — 2026-07-21 — GOV-P0-02 authority-docket proposal

- Added a draft exact-bound PG-G0 authority docket using only actions present in the live draft authority matrix.
- Added fail-closed human-identity, concurrence, Git/tree, artifact-hash, expiry and non-authority validation.
- Proposed DEC-0012 for five missing root instruction paths and generated-manifest handling.
- Preserved missing governance/register/gate actions, technology checker dates and every human disposition as blockers.
- Kept PG-G0 NOT_READY and production implementation unauthorized.

## Append-only entry — 2026-07-21 — GOV-P0-02 authority-record hardening

- Required explicit action, subject, validity, revocation and evidence controls for bound authority identity records.
- Required grantors to carry explicit delegation-specific action and subject scopes.
- Bound identity and delegation evidence existence to the referenced commit.
- Added negative tests for omitted scopes, malformed scope types, revoked identities, malformed validity and missing historical evidence.
- Preserved all authority and implementation outcomes as false pending external human authority.

## Append-only entry â€” 2026-07-22 â€” QUAL-INTEG-001 review candidate

- Composed exact GOV-P0-03, QUAL-P0-00, TECH-P0-01 and QUAL-P0-02 proposal chains and reconstructed RES-P0-05 in an isolated review branch.
- Preserved canonical and historical manifests as immutable Git-object-bound bytes and introduced a separately named aggregate snapshot and append-only index.
- Reconciled shared validation, workflow and documentation surfaces by semantic union while retaining every fail-closed non-authority control.
- Kept technology/provider selection, qualification execution, gate passage, merge, release, runtime and production implementation unauthorized.

## Append-only entry â€” 2026-07-22 â€” QUAL-INTEG-001 immutable-manifest rework

- Removed package commands capable of overwriting canonical or historical manifests.
- Restricted manifest writes to explicit create-once aggregate snapshots at new versioned paths.
- Added binary Git-history prefix validation for the append-only manifest index.
- Added 10 adversarial write/history tests and raised the full validated floor from 230 to 240.
- Preserved every prior manifest/index byte and all non-authority states.

## Append-only entry - 2026-07-22 - QUAL-INTEG-001 current-tree readiness projection

- Preserved the historical PG-G0 docket, blocker report, canonical manifests and indexed snapshots byte-for-byte.
- Added a closed-schema deterministic projection separating historical bound-commit evidence from bounded current-tree technical observations.
- Added 10 fail-closed negative tests for root-control integrity, human-only blockers, unknown blockers, CI/PR non-authority, false readiness and closed object shapes.
- Retained 17 active blockers and every authority, qualification, gate, merge, release, runtime and production flag as false.
