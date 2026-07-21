# BOPEN-GOAL-001 — bOPEN Program Goal and Measurable Outcomes

**Version:** 0.2
**Status:** Draft
**Owner:** Product Authority
**Issued:** 2026-07-21
**Work package:** GOV-P0-01
**Source:** User-supplied `bOPEN Program Goal and Measurable Outcomes v0.2`
**Source SHA-256:** `e9ef66ba78ebc656dd613b835fabd568bff50ac2932ab07278b91526ac2125c0`
**Governing artifact:** BOPEN-BOOT-001 (documentation drafting authority only)
**Dependent artifacts:** BOPEN-REQ-001, BOPEN-ARCH-001, BOPEN-TENANT-001, BOPEN-AUTHZ-001, BOPEN-ENT-001, BOPEN-MOD-001, BOPEN-SEC-001

> This is a faithful controlled draft of the supplied program goal. It does not approve the goal, pass any program, bootstrap, roadmap, research or conformance gate, certify a module, authorize a release, or authorize production implementation.

## 1. Program goal

bOPEN shall establish a secure, reusable and governed multi-tenant business platform kernel that enables BST to build, deploy and operate multiple products, shared capabilities and industry modules without repeatedly rebuilding identity, tenancy, authorization, entitlement, audit, workflow, integration and operational foundations.

bOPEN shall enable bPro, bFleet, tourism, agriculture, property, insurance and future digital platforms to share a common architecture while maintaining strong tenant isolation, modular domain boundaries, consistent security and governance, controlled product composition, repeatable module delivery, measurable operational reliability, and traceable human and agent accountability.

The target operating model is:

```text
Governed Goal
-> Approved Requirement
-> Architecture Decision
-> Authorized Work Item
-> Isolated Implementation
-> Independent Verification
-> Evidence
-> Controlled Release
-> Operational Outcome
-> Verified Learning
-> Reusable Capability
```

## 2. North Star outcome

By completion of `PG-P4`, BST shall demonstrate that a new multi-tenant product or module can be registered, specified, implemented, verified, activated and operated on bOPEN without rebuilding the platform kernel or weakening tenant isolation.

### NS-01 — Certified Module Enablement Rate

```text
Certified Module Enablement Rate
= certified modules reaching pilot through the standard lifecycle
/ total modules submitted for pilot
* 100
```

An empty denominator is `not measurable`, never 100%. Partially implemented modules do not count as certified.

| Target ID | Program point | Target |
|---|---|---:|
| NS-T01 | PG-P2 | At least 1 certified platform module |
| NS-T02 | PG-P3 | At least 3 certified shared-foundation modules |
| NS-T03 | PG-P4 | At least 1 complete product composition and 5 certified modules |
| NS-T04 | Post-P4 | At least 90% of eligible modules reach pilot without kernel modification |

A module is certified only when all eight conditions are evidenced: approved module contract; declared capabilities and dependencies; verified tenant isolation; registered permissions and entitlements; complete tests; an evidence envelope; an operational runbook; and independent acceptance.

## 3. Strategic outcomes

### OUT-01 — Governed and traceable delivery

Every material change shall be authorized, traceable, independently reviewed and supported by reproducible evidence.

| Indicator | Target |
|---|---:|
| Work items linked to approved requirements | 100% |
| Material work items with assigned maker and checker | 100% |
| Work items executed in registered branches or worktrees | 100% |
| Accepted work items with evidence envelopes | 100% |
| Architecture-impacting changes linked to an ADR | 100% |
| Unauthorized changes to protected branches | 0 |
| Expired exceptions remaining active | 0 |
| Releases with attributable human authorization | 100% |

Success requires traceability, independent verification and evidence; code or green tests alone are insufficient.

### OUT-02 — Verified tenant isolation

One tenant shall not access, modify, reference or infer another tenant's protected data or resources.

| Indicator | Target |
|---|---:|
| Tenant-aware tables with an approved tenant key | 100% |
| Tenant-aware tables protected by verified RLS or stronger isolation | 100% |
| Cross-tenant read negative tests | 100% pass |
| Cross-tenant write negative tests | 100% pass |
| Cross-tenant resource-reference tests | 100% pass |
| Background-job tenant-context tests | 100% pass |
| Cache, file, search and export isolation tests | 100% pass |
| Missing or invalid tenant-context tests | 100% deny |
| Critical or high unresolved isolation findings at release | 0 |
| Confirmed cross-tenant production incidents | 0 |

