# BOPEN-RES-001 — bOPEN Open-Source Platform Kernel Research, Clone Governance & Clean-Room Study Plan v1.0

**Document ID:** BOPEN-RES-001  
**Version:** 1.0  
**Status:** Approved for research execution  
**Issued:** 2026-07-12  
**Primary research target:** BoxyHQ SaaS Starter Kit  
**Pinned upstream repository:** `boxyhq/saas-starter-kit`  
**Pinned study commit:** `abc9b686823cbfb4973c79bc36fea37a3244be6c`  
**Reference release:** `v1.6.0`  

## 1. Executive Decision

bOPEN will not be created by renaming or lightly modifying an upstream SaaS starter kit. bOPEN will be developed as an independently governed platform kernel informed by traceable, evidence-based study of selected open-source systems.

BoxyHQ SaaS Starter Kit is approved as the first research clone because it exposes an integrated enterprise SaaS lifecycle across account creation, team creation, team membership, invitation, role-based authorization, SSO/directory-sync integration, audit, webhooks, API keys and subscription/payment integration.

The first study shall map BoxyHQ against the bOPEN reference chain:

```text
PLATFORM
  -> PRINCIPAL
  -> TENANT
  -> MEMBERSHIP
  -> CONTEXT
  -> AUTHORIZATION
  -> ENTITLEMENT
  -> CAPABILITY
```

The study shall explicitly identify where BoxyHQ provides direct evidence, where it provides only an analogy, and where bOPEN requires a materially stronger abstraction.

## 2. Strategic Objective

The objective of BOPEN-RES-001 is to produce reusable architecture knowledge without creating uncontrolled code inheritance, licensing ambiguity, accidental coupling, or false equivalence between a SaaS starter and a multi-industry platform kernel.

The package establishes:

1. source and clone governance;
2. a reproducible upstream pin;
3. evidence classification and citation controls;
4. a clean-room separation model;
5. BoxyHQ lifecycle and domain mapping;
6. work packages, exit gates and evidence requirements;
7. approved templates for future research targets;
8. a controlled handoff from research findings to bOPEN requirements, contracts and ADRs.

## 3. Scope

### 3.1 In scope

- BoxyHQ repository provenance and license verification.
- Reproducible study-clone setup.
- Runtime and repository orientation.
- Data-model trace from `User` through `TeamMember` to `Team`.
- Team creation and owner-membership creation.
- Invitation creation, validation, acceptance, expiration and removal.
- Active-team context discovery and enforcement.
- Role/permission evaluation.
- SSO and directory-sync integration boundaries.
- Audit and webhook event boundaries.
- API-key and subscription/payment boundaries.
- Security assumptions, failure modes and bOPEN gaps.
- Translation of observations into bOPEN requirements and architecture decisions.

### 3.2 Out of scope

- Production use of the BoxyHQ clone.
- Rebranding BoxyHQ as bOPEN.
- Copying upstream product UI, naming, database schema or source files into bOPEN.
- Treating BoxyHQ roles as the final bOPEN authorization model.
- Treating BoxyHQ subscriptions as the final bOPEN entitlement model.
- Legal advice or final license clearance.
- Implementing bOPEN production code under this package.
- Comparing all secondary research targets; those are follow-on packages.

## 4. Governing Architecture Baseline

The research shall evaluate BoxyHQ against the following bOPEN definitions.

| bOPEN concept | Normative meaning |
|---|---|
| Platform | The governed operating environment, control plane, products, policies and shared services. |
| Principal | A human, agent, service account, application, device or system identity capable of acting. |
| Tenant | The commercial, security, policy and data-isolation boundary. |
| Membership | The governed relationship between a principal and a tenant. |
| Context | The validated tenant, organization, workspace and resource scope in which an action is evaluated. |
| Authorization | The decision on whether a principal may perform an action on a resource in context. |
| Entitlement | The tenant's commercial or administrative right to use a product, module, feature, quota or capacity. |
| Capability | A registered action/resource contract exposed by a product or module. |

The required access equation is:

