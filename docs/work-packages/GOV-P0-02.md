# GOV-P0-02 — PG-G0 Authority Docket and Approval Envelope

**Version:** 0.1
**Status:** Proposed; not accepted
**Owner:** Engineering Authority
**Authorization source:** User direction to proceed; BOPEN-BOOT-001 documentation and contract drafting authority only
**Accepted by/at:** Pending attributable Human Engineering Authority disposition
**Lifecycle:** PG-G0 proposal; no gate passage
**Dependencies:** GOV-P0-01 at `c893062c197e74c15214e5ce1c425b9e9ed8002f`; BOOT-P0-12/DEC-0007; DEC-0010
**Governing artifacts:** Supplied Program Goal v0.2; BOPEN-GOAL-001 Draft; BOPEN-GOV-001 Draft
**Maker:** Codex root proposal maker
**Checker:** Independent exact-SHA checker pending
**Branch/worktree:** `codex/GOV-P0-02-authority-docket` / `C:\laragon\www\bopen-worktrees\gov-p0-02-authority-docket`
**Allowed paths:** `contracts/governance/`, `docs/`, `tools/validate_pg_g0_authority_docket.py`, `tests/governance/test_pg_g0_authority_docket.py`, package/CI validation surfaces and the dedicated validation artifact
**Prohibited paths:** `apps/`, `services/`, `packages/`, `infrastructure/`, migrations, runtime configuration, production data, research execution and secrets
**Base SHA:** `c893062c197e74c15214e5ce1c425b9e9ed8002f`
**Base tree:** `f336976981c9b7e95c96ec8289589e53c1ac506c`
**Expiry:** 2026-08-21T00:00:00+07:00

## Objective

Prepare a strict, reviewable and non-effective authority docket for the five PG-G0 decisions that map to actions in the live draft authority matrix. The package must expose missing authority actions and instruction surfaces rather than inferring them.

## In scope

- a draft, versioned PG-G0 authority-docket schema and pending instance;
- exact artifact, commit, tree and SHA-256 bindings;
- human-only final authority and concurrence records;
- deterministic fail-closed validation and negative tests;
- a proposed DEC-0012 instruction-surface and generated-manifest decision;
- append-only status, traceability, evidence and work-package routing;
- an independently reviewed technical evidence envelope.

## Out of scope

Accepting this package; approving DEC-0007, DEC-0010, BOPEN-GOAL-001 or BOPEN-GOV-001; approving registers; creating human identities or delegations; assigning technology checkers or dates; passing PG-G0; merging PRs; runtime execution; release; deployment; production implementation.

## Deliverables

1. `pg-g0-authority-docket.schema.json` and pending `PG-G0-AUTH-001.json`.
2. Human-readable authority docket and draft gate-decision contract.
3. Deterministic validator, negative tests and readiness artifact.
4. DEC-0012 proposal for unresolved exact-path and manifest rules.
5. EVD-GOV-002 and append-only traceability/status updates.

## Acceptance criteria

- only live authority-matrix action IDs are used;
- missing governance/register/gate action mappings remain blockers;
- every effective final authority or concurrence actor must be a bound human identity;
- maker, checker and final authority cannot collapse into self-review;
- exact commit/tree and file SHA-256 mismatches fail closed;
- pending records cannot claim actors, evidence or effect;
- all five missing instruction paths are disclosed until a human decision designates or creates them;
- current output is `NOT_READY`, PG-G0 false and production implementation false;
- a different checker accepts the exact final SHA;
- no technical verdict is represented as human approval.

## Required checks/evidence

Full Python suite; contract validation; repository, clean-room, secret and supply-chain checks; deterministic authority-docket report check; versioned document-manifest snapshot; `git diff --check`; exact-SHA EVD-GOV-002 checker receipt.

## Stop conditions

Stop if an approval identity is invented, a draft action is treated as effective, an absent action ID is fabricated, the package attempts to pass PG-G0, a governed artifact changes after its bound SHA-256, scope enters runtime code, or a human authority disposition is inferred from CI/PR/agent evidence.

## Risks and rollback

Risk: a populated JSON field is mistaken for authenticated authority. Control: the draft schema forces all effective outcome and authority flags false; the validator treats the draft matrix and unauthenticated identities as ineffective. Rollback: remove the isolated proposal branch/worktree; no runtime or protected-branch state is changed.

## Extend-only change note

Reason: GOV-P0-01 exposed source-complete controls but no attributable approval envelope. Benefit of the old phase: it preserved exact draft artifacts and fail-closed readiness. Expected outcome: Human Engineering Authority receives a bounded proposal that can be accepted, rejected or revised without silently promoting any gate.

## Completion record

Maker draft implementation and local validation are complete. Exact-SHA technical checker verdict and Human Engineering Authority acceptance remain pending. This proposed package cannot accept itself.

## Append-only allowed-path clarification — 2026-07-21

Reason: exact-SHA review found that the original bounded-path statement described package and CI validation surfaces generically but did not explicitly name three files changed to route the proposal and preserve its generated evidence: `.gitignore`, `README.md`, and `tools/generate_document_manifest.py`. Benefit of the old phase: the original statement constrained work to governance documents, contracts, validation and evidence and correctly prohibited every runtime and production zone. Expected outcome: the proposal's declared scope now matches the exact candidate diff without broadening authority beyond documentation, deterministic manifest handling and validation.

The three additional allowed paths are exactly `.gitignore`, `README.md`, and `tools/generate_document_manifest.py`. This clarification does not accept GOV-P0-02, authorize further root-file changes, or change any human, gate, merge, release, runtime or production disposition.
