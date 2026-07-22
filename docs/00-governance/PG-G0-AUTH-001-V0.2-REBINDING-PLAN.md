# PG-G0-AUTH-001 v0.2 Rebinding Plan

**Document ID:** PG-G0-AUTH-001-REBIND-PLAN
**Version:** 0.1
**Status:** Draft; non-effective
**Owner:** Engineering Authority
**Issued:** 2026-07-22
**Work package:** GOV-P0-04 (Proposed; not accepted)
**Governing artifacts:** BOPEN-GOV-001 Draft; PG-G0-AUTH-001 v0.1 Draft; DEC-0013 Proposed
**Evidence reference:** EVD-GOV-005
**Prepared by:** BST-Codex-Motor
**Source:** User-authorized Codex follow-up review of `203ed05162dccb2729d4c39e25050817384c3b4b`
**Effective:** false
**PG-G0 effect:** none

## Purpose

Define the bounded, reproducible sequence for preparing a v0.2 successor to the PG-G0 authority docket after the authority identity and matrix contracts are corrected and separately approved. This plan does not create the successor, approve an authority, dispose a decision, pass PG-G0 or authorize merge, release, deployment or production implementation.

## Preconditions

No rebinding work may begin until one immutable substrate commit contains all of the following and passes the repository checks:

1. An approved canonical authority identity register at `docs/00-governance/registers/AUTHORITY-IDENTITY-REGISTER.json`.
2. An approved authority matrix at `docs/00-governance/registers/AUTHORITY-MATRIX.json` containing the three proposed PG-G0 actions and the disposed `ACCEPT_WORK_ITEM` concurrence rule.
3. Approved schema revisions whose actor, identity, approval-provenance, evidence and delegation fields agree with the docket validator.
4. A disposed DEC-0013 and accepted work-package records, each with attributable human receipts.
5. Current program-readiness artifacts and document manifest.
6. Green focused tests, full tests, `npm run validate` and `git diff --check`.

The GOV-P0-04 candidate at `203ed05162dccb2729d4c39e25050817384c3b4b` does not meet these preconditions. EVD-GOV-005 records the exact-SHA `REJECT` verdict and the required corrections.

## Required contract corrections before activation

- Define one canonical meaning for `identity_provider` and `identity_subject` across the identity-register schema, the docket schema and the validator. The current docket contract requires provider `bopen-authority-identity-registry` and a `HUMAN-*` subject, while the proposal uses `google` and an email address.
- Require non-null `approved_by`, `approved_at` and `approval_ref` when register status is `approved`; require them to be null while status is `draft`.
- Require at least one bound evidence reference for an approved authority record.
- Define delegated-authority fields consistently with the docket validator, including grantor delegation scopes and revocation state.
- Add semantic tests that prove an approved identity record can authorize every intended action/subject pair and that malformed or incomplete approval records fail closed.
- Release compatible v0.2 authority-matrix and docket schema identifiers; do not make validators accept arbitrary versions.

## Rebinding sequence

### R0 — Freeze the approved substrate

After the preconditions pass, commit the approved canonical inputs without a v0.2 docket mutation. Record the immutable substrate commit SHA and tree SHA. Every v0.2 artifact digest must be calculated from `git show <substrate-sha>:<path>`, not from mutable worktree bytes.

### R1 — Build a binding inventory

Create a deterministic inventory containing, at minimum:

- BOPEN-GOV-001;
- BOPEN-GOAL-001;
- DEC-0007, DEC-0010 and DEC-0013;
- GOV-P0-01 through GOV-P0-04;
- EVD-GOV-001 through EVD-GOV-005;
- the approved authority matrix;
- the approved authority identity register;
- the seven approved program registers;
- the docket and matrix schema versions used by the successor.

For each item record artifact ID, version, status, repository path and SHA-256 at the substrate commit. Reject duplicate IDs, missing paths, mutable references and worktree-only files.

### R2 — Prepare the v0.2 successor

Prepare `PG-G0-AUTH-001` v0.2 in a successor commit that binds the R0 substrate commit/tree. Do not attempt a self-referential binding to the commit that contains the successor docket. Preserve the five decision IDs unless an approved decision explicitly changes their set. Keep all undecided dispositions pending and ineffective.

The successor must:

- bind the approved authority matrix as its effective authority source;
- include the approved identity register as an approved governing artifact;
- bind every decision subject and concurrence source to the substrate commit/tree;
- preserve `production_implementation_authorized: false`, `merge_authorized: false`, `release_authorized: false` and `deployment_authorized: false`;
- remain `DRAFT` or `PENDING_HUMAN_DECISIONS` until its own independent technical review and all human receipts are valid;
- replace obsolete blocker text with deterministic blockers derived from current state.

### R3 — Update validator and fixtures together

In the same candidate as the v0.2 schema/instance change:

- teach `validate_pg_g0_authority_docket.py` the exact v0.2 schema and action set;
- retain v0.1 validation for historical evidence or explicitly mark v0.1 superseded;
- validate the identity register against its schema, including approval-state coupling;
- resolve committed-file test fixtures from their temporary root before the live repository root;
- add negative tests for stale substrate hashes, identity-provider/subject mismatch, missing approval provenance, missing evidence, duplicate identities and invalid delegation scope;
- regenerate deterministic readiness reports and the required document manifest.

### R4 — Independent exact-SHA review

A checker who did not make the v0.2 candidate must review its exact commit and tree. The receipt must enumerate commands, exit codes, artifact hashes and any residual findings. `ACCEPT_EXACT_SHA` is technical evidence only and cannot activate the docket.

### R5 — Human dispositions

Only after R4 may attributable humans record the separately authorized preparation, activation and PG-G0 decisions. Each receipt must bind the exact action, subject, authority identity, concurrence, evidence, effective time, expiry and revocation channel. A single technical-access credential, agent statement, CI result or repository approval is insufficient.

## Required validation matrix

| Check | Required result |
|---|---|
| Identity-register schema and semantic tests | Approved/draft coupling and actor compatibility pass |
| Authority-matrix schema and semantic tests | Exact v0.2 actions and concurrence policy pass |
| Docket focused suite | All positive and negative cases pass |
| Full unittest discovery | Pass |
| `npm run validate` | Exit 0 |
| `git diff --check` | Exit 0 |
| Independent exact-SHA review | `ACCEPT_EXACT_SHA` before human activation |

## Rollback and non-effects

Before activation, rollback is deletion of the isolated candidate branch/worktree. The v0.1 docket and all approved substrate artifacts remain immutable. No step in this plan authorizes protected-branch mutation, force-push, merge, release, deployment, production implementation or PG-G0 passage.
