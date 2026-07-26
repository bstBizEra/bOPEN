# PG-P0-GATE-001 — PG-P0 Completion Gate Decision Contract

**Version:** 0.1-draft
**Status:** Draft; ineffective
**Owner:** Architecture Authority (schedule entry owner for PG-P0)
**Issued:** 2026-07-25
**Work package:** GATE-P0-01 (Proposed; not accepted)
**Governing goal:** BOPEN-GOAL-001 v0.2 (Draft)
**Predecessor pattern:** [PG-G0-GATE-001](PG-G0-GATE-CONTRACT-DRAFT.md)

## Purpose

Define, fail-closed, the conditions under which program phase **PG-P0 ("Platform Skeleton")**
may be presented for a human completion decision (`ACTIVE → COMPLETE` in the approved schedule
register). No such definition exists today; without it, "PG-P0 is complete" is undefined and no
completion mandate can be defensibly signed. This contract is a **draft** and is **ineffective**:
it authorizes nothing and completes nothing.

## Candidate completion rule

PG-P0 may be presented for a human completion decision only when ALL of the following hold, each
evidenced by an attributable, effective envelope:

1. **Skeleton delivered and accepted.** The platform-skeleton work item(s) — at minimum
   `SKEL-P0-01` — carry a Human Engineering Authority `ACCEPT_WORK_ITEM` at an exact SHA, with
   independent exact-SHA review evidence, AND the repository status surfaces for those work items
   (e.g. the `SKEL-P0-01` work-package header) are reconciled with that acceptance record.
   *(Current observed state: an append-only Human Engineering Authority `ACCEPT_WORK_ITEM` record
   for `SKEL-P0-01` at `f1eea272` is encoded in the accepted head `73912e4`; however some status
   surfaces still read `Proposed; not accepted`. This unreconciled inconsistency is itself a
   `NOT_READY` condition under the dispositions below and MUST be resolved before disposition.)*
2. **Authorized-scope coverage.** Every item in the PG-P0 authorized scope of the phase-opening
   record ([SIGNING-PASS-5](signing/SIGNING-PASS-5.md)) is in its required terminal state for
   this phase (see the scope-boundary decision below): repository skeleton for the clean zones,
   draft contract shells traced to the eight normative artifacts, and test-harness scaffolding.
3. **Executable transition controls.** The signature-safe transition controls are executable and
   independently verified — deterministic recompute, RFC 8785 canonicalization, DSSE/authority
   verification, compare-and-swap anti-replay, single-use, invariant enforcement.
   *(Candidate: `VERIFY-P0-01`, independent `ACCEPT_EXACT_SHA`; human acceptance pending.)*
4. **Authority action resolved.** The approved authority matrix names the completion action and
   its accountable human authority, concurrences, and expiry, and that action is bound to the
   signing identity in the identity register (see [the companion proposal](AUTHORITY-MATRIX-COMPLETE-PHASE-PROPOSAL.md)).
5. **Trust root effective.** A governed trust root binds the signing key id to the accountable
   authority identity, OR the completion is recorded under the approved human attestation-record
   model; the chosen mechanism is stated and effective.
6. **Signed Stage-1 mandate.** A completion mandate exists that binds the predecessor schedule
   digest, the permitted transform, the transform-specification digest, and the declared
   invariants, and is signed by the accountable authority.
7. **Independent evidence accepted.** Independent exact-SHA review evidence for the successor
   register commit is accepted through an attributable `ACCEPT_EVIDENCE` envelope.
8. **Invariants preserved.** `PG-P1` remains `NOT_READY`; no signed PG-G0 outcome is altered;
   production implementation remains unauthorized; `docs/00-governance/**` signed surfaces are
   byte-unchanged except the single sanctioned register entry mutation.

## Scope-boundary decision (REQUIRES ARCHITECTURE AUTHORITY DECISION — unresolved)

Criterion 2 depends on an unresolved scoping decision that this draft does **not** presume to
settle. The phase-opening record placed *both* the eight normative drafts and BOPEN-RES-001 gates
G3+ inside PG-P0's authorized scope, yet those are also the entry conditions for PG-P1.

- **Option A — Skeleton-boundary completion.** PG-P0 completes when the skeleton + draft shells +
  test scaffolding are accepted; the eight normative artifacts remain `Draft` and BOPEN-RES-001
  G3–G7 graduate at the PG-P0 → PG-P1 boundary (i.e. they are *entry* conditions for PG-P1, not
  *exit* conditions for PG-P0).
- **Option B — Maturity-boundary completion.** PG-P0 completes only when the eight normative
  artifacts reach their required maturity and BOPEN-RES-001 G3–G7 are closed, so that entering
  PG-P1 is immediate.

Current observed state (evidence, not a disposition): the eight normative artifacts are `Draft —
no implementation authority`; BOPEN-RES-001 records "G3 through G7 remain open. No implementation
handoff is authorized."; readiness reports `Production implementation authorized: false`. Under
Option B, PG-P0 is **not** presently completable; under Option A it may be, pending criteria
1 and 3–7. The accountable Architecture Authority must select the boundary before this contract
can be finalized.

## Fail-closed dispositions

- Any missing, draft, expired, deferred, rejected, non-concurring, self-reviewed, unauthenticated,
  or unreconciled record for criteria 1–8 produces `NOT_READY`.
- `READY_FOR_HUMAN_COMPLETION_DECISION` is not `COMPLETE`.
- Only an effective human receipt under an approved successor contract may record a completion
  disposition; no agent, and no independent-review receipt, may complete PG-P0.
- PG-P0 completion would not by itself authorize production implementation, open PG-P1, or
  authorize BOPEN-RES-001 G3+ research; those remain separately gated.

## Current effectiveness

This contract is **Draft** and cannot complete PG-P0. The live authority matrix has **no
`COMPLETE_PHASE` (or `PASS_PROGRAM_GATE`) action**, so the completion action and its accountable
authority remain unresolved — the same unresolved-action condition recorded for PG-G0. The
scope-boundary decision above is also unresolved.

## Supersession rule

An approved successor must preserve this draft as historical evidence, record the Architecture
Authority's scope-boundary decision, add the missing completion-action mapping (via the companion
proposal or an equivalent approved register revision), define concurrence and expiry, state the
effective trust mechanism, and link the exact approval envelope.

## Non-authorization

This artifact asserts no authority. It does not complete PG-P0, does not sign, consume, apply, or
verify any mandate, does not mutate any register, and does not open PG-P1 or authorize research or
production. Human authorities remain accountable for every decision it describes.
