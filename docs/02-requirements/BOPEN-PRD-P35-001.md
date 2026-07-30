# BOPEN-PRD-P35-001 - Runtime Assurance and Completion Product Requirements

**Document ID:** `BOPEN-PRD-P35-001`  
**Version:** `0.1.0`  
**Status:** Proposed - assists `BOPEN-P35-001`; no implementation authority  
**Issued:** 2026-07-31  
**Owner:** Product Authority (approval pending)  
**Classification:** Product Requirements Candidate  
**Governing artifacts:** `BOPEN-REQ-001`, `BOPEN-ARCH-001`, `BOPEN-TENANT-001`,
`BOPEN-AUTHZ-001`, `BOPEN-IDP-001`, `BOPEN-MOD-001`, `BOPEN-ENT-001`,
`BOPEN-GOV-EBIV-001`, `AGENTS.md` sections 7-11, 14, 16, 20  
**Assisted plan:** [`BOPEN-P35-001`](../work-packages/BOPEN-P35-001-EXECUTION-PLAN.md)  
**Pending decisions:** `DEC-P35-RUNTIME`, `DEC-P35-AUDIT-ENVELOPE`,
`DEC-P35-PHASE2-STORAGE`, `DEC-P35-AUTH-BOUNDARY`

---

## 1. Purpose and authority boundary

This PRD translates the 2026-07-31 independent review of the bOPEN codebase into a
bounded set of product requirements that can strengthen the existing Phase 3.5 plan.
It does not replace an approved normative specification, amend a frozen contract,
authorize Phase 3.5 implementation, open Phase 4, or record completion.

The PRD is intentionally narrower than the bOPEN product vision. It addresses the
conditions required for the existing platform kernel to become a dependable service
boundary for satellite products. Approval of this PRD would authorize planning only
to the extent explicitly granted by the approving authority and accepted work package.

## 2. Problem statement

The platform now has meaningful runtime implementation: a FastAPI surface, signed
context tokens, PostgreSQL repositories, migrations, and a live RLS conformance suite.
The canonical suite passed 414 of 414 tests during the review. Those results establish
useful progress, especially for PostgreSQL tenant isolation.

They do not establish completion. Adversarial probes reproduced six product-level gaps:

1. an active `owner` or `member` receives `ALLOW` for an unknown action and resource;
2. an invitation for one address can activate a membership for an unrelated principal;
3. an idempotent usage replay can return the same event ID with a different `context_id`;
4. a module manifest can enter the registry as `available` without validation or approval;
5. tenant, owner membership, and audit creation commit as separate operations;
6. the authorization HTTP response does not conform to its frozen schema.

The review also found vulnerable pinned Python dependencies, five constraining schemas
without real-instance coverage, and status registers that disagree with the operative
gate in `AGENTS.md` section 20.2.

The product problem is therefore not "add more platform features." It is:

> Make the existing kernel enforce its approved boundaries consistently at the HTTP,
> domain, persistence, contract, and evidence layers before another product depends on it.

## 3. Product outcomes

The approved implementation of this PRD MUST produce these outcomes:

- unknown or unapproved operations cannot receive an allow decision;
- identity and membership activation require a verified subject, not an asserted identifier;
- durable events reproduce the same security and idempotency context on every replay;
- module availability can be reached only through the approved lifecycle;
- multi-record business operations either commit completely or leave no partial state;
- every externally observable response conforms to its versioned contract;
- production dependency baselines contain no known critical or high vulnerability without
  an approved, time-bounded exception;
- completion status is derived from admissible evidence and agrees across controlled registers.

## 4. Users and stakeholders

| Actor | Need |
|---|---|
| Satellite product service | A stable kernel decision that cannot allow an unknown action |
| Tenant administrator | Membership and audit data protected by explicit authorization |
| Invited principal | An invitation cannot be claimed by a different identity |
| Security reviewer | Reproducible negative probes for every material security invariant |
| Platform operator | Atomic provisioning, actionable readiness, and safe dependency baselines |
| Product and completion authorities | One consistent status backed by exact-commit evidence |