```text
ACCESS =
Platform policy satisfied
AND Principal active
AND Tenant active
AND Membership active
AND Context valid
AND Entitlement granted
AND Capability enabled
AND Authorization allowed
AND Conditions satisfied
```

BoxyHQ is expected to provide strong evidence for human user, team, membership, invitation and simple RBAC. It is not expected to provide a complete bOPEN principal abstraction, generalized context model, entitlement engine, capability registry, resource graph, isolation profile or industry package model.

## 5. BoxyHQ Upstream Baseline

As observed on 2026-07-12:

- repository: `boxyhq/saas-starter-kit`;
- repository status: public and not archived;
- default branch: `main`;
- study pin: `abc9b686823cbfb4973c79bc36fea37a3244be6c`;
- latest observed commit date: 2026-05-08;
- repository license file: Apache License 2.0;
- package version: 1.6.0;
- principal stack elements: Next.js, React, TypeScript, PostgreSQL, Prisma and NextAuth;
- enterprise integrations described upstream: SAML SSO/directory sync, audit logs, webhooks, Stripe and Playwright;
- corporate lineage note: BoxyHQ was acquired by Ory; the repository and package dependencies must therefore be monitored for renaming, archival, transfer or integration changes.

The clone shall always be pinned to a commit SHA. Branch-only references are prohibited as formal evidence.

## 6. Initial BoxyHQ-to-bOPEN Mapping

| BoxyHQ element | bOPEN target | Mapping strength | Initial conclusion |
|---|---|---:|---|
| SaaS application and integrations | Platform | Partial | Useful lifecycle shell, but not a platform control plane. |
| `User` | Human Principal / User Account | Strong for human user | No generic principal supertype. |
| `Team` | Tenant candidate | Strong analogy | Team lacks full tenant lifecycle, policy and isolation profile. |
| `TeamMember` | Membership | Strong | Membership and role are combined more tightly than desired for bOPEN. |
| Team slug / route / access resolver | Context candidate | Partial | Must trace how context is selected, propagated and validated. |
| `Role` + permission map | Authorization | Strong for simple RBAC | No generalized scope, conditions, ReBAC or policy engine. |
| `Subscription`, billing identifiers | Entitlement candidate | Weak | Commercial state is not a generalized feature/quota entitlement model. |
| Permission resources and service features | Capability candidate | Weak/partial | No versioned capability registry or module contract. |
| `Invitation` | Pre-membership lifecycle | Strong | Valuable for controlled onboarding and domain-gated links. |
| `ApiKey` | Non-human access credential | Partial | API key is tenant-bound but not a full service-principal model. |
| Svix events | Integration event | Strong for webhook emission | Not a complete domain-event/outbox contract. |
| Retraced audit calls | Audit integration | Strong boundary evidence | bOPEN needs native immutable audit contracts and correlation. |
| SAML Jackson | Tenant enterprise IdP boundary | Strong integration evidence | Must remain separate from tenant and membership domain authority. |

## 7. Confirmed Lifecycle Evidence

### 7.1 Self-registration path

The upstream registration handler creates a `User`. When no invitation is supplied, it requires a team name, creates a `Team`, and then creates an `OWNER` `TeamMember` relation for the new user.

```text
Registration request
  -> validate account data
  -> create User
  -> create Team
  -> create OWNER TeamMember
  -> initialize webhook application
  -> optional verification email
```

bOPEN inference:

```text
Create human principal
  -> create user account
  -> provision tenant
  -> create owner membership
  -> establish initial tenant context
```

The inference must not be implemented directly until tenant provisioning, lifecycle states and transaction boundaries are specified in BOPEN-TENANT-001.

### 7.2 Invitation path

BoxyHQ supports email invitations and reusable link invitations with allowed-domain restrictions. Invitations are assigned a role, issued with a random token and a seven-day expiry. Acceptance validates the authenticated email or allowed domain, creates/upserts `TeamMember`, emits a member-created event, and removes an email invitation after acceptance.

bOPEN must strengthen this model with explicit invitation status, single-use governance, revocation metadata, acceptance actor, replay protection, risk events and auditable state transitions.

### 7.3 Membership and roles

