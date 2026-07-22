# EVD-GOV-005 — Independent Review of GOV-P0-04 Candidate

**Version:** 0.1
**Status:** Draft technical evidence
**Work package:** GOV-P0-04 (Proposed; not accepted)
**Generated:** 2026-07-22
**Maker under review:** Claude (BST-SA Motor worker agent)
**Independent checker:** BST-Codex-Motor
**Checker independence:** Different agent runtime and session; the checker authored none of the reviewed commit.
**Candidate commit SHA:** `203ed05162dccb2729d4c39e25050817384c3b4b`
**Candidate tree SHA:** `24d100482b39d42bb99a84ccd97e63d647d763ad`
**Candidate parent SHA:** `a29ec1d8ab28d38621dc4db176b7b2abf2ea44cb`
**Candidate branch:** `claude/GOV-P0-04-authority-identity-surfaces`
**Review worktree:** `C:\laragon\www\bopen-worktrees\gov-p0-04-review-203ed05`
**Verdict:** `REJECT` (exact-SHA technical receipt)

## Scope

The review covers the seven files introduced by the candidate, the repository validation chain, the authority-docket actor/identity boundary, the disclosed test-fixture defect and the requested v0.2 rebinding plan. The verdict applies only to the immutable candidate SHA above.

## Candidate check results

| Command | Exit | Result |
|---|---:|---|
| `python -m unittest tests.governance.test_pg_g0_authority_docket` | 0 | 44 tests passed |
| `python -m unittest discover -s tests -p "test_*.py"` | 0 | 160 tests passed |
| `npm run validate` | 1 | Failed: `docs/manifests/GOV-P0-02-DOCUMENT-MANIFEST.json` stale |
| `python tools/validate_root_control_surfaces.py` | 0 | 5 root controls and 11 package files passed |
| `python tools/validate_pg_g0_authority_docket.py --check` | 0 | Current v0.1 docket valid and `NOT_READY` |
| `python tools/check_clean_room.py` | 0 | Passed |
| `python tools/check_secrets.py` | 0 | Passed |
| `python tools/check_supply_chain.py` | 0 | Passed |
| `git diff --check 203ed05^ 203ed05` | 0 | Passed |

## Reject findings

### GOV-P0-04-RF-001 — Required repository validation fails

The candidate adds six controlled documents plus one contract but does not refresh the versioned document manifest required by `npm run validate`. This contradicts the work package acceptance criterion that the repository validation checks remain green. Passing unit tests does not override the failing repository check.

### GOV-P0-04-RF-002 — Proposed identity records cannot satisfy the docket actor contract

The proposed record uses `identity_provider: "google"` and `identity_subject: "ounkhamvilay@gmail.com"`. The existing docket actor schema requires provider `bopen-authority-identity-registry` and an identity subject matching `HUMAN-*`; the validator requires the registry record to match those actor fields. Either actor shape therefore fails: using the proposal values violates the docket schema, while using the docket values does not match the proposed record.

The proposed entry also has no evidence references. The docket validator requires identity-role-binding evidence to exist at the bound commit for a terminal authority decision. Following the operator packet's Step 1 literally would therefore not produce a usable authority record.

### GOV-P0-04-RF-003 — Approved state is not fail-closed in the new schema

The identity-register schema allows `status: "approved"` while `approved_by`, `approved_at` and `approval_ref` remain null. It also allows an approved entry with an empty evidence list. The candidate's claim that the schema is fail-closed is therefore not established. Approval-state coupling and semantic negative tests are required before adoption.

### GOV-P0-04-RF-004 — Delegation representation is inconsistent

The new schema exposes `authority_mode: "DELEGATED"` but does not model the grantor delegation scopes and evidence that the docket validator enforces. Its `additionalProperties: false` entry shape would reject the validator's existing grantor fields. The schema and validator must be reconciled before a v0.2 docket can safely depend on the register.

## Required corrections

1. Align authority identity semantics across the register schema, docket schema, instance and validator.
2. Add status-dependent approval provenance and evidence constraints with negative tests.
3. Define one complete delegated-authority record model or remove `DELEGATED` from this revision.
4. Refresh the required manifest and prove `npm run validate` exits 0.
5. Subject the corrected candidate to a new independent exact-SHA review; this receipt cannot be upgraded in place.

## Authorized follow-up completed in this review branch

- Correct the docket test helper so temporary fixture files take precedence over live repository files.
- Add a regression test with a conflicting live-repository decoy.
- Draft `PG-G0-AUTH-001-V0.2-REBINDING-PLAN.md` without creating or activating a successor docket.
- Refresh the deterministic manifest required by the repository validation command.

These repairs do not change the `REJECT` verdict for `203ed05`; a new candidate SHA requires a new receipt.

## Decision boundary

This is independent technical evidence only. It does not accept GOV-P0-04, approve DEC-0013, approve an identity or authority matrix, activate governance, pass PG-G0, authorize protected-branch mutation, merge, release, deployment or production implementation.

## Self-certification

```yaml
self_certification:
  agent_id: BST-Codex-Motor
  peer_agent_id: Claude BST-SA Motor
  certification_scope: advisory_only
  execution_authority: false
  approval_authority: false
  candidate_verdict: REJECT
  ready_for_maker_correction: true
```