## 5. Scope

### 5.1 In scope

- Phase 1 authorization and HTTP enforcement defects exposed by the review;
- Phase 2 invitation-to-principal binding at acceptance;
- Phase 3 module lifecycle and metering provenance defects;
- Phase 3.5 transaction, contract, dependency, and evidence requirements;
- tests, contract updates approved through the contract-first workflow, migrations where
  durable fields are missing, and document/register reconciliation;
- removal or explicit non-production isolation of parallel in-memory production paths.

### 5.2 Out of scope

- Phase 4 business foundations and satellite product features;
- new industry semantics;
- UI work;
- production deployment or activation;
- API gateway and enterprise IdP feature expansion beyond what is needed to close the
  requirements below;
- choosing the audit envelope before `DEC-P35-AUDIT-ENVELOPE` is decided;
- choosing Phase 2 storage shapes before `DEC-P35-PHASE2-STORAGE` is decided;
- treating a successful test run as approval or production authority.

## 6. Functional requirements

### PRD-P35-AUTH-001 - Explicit authorization policy match

**Statement:** The authorization evaluator MUST return `ALLOW` only when the validated
principal, tenant, membership, action, resource type, resource identity, and policy version
match an explicit approved rule. Unknown actions, resources, roles, states, and policy
versions MUST return `DENY`.

**Priority:** P0  
**Source:** `BOPEN-AUTHZ-001`; `BOPEN-P1-001` invariants `INV-P1-008`..`INV-P1-010`  
**Acceptance:** A request for `platform:drop_all_tenants` or any unregistered action returns
`DENY_UNSUPPORTED_ACTION`; removing the supported-action check makes the test fail.

### PRD-P35-AUTH-002 - Authorization on every protected endpoint

**Statement:** Every endpoint that reads confidential tenant data or mutates tenant-owned
state MUST obtain and enforce an authorization decision before the operation. A validated
context establishes identity and tenant scope; it MUST NOT be treated as permission.

**Priority:** P0  
**Source:** `AGENTS.md` section 9; `BOPEN-AUTHZ-001`  
**Acceptance:** A context whose role has no explicit rule cannot list audit events, create a
tenant resource, or read a tenant resource. Each denial emits one correlated terminal audit
decision and performs no protected operation.

### PRD-P35-IDP-001 - Verified invitation acceptance

**Statement:** Invitation acceptance MUST consume a server-established authenticated principal.
The acceptance flow MUST prove an approved identity-linking basis under `BOPEN-IDP-001`
section 11 and MUST NOT accept an arbitrary caller-supplied `principal_id`.

**Priority:** P0  
**Source:** `BOPEN-IDP-001` sections 6.4 and 11; `BOPEN-P2-001` section 9.4  
**Acceptance:** An invitation issued to identity A cannot create or activate a membership for
principal B. The denial is generic, audited, and leaves both invitation and membership state
unchanged.

### PRD-P35-METER-001 - Durable replay provenance

**Statement:** Every field required by the usage-metered-event contract, including
`context_id`, MUST be stored durably or derived from an immutable stored reference. An
idempotent replay MUST return the original event byte-for-byte after canonical serialization.

**Priority:** P0  
**Source:** `BOPEN-ENT-001`; `usage-metered-event.schema.json`  
**Acceptance:** Reusing one tenant-scoped idempotency key with a different `context_id`,
`correlation_id`, principal, capability, quantity, or unit fails closed. An equivalent replay
returns the original event ID, context, correlation, payload, and timestamp.

### PRD-P35-MOD-001 - Non-bypassable module lifecycle

**Statement:** A submitted module manifest MUST be validated against the approved schema before
it reaches the registry. Input MUST NOT set lifecycle status. Only the explicit
`registered -> validated -> approved -> available` transition operations may advance status.

