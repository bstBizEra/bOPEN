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
