# Documentation Changelog

## 2026-07-27 - SIGNING-PASS-11: C2 trust-root approval (APPROVED_PENDING_PROOF_OF_POSSESSION)

- Encoded HUMAN-OPERATOR-001 C2 approval of the trust-root candidate at 8346f33e (separate receipt per the no-circularity rule; binds candidate commit 8346f33e, tree 42ab3439, trust-root blob 0641b01a, raw sha256 a6806c16, public key + fingerprint, authority basis PG-P0-INTERP-002 v0.3). Lifecycle CANDIDATE_PENDING_C2_APPROVAL -> APPROVED_PENDING_PROOF_OF_POSSESSION. The candidate JSON is NOT mutated (bound digests stay valid).
- Boundary: approval binds the key to authority but does NOT activate the trust root; it becomes ACTIVE only on the first valid C4 mandate signature verified by VERIFY-P0-01 (proof of possession). No mandate accepted; no register/validator mutation; PG-P0 ACTIVE; PG-P1 NOT_READY; main a908bbe. Next: C3 manifest + mandate-bytes freeze.

## 2026-07-27 - K4: trust-root CANDIDATE with operator public key (CANDIDATE_PENDING_C2_APPROVAL)

- Added docs/00-governance/signing/PG-P0-COMPLETION-TRUST-ROOT-CANDIDATE.json: the operator-generated Ed25519 PUBLIC key (raw-32 hex) + SHA-256 fingerprint, intake-validated per the corrected K3 logic (strict lowercase-hex, constant-time fingerprint match, canonical decompress/recompress roundtrip = structural validity only). Profile named sha256:rfc8032-ed25519-raw-32. Private key generated and held solely by the operator (encrypted PKCS8, offline); no agent generated, received, or handles it.
- Lifecycle: CANDIDATE_PENDING_C2_APPROVAL -> APPROVED_PENDING_PROOF_OF_POSSESSION (operator signed C2 receipt) -> ACTIVE (valid C4 mandate signature = proof of possession). No circularity: the separate C2 receipt binds the resulting commit/tree/blob digests. V2 placeholder draft preserved as history. Additive; no live surface changed. PG-P0 ACTIVE; PG-P1 NOT_READY.

## 2026-07-27 - EVD-CLOSURE-004: durable receipt for the SIGNING-PASS-10 encoding (ACCEPT_EXACT_SHA)

- Persisted verbatim the independent checker receipt for the v0.3 re-issuance encoding at 266ca800: binding digests recomputed exact; supersession of the v0.2 issuance correct with history byte-preserved; strictly additive; validators 11/11; full tests 189/189; no finding. C1 final; C2 (operator keygen) next.

## 2026-07-27 - SIGNING-PASS-10: re-issue PG-P0-INTERP-002 against v0.3 exact text (C1 final)

- Encoded HUMAN-OPERATOR-001 re-issuance attestation: PG-P0-INTERP-002 v0.3 EFFECTIVE against exact text at a210e8a4 (v0.3 blob sha256 15c01709...), superseding the v0.2 issuance (SIGNING-PASS-9, preserved as history), with independent review receipt EVD-CLOSURE-003 (ACCEPT_EXACT_SHA, no finding) on file. Appended the issuance record to the v0.3 doc (extend-only; immutable Draft header preserved).
- Closure C1 COMPLETE on the consolidated execution lineage. C2-C11 remain separately gated (trust root placeholder/NOT EFFECTIVE; no mandate; no register/validator mutation). PG-P0 ACTIVE; PG-P1 NOT_READY; main a908bbe.

## 2026-07-27 - EVD-CLOSURE-003: durable receipt for INTERP-002 v0.3 (ACCEPT_EXACT_SHA)

- Persisted verbatim the independent checker receipt for v0.3 at a210e8a4: hard check PASS (verifier in-lineage, 27/27), byte-faithful carries PASS, sorted-refs rule + preserved controls confirmed, validators 11/11, full suite 189/189, v0.3 blob digest exact match, no finding. Advisory only; human re-issuance remains authoritative.

