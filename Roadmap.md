# bOPEN Root Roadmap Control

**Document ID:** GOV-P0-03-ROOT-ROADMAP
**Version:** 0.1
**Status:** Draft
**Lifecycle:** Inactive
**Owner:** Product and Architecture Authorities
**Issued:** 2026-07-21
**Last appended:** 2026-07-21
**Governing artifacts:** BOPEN-BOOT-001; BOPEN-GOAL-001 Draft; BOPEN-GOV-001 Draft
**Dependent artifacts:** Master_Standards.md; Progress_Log.md; Backlog.md; Recap_Today.md
**Decision reference:** DEC-0012 option 1 user-level drafting authorization
**Work package:** GOV-P0-03 (Draft; not accepted)
**Evidence reference:** EVD-GOV-003
**Source:** Explicit user-level instruction in the current Codex task
**Agent ID:** /root/gov_p0_03_preflight
**Base commit:** 82ed6b38b118aab14a9961c5d75a33e515cb136a
**Base tree:** cad6b595fb74a70cc706a78d45778e15524aebd9
**Append-only:** true
**PG-G0 passed:** false
**Production implementation authorized:** false
**Merge authorized:** false
**Release authorized:** false

This file is a non-normative root locator. It does not replace the controlled roadmap in `docs/01-product/roadmap.md`, approve a phase, or create implementation authority.

## Current bounded state

| Namespace | State | Effective scope |
|---|---|---|
| PROGRAM / PG-G0 | NOT_READY | Draft governance preparation only |
| ROADMAP / RM-0 | ACTIVE_WITH_LIMITS | Documentation, research, contracts, tests and evidence only |
| BOOT / B7 | PENDING | Human Architecture Authority review required |
| PRODUCTION | UNAUTHORIZED | No runtime implementation, activation, release or deployment |

## Root control links

- [Roadmap.md](Roadmap.md)
- [Master_Standards.md](Master_Standards.md)
- [Progress_Log.md](Progress_Log.md)
- [Backlog.md](Backlog.md)
- [Recap_Today.md](Recap_Today.md)
- [README.md](README.md)
- Work package: [GOV-P0-03](docs/work-packages/GOV-P0-03.md)
- Evidence: [EVD-GOV-003](docs/evidence/EVD-GOV-003-root-control-surfaces.md)

## Global configuration dependencies

The instruction-level configuration paths `/opt/bizera-smartthink/config/agents.yaml`, `/opt/bizera-smartthink/config/routing.yaml`, and `/opt/bizera-smartthink/config/system.yaml` are `UNRESOLVED_EXTERNAL_DEPENDENCY`. No values are inferred or hard-coded from them.

## Append-only genesis event

**Event ID:** GOV-P0-03-ROADMAP-0001
**Timestamp:** 2026-07-21T00:00:00+07:00
**Reason:** DEC-0012 identified that the required exact root roadmap path was absent.
**Benefit of old phase:** The controlled `docs/` roadmap preserved the established bootstrap record and remained authoritative within its approved scope.
**Expected outcome:** Agents can locate the current bounded phase state from the exact required path without treating this locator as a phase approval.

Future changes must append new dated events. Existing bytes, events and state history must not be rewritten.

## Root control activation event

**Activation status:** Active
**Activation lifecycle:** Active
**Activated by:** HUMAN-OPERATOR-001
**Activated at:** 2026-07-23T00:45:00+07:00
**Activation decision ref:** docs/00-governance/signing/SIGNING-PASS-2.md#B6
**Activation evidence ref:** docs/00-governance/signing/SIGNING-PASS-2.md
**Activation substrate commit:** 26bea090c0aca14f1337c4be1a146fd48bb1f626

## PG-G0 gate passage event

**Gate passage status:** PASSED
**Gate passage lifecycle:** PG-P0 OPEN
**Passed by:** HUMAN-OPERATOR-001
**Passed at:** 2026-07-24T00:20:36+07:00
**Gate decision ref:** docs/00-governance/signing/SIGNING-PASS-4.md#signed-gate-decision
**Gate evidence ref:** docs/evidence/EVD-GOV-015-docket-v04-remediation-v3-acceptance.md
**Gate substrate commit:** 7995d171ccaf43074155828c6a6bcca5c75d8359

## PG-P0 preparation transition event

**Transition:** READY_FOR_AUTHORITY_REVIEW -> ACTIVE
**Phase:** PG-P0
**Authorized by:** HUMAN-OPERATOR-001
**Authorized at:** 2026-07-24T01:15:27+07:00
**Decision ref:** docs/00-governance/signing/SIGNING-PASS-5.md#signed-decision
**Evidence ref:** docs/evidence/EVD-GOV-017-terminal-gate-passed-review.md
**Work package:** SKEL-P0-01 (proposed; not accepted)
**Scope:** Preparation and independent review only; production implementation, migration, merge, release and runtime remain unauthorized.