The schema enforces uniqueness of `(teamId, userId)` and assigns one of `OWNER`, `ADMIN` or `MEMBER` to the membership. This is an effective educational reference for a first-class membership relation, but bOPEN shall separate:

```text
Membership
  != Role assignment
  != Job title
  != Permission
  != Entitlement
```

### 7.4 Authorization

The upstream permission map associates roles with resource/action pairs. Owner and admin receive broad team-management permissions; member receives team read and leave access. bOPEN shall study this as a baseline RBAC implementation while rejecting it as the final authorization architecture.

Required bOPEN extensions include:

- explicit scope type and scope identifier;
- deny and precedence rules;
- effective dates;
- conditions and policy inputs;
- delegated support grants;
- resource relationships;
- cross-tenant access boundaries;
- agent/tool grants;
- decision reason and audit evidence.

### 7.5 Entitlement and capability

BoxyHQ contains subscription, service and price records, as well as team payment permission resources. This is commercially useful but does not establish a generalized entitlement engine. Research must distinguish:

```text
Paid subscription state
  from
Entitlement decision
  from
Feature rollout flag
  from
User authorization
```

No bOPEN capability contract may be derived merely by renaming the upstream permission resources.

## 8. Clean-Room Operating Model

The mandatory information flow is:

```text
UPSTREAM CLONE
  -> SOURCE OBSERVATION
  -> EVIDENCE RECORD
  -> CAPABILITY FINDING
  -> ARCHITECTURE INFERENCE
  -> bOPEN REQUIREMENT
  -> bOPEN CONTRACT / ADR
  -> INDEPENDENT IMPLEMENTATION
```

The prohibited flow is:

```text
UPSTREAM SOURCE
  -> copy / rename / translate
  -> bOPEN production code
```

### 8.1 Separation of duties

- **Source Analysis Zone:** may inspect and execute the upstream clone.
- **Synthesis Zone:** may use evidence records and findings; quotations and code fragments remain tightly controlled.
- **Clean Implementation Zone:** may use approved bOPEN requirements, contracts and ADRs only.
- **Compliance Review:** verifies license obligations and provenance before any code handoff.

An agent or developer who has studied upstream code may still participate in bOPEN design, but direct code transplantation is prohibited. For high-risk components, implementation shall be assigned to a separate agent or developer using only approved clean-room specifications.

## 9. Evidence Standard

Every material finding shall contain:

- evidence ID;
- source repository and pinned commit;
- source path and line/function locator;
- observation statement;
- evidence classification;
- confidence;
- bOPEN relevance;
- inference, if any, clearly separated from observation;
- decision or follow-up status;
- reviewer and review date.

Evidence classes:

| Class | Meaning |
|---|---|
| E0 | Unverified note or search lead. |
| E1 | Upstream documentation or README statement. |
| E2 | Source-code or schema observation at pinned commit. |
| E3 | Reproduced runtime behavior or automated test evidence. |
| E4 | Triangulated evidence from code, runtime and tests. |
| E5 | Approved architecture decision backed by reviewed evidence. |

Only E2-E4 evidence may support a formal bOPEN requirement. E5 is produced only after architecture approval.

## 10. Work Packages

| ID | Work package | Primary outcome |
|---|---|---|
| RES-P0-01 | Governance and repository setup | Controlled research workspace and approvals. |
| RES-P0-02 | Provenance and license baseline | Pinned source, license register and acquisition lineage note. |
| RES-P0-03 | Reproducible clone bootstrap | Verified clone, dependency lock and environment record. |
| RES-P0-04 | Repository orientation | Architecture map and source-path index. |
| RES-P0-05 | Identity and principal trace | User/account/session/authentication findings. |
| RES-P0-06 | Tenant and membership trace | Team, member, owner and tenant-gap findings. |
| RES-P0-07 | Invitation lifecycle trace | Create, fetch, accept, revoke/expire evidence. |
| RES-P0-08 | Context and authorization trace | Context resolver, middleware and permission evaluation. |
| RES-P0-09 | Enterprise identity trace | SSO, directory sync and domain boundaries. |
| RES-P0-10 | Entitlement and commercial trace | Subscription/payment mapping and gaps. |
| RES-P0-11 | Events, audit and API-key trace | Integration boundaries and non-human access findings. |
| RES-P0-12 | Security and failure-mode review | Threats, controls, tests and residual risks. |
| RES-P0-13 | bOPEN gap synthesis | Requirements, non-requirements and ADR candidates. |
| RES-P0-14 | Clean-room handoff | Approved evidence pack for BOPEN-REQ/ARCH/TENANT/AUTHZ. |