A mandatory isolation failure, unapproved skip, or missing reproducible evidence blocks release.

### OUT-03 — Reusable platform kernel

The reusable platform capability set is: Principal and identity; Tenant; Membership; Active tenant context; Authorization; Entitlement; Product and module registry; Events; Transactional outbox; Audit; Files; Notifications; Integration; Observability; and Operational controls.

| Indicator | Target |
|---|---:|
| Products using the canonical principal model | 100% |
| Products using first-class tenant membership | 100% |
| Products using the common authorization layer | 100% |
| Products using the common audit and event foundation | 100% |
| Duplicate tenant identity implementations | 0 |
| Duplicate platform authorization engines | 0 |
| Industry-specific logic introduced into the platform kernel | 0 unapproved |
| Shared capabilities with defined owners and contracts | 100% |

Product teams extend bOPEN through modules and registered interfaces, not product-specific kernel modifications.

### OUT-04 — Repeatable module factory

| Indicator | PG-P2 target | Post-P4 target |
|---|---:|---:|
| Modules with complete `module.yaml` manifests | 100% | 100% |
| Modules with documented APIs and events | 100% | 100% |
| Modules with permissions and entitlements registered | 100% | 100% |
| Modules passing automated contract validation | At least 90% | At least 98% |
| Median registration-to-authorized-build time | At most 10 business days | At most 5 business days |
| Median authorized-build-to-pilot time | Baseline established | At most 30 calendar days |
| Modules requiring unrelated kernel modifications | At most 20% | At most 10% |
| Reusable scaffolding coverage | At least 60% | At least 85% |

The controlled lifecycle is Registered -> Specified -> Contracted -> Authorized -> Implemented -> Verified -> Entitled -> Enabled -> Piloted.

### OUT-05 — bPro reference-product validation

The required reference flow is:

```text
Authenticate user
-> identify available memberships
-> select active tenant
-> validate membership
-> validate module entitlement
-> enter bPro
-> create tenant-owned project resource
-> authorize resource action
-> emit domain event
-> write audit record
-> execute background processing
-> retrieve tenant-scoped result
-> verify another tenant cannot access it
```

| Indicator | Target |
|---|---:|
| Complete reference flow successfully executed | 100% |
| Reference-flow requirements with automated tests | 100% |
| Tenant-isolation cases for the reference flow | 100% pass |
| Audit coverage for material actions | 100% |
| Outbox delivery without data inconsistency | 100% in conformance tests |
| Portal restricted and not-entitled states implemented | 100% |
| Critical reference-flow defects at PG-P4 exit | 0 |
| High-severity unresolved defects at pilot decision | 0 |

bPro must prove platform contracts without product-specific shortcuts.

### OUT-06 — Operational reliability and recovery

| Indicator | PG-P0/PG-P1 target | Pilot target |
|---|---:|---:|
| Critical services instrumented | 100% | 100% |
| Required logs, traces and metrics available | 100% | 100% |
| Successful automated backup rate | At least 99% | At least 99.5% |
| Restoration tests | At least monthly | At least monthly |
| Restoration-test pass rate | 100% | 100% |
| Release rollback procedure verified | 100% of releases | 100% |
| Critical alert ownership assigned | 100% | 100% |
| Critical incident runbooks completed | 100% | 100% |
| Unresolved critical vulnerabilities at release | 0 | 0 |
| Unresolved high vulnerabilities without approved treatment | 0 | 0 |

Initial pilot objectives are: availability at least 99.5%; successful authenticated request rate at least 99.5%; P95 standard interactive API latency at most 500 ms; audit-event persistence at least 99.99%; recovery point objective at most 24 hours during PG-P0; and recovery time objective at most 8 hours during PG-P0. These targets require evidence-based revision before regulated workloads or general availability.

### OUT-07 — Effective multi-agent delivery

| Indicator | Target |
|---|---:|
| Active agents recorded in the agent register | 100% |
| Agent tasks with bounded repository scope | 100% |
| Agent sessions linked to work-item IDs | 100% |
| Material agent changes independently reviewed | 100% |
| Structured handoffs meeting the handoff contract | At least 95% |
| Agent-produced claims supported by evidence | 100% |
| Agents receiving plaintext production credentials | 0 |
| Agents independently authorizing their own release | 0 |
| Conflicting concurrent mutations to controlled files | 0 |
| Agent-caused unauthorized production changes | 0 |