## 2026-07-27 - INTERP-002 v0.3 + consolidated execution lineage on accepted base'

- Consolidated the PG-P0 closure records into the accepted integrated base' `52bd96ec` — the lineage that contains VERIFY-P0-01 in-tree (operator hard check: the verifier must exist in the exact execution lineage). Carried byte-faithfully: SIGNING-PASS-8 + issued PG-P0-INTERP-001 (from `d6252de1`); SIGNING-PASS-9 + INTERP-002 v0.2 text + trust-root v2 draft (from `32271aa2`); EVD-CLOSURE-001/002 (from `52359dc4`).
- Added `PG-P0-INTERP-002-CLOSURE-AUTHORIZATION-V0.3.md`: supersedes v0.2 per operator direction (a signed exact-text blob must not carry a known ordering ambiguity). The correction is normative: the executed successor's `evidence_refs` MUST be the canonical `sorted(...)` of the sanctioned set (EVD-CLOSURE-002 finding); examples are non-normative. All other content (authority-scope finding, corrections 2–4, C0–C11, negative tests, six-condition rule) preserved; C1 re-executes on human re-issuance against the v0.3 exact text.
- Drafts only; no live register/schema/docket/validator mutation; nothing issued or signed by this commit. PG-P0 ACTIVE; PG-P1 NOT_READY; main a908bbe.

## 2026-07-25 - PG-P0 preparation base' — integrate the SIGNING-PASS-6 accepted batch

