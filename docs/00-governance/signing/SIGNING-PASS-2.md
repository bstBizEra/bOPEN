# PG-G0 Signing Pass 2 — Pending Human Dispositions

**Version:** 0.1
**Status:** Prepared; unsigned
**Prepared by:** BST-Codex-Motor
**Operator:** `HUMAN-OPERATOR-001`
**Prepared:** 2026-07-22T23:45:00+07:00
**Substrate commit:** `26bea090c0aca14f1337c4be1a146fd48bb1f626`
**Substrate tree:** `8789c5e70c2ce87298928d4d02add7ffe5867402`
**Docket target state:** `PENDING_HUMAN_DECISIONS`
**Signed:** false

## Purpose

Present the Batch 2 disposition surfaces prepared by the PG-G0-AUTH-001 v0.2 rebinding candidate. This document contains no operator signature, concurrence, decision timestamp or effective outcome. Each disposition MUST remain `PENDING` until the operator signs it after independent exact-SHA review of the complete candidate.

## Pending surfaces

| Batch item | Action | Subject | Requested state |
|---|---|---|---|
| B2 | APPROVE_GOVERNANCE_BASELINE | BOPEN-GOV-001 | Approved |
| B2 | APPROVE_PROGRAM_REGISTERS | AUTHORITY-MATRIX v0.2 | Approved |
| B2 | APPROVE_GOVERNANCE_BASELINE | DEC-0013 | Accepted |
| B3 | APPROVE_PROGRAM_REGISTERS | GOAL, AGENT, MODULE, SKILL, SCHEDULE and TECHNOLOGY-DECISION-ASSIGNMENTS registers | Approved |
| B4 | ACCEPT_WORK_ITEM | GOV-P0-01 and GOV-P0-04 | Accepted |
| B5 | APPROVE_ARCHITECTURE | DEC-0007 / BOOT-B7 | Approved |
| B6 | APPROVE_GOVERNANCE_BASELINE | GOV-P0-03 root-control package | Active through an atomic append-only activation event |

The existing five docket decisions `PG-G0-DEC-001` through `PG-G0-DEC-005` remain separately pending for B8. `PASS_PG_G0` remains separately pending for B9 and cannot be prepared as effective until the readiness and independent-conformance gates pass.

## Signing prerequisites

1. The v0.2 candidate has an independent `ACCEPT_EXACT_SHA` receipt.
2. The exact candidate commit and tree are recorded in the signing record.
3. Each disposition records the required final authority, concurrence, evidence, effective time, expiry and revocation channel.
4. Root-control activation is appended to all five ledgers atomically with identical signed fields; no genesis bytes are rewritten.
5. `PG-G0`, production implementation, merge, release, deployment and runtime activation remain false unless separately authorized by their own gate.

## B6 activation record template — not signed

The following block may be appended to each root ledger only after the prerequisites pass and the operator explicitly signs B6:

```markdown
## Root control activation event

**Activation status:** Active
**Activation lifecycle:** Active
**Activated by:** HUMAN-OPERATOR-001
**Activated at:** <signed RFC3339 timestamp>
**Activation decision ref:** docs/00-governance/signing/SIGNING-PASS-2.md#B6
**Activation evidence ref:** docs/00-governance/signing/SIGNING-PASS-2.md
**Activation substrate commit:** 26bea090c0aca14f1337c4be1a146fd48bb1f626
```

## Non-effects

This prepared surface does not approve BOPEN-GOV-001 or DEC-0013, approve a register, accept GOV-P0-01 or GOV-P0-04, approve BOOT-B7, activate a root ledger, dispose B8, pass B9/PG-G0, merge, release, deploy or authorize production implementation.