**Priority:** P0  
**Source:** `BOPEN-MOD-001` sections 3 and 4; `module-manifest.schema.json`  
**Acceptance:** A manifest containing `status: available` is rejected and cannot make
`is_available()` true. Invalid identifiers, duplicate capabilities, unsupported versions,
extra properties, and unsatisfied version constraints are rejected before registration.

### PRD-P35-TXN-001 - Atomic tenant provisioning

**Statement:** Tenant creation, initial owner membership, and their mandatory audit/outbox
records MUST commit in one database unit of work. A retry MUST be idempotent and MUST NOT
create duplicate tenants or memberships.

**Priority:** P0  
**Source:** `BOPEN-P1-001` section 11.4; `AGENTS.md` sections 8 and 14  
**Acceptance:** Failure injection at each write boundary leaves no tenant, membership, audit,
or outbox fragment. A successful retry returns the one committed logical result.

### PRD-P35-CONTRACT-001 - Producer-to-contract fidelity

**Statement:** Every externally observable response, event, manifest, and transition receipt
MUST have one versioned contract and at least one test validating a real producer instance.
Characterization tests that demonstrate a known contradiction MUST NOT count as conformance.

**Priority:** P0  
**Source:** `AGENTS.md` section 10; `BOPEN-GOV-EBIV-001` R2 and R4  
**Acceptance:** The authorization response includes required `policy_version`, contains no
undeclared properties, and validates against `authorization-decision.json`. The five currently
uncovered constraining schemas are either covered by real instances or retired/superseded by
an approved decision.

### PRD-P35-RUNTIME-001 - One production execution path

**Statement:** Production entrypoints MUST use PostgreSQL-backed repositories and the approved
HTTP/context boundary. Parallel in-memory services MAY remain only as explicitly named test
fixtures or examples that production packaging cannot import accidentally.

**Priority:** P1  
**Source:** `BOPEN-P35-001` objective and D-06..D-08  
**Acceptance:** A production-startup test proves that state survives process restart and that
no configuration can silently select `PlatformKernelService` or another in-memory store.

### PRD-P35-SUPPLY-001 - Dependency security floor

**Statement:** Direct and transitive runtime dependencies MUST be audited from the locked
resolution. A known critical or high vulnerability MUST block completion unless an approved
exception identifies exposure, compensating controls, owner, and expiry.

**Priority:** P0  
**Source:** `AGENTS.md` section 13; `BOPEN-SEC-001`  
**Acceptance:** Python and JavaScript audits run from repository commands and report no
unexcepted critical or high findings. The PyJWT and Starlette findings observed on 2026-07-31
are remediated or covered by approved exceptions and regression tests.

### PRD-P35-EVIDENCE-001 - Reproducible validation environment

**Statement:** One documented repository command MUST load the non-secret local validation
configuration and run the canonical suite, contract conformance, repository validation,
clean-room validation, evidence anchors, and authority bootstrap without manual shell-specific
steps.

**Priority:** P1  
**Source:** `AGENTS.md` sections 5, 11, and 19.4  
**Acceptance:** A fresh supported workstation with provisioned local dependencies can run the
command and receive one machine-readable result. Missing PostgreSQL or credentials reports
`CANNOT_RUN`, never `PASS`.

### PRD-P35-STATUS-001 - Consistent phase and artifact status

**Statement:** `AGENTS.md`, `DOCUMENT-STATUS.md`, `DOCUMENT-COVERAGE.md`, artifact and work
package registers, roadmap documents, and evidence manifests MUST report the same authorization
and verification state.

**Priority:** P0  
**Source:** `AGENTS.md` sections 4, 12, and 20.2  
**Acceptance:** A validator fails when any controlled register claims `Completed`, `Verified`,
or `Authorized` contrary to the operative gate or admissible exact-commit evidence.

## 7. Non-functional requirements

