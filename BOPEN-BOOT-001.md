# BOPEN-BOOT-001 — bOPEN Repository Bootstrap, AGENTS.md, Documentation System, Engineering Controls & P0 Execution Pack v1.0

**Document ID:** `BOPEN-BOOT-001`  
**Version:** `1.0`  
**Status:** Approved for bootstrap execution  
**Issued:** 2026-07-12  
**Owner:** bOPEN Architecture Authority  
**Classification:** Internal engineering governance  

## 1. Executive decision

bOPEN shall proceed with a governed repository bootstrap. This artifact authorizes the repository control plane, agent instruction hierarchy, documentation framework, research separation, engineering quality gates and P0 work packages.

It does not authorize production implementation of the identity, tenancy, membership, authorization, entitlement, capability or industry kernels.

## 2. Objectives

1. Make architectural authority explicit before code exists.
2. Prevent coding agents from inventing platform semantics.
3. Preserve a clean-room boundary between upstream research and bOPEN implementation.
4. Establish document control, traceability and evidence requirements.
5. Provide repeatable CI, security and quality checks.
6. Create an execution queue that can begin immediately without bypassing research or architecture gates.

## 3. Source-of-truth hierarchy

```text
Approved normative artifact
  > Approved ADR
  > Versioned contract
  > Accepted work package
  > Implementation
  > Automated test and evidence
  > Informal note or conversation
```

A lower-order source shall not contradict a higher-order source. Conflicts require an ADR or controlled document revision.

## 4. Repository model

```text
bopen/
├── AGENTS.md
├── apps/
├── services/
├── packages/
├── contracts/
├── sdk/
├── infrastructure/
├── tools/
├── tests/
├── research/
└── docs/
```

The repository is a monorepo for governance and contract coherence. Deployment topology may later use modular services, deployment stamps or dedicated tenant infrastructure without changing this repository decision.

## 5. Agent governance

The root `AGENTS.md` is mandatory and applies repository-wide. Scoped files add stricter rules for their directories. Agents shall:

- read all applicable instruction files before editing;
- operate only within an accepted work package;
- cite governing artifact and requirement IDs;
- stop when a required normative decision does not exist;
- preserve tenant isolation, authorization and clean-room boundaries;
- run required validation and attach evidence;
- never weaken a test or control to obtain a passing result.

## 6. Clean-room boundary

```text
UPSTREAM CLONE
  -> SOURCE OBSERVATION
  -> EVIDENCE RECORD
  -> FINDING
  -> REQUIREMENT / ADR
  -> VERSIONED CONTRACT
  -> INDEPENDENT IMPLEMENTATION
```

Direct code, schema, UI, naming or migration transplantation from research clones into production zones is prohibited.

## 7. Documentation system

The `/docs` hierarchy contains governance, product, requirements, architecture, platform domains, foundation domains, contracts, security, engineering, operations, products, ADRs, decisions, risks, evidence, work packages, templates and research resources.

Every controlled artifact shall include an ID, version, status, owner, approval state and traceability links.

## 8. Engineering quality gates

Minimum repository checks:

- mandatory file and hierarchy validation;
- document ID and status validation;
- scoped `AGENTS.md` validation;
- clean-room path validation;
- secret scanning;
- dependency review;
- formatting, linting, type checking and tests when code is introduced;
- migration and tenant-isolation tests for tenant-owned data;
- evidence generation for every accepted work package.

## 9. P0 work packages

| ID | Outcome |
|---|---|
| BOOT-P0-01 | Repository initialized with protected governance files. |
| BOOT-P0-02 | Root and scoped agent instructions installed. |
| BOOT-P0-03 | Documentation framework, indexes and templates operational. |
| BOOT-P0-04 | Artifact, ADR, decision, risk and evidence controls operational. |
| BOOT-P0-05 | CI and repository validation operational. |
| BOOT-P0-06 | Security and supply-chain controls operational. |
| BOOT-P0-07 | BOPEN-RES-001 integrated as controlled research input. |
| BOOT-P0-08 | CODEOWNERS and review governance defined. |
| BOOT-P0-09 | Local development and environment strategy documented. |
| BOOT-P0-10 | Contract-first architecture drafting initiated. |
| BOOT-P0-11 | First vertical-slice implementation specification prepared. |
| BOOT-P0-12 | Bootstrap exit gate reviewed and recorded. |

## 10. Bootstrap gates

| Gate | Pass condition |
|---|---|
| B0 | Bootstrap scope and owners approved. |
| B1 | Repository structure and branch controls established. |
| B2 | Root and scoped `AGENTS.md` validated. |
| B3 | Document manifest, status and traceability operational. |
| B4 | CI and security controls pass. |
| B5 | Research sources isolated and provenance controlled. |
| B6 | Normative architecture drafting queue accepted. |
| B7 | Bootstrap evidence approved; production implementation remains separately gated. |

## 11. Exit criteria

BOPEN-BOOT-001 is complete when:

- all mandatory files exist;
- repository validators pass;
- document and work-package registers are current;
- clean-room controls are operational;
- no production implementation has bypassed the architecture gates;
- the next accepted work packages are assigned.

## 12. Approval statement

This artifact authorizes repository bootstrap and governed architecture work. It does not authorize production adoption of upstream code, final licensing decisions or production kernel implementation.
