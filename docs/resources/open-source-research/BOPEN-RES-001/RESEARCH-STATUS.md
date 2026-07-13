# Research Status

**As of:** 2026-07-13

**Overall status:** `R0 EXECUTED / G0-G2 PASS WITH CONDITIONS`

**Primary target:** BoxyHQ SaaS Starter Kit  
**Pinned commit:** `abc9b686823cbfb4973c79bc36fea37a3244be6c`

| Area | Status | Evidence |
|---|---|---|
| Artifact charter | Complete | `BOPEN-RES-001.md` |
| Repository identified | Complete | `boxyhq/saas-starter-kit` |
| Repository status checked | Complete | Public, not archived at baseline |
| Commit pin established | Complete | `abc9b686823cbfb4973c79bc36fea37a3244be6c` |
| License baseline | Independently checksum-verified; legal review pending | Apache-2.0, SHA-256 recorded in pin contract |
| Clone scripts | Executed and hardened | Credential prompting disabled; expected hashes fail closed |
| Runtime reproduction | Reproduced by ENGIN and REV | Same seven-command exit matrix in separate workspaces |
| Repository structure study | Prepared | `01-boxyhq/repository-structure-study.md` |
| Lifecycle trace | Initial evidence captured | `01-boxyhq/lifecycle-map.md` |
| Authorization trace | Initial evidence captured | `01-boxyhq/authorization-analysis.md` |
| Entitlement trace | Initial gap finding | `01-boxyhq/entitlement-commercial-analysis.md` |
| Security review | Prepared | `01-boxyhq/security-review-checklist.md` |
| Clean-room handoff | Blocked | Requires G0-G6 completion |

## Current blockers

- Legal review must confirm obligations for any intended redistribution or derivative use.
- Runtime-level context resolution and SSO/directory-sync flows require execution evidence.
- npm 11 rejects the pinned package-lock; R0 reproduction requires npm 10.9.2.
- The pinned upstream format check fails on 300 files; this is recorded upstream evidence, not corrected in bOPEN.

## Next controlled action

Begin Sprint R1 with `RES-P0-04` through `RES-P0-07`: repository orientation, identity/principal, tenant/membership and invitation lifecycle traces. Preserve G3 as open until positive and negative runtime evidence is reviewed.

## R1 update - 2026-07-13

**Status:** `R1 STATIC TRACE EXECUTED / G3 OPEN`

- RES-P0-04 is complete at E2 with a machine-verified path inventory.
- RES-P0-05 and RES-P0-06 traces are complete, but runtime acceptance remains partial.
- RES-P0-07 trace is complete, but its end-to-end, event/audit, replay and concurrency acceptance is not satisfied.
- Two external operators reproduced 56 case-specific evidence records, including 46 observations and 10 gap anchors, plus 42 static test declarations in 9 tracked files without executing upstream code.
- EVD-RES-003 records the identity, owner-invariant, invitation-state and event/audit findings.

**Next controlled action:** design the isolated synthetic G3 runtime pack. Do not start RES-P0-08 or production implementation until the missing R1 runtime evidence is executed and reviewed.