Detailed acceptance criteria are defined in `02-execution/work-package-register.md`.

## 11. Stage Gates

| Gate | Decision |
|---|---|
| G0 Research authorization | Scope, roles and legal-review owner assigned. |
| G1 Source integrity | Repository, license, commit and upstream status verified. |
| G2 Reproducibility | Clone and baseline tests can be reproduced from scripts. |
| G3 Lifecycle traceability | Registration, tenant creation, invitation and membership paths evidenced. |
| G4 Access traceability | Context and authorization checks traced end to end. |
| G5 Commercial/security review | Entitlement gaps, secrets, dependencies and threat cases reviewed. |
| G6 Architecture synthesis | Observations converted into approved bOPEN requirements/ADR candidates. |
| G7 Clean-room release | Implementation team receives only approved clean-room inputs. |

A gate shall be marked `PASS`, `PASS WITH CONDITIONS`, `FAIL` or `DEFERRED`. No implementation handoff is permitted before G7.

## 12. Required Research Outputs

The minimum accepted output set is:

- source and license register;
- upstream pin manifest;
- reproducible clone instructions;
- repository structure map;
- lifecycle map;
- data/domain model mapping;
- context and authorization trace;
- entitlement/capability gap analysis;
- threat and failure-mode register;
- evidence index and matrix;
- bOPEN gap register;
- decision and ADR candidate register;
- clean-room implementation handoff.

This package contains the initial versions of those controls and templates.

## 13. Initial Architecture Conclusions

1. **BoxyHQ validates Membership as a first-class relation.** `TeamMember` is not a duplicate user record; it connects a global user to a team.
2. **BoxyHQ validates owner membership creation during tenant-like provisioning.** bOPEN must add explicit tenant states and transaction orchestration.
3. **BoxyHQ invitations are a useful pre-membership reference.** bOPEN requires a richer state machine and replay/audit controls.
4. **BoxyHQ RBAC is intentionally simple.** bOPEN needs scoped RBAC plus conditional and relationship-aware authorization.
5. **BoxyHQ does not provide a full Principal abstraction.** API keys and integrations do not replace service, agent, device and system principals.
6. **BoxyHQ commercial records are not a complete Entitlement engine.** bOPEN must model boolean, static, capacity, seat and metered entitlements independently from authorization.
7. **BoxyHQ permission resources are not a Capability Registry.** bOPEN requires versioned product/module/feature/action/resource contracts.
8. **BoxyHQ is an educational lifecycle baseline, not the bOPEN codebase.** The clone remains outside production packages.

## 14. Follow-On Artifact Dependencies

BOPEN-RES-001 shall feed, but not replace:

- `BOPEN-REQ-001` — Product Requirements Specification;
- `BOPEN-ARCH-001` — Platform Kernel Architecture;
- `BOPEN-TENANT-001` — Tenant, Organization, Membership, Context and Isolation;
- `BOPEN-AUTHZ-001` — Authorization, Scope, Delegation and Policy;
- `BOPEN-ENT-001` — Entitlement, Usage and Commercial Kernel;
- `BOPEN-MOD-001` — Product, Module and Capability Contracts;
- `BOPEN-SEC-001` — Application Security and Software Supply Chain;
- `BOPEN-BOOT-001` — Repository Bootstrap and P0 Execution Pack.

## 15. Approval Statement

BOPEN-RES-001 v1.0 authorizes the BoxyHQ study clone and the associated research work packages. It does not authorize production adoption, code copying, branding reuse, license interpretation, or replacement of bOPEN architecture decisions with upstream implementation choices.
