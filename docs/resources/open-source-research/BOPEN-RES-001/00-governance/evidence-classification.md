# Evidence Classification

## Evidence levels

| Level | Definition | Permitted use |
|---|---|---|
| E0 | Unverified lead, issue, discussion or memory | Search guidance only |
| E1 | Upstream documentation statement | Scope hypothesis and setup guidance |
| E2 | Source/schema/config observation at pinned commit | Supports technical finding |
| E3 | Reproduced runtime or automated-test result | Supports behavioral finding |
| E4 | Triangulated code + runtime + test evidence | Supports normative requirement proposal |
| E5 | Reviewed and approved architecture decision | Clean-room implementation input |

## Confidence

Use `LOW`, `MEDIUM`, `HIGH` and explain uncertainty. Evidence quantity does not replace relevance.

## Observation vs inference example

**Observation (E2):** `createTeam` creates a `Team`, then upserts `TeamMember` with role `OWNER`.

**Inference:** bOPEN tenant provisioning should create an owner membership in the same orchestration boundary.

**Decision status:** proposed until transaction, failure and lifecycle requirements are approved.
