# BOPEN-GOV-001 — bOPEN Governed Platform, Product, Module and Delivery Operating Model v0.1

**Status:** PROPOSED FOR APPROVAL  
**Owner:** bOPEN Program Authority  
**Applies to:** bOPEN platform, BST products, shared capabilities, industry packs,
tenant extensions, agents, skills and releases.

## 1. Purpose

Establish one operating model governing how bOPEN work is proposed, specified,
architected, authorized, implemented, verified, evidenced, released, operated, learned
from and retired.

## 2. Governance outcomes

bOPEN shall provide:

- clear decision rights and artifact precedence;
- lifecycle gates for projects, products, modules, skills and releases;
- multi-agent operation with bounded authority and structured handoffs;
- traceability from goals to requirements, code, tests and evidence;
- non-waivable tenant-isolation controls;
- repeatable module onboarding and certification;
- operational and learning loops;
- human accountability for high-impact decisions.

## 3. Scope classification

Every deliverable must be classified as:

1. Platform kernel
2. Common business foundation
3. Shared capability package
4. Industry pack
5. Product composition
6. Tenant-specific extension
7. External integration
8. Operations or governance capability

Misclassification is an architecture issue and must be resolved before implementation.

## 4. Authority model

### 4.1 Accountable human authorities

- Portfolio Sponsor
- Product Authority
- Architecture Authority
- Security Authority
- Data Authority
- Delivery Authority
- Conformance Authority
- Release Authority
- Operations Authority

Agents may prepare recommendations and evidence but do not inherit human authority by
default.

### 4.2 Decision classes

| Class | Examples | Minimum authority |
|---|---|---|
| D0 Routine | formatting, bounded test repair | Authorized work-item owner |
| D1 Material | public contract, migration, dependency | Module owner + checker |
| D2 High risk | authz, RLS, identity, data retention | Architecture + security |
| D3 Critical | production release, destructive migration, exception | Human release authority |

## 5. Artifact hierarchy

```text
Corporate policy
→ BOPEN-GOV
→ BOPEN-SYS / phase control
→ Security, tenancy and data policy
→ Approved ADR/TDR
→ Product or module specification
→ AGENTS instructions
→ Authorized work item
→ Execution evidence
```

## 6. Lifecycle gates

### G0 Registration

Required: project ID, owner, repository, classification, data/security level, evidence
destination and release authority.

### G1 Requirements baseline

Required: functional and non-functional requirements, actors, acceptance criteria,
dependencies, risks and traceability IDs.

### G2 Design baseline

Required: domain model, state machines, user journeys, interface design, restricted
states and accessibility expectations.

### G3 Architecture and technology freeze

Required: architecture views, threat model, tenancy design, ADRs, technology decisions,
dependency and licensing review.

### G4 Implementation authorization

Required: work packages, assigned paths/worktrees, maker/checker, verification matrix,
evidence plan and rollback.

### G5 Conformance pass

Required: functional, contract, integration, tenant-isolation, security, recovery and
independent review evidence.

### G6 Release authorization

Required: attributable human decision, release manifest, SBOM/provenance, migration,
backup and rollback proof.

### G7 Operational acceptance

Required: monitoring, alerts, runbooks, support, incident response, capacity, backup and
restoration readiness.

### G8 Learning disposition

Required: verified outcome classification and decision to close, document, test,
redesign, remediate or promote a reusable capability.

## 7. Project state machine

```text
DRAFT
→ REGISTERED
→ DISCOVERY
→ SPECIFIED
→ DESIGNED
→ PLANNED
→ AUTHORIZED
→ IMPLEMENTING
→ VERIFYING
→ PILOT
→ ACTIVE
→ MAINTENANCE
→ DEPRECATED
→ RETIRED
```

Holding states: `BLOCKED`, `QUARANTINED`, `REMEDIATION_REQUIRED`.

## 8. Module governance

Every module must possess a manifest, requirements, design, architecture, data model,
security classification, permissions, entitlements, API/events, tests, operational
runbook and owner.

Module lifecycle:

```text
PROPOSED
→ REGISTERED
→ SPECIFIED
→ APPROVED
→ AVAILABLE
→ ENTITLED
→ ENABLED
→ CONFIGURED
→ ACTIVE
→ DEPRECATED
→ DISABLED
→ RETIRED
```

`AVAILABLE`, `ENTITLED`, `ENABLED`, `AUTHORIZED` and `ACTIVE` are distinct states.

## 9. Agent governance

Agents are registered principals with explicit purpose, runtime, tools, repository
scope, network policy, credential policy, expiry and evidence destination.

Agent output is advisory or contributory unless a human authority explicitly delegates a
bounded decision. No agent may self-grant broader authority.

## 10. Skills governance

Skills are version-controlled operating procedures, not permissions. Skills must be
reviewed, sandboxed, evaluated, approved, monitored and revocable.

## 11. Tenant isolation

Tenant isolation is a release-critical invariant. Missing tenant context must deny
access. Cross-tenant data leakage, reference leakage, cache leakage, file leakage,
search leakage or event leakage blocks release and triggers incident handling.

## 12. Evidence

Evidence must be attributable, reproducible, immutable or hash-verifiable where
practical, and linked to requirements and decisions. Narrative claims without supporting
artifacts do not satisfy a gate.

## 13. Exception process

An exception must include:

- control being excepted;
- business justification;
- risk and affected tenants/data;
- compensating controls;
- owner and approvers;
- effective and expiry dates;
- monitoring;
- remediation plan.

Tenant-isolation default-deny, credential protection and release accountability are not
waivable under P0.

## 14. Governance disposition

Adopt BOPEN-GOV-001 above BOPEN-P0-001 as the umbrella operating model. BOPEN-P0-001
continues to govern the currently authorized implementation phase.
