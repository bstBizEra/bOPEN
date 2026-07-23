# EVD-GOV-011 - PG-G0 Authority Docket v0.4 B8 Signed-State Candidate

**Evidence ID:** EVD-GOV-011
**Timestamp:** 2026-07-23T09:30:00+07:00
**Agent ID:** BST-Codex-Motor
**Source:** Operator Signing Pass 3 at `7834c48f84c01be8a03cf00380dd06f2bdea0b81`
**Work package:** GOV-P0-04
**Branch:** `codex/GOV-P0-04-docket-v04`
**Substrate commit:** `7834c48f84c01be8a03cf00380dd06f2bdea0b81`
**Substrate tree:** `6988941a5afacd3ea2ca6d0dd62f3ff8ebf4c256`
**Prerequisite receipt:** EVD-GOV-010 `ACCEPT_EXACT_SHA` at `a5d89b28884440b4185237986b207411678a40ed` for v0.3 candidate `65da2fb3deec1684d07f184f8c06a773ac36b504`
**Evidence status:** `SIGNED_STATE_CANDIDATE`; independent exact-SHA review pending

## Atomic result

PG-G0-AUTH-001 v0.4 encodes exactly the five operator-approved B8 dispositions from `SIGNING-PASS-3.md` at `2026-07-23T09:14:00+07:00`, with decision references and final-authority/concurrence actor blocks resolved through the identity register at the signed substrate. Existing v0.3 signed outcomes and Batch 2 provenance are preserved; no signed outcome is rewritten.

The rebound inventory contains 46 exact substrate records. Readiness deterministically computes `ready_for_pg_g0_gate_decision: true` with zero validation errors. B9 `PASS_PG_G0` is surfaced as `PENDING` and ineffective, with a fresh independent-conformance receipt explicitly required before any final disposition. No B9 signature, merge, release, runtime or production authority is asserted.

## Fail-closed review controls

- Schema and validator require v0.4 bindings, exact inventory regeneration, immutable B8 subjects/outcomes, and identity-register provenance.
- B9 rejects any final actor or effective disposition until its independent-conformance prerequisite is bound.
- Unknown fields, altered signed outcomes, stale digests, fabricated actors and readiness regressions fail closed.
- The candidate SHA is intentionally not self-asserted in this evidence; Claude must issue a new receipt against the final exact commit and tree. EVD-GOV-010 remains bound only to v0.3.

## Handoff boundary

Claude's independent review must verify the final commit's parent is `7834c48f84c01be8a03cf00380dd06f2bdea0b81`, rerun the validator/test chain, and issue a new exact-SHA receipt. Human disposition of B9 remains separate and unsigned.

## Append-only RF-001/RF-002 remediation disposition

EVD-GOV-012 rejected this candidate only for coverage accounting and an unreproduced order-sensitive manifest claim. The B8 encoding, B9 staging and readiness result remain unchanged. The 33 removed predecessor tests are itemized in `docs/work-packages/GOV-P0-04.md` (items 1-33), each marked obsolete under v0.4 semantics or mapped to an equal-or-stronger maintained control. A new repeatability/order-stability test was added for RF-002. In a fresh exact checkout of this candidate, full unittest discovery completed 143/143 with no stale-manifest failure, and the root validator passed on repeated calls. EVD-GOV-012 remains an immutable `REJECT`; this note does not upgrade it.

Itemized RF-001 names: 1 `test_committed_file_mock_prefers_temp_fixture_over_repository_file`; 2 `test_missing_docket_fails_closed`; 3 `test_missing_or_duplicate_decision_fails_closed`; 4 `test_unknown_top_level_field_fails_closed`; 5 `test_unknown_nested_decision_field_fails_closed`; 6 `test_malformed_commit_and_wrong_tree_fail_closed`; 7 `test_stale_artifact_hash_fails_closed`; 8 `test_append_only_governing_artifact_rewrite_fails_closed`; 9 `test_post_bound_mutation_cannot_be_hidden_by_rewriting_docket_hashes`; 10 `test_subject_must_match_exact_governing_artifact_map`; 11 `test_agent_cannot_be_final_human_authority`; 12 `test_pending_decision_cannot_claim_effect`; 13 `test_pending_concurrence_cannot_claim_actor`; 14 `test_self_reviewed_technical_acceptance_fails_closed`; 15 `test_normalized_technical_identities_cannot_bypass_self_review`; 16 `test_future_review_and_missing_evidence_fail_closed`; 17 `test_technical_acceptance_requires_distinct_resolved_candidate_and_bound_evidence`; 18 `test_technical_acceptance_rejects_repository_binding_as_candidate`; 19 `test_technical_acceptance_rejects_wrong_tree_and_unbound_evidence`; 20 `test_technical_acceptance_rejects_non_ancestor_candidate`; 21 `test_expired_decision_request_fails_closed`; 22 `test_terminal_reject_still_requires_human_independence_and_evidence`; 23 `test_five_b8_decisions_cannot_be_changed_by_signed_state_successor`; 24 `test_fabricated_identity_binding_fails_without_approved_registry_record`; 25 `test_identity_binding_hash_tree_status_and_structured_record_must_match`; 26 `test_delegation_ref_and_bound_record_must_match`; 27 `test_delegation_bound_hash_and_structured_scope_must_match`; 28 `test_delegation_grantor_requires_explicit_action_and_subject_scopes`; 29 `test_revoked_delegate_and_grantor_identities_fail_closed`; 30 `test_identity_validity_and_evidence_are_mandatory_and_well_formed`; 31 `test_delegation_scope_types_fail_closed_without_exceptions`; 32 `test_identity_evidence_must_exist_at_bound_commit`; 33 `test_nonconcur_requires_attributable_human_time_expiry_and_evidence`.
