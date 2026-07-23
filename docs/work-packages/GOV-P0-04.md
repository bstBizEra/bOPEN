# GOV-P0-04 — Authority Identity Surfaces, Matrix v0.2 Proposal and Operator Decision Packet

**Version:** 0.1
**Status:** Proposed; not accepted
**Owner:** Engineering Authority
**Authorization source:** User direction ("help finish the G0 phase; assist Codex"); BOPEN-BOOT-001 documentation and contract drafting authority only
**Accepted by/at:** Pending attributable Human Engineering Authority disposition
**Lifecycle:** PG-G0 proposal; no gate passage
**Dependencies:** GOV-P0-01 at `c893062`; GOV-P0-02 at `82ed6b3`; GOV-P0-03 at `a29ec1d`; DEC-0012; DEC-0013 (this package)
**Governing artifacts:** BOPEN-BOOT-001; BOPEN-GOV-001 Draft; PG-G0-AUTH-001
**Maker:** Claude (BST-SA Motor worker agent; claude-sonnet-5)
**Independent checker:** Pending (must not be the maker; Codex checker eligible)
**Branch/worktree:** `claude/GOV-P0-04-authority-identity-surfaces` / `C:\laragon\www\bopen\.claude\worktrees\elegant-jackson-05259b`
**Base SHA:** `a29ec1d8ab28d38621dc4db176b7b2abf2ea44cb`
**Base tree:** `ff3cb910385f04ccc3b0e077cf4329b79f7fe3f6`
**Expiry:** 2026-08-21T00:00:00+07:00

## Objective

Prepare the draft surfaces that the PG-G0 authority docket records as absent — a hash-bindable human authority identity register, an authority matrix v0.2 proposal covering the three missing actions and the ACCEPT_WORK_ITEM reconciliation — plus an independent verification receipt for the GOV-P0-03 candidate and a single consolidated operator decision packet.

## In scope

- `contracts/governance/authority-identity-register.schema.json` (draft);
- `docs/00-governance/AUTHORITY-IDENTITY-REGISTER-DRAFT.json` (draft; one pending solo-operator record with independence disclosure; moved to the validator-bound registers path only at approval);
- `docs/00-governance/AUTHORITY-MATRIX-0.2.0-PROPOSAL.json` (proposal file; bound v0.1 register untouched);
- `docs/decisions/DEC-0013.md` (proposed);
- `docs/evidence/EVD-GOV-004-gov-p0-03-independent-verification.md` (independent exact-SHA receipt for `a29ec1d`);
- `docs/00-governance/PG-G0-OPERATOR-DECISION-PACKET.md` (advisory).

## Out of scope

Approving any register, matrix, identity, decision, work package or gate; modifying the bound AUTHORITY-MATRIX.json or the PG-G0 docket; docket v0.2 rebinding (Codex follow-up); production code, migrations, runtime or infrastructure; research gate changes.

## Allowed paths

`docs/00-governance/`, `docs/decisions/DEC-0013.md`, `docs/evidence/EVD-GOV-004*`, `docs/work-packages/GOV-P0-04.md`, `contracts/governance/authority-identity-register.schema.json`.

## Prohibited paths

`apps/`, `services/`, `packages/`, `infrastructure/`, `research/upstream/`, migrations, runtime configuration, secrets, existing bound registers and dockets.

## Acceptance criteria

- All new artifacts are additive; no bound artifact SHA changes;
- register and schema are structurally valid and fail closed (draft status, pending record, null approvals);
- matrix proposal preserves all seven v0.1 entries and only adds the three missing actions plus the prose-aligned ACCEPT_WORK_ITEM concurrence;
- existing repository, contract, program-control, docket, clean-room, secret and supply-chain checks remain green at the candidate SHA;
- an independent checker (not Claude) accepts the exact final SHA.

## Risks and rollback

Risk: the pending identity record or matrix proposal is mistaken for an effective approval. Control: draft/pending statuses, null approval fields and fail-closed validators; the docket continues to report `NOT_READY`. Rollback: delete the isolated branch; no bound state is touched.

## Completion record

Maker drafting complete. Independent checker verdict and Human Engineering Authority acceptance pending. This proposed record does not accept itself.

## Codex independent review — 2026-07-22

Independent checker `BST-Codex-Motor` reviewed exact commit `203ed05162dccb2729d4c39e25050817384c3b4b` (tree `24d100482b39d42bb99a84ccd97e63d647d763ad`) and recorded `REJECT` in EVD-GOV-005. The candidate fails the required repository validation because its versioned document manifest is stale, and its proposed authority identity fields, approval-state constraints, evidence requirements and delegation representation do not yet interoperate with the existing docket contract and validator.

