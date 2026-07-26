# Proposal — `COMPLETE_PHASE` Authority Action Mapping

**Version:** 0.1-draft
**Status:** Draft proposal; ineffective — NOT an edit to the live authority matrix
**Owner:** Engineering Authority (authority-matrix owner)
**Issued:** 2026-07-25
**Work package:** GATE-P0-01 (Proposed; not accepted)
**Relates to:** [PG-P0-GATE-001](PG-P0-GATE-CONTRACT-DRAFT.md) criterion 4; the live
[AUTHORITY-MATRIX.json](registers/AUTHORITY-MATRIX.json); the identity register
[AUTHORITY-IDENTITY-REGISTER.json](registers/AUTHORITY-IDENTITY-REGISTER.json)

## The gap

The live authority matrix defines `APPROVE_GOAL`, `ACCEPT_WORK_ITEM`, `APPROVE_ARCHITECTURE`,
`ACCEPT_EVIDENCE`, `CERTIFY_MODULE`, `PROMOTE_SKILL`, `AUTHORIZE_RELEASE`,
`APPROVE_GOVERNANCE_BASELINE`, `APPROVE_PROGRAM_REGISTERS`, and `PASS_PG_G0` — but **no action
for completing or transitioning a program phase**. [PG-G0-GATE-001](PG-G0-GATE-CONTRACT-DRAFT.md)
already records this as unresolved: *"the live authority matrix has no `PASS_PROGRAM_GATE` action,
so the final gate action and authority remain unresolved."* Consequently PG-G0 completion and the
PG-P0 opening were recorded via ad-hoc operator signing records rather than a matrix-bound action,
and a `VERIFY-P0-01` authority check has no action to require.

## Proposed action (for human approval via `APPROVE_GOVERNANCE_BASELINE` / `APPROVE_PROGRAM_REGISTERS`)

Add one action to the authority matrix. Illustrative shape (final wording is the accountable
authority's to set):

```json
{
  "action_id": "COMPLETE_PHASE",
  "action_class": "program_phase_transition",
  "status": "draft",
  "accountable_human_authority": "Architecture Authority",
  "concurring_authorities": ["Product Authority", "Engineering Authority"],
  "final_decision_role": "Architecture Authority",
  "scope": "Transition an approved schedule-register entry ACTIVE -> COMPLETE against a signed Stage-1 completion mandate whose predecessor digest matches the current register.",
  "preconditions_ref": "docs/00-governance/PG-P0-GATE-CONTRACT-DRAFT.md",
  "expiry_policy": "per-decision effective window recorded in the signing envelope",
  "non_authorization": "Does not open the successor phase, authorize research gates, or authorize production implementation."
}
```

Then bind the action to the accountable identity by appending `COMPLETE_PHASE` to the
`action_ids` of the relevant entry in the identity register (e.g. `HUMAN-OPERATOR-001`, which
already holds the `Architecture Authority` role).

## What this proposal is NOT

- It does **not** modify `registers/AUTHORITY-MATRIX.json` or the identity register. Those are
  effective, signed surfaces; any change is a human `APPROVE_GOVERNANCE_BASELINE` /
  `APPROVE_PROGRAM_REGISTERS` act, recorded append-only.
- It does **not** sign, consume, apply, or verify any mandate, and it creates, holds, or
  distributes **no key material**. It only proposes an action *definition* for human approval.
- It does **not** grant, assume, or delegate authority, does not complete or transition any phase,
  does not open PG-P1, and does not authorize research or production.
- It is naming-illustrative: `COMPLETE_PHASE` vs `PASS_PROGRAM_GATE` and the exact concurrence
  set are the accountable authority's decision.

## Interaction with the verifier

Once approved and bound, a `VERIFY-P0-01` mandate would set `authority.required_action =
"COMPLETE_PHASE"` and `authority.required_role = "Architecture Authority"`; the verifier would
then confirm the signer identity holds both, is inside its validity window, and is not revoked —
otherwise it rejects with `AUTHORITY_DENIED`. Until the action exists and is bound, no real
completion mandate can pass verification.
