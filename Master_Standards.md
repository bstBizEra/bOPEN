# bOPEN Root Standards Locator

**Document ID:** GOV-P0-03-ROOT-STANDARDS
**Version:** 0.1
**Status:** Draft
**Lifecycle:** Inactive
**Owner:** Architecture and Engineering Authorities
**Issued:** 2026-07-21
**Last appended:** 2026-07-21
**Governing artifacts:** AGENTS.md; BOPEN-BOOT-001; GOVERNANCE.md; BOPEN-GOV-001 Draft
**Dependent artifacts:** Roadmap.md; Progress_Log.md; Backlog.md; Recap_Today.md
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

This file is a locator and precedence map. It does not create a new normative standard, approve a draft artifact, or replace a higher-precedence source.

## Source-of-truth order

1. Current explicit user instruction.
2. Applicable `AGENTS.md`, deepest scope first.
3. Approved normative artifacts.
4. Approved ADRs and versioned contracts.
5. Accepted work packages.
6. Implementation and reproducible evidence.
7. Informal notes.

The live repository sources remain [AGENTS.md](AGENTS.md), [GOVERNANCE.md](GOVERNANCE.md), [BOPEN-BOOT-001.md](BOPEN-BOOT-001.md), and the controlled documents under `docs/`.

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

| Required path | State | Handling |
|---|---|---|
| `/opt/bizera-smartthink/config/agents.yaml` | UNRESOLVED_EXTERNAL_DEPENDENCY | Do not invent agent identities, roles or resource limits. |
| `/opt/bizera-smartthink/config/routing.yaml` | UNRESOLVED_EXTERNAL_DEPENDENCY | Do not invent routing or activation rules. |
| `/opt/bizera-smartthink/config/system.yaml` | UNRESOLVED_EXTERNAL_DEPENDENCY | Do not invent system or deployment values. |

## Append-only genesis event

**Event ID:** GOV-P0-03-STANDARDS-0001
**Timestamp:** 2026-07-21T00:00:00+07:00
**Reason:** DEC-0012 identified that the exact root standards path was absent while instruction-level global configuration sources were unavailable.
**Benefit of old phase:** Existing scoped governance documents continued to preserve approved boundaries without fabricating missing global configuration.
**Expected outcome:** Agents receive an exact-path locator that fails closed on missing external configuration and preserves source precedence.

Future changes must append new dated events. Existing bytes, events and dependency history must not be rewritten.

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

## SKEL-P0-01 maker candidate event

**Work package:** SKEL-P0-01
**Phase:** PG-P0
**Maker:** Claude (claude-opus-4-8), sole maker
**Candidate base commit:** 29949f460345a55b8f8079cad802d6ca85cbe46e
**Evidence ref:** docs/evidence/EVD-SKEL-002-skeleton-maker-candidate.md
**Candidate status:** Proposed; not accepted
**Scope:** Production implementation, migration, merge, release, deployment and runtime remain unauthorized.