The checker separately repaired the disclosed temporary-fixture path preference and drafted a non-effective v0.2 rebinding plan. Those follow-up changes do not alter the immutable candidate verdict. GOV-P0-04 remains proposed and unaccepted; all authority, activation, PG-G0, merge, release, deployment and production outcomes remain false.

## Append-only correction record — 2026-07-22

The independent checker (BST-Codex-Motor) reviewed candidate `203ed05162dccb2729d4c39e25050817384c3b4b` and returned `REJECT` with findings RF-001..004 (EVD-GOV-005, checker review branch `codex/GOV-P0-04-review-203ed05`). The maker accepts all four findings. Scope extension for the corrective candidate (reason: RF-003 requires semantic negative tests and a dedicated validator; benefit of the old phase: it kept the first candidate documentation-only; expected outcome: fail-closed register semantics proven by tests):

- **Allowed paths extended:** `tools/validate_authority_identity_register.py`, `tests/governance/test_authority_identity_register.py`, `package.json` (validate chain only), `docs/manifests/GOV-P0-02-DOCUMENT-MANIFEST.json` (deterministic regeneration only).
- Corrections per DEC-0013 append-only correction note: docket-compatible identity semantics, status-coupled approval provenance, DIRECT-only authority mode, refreshed manifest, `pnpm validate` green.
- The `REJECT` receipt for `203ed05` stands; this corrective candidate carries a new SHA and requires a new independent exact-SHA review.

## Independent corrective-candidate review — 2026-07-22

BST-Codex-Motor independently reviewed exact candidate `d7d8699326345bb1a2f027e4027fb90d18649022` (tree `64d0b5891a7460067fc472772b49d505e21bc6d3`) and issued EVD-GOV-006 with verdict `ACCEPT_EXACT_SHA`. RF-001 through RF-004 are technically closed at that immutable SHA; 12/12 authority-identity tests, 44/44 docket tests, 172/172 full tests, `pnpm validate` and the exact-diff check passed. The EVD-GOV-005 `REJECT` for `203ed05` remains unchanged and is bound by review commit `45aae0a9f49c1402f8b976e39deaf8d2894d8be4`.

This technical receipt does not accept this work package, approve DEC-0013, activate authority, pass PG-G0 or authorize merge, release, deployment or production implementation. Human Engineering Authority disposition remains pending.

## Append-only docket v0.2 preparation — 2026-07-23

Following Operator Batch 1 at exact commit `26bea090c0aca14f1337c4be1a146fd48bb1f626` / tree `8789c5e70c2ce87298928d4d02add7ffe5867402`, BST-Codex-Motor prepared the atomic Batch 2 candidate on `codex/GOV-P0-04-docket-v02`.

Scope extends to the authority-matrix, docket and root-control schemas/validators/tests; the bound draft matrix; the v0.2 binding inventory and signing surface; deterministic reports/manifests; and append-only evidence/cross-links. Reason: the authorized rebinding plan requires these artifacts to move as one fail-closed unit. Benefit of the old phase: Batch 1 created an immutable approved identity substrate and accepted GOV-P0-02/03 without approving the remaining surfaces. Expected outcome: one independently reviewable exact-SHA candidate exposes every remaining human disposition without exercising it.

Current state is `PENDING_HUMAN_DECISIONS`. The matrix, BOPEN-GOV-001, six remaining register surfaces, GOV-P0-01, GOV-P0-04, DEC-0007/BOOT-B7 and the root-ledger activation event are unsigned and ineffective. GOV-P0-04 is not accepted by this maker record. PG-G0, merge, release, deployment and production implementation remain false.

## Append-only acceptance record — 2026-07-23

**Outcome:** ACCEPTED; effective
**Accepted by:** HUMAN-OPERATOR-001 (Engineering Authority, DIRECT)
**Owning-artifact concurrence:** HUMAN-OPERATOR-001 acting as Engineering Authority under the approved solo-operator identity disclosure
**Accepted at:** 2026-07-23T00:45:00+07:00
**Decision ref:** docs/00-governance/signing/SIGNING-PASS-2.md#append-only-batch-2-signing-record--2026-07-23
**Technical prerequisite:** EVD-GOV-008 `ACCEPT_EXACT_SHA` for `b929821af83ff774be2bfb10dcb5588d862dcaf2`

The package is accepted exactly as signed. The v0.3 mechanical successor still requires independent exact-SHA review; B8, B9/PG-G0, merge, release, deployment, runtime and production implementation remain pending or false.

## Append-only RF-001/RF-002/RF-003 remediation disposition - 2026-07-23

Rebuilt from v0.4 candidate `8a0987070efa4108e7f9ada716a8fb533fa47e42`; the signed docket, inventory, B8 approvals, B9 pending state and readiness remain byte-for-byte unchanged. The 33 predecessor tests removed during the v0.4 reduction are itemized below. `OBSOLETE/SUPERSEDED` means the v0.4 test named in the disposition is the maintained equal-or-stronger control; no signed outcome is altered.