| ID | Requirement |
|---|---|
| PRD-P35-NFR-001 | Cross-tenant reads and writes allowed by the database: zero |
| PRD-P35-NFR-002 | Unknown operations fail closed without resource or tenant enumeration |
| PRD-P35-NFR-003 | Security decisions and mutations carry one end-to-end correlation ID |
| PRD-P35-NFR-004 | Idempotent operations remain correct across processes and restarts |
| PRD-P35-NFR-005 | Audit and lifecycle evidence is append-only and reproducible from storage |
| PRD-P35-NFR-006 | Contract and migration changes are versioned, reversible, and independently testable |
| PRD-P35-NFR-007 | No production secret or real personal data appears in source, fixtures, or evidence |

No latency or throughput target is invented here. Performance targets require an observed
workload and an approved service-level objective.

## 8. Required user journeys

### 8.1 Authorized tenant resource access

1. A principal authenticates through an approved identity boundary.
2. The kernel validates the active membership and issues a short-lived context token.
3. A satellite product requests an action on a tenant resource.
4. The kernel resolves an explicit policy version and rule.
5. The operation proceeds only on `ALLOW`.
6. The decision and operation share one correlation ID and durable audit chain.

### 8.2 Invitation acceptance

1. An authorized tenant actor issues an invitation to a normalized destination.
2. The recipient proves control through an approved authentication/linking path.
3. The kernel binds the verified principal to the invitation.
4. Invitation consumption, membership activation, and audit commit atomically.
5. Reuse by the same or another principal cannot create another membership.

### 8.3 Idempotent usage ingestion

1. A validated context submits a usage event with a tenant-scoped idempotency key.
2. The kernel stores the complete canonical event and outbox record in one transaction.
3. An equivalent retry returns the stored event.
4. Any conflicting retry is refused without disclosing another tenant's data.

## 9. Delivery sequence within the existing plan

This sequence assists `BOPEN-P35-001`; it does not create new work-package authority.

| Sequence | Existing plan area | Required closure |
|---|---|---|
| 0 | Decision prerequisites | Decide runtime gate, audit envelope, Phase 2 storage, and auth boundary |
| 1 | WP-P35-02 / WP-P35-03 | Close authorization and invitation identity-binding P0 defects |
| 2 | WP-P35-01 | Add missing durable provenance and atomic units of work |
| 3 | Phase 3 repair before completion | Enforce module lifecycle and producer-contract fidelity |
| 4 | Cross-cutting verification | Remediate dependency findings and add one reproducible validation command |
| 5 | Completion preparation | Reconcile registers and generate exact-commit admissible evidence |

WP-P35-04 and WP-P35-05 feature expansion need not block closure of defects that already
exist in the kernel. They remain governed by the original sequence and pending decisions.

## 10. Acceptance matrix

| Test ID | Proposition | Expected result | Mechanism whose removal must fail the test |
|---|---|---|---|
| P35-PRD-T001 | Unknown action is not authorized | `DENY_UNSUPPORTED_ACTION` | supported-action policy match |
| P35-PRD-T002 | Context alone is not permission | audit/resource endpoints return 403 | endpoint decision enforcement |
| P35-PRD-T003 | Invitation cannot be claimed by another principal | generic denial, no state change | verified identity binding |
| P35-PRD-T004 | Usage replay preserves context | original event returned or conflict | stored `context_id` and canonical fingerprint |
| P35-PRD-T005 | Manifest cannot self-publish | contract rejection | schema-first loader and server-owned status |
| P35-PRD-T006 | Provisioning failure is atomic | zero partial rows | shared transaction/unit of work |
| P35-PRD-T007 | Authorization response matches contract | JSON Schema pass | real-instance contract validation |
| P35-PRD-T008 | Production restart preserves state | same state after restart | PostgreSQL production repository binding |
| P35-PRD-T009 | Dependency floor holds | no unexcepted critical/high findings | locked dependency audit |
| P35-PRD-T010 | Controlled statuses agree | register validator pass | cross-register status comparison |