Productivity measures are accepted work per delivery cycle, first-pass acceptance rate, major-rework percentage, median handoff-to-review time, conflict-free parallel workstreams, and human review time saved without reduced control coverage. Generated code volume alone is not a productivity measure.

### OUT-08 — Evidence-to-learning and capability reuse

| Indicator | Target |
|---|---:|
| Material failures with evidence envelopes | 100% |
| High-impact failures with root-cause analysis | 100% |
| Verified lessons linked to corrective actions | 100% |
| Promoted skills with sandbox and evaluation evidence | 100% |
| Skills with named owners and review dates | 100% |
| Expired or failing skills remaining active | 0 |
| Repeated defects with previously verified root causes | Decreasing |
| Reuse of approved patterns and skills | Increasing each phase |

The controlled learning lifecycle is Evidence -> Reproduction -> Root Cause -> Verified Lesson -> Knowledge -> Test, ADR, Runbook or Skill -> Evaluation -> Controlled Promotion. Raw model memory, session summaries and unsupported agent conclusions are not governing knowledge.

## 4. Program lifecycle gates

Program lifecycle IDs are namespaced `PG-*`; see `program-lifecycle-crosswalk.md`. Bare `G0` or `P0` is prohibited in new status assertions.

| ID | Gate | Required demonstration |
|---|---|---|
| PG-G0 | Governance bootstrap | Controlling governance approved; agent, goal, module, skill and schedule registers established; authority matrix approved; technology decisions assigned; work-item and evidence templates operational. |
| PG-P0 | Platform skeleton | Repository and CI controls; principal and tenant skeleton; active-context proof; PostgreSQL RLS proof; module-registry skeleton; audit and outbox foundations; complete evidence for all PG-P0 work packages. |
| PG-P1 | Core multi-tenant kernel | Global principal; tenant and membership lifecycles; secure tenant switching; authorization and entitlements; cross-tenant negative testing; tenant-aware background processing; support-access governance. |
| PG-P2 | Module platform | Module registration; capability, permission and entitlement registries; dependency validation; enablement lifecycle; event/interface contracts; at least one certified module. |
| PG-P3 | Common business foundation | Shared Party, Organization, Location, Document, Asset, Money, Measurement, Classification, Approval and Notification foundations. |
| PG-P4 | Reference product | Complete bPro flow; multiple reusable modules; portal composition; tenant isolation; recovery; independent conformance evidence. |
| PG-C0 | Conformance | Independent verdict covering governance, architecture, isolation, authorization, security, audit/outbox, recovery, supply chain, operational readiness and evidence completeness. |

No gate inherits the status of a roadmap phase, bootstrap gate, research gate, research wave or work-package wave.

## 5. Measurement rules

1. A control passes only with reproducible evidence.
2. Skipped tests do not pass.
3. Partially implemented modules are not certified.
4. The implementing agent's report is not independent verification.
5. An on-time release that fails a mandatory gate is unsuccessful.
6. Productivity improvements shall not reduce test, security, evidence or review coverage.
7. Targets shall be re-baselined when measured evidence shows an estimate is unrealistic.
8. Re-baselining requires a formal record and shall preserve the intended control outcome.

## 6. Final success definition

bOPEN succeeds when BST repeatedly delivers multi-tenant products and modules with less duplicated platform development, faster controlled module onboarding, verified tenant isolation, consistent security and authorization, complete traceability and evidence, reliable operations and recovery, and reusable architecture, knowledge and skills.

The program objective is a repeatable digital-product operating capability, not merely source-code completion.

## 7. Current disposition

All program gates are `NOT_READY`. Current repository evidence may be mapped as evidence, draft-only, placeholder, missing or future evidence, but no mapping is a gate decision. `BOOT-B7` and BOPEN-RES-001 `RES-G3` through `RES-G7` remain separate and open. Production implementation remains unauthorized.

## 8. Approval

| Authority | Required disposition | Current disposition |
|---|---|---|
| Product Authority | Approve goal, outcomes and targets | Pending |
| Architecture Authority | Concur on lifecycle and platform boundaries | Pending |
| Security Authority | Concur on isolation, authorization and security outcomes | Pending |
| Data Authority | Concur on tenant-data and foundation outcomes | Pending |
| Engineering Authority | Accept delivery-control implementation work packages | Pending |