| # | Removed predecessor test | Disposition |
|---:|---|---|
| 1 | `test_committed_file_mock_prefers_temp_fixture_over_repository_file` | OBSOLETE/SUPERSEDED by v0.4 fixture isolation |
| 2 | `test_missing_docket_fails_closed` | OBSOLETE/SUPERSEDED by repository validation |
| 3 | `test_missing_or_duplicate_decision_fails_closed` | OBSOLETE/SUPERSEDED by v0.4 decision-set validation |
| 4 | `test_unknown_top_level_field_fails_closed` | SUPERSEDED by `test_unknown_fields_fail_closed` |
| 5 | `test_unknown_nested_decision_field_fails_closed` | SUPERSEDED by `test_unknown_fields_fail_closed` |
| 6 | `test_malformed_commit_and_wrong_tree_fail_closed` | SUPERSEDED by exact v0.4 repository binding |
| 7 | `test_stale_artifact_hash_fails_closed` | SUPERSEDED by inventory digest test |
| 8 | `test_append_only_governing_artifact_rewrite_fails_closed` | OBSOLETE v0.4 artifact transition |
| 9 | `test_post_bound_mutation_cannot_be_hidden_by_rewriting_docket_hashes` | SUPERSEDED by inventory/subject immutability |
| 10 | `test_subject_must_match_exact_governing_artifact_map` | SUPERSEDED by B8 and Batch 2 subject tests |
| 11 | `test_agent_cannot_be_final_human_authority` | SUPERSEDED by identity-register actor checks |
| 12 | `test_pending_decision_cannot_claim_effect` | SUPERSEDED by B9 pre-sign test |
| 13 | `test_pending_concurrence_cannot_claim_actor` | OBSOLETE v0.4 pending-concurrence shape |
| 14 | `test_self_reviewed_technical_acceptance_fails_closed` | OBSOLETE v0.3 review state |
| 15 | `test_normalized_technical_identities_cannot_bypass_self_review` | OBSOLETE v0.3 review state |
| 16 | `test_future_review_and_missing_evidence_fail_closed` | SUPERSEDED by B9 prerequisite test |
| 17 | `test_technical_acceptance_requires_distinct_resolved_candidate_and_bound_evidence` | OBSOLETE external receipt shape |
| 18 | `test_technical_acceptance_rejects_repository_binding_as_candidate` | OBSOLETE external receipt shape |
| 19 | `test_technical_acceptance_rejects_wrong_tree_and_unbound_evidence` | SUPERSEDED by exact substrate checks |
| 20 | `test_technical_acceptance_rejects_non_ancestor_candidate` | OBSOLETE external review-chain assertion |
| 21 | `test_expired_decision_request_fails_closed` | SUPERSEDED by common schema validation |
| 22 | `test_terminal_reject_still_requires_human_independence_and_evidence` | OBSOLETE; B8 outcomes are signed APPROVE |
| 23 | `test_five_b8_decisions_cannot_be_changed_by_signed_state_successor` | SUPERSEDED by B8 subject/outcome tests |
| 24 | `test_fabricated_identity_binding_fails_without_approved_registry_record` | SUPERSEDED by actor provenance test |
| 25 | `test_identity_binding_hash_tree_status_and_structured_record_must_match` | SUPERSEDED by identity-register validator |
| 26 | `test_delegation_ref_and_bound_record_must_match` | OBSOLETE; DELEGATED is rejected and null placeholders are compatibility-only |
| 27 | `test_delegation_bound_hash_and_structured_scope_must_match` | OBSOLETE; DELEGATED is rejected |
| 28 | `test_delegation_grantor_requires_explicit_action_and_subject_scopes` | OBSOLETE; DELEGATED is rejected |
| 29 | `test_revoked_delegate_and_grantor_identities_fail_closed` | OBSOLETE; DELEGATED is rejected |
| 30 | `test_identity_validity_and_evidence_are_mandatory_and_well_formed` | SUPERSEDED by identity-register validator |
| 31 | `test_delegation_scope_types_fail_closed_without_exceptions` | OBSOLETE; DELEGATED is rejected |
| 32 | `test_identity_evidence_must_exist_at_bound_commit` | SUPERSEDED by exact registry substrate checks |
| 33 | `test_nonconcur_requires_attributable_human_time_expiry_and_evidence` | OBSOLETE v0.3 pending transition |

RF-002 is closed by a temporary-root repeatability test that copies the package fixture, builds its manifest, and validates twice. RF-003 is closed by `test_delegated_authority_mode_fails_closed`; schema authority mode is `DIRECT`-only and the validator no longer has a live DELEGATED branch. The GOV-P0-03 ledger entry and package manifest are committed together in this rebuilt candidate.
