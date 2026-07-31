# Work-Package Register

| ID | Title | Status | Primary outcome |
|---|---|---|---|
| BOOT-P0-01 | Repository initialization and protections | Proposed | Create repository structure, protected governance files and branch-control evidence. |
| BOOT-P0-02 | AGENTS.md hierarchy | Proposed | Install and validate root/scoped agent rules. |
| BOOT-P0-03 | Documentation system | Proposed | Install document hierarchy, manifest, status, glossary and traceability. |
| BOOT-P0-04 | Control templates and registers | Proposed | Install ADR, decision, risk, evidence, exception and work-package controls. |
| BOOT-P0-05 | CI and validation | Proposed | Operationalize repository validation and governance tests. |
| BOOT-P0-06 | Security and supply chain | Proposed | Install secret/dependency/license review baseline and security owners. |
| BOOT-P0-07 | Research integration | Proposed | Integrate BOPEN-RES-001 without distributing upstream source. |
| BOOT-P0-08 | Ownership and review governance | Proposed | Activate CODEOWNERS and required reviews. |
| BOOT-P0-09 | Local development baseline | Proposed | Document environments, tooling and synthetic data policy. |
| BOOT-P0-10 | Normative architecture queue | Proposed | Initiate REQ/ARCH/TENANT/AUTHZ/ENT/MOD/PARTY/SEC drafts. |
| BOOT-P0-11 | First vertical-slice specification | Proposed | Specify principal -> tenant -> owner membership -> context -> authorization -> audit. |
| BOOT-P0-12 | Bootstrap exit gate | Proposed | Review B0–B7 and approve next execution phase. |
| [BOPEN-P1-001](BOPEN-P1-001-EXECUTION-PLAN.md) | Platform Kernel Vertical Slice execution plan | **IMPLEMENTED_UNVERIFIED** | Deliver principal -> tenant -> owner membership -> context -> authorization -> audit. |
| [BOPEN-P2-001](BOPEN-P2-001-EXECUTION-PLAN.md) | Membership & Enterprise Onboarding execution plan (`MILE-2.1`..`MILE-2.5`) | **IMPLEMENTED_UNVERIFIED** | Deliver invitation engine, membership state machine, tenant context switching, enterprise IdP/SCIM sync and delegated cross-tenant access. |
| [BOPEN-P3-001](BOPEN-P3-001-EXECUTION-PLAN.md) | Capability and commercial entitlement kernel execution plan (`WP-P3-00`..`WP-P3-07`) | **IMPLEMENTED_UNVERIFIED** — authorized `GO ON EVIDENCE` | Govern capability registration, entitlement decisions, usage metering, rate limiting, RLS, and evidence execution. |
| [BOPEN-P35-001](BOPEN-P35-001-EXECUTION-PLAN.md) | Phase 3.5 Runtime Realization (`WP-P35-01`..`05a`) | **IMPLEMENTED_UNVERIFIED** — accepted 2026-07-31, zero ballots | Persistence and tenant-scoped sessions, kernel HTTP surface, signed context token, API gateway, kernel authentication boundary. |
| [WP-P35-06](BOPEN-P35-006-SHARD-ROUTING.md) | Tenant placement routing | **Accepted, not started** — maker unassigned | Resolve a tenant to a connection target: dedicated database or shared RLS pool. |
| [BOPEN-P36-001](BOPEN-P36-001-EXECUTION-PLAN.md) | Phase 3.6 Tenant Privacy and Platform Observability (`WP-P36-01`..`03`) | **Proposed** — entry blocked on Security and Privacy review of `DEC-P35-CONTROL-PLANE` | Plane assignment, cross-plane integrity for 12 foreign keys, control-plane credential boundary, telemetry, disclosure. |

> **Status correction, 2026-07-31.** `BOPEN-P1-001`, `BOPEN-P2-001` and `BOPEN-P3-001` were
> recorded here as *Completed & Verified* and *GO ON EVIDENCE*. Both readings conflict with
> [`AGENTS.md` §20.2](../../AGENTS.md), the single operative gate register, which records all
> three as `IMPLEMENTED_UNVERIFIED`. No ballot has been cast on any work package in this
> repository (`python tools/check_ballot_attribution.py` — "no ballots recorded yet").
>
> The authorizations were real; the verification was not. "Verified" in this register meant a
> passing test suite, which `BOPEN-GOV-EBIV-001` §8 holds to be maker self-assessment carrying no
> verdict weight. Corrected rather than left, because a register that overstates completion is
> the drift `AGENTS.md` §20 exists to stop.