- Integrated, at their exact accepted bytes, the four work items accepted by HUMAN-OPERATOR-001 in SIGNING-PASS-6 into a single governed preparation successor (base') off the accepted head `73912e4`:
  - VERIFY-P0-01 (`3946e946`): `tools/verify_phase_transition.py`, `tests/governance/test_phase_transition_verify.py`, `docs/work-packages/VERIFY-P0-01.md`, `docs/evidence/EVD-VERIFY-001-executable-verifier.md`.
  - GATE-P0-01 (`f552da30`): `docs/00-governance/PG-P0-GATE-CONTRACT-DRAFT.md` (v0.1 draft), `docs/00-governance/AUTHORITY-MATRIX-COMPLETE-PHASE-PROPOSAL.md`, `docs/work-packages/GATE-P0-01.md`.
  - DEC-0014 (`8b8b79ed`): `docs/decisions/DEC-0014.md` + its `DECISION-REGISTER.md` row.
  - SKEL-P0-01 reconciliation (`11329bba`): the appended "Current status (derived)" section.
- Carried the acceptance record `docs/00-governance/signing/SIGNING-PASS-6.md` (`98ec002f`).
- Regenerated the document manifest; reconciled this changelog. Additive only: no live register mutated (AUTHORITY-MATRIX.json / AUTHORITY-IDENTITY-REGISTER.json byte-unchanged); no merge to `main`; PG-P0 remains ACTIVE; PG-P1 NOT_READY. This base' is the ground on which the effective-successor gate contract and the completion-enablement drafts are rebuilt so their references resolve in-tree.

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

## Append-only entry — 2026-07-22 — GOV-P0-04 exact-SHA review

- Recorded EVD-GOV-005 with a technical `REJECT` verdict for exact candidate `203ed05`.
- Preserved the passing 44-test focused and 160-test full-suite results while disclosing the failing required manifest check.
- Identified identity-provider/subject, approval-provenance, evidence and delegation incompatibilities between the proposal and docket validator.
- Repaired the docket test helper to prefer temporary fixtures and added a conflicting-repository-file regression case.
- Drafted a non-effective PG-G0 authority-docket v0.2 rebinding plan.

## Append-only entry — 2026-07-22 — GOV-P0-04 corrective-candidate review

- Issued EVD-GOV-006 as independent `ACCEPT_EXACT_SHA` evidence for candidate `d7d8699326345bb1a2f027e4027fb90d18649022` after all focused, full and repository checks passed.
- Preserved EVD-GOV-005 as an immutable `REJECT` for predecessor `203ed05162dccb2729d4c39e25050817384c3b4b`.
- Kept GOV-P0-04 proposed, PG-G0 not ready and every activation, merge, release, deployment and production outcome false pending human authority.

## Append-only entry — 2026-07-23 — PG-G0 authority docket v0.2 preparation

- Bound the successor docket to Operator Batch 1 commit `26bea090c0aca14f1337c4be1a146fd48bb1f626` and its exact 34-record substrate inventory.
- Adopted the ten-entry authority-matrix proposal as a draft bound matrix with approval provenance still null.
- Prepared 13 unsigned and ineffective Batch 2 disposition surfaces while preserving the original five pending docket decisions.
- Revised root-control validation so activation can occur only as one complete five-ledger Signing Pass 2 event; no activation event was added.
- Kept independent review pending and PG-G0, merge, release, deployment and production implementation false.

## Append-only entry — 2026-07-23 — PG-G0 authority docket v0.3 signed state

- Encoded all thirteen operator-signed Batch 2 dispositions with exact role-bound human actors and required concurrence blocks.
- Approved the authority matrix and six program registers with attributable provenance; made BOPEN-GOV-001 and DEC-0013 effective; accepted GOV-P0-01/GOV-P0-04; approved DEC-0007/BOOT-B7.
- Activated the five root ledgers through one identical append-only B6 event and retained their immutable Draft/Inactive genesis prefixes.
- Rebound the v0.3 inventory to Signing Pass 2 commit `60c4831f4fcdfabb876d62f4eb98949b4a1a5a66` and enforced exact signed transformations in schema, validator and negative tests.
- Preserved all five B8 requests as `PENDING` and PG-G0, merge, release, deployment, runtime and production implementation as unauthorized pending a new independent exact-SHA review and later decisions.

## Append-only entry - 2026-07-24 - PG-G0 terminal gate passage

- Encoded the operator's Signing Pass 4 `PG-G0-DEC-006` `PASS_PG_G0` approval without altering the signed subject or outcome.
- Transitioned the docket to terminal `DISPOSED`, regenerated readiness as `PG_G0_PASSED`, appended the passage event to all five root ledgers, and opened PG-P0 for authority review.
- Kept production implementation, merge, release, deployment and runtime flags false; final independent exact-SHA review remains required.

## Append-only entry - 2026-07-24 - PG-P0 preparation opening

- Encoded the operator's Signing Pass 5 transition of PG-P0 from `READY_FOR_AUTHORITY_REVIEW` to `ACTIVE` preparation.
- Bound the schedule entry to SKEL-P0-01, SIGNING-PASS-5 and EVD-GOV-017; the work package remains proposed and unaccepted.
- Preserved preparation/review-only scope and kept production implementation, migrations, merge, release, deployment and runtime unauthorized.

## Append-only entry - 2026-07-24 - SKEL-P0-01 checker review

- Recorded Codex concurrence with bounded findings on scope, allowed paths, acceptance reproducibility and the fail-closed skeleton-validator requirement.
- Kept SKEL-P0-01 proposed and unaccepted pending Human Engineering Authority disposition; no skeleton implementation was performed.

## Append-only entry - 2026-07-23 - v0.4 remediation rebuild

- Rebuilt from `8a0987070efa4108e7f9ada716a8fb533fa47e42`, preserving the signed docket and all B8 outcomes.
- Appended the remediation ledger event after the existing final entry and regenerated the GOV-P0-03 package manifest in the same commit.
- Removed the live DELEGATED validator path, added temporary-fixture manifest ordering and DIRECT-only negative coverage, and retained the 33-item disposition table.

## Append-only entry - 2026-07-23 - PG-G0 authority docket v0.4 B8 signed successor

- Encoded exactly the five Signing Pass 3 B8 approvals with final-authority identity-register provenance, signing timestamp and decision references.
- Rebound the v0.4 inventory and repository binding to the post-signing substrate; readiness now reports `ready_for_pg_g0_gate_decision: true` with zero validation errors.
- Surfaced B9/PASS_PG_G0 as pending with an independent-conformance prerequisite; no B9, merge, release, deployment, runtime or production authority was signed.

## Append-only entry - 2026-07-23 - v0.4 review-finding remediation

- Preserved the v0.4 docket, inventory, B8 approvals, B9 staging and readiness bytes unchanged.
- Itemized all 33 removed predecessor docket tests with v0.4 obsolescence/supersession decisions and added a repeatable root-manifest regression test.
- Clean-checkout discovery passes 144/144; `pnpm validate` passes. EVD-GOV-012 remains an immutable reject and a new exact-SHA review is required.

## Append-only entry - 2026-07-24 - MANIFEST-P0-01 deterministic manifest check

- Fixed `tools/generate_document_manifest.py`: `--check` now adopts the committed `generated` date so a byte-frozen candidate no longer goes stale at UTC-midnight rollover, restoring exact-SHA reproducibility; content drift (paths/sha256/bytes/count) still fails. Write mode uses `newline="\n"` (LF) to fix silent CRLF emission on Windows.
- Added regression test `tests/governance/test_document_manifest_reproducibility.py` proving date-invariance and content-sensitivity.
- Demonstrated on an isolated branch for operator disposition; the tool is outside SKEL-P0-01 allowed paths, so acceptance/merge requires a separate operator decision. No manifest content changed; no signed byte changed. Status: Proposed; not accepted.

## Append-only entry - 2026-07-24 - MANIFEST-P0-01 acceptance-criteria correction

- Corrected a self-contradicting acceptance criterion in `docs/work-packages/MANIFEST-P0-01.md`: it read "no manifest content changes", but the commit legitimately adds its own work-package record and changes the CHANGELOG record in GOV-P0-02. The criterion now states the ONLY manifest record changes are the documents this commit adds/changes (its work package + changelog), with no other record change and no signed byte change. Independent-review finding (WSL BST-Codex-Motor); wording-only fix, no behavior change.

## 2026-07-24 — MANIFEST-P0-01 acceptance

- HUMAN-OPERATOR-001 accepted `MANIFEST-P0-01` at exact SHA `78e985b41ed8354f6525154d5cdfbe4b1052a2d5` after dual independent `ACCEPT_EXACT_SHA` receipts and canonical reproducibility verification.
- This acceptance advances only the governed preparation lineage; merge, release, deployment, runtime activation, production implementation, PG-P0 completion and PG-P1 transition remain unauthorized.

## Append-only entry - 2026-07-24 - SKEL-P0-01 sole-maker candidate on accepted base'

- Rebuilt SKEL-P0-01 as a fresh sole-Claude-maker candidate on governed base' `aab8bd9` (Option B): the human-accepted MANIFEST-P0-01 reproducibility fix is inherited from the accepted base, so SKEL owns only the reconciled `pnpm-lock.yaml` (workspace importers), not the manifest tool.
- Every SKEL byte is authored solely by Claude (`claude-opus-4-8`); the earlier operator replay `700cf1e` carried Codex-authored bytes from conflict resolution and is superseded. Re-authored skeleton validator (fail-closed non-.d.ts rule); references the MANIFEST-P0-01 acceptance record.
- Canonical `pnpm validate` clean under `--frozen-lockfile`; signed surfaces byte-unchanged. Status: Proposed; not accepted; fresh independent Codex review required.

## 2026-07-25 — SKEL-P0-01 acceptance

- HUMAN-OPERATOR-001 authorized the `pnpm-lock.yaml` scope amendment and accepted SKEL-P0-01 at exact SHA `f1eea272442a0587ab5843ba28c6ce47b91e1615`.
- Acceptance is bounded to the governed preparation lineage; merge, release, deployment, runtime activation, PG-P0 completion and PG-P1 transition remain separately gated.