Every P0 test requires a negative variant. Evidence is inadmissible if the test still passes
after the named mechanism is removed or bypassed.

## 11. Success metrics

Completion candidates MUST report:

- 100% of P0 requirements traced to named tests and exact implementation paths;
- zero reproducible cross-tenant disclosure or write;
- zero `ALLOW` decision without an explicit policy rule and version;
- zero invitation activation for an unverified principal;
- zero conflicting idempotent replay accepted;
- zero lifecycle transition reachable through an input-only status field;
- zero externally observable producer instances failing their approved schema;
- zero unexcepted critical/high runtime dependency findings;
- zero controlled-register disagreements;
- two or more admissible independent verifier ballots where the approved governance requires
  a quorum, with any reproducible refutation unresolved count equal to zero.

## 12. Release and rollback requirements

- No requirement in this PRD authorizes production release.
- Contract changes require compatible versioning or an approved migration rule.
- Database changes require forward, rollback, or explicit compensation strategy.
- Authorization widening and identity-linking changes require security review.
- A rollout MUST fail closed when policy, token verification, database context, audit, or
  dependency checks cannot run.
- Rollback MUST NOT restore an in-memory production fallback or an unauthenticated credential
  issuance path.

## 13. Risks and open decisions

| Risk or decision | Effect | Required disposition |
|---|---|---|
| `DEC-P35-RUNTIME` remains proposed | Phase 3.5 implementation authority is absent | Authority decision before execution |
| Audit envelope conflict | Producer and frozen schema cannot both be authoritative | Decide `DEC-P35-AUDIT-ENVELOPE` |
| Phase 2 storage decisions unresolved | Secure invitation persistence cannot be designed by code default | Decide `DEC-P35-PHASE2-STORAGE` |
| Authentication boundary unresolved | Invitation and context fixes could embed an IdP accidentally | Decide `DEC-P35-AUTH-BOUNDARY` |
| Existing tests characterize defects | Green count can be misread as conformance | Separate characterization from acceptance |
| Dependency remediation may require framework upgrade | Compatibility and behavior may change | Bounded upgrade with contract and security regression tests |

## 14. Traceability summary

| PRD requirement | Governing artifact | Existing plan | Evidence required |
|---|---|---|---|
| AUTH-001, AUTH-002 | BOPEN-AUTHZ-001 | WP-P35-02/03 | HTTP and evaluator negative tests |
| IDP-001 | BOPEN-IDP-001 | WP-P35-03/05 | verified-principal acceptance tests |
| METER-001 | BOPEN-ENT-001 | WP-P35-01 | PostgreSQL replay and schema tests |
| MOD-001 | BOPEN-MOD-001 | Phase 3 repair | schema-first lifecycle tests |
| TXN-001 | BOPEN-P1-001 | WP-P35-01/02 | database failure-injection tests |
| CONTRACT-001 | AGENTS.md section 10 | WP-P35-02 | producer-instance contract tests |
| RUNTIME-001 | BOPEN-P35-001 | D-06..D-08 | restart and packaging tests |
| SUPPLY-001 | BOPEN-SEC-001 | cross-cutting | locked dependency audits |
| EVIDENCE-001, STATUS-001 | BOPEN-GOV-EBIV-001 | completion preparation | validator and exact-commit evidence |

## 15. Review provenance

This candidate was prepared from an independent review performed on branch
`claude/BOPEN-P35-001-runtime-realization` at commit
`4e1bcedeb62e5b0c3a6e14915ac44083d251f017`.

Two pre-existing working-tree modifications were present during review:

- `docs/evidence/EVD-SEC-001-kernel-security-review.md`;
- `services/platform-kernel/python/platform_kernel/api.py`.

The review therefore validated the live working tree but did not cast an exact-commit verdict
on those two modified files. The reproduced probes and validator results are inputs to this
PRD, not approval evidence. This document has:

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
```
