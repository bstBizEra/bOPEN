# Program Lifecycle Namespace and Crosswalk

**Version:** 0.1
**Status:** Draft
**Owner:** Architecture Authority
**Issued:** 2026-07-21
**Work package:** GOV-P0-01
**Governing artifact:** BOPEN-GOAL-001 (Draft)

## Purpose

Prevent status leakage between similarly named program, roadmap, bootstrap, research and work-package lifecycle tokens. This document adds presentation aliases only; it does not rename or supersede existing IDs.

## Canonical namespaces

| Namespace | Canonical IDs | Existing presentation | Meaning |
|---|---|---|---|
| Program Goal | `PG-G0`, `PG-P0`–`PG-P4`, `PG-C0` | Goal v0.2 G0/P0–P4/C0 | Program outcome gates |
| Strategic roadmap | `RM-0`–`RM-4` | Roadmap Phase 0–4 | Sequencing and intent |
| Bootstrap | `BOOT-B0`–`BOOT-B7` | B0–B7 | Repository bootstrap exit gates |
| Research quality | `RES-G0`–`RES-G7` | BOPEN-RES-001 G0–G7 | Research/clean-room quality gates |
| Research execution | `RES-R0`, `RES-R1` | BOPEN-RES-001 R0/R1 | Evidence-production waves, not gates |
| Strategic outcomes | `OUT-01`–`OUT-08` | Outcomes 1–8 | Orthogonal measurable outcomes |

Existing `BOOT-P0-*`, `RES-P0-*` and `DEV-P0-*` work-package IDs are immutable. Their `P0` token means work-package wave P0; it is never evidence that `PG-P0` or `RM-0` passed.

## Non-equivalence rules

1. A status statement must identify namespace, ID, artifact/version, evidence SHA, disposition and deciding authority.
2. Bare `G0` and `P0` are invalid in new cross-namespace status assertions.
3. `BOOT-B7` closes only bootstrap and cannot authorize runtime implementation.
4. `RES-G7` alone cannot authorize runtime implementation; normative approvals, accepted contracts/tests and an accepted implementation work package remain required.
5. `RES-R0` and `RES-R1` are research waves, not program or release phases.
6. A passing status in one namespace shall not be inferred in another.
7. `PG-C0` is an independent assurance overlay, not roadmap Phase 5.

## Crosswalk

| Program gate | Primary roadmap relationship | Other prerequisites | Non-equivalence warning |
|---|---|---|---|
| PG-G0 | Mostly RM-0 | BOOT-B0–B7 evidence and approved program controls | Bootstrap evidence does not itself pass PG-G0. |
| PG-P0 | Mostly RM-1 | Repository/CI controls from RM-0 | DEV/BOOT/RES P0 work-package IDs are not PG-P0 proof. |
| PG-P1 | RM-1, RM-2 and entitlement portion of RM-3 | Approved tenant/authz/entitlement contracts | Draft fixtures are not runtime proof. |
| PG-P2 | Mostly RM-3 | Certified-module lifecycle | A draft manifest is not a certified module. |
| PG-P3 | Foundation portion of RM-4 | Approved shared-foundation contracts | Product placeholders are not shared foundations. |
| PG-P4 | Product-composition portion of RM-4 | bPro runtime and independent evidence | Conceptual composition is not reference-flow proof. |
| PG-C0 | No roadmap equivalent | Independent consolidated assurance | Cannot be issued by maker or self-review. |

## Current status tuple

`{ namespace: PROGRAM, id: PG-G0, artifact: BOPEN-GOAL-001 v0.2 Draft, evidence_sha: pending, disposition: NOT_READY, authority: Product/Architecture Authorities pending }`

This tuple is descriptive and non-authorizing.
