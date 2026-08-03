# bOPEN Strategic Roadmap & Full Phase Execution Outline v1.0

**Document ID:** `BOPEN-PROD-OUTLINE-001`  
**Version:** `1.1`  
**Status:** Approved Master Specification  
**Issued:** 2026-07-29  
**Corrected:** 2026-07-30  
**Owner:** Product Authority & Architecture Authority  
**Classification:** Master Roadmap Execution Outline  

> **STATUS RECONCILIATION — 2026-07-30.** The per-phase `Status` lines in v1.0 had drifted
> out of agreement with `DECISION-REGISTER` and with the working tree: Phase 2 was recorded
> as "NEXT IMMEDIATE FOCUS" and Phase 3 as "FUTURE MILESTONE" while both had been
> implemented and authorized. Statuses below are reconciled against
> [`AGENTS.md` §20.2](../../AGENTS.md), which is the single operative gate register.
>
> Statuses now carry two independent axes, because conflating them is what allowed the
> drift: **authorization** (may work proceed) and **verification** (is the result proven).
> A phase can be authorized and implemented while remaining unverified. That is the current
> state of Phases 1 through 3.

---

## Executive Overview

bOPEN is structured across **7 sequential strategic phases** to ensure absolute clean-room separation, multi-tenant security, and contract-first integrity:

$$\text{Phase 0 (Govern/Research)} \longrightarrow \text{Phase 1 (Kernel Slice)} \longrightarrow \text{Phase 2 (Membership/SSO)} \longrightarrow \text{Phase 3 (Entitlement/Capabilities)} \longrightarrow \text{Phase 3.5 (Runtime Realization)} \longrightarrow \text{Phase 3.6 (Tenant Privacy)} \longrightarrow \text{Phase 4 (Foundations/Products)}$$

> **Corrected 2026-07-31.** This overview read "5 Sequential Strategic Phases" and omitted
> Phase 3.5 from the chain, having not been updated when 3.5 was inserted on 2026-07-30.
> **Extended 2026-07-31** with Phase 3.6 under `DEC-P35-TENANCY-MODEL` §8. The count is seven.
>
> Both corrections have the same cause: a phase was inserted and this overview was not updated.
> The count is a fact that drifts silently, so it is now stated with the date it was last
> checked rather than left as prose.

---

## Detailed Outline of Each Phase

### Phase 0 — Governance, Research & Architecture Baseline
**Status**: **COMPLETED & ESTABLISHED**

* **Objective**: Build governed monorepo plane, execute clean-room research, author normative specs, and create machine-readable contracts.
* **Key Deliverables**:
  1. **Governance & Tooling**: `BOPEN-BOOT-001` pack, [AGENTS.md](file:///c:/laragon/www/bopen/AGENTS.md) operating rules, multi-agent single-workspace policy, repository validators (`validate_repository.py`, `check_clean_room.py`).
  2. **Clean-Room Clearance**: `BOPEN-RES-001 Gate G7` clearance ([EVD-RES-001-G7](file:///c:/laragon/www/bopen/docs/evidence/EVD-RES-001-gate-g7-clearance.md)).
  3. **Normative Specifications**: Approved specs for Requirements ([BOPEN-REQ-001](file:///c:/laragon/www/bopen/docs/02-requirements/BOPEN-REQ-001.md)), Architecture ([BOPEN-ARCH-001](file:///c:/laragon/www/bopen/docs/03-architecture/BOPEN-ARCH-001.md)), Tenancy ([BOPEN-TENANT-001](file:///c:/laragon/www/bopen/docs/04-platform/BOPEN-TENANT-001.md)), and Authorization ([BOPEN-AUTHZ-001](file:///c:/laragon/www/bopen/docs/04-platform/BOPEN-AUTHZ-001.md)).
  4. **Machine-Readable Schemas**: JSON schemas in `contracts/schemas/` ([tenant-context.json](file:///c:/laragon/www/bopen/contracts/schemas/tenant-context.json), [authorization-decision.json](file:///c:/laragon/www/bopen/contracts/schemas/authorization-decision.json), [audit-event.json](file:///c:/laragon/www/bopen/contracts/schemas/audit-event.json), [membership-transition.json](file:///c:/laragon/www/bopen/contracts/schemas/membership-transition.json)).
  5. **Physical Database Isolation**: PostgreSQL Row-Level Security DDL ([001_tenant_isolation_baseline.sql](file:///c:/laragon/www/bopen/infrastructure/database/001_tenant_isolation_baseline.sql)) and negative isolation unit tests ([test_tenant_isolation.py](file:///c:/laragon/www/bopen/tests/isolation/test_tenant_isolation.py)).
  6. **Strategic Matrices & Master Plan**: [CAPABILITY-MATRIX.md](file:///c:/laragon/www/bopen/docs/01-product/CAPABILITY-MATRIX.md), [FUTURE-DEVELOPMENT-PLAN.md](file:///c:/laragon/www/bopen/docs/01-product/FUTURE-DEVELOPMENT-PLAN.md), [TECHNOLOGY-MATRIX.md](file:///c:/laragon/www/bopen/docs/03-architecture/TECHNOLOGY-MATRIX.md), [PROGRAMMING-LANGUAGES-MATRIX.md](file:///c:/laragon/www/bopen/docs/08-engineering/PROGRAMMING-LANGUAGES-MATRIX.md), and [FINAL-TECH-PLAN.md](file:///c:/laragon/www/bopen/docs/03-architecture/FINAL-TECH-PLAN.md).

---

### Phase 1 — Platform Kernel Vertical Slice
**Authorization**: **AUTHORIZED** (`AGENTS.md` §3)
**Verification**: **IMPLEMENTED_UNVERIFIED** — the slice runs in-process only. No evidence has been executed against PostgreSQL, so the isolation guarantee it depends on is asserted rather than proven. "Operational" in v1.0 described the test suite, not a running service.

* **Objective**: Build the minimum governed relationship chain without billing, workflows, or industry logic.
* **Key Execution Chain**:
  ```text
  Register Principal -> Provision Tenant -> Create Owner Membership -> Establish Context -> Authorize Read -> Emit Audit Event
  ```
* **Key Deliverables**:
  1. **Kernel Core Models** ([kernel_core/types.py](file:///c:/laragon/www/bopen/packages/kernel-core/python/kernel_core/types.py)): `Principal`, `Tenant`, `Membership`, `ContextPayload`, `AuthorizationRequest`, `AuthorizationDecision`.
  2. **Deny-by-Default Evaluator** ([kernel_core/evaluator.py](file:///c:/laragon/www/bopen/packages/kernel-core/python/kernel_core/evaluator.py)): ReBAC/ABAC authorization evaluator.
  3. **Audit Dispatcher** ([kernel_core/audit.py](file:///c:/laragon/www/bopen/packages/kernel-core/python/kernel_core/audit.py)): Correlated security audit log engine.
  4. **Platform Kernel Service** ([platform_kernel/service.py](file:///c:/laragon/www/bopen/services/platform-kernel/python/platform_kernel/service.py)): End-to-end kernel orchestrator.
  5. **Integration Suite**: [test_phase1_vertical_slice.py](file:///c:/laragon/www/bopen/tests/integration/test_phase1_vertical_slice.py).

---

### Phase 2 — Membership & Enterprise Onboarding
**Authorization**: **AUTHORIZED** — implementation hold discharged by `DEC-0009`..`DEC-0011` (`DEC-P2-DOCKET`) and `DEC-P3-ENTRY`
**Verification**: **IMPLEMENTED_UNVERIFIED** — `EVD-P2-PROVISIONAL-001` records the independent checker and the security reviewer as NOT ASSIGNED. Under `BOPEN-GOV-EBIV-001` §6.1 a panel below two verifiers cannot realize a verdict.

* **Objective**: Full lifecycle membership state machines, tenant switching APIs, enterprise SSO / SCIM provisioning, and delegated cross-tenant access.
* **Key Execution Outline**:
  1. **MILE-2.1 Principal Invitation Engine**: Issue, validate, accept, decline, and expire invitations (`invited` -> `active` / `declined` / `expired`).
  2. **MILE-2.2 Membership State Machine Engine**: Full transition handler (`invited`, `active`, `suspended`, `revoked`, `expired`, `left`, `removed`).
  3. **MILE-2.3 Tenant Context Switching Service**: API headers and tokens for switching active tenant context seamlessly without re-authenticating.
  4. **MILE-2.4 Enterprise IdP & SCIM 2.0 Sync**: Automatic user provisioning/deprovisioning via BoxyHQ Jackson / SAML / OIDC / SCIM 2.0 ([BOPEN-IDP-001](file:///c:/laragon/www/bopen/docs/04-platform/BOPEN-IDP-001-DRAFT.md)).
  5. **MILE-2.5 Delegated Cross-Tenant Access**: Time-bounded partner and support access grants with auto-revocation.

---

### Phase 3 — Capability & Commercial Entitlement Kernel
**Authorization**: **AUTHORIZED** — `DEC-P3-ENTRY`
**Verification**: **IMPLEMENTED_UNVERIFIED** — completion evidence assessed INADMISSIBLE against `BOPEN-GOV-EBIV-001` §5 (fails R1–R5). See [`docs/evidence/phase-3/completion-decision.md`](../evidence/phase-3/completion-decision.md) §4.

* **Objective**: Commercial licensing, plan tiers, dynamic capability registry, feature rollout flags, and real-time usage metering.
* **Key Execution Outline**:
  1. **MILE-3.1 Capability Registry Service (`BOPEN-MOD-001`)**: Dynamic registration and discovery of versioned module capabilities and dependency graphs.
  2. **MILE-3.2 Commercial Entitlement Engine (`BOPEN-ENT-001`)**: Subscription plan tiers, quota enforcement, and feature rollout flags.
  3. **MILE-3.3 Real-Time Usage & Metering**: Aggregate usage event pipeline tracking API calls, storage, and feature consumption against tenant quotas.
  4. **MILE-3.4 Commercial Overages & Throttling**: Rate limiting and quota rejection when tenant usage exceeds entitled capacity.

---

### Phase 3.5 — Runtime Realization *(inserted 2026-07-30)*
**Authorization**: **AUTHORIZED 2026-07-31** — [`DEC-P35-RUNTIME`](../decisions/DEC-P35-RUNTIME.md) approved (Option C); [`BOPEN-P35-001`](../work-packages/BOPEN-P35-001-EXECUTION-PLAN.md) bound as the implementation plan
**Verification**: **CLOSED under the two-agent profile (2026-08-02, `BOPEN-GOV-EBIV-001` §6.5).** `WP-P35-01`..`03` are `CONFIRMED_UNDER_TWO_AGENT_PROFILE` (one verifier + operator disposition; the single verifier reran maker tests for many ballots, so tenant isolation rests on rerun evidence — recorded). `WP-P35-04` is accepted with two standing refutations. `WP-P35-05a` is `CONFIRMED_UNDER_TWO_AGENT_PROFILE` at `2c31379` — 27 propositions incl. the AUTH-D3 tenant-provisioning gate, Codex ballot `5158629`, operator disposition ([`wp-p35-05a-disposition.md`](../evidence/phase-3.5/wp-p35-05a-disposition.md)); the last live authentication hole is closed. All five WPs are disposed. `WP-P35-05b` (BoxyHQ federation) remains moved out and blocked

* **Objective**: Convert the specification model into a running multi-tenant service. `BOPEN-ARCH-PLAN-001` §2 binds a five-layer production blueprint; four of those five layers currently have no implementation.
* **Rationale**: Phase 4 satellite products must call the kernel across a network boundary. On the current baseline they could only `import kernel_core` in-process, giving each product its own copy of tenant, membership and entitlement state — which would make the kernel a shared library rather than an isolation boundary.
* **Key Execution Outline**:
  1. **WP-P35-01 Persistence & tenant-scoped session layer** — psycopg3, `SET LOCAL app.current_tenant_id` per transaction, RLS conformance executed against a live PostgreSQL instance.
  2. **WP-P35-02 Kernel HTTP surface** — FastAPI + Pydantic v2 over `contracts/schemas/`.
  3. **WP-P35-03 Signed context token** — `sub`, `tid`, `mid`, `roles`, `scopes`; active context survives a process boundary.
  4. **WP-P35-04 API gateway** — Hono + Zod bound to `HTTP_HEADER_SPEC.md`. Implemented 2026-07-31 in `apps/gateway`; see [`EVD-P35-04-MAKER`](../evidence/phase-3.5/wp-p35-04-maker-submission.md).
  5. **WP-P35-05a Kernel authentication boundary** — an external authenticator's signed assertion is required before context issuance, and a configured authenticator cannot be disabled by the development flag. Implemented 2026-07-31; see [`EVD-P35-05A-MAKER`](../evidence/phase-3.5/wp-p35-05a-maker-submission.md). Split from `WP-P35-05` by [`DEC-P35-IDP-SPLIT`](../decisions/DEC-P35-IDP-SPLIT.md).
* **Moved out of this phase**: **WP-P35-05b Enterprise IdP federation** (BoxyHQ Jackson, per-tenant connections, SCIM). Blocked by `D-P35-011`..`D-P35-014` **and** by `D-P35-004`..`D-P35-010`, which its connection storage needs.
* **Deferred**: Go event microservices (blueprint layer 5). Not cancelled; revisited when metering throughput is measured rather than projected.

---

### Phase 3.6 — Tenant Privacy & Platform Observability *(inserted 2026-07-31)*
**Authorization**: **PARTIAL** — `DEC-P35-TENANCY-MODEL` §8 approved (hybrid placement); [`DEC-P35-CONTROL-PLANE`](../decisions/DEC-P35-CONTROL-PLANE.md) **Proposed, Security and Privacy review required before implementation**
**Verification**: not started

* **Objective**: Make tenant privacy a structural property rather than a policy promise — a dedicated database per tenant by default, a shared RLS pool for trial and free tier — while the platform retains capacity planning, performance management and billing without reading a business row.
* **Driver**: tenant privacy. Recorded explicitly, because `DEC-P35-TENANCY-MODEL` §7 answered a *load* question and §8 supersedes it on a different one.
* **Requirements**: [`BOPEN-PRD-P35-002`](../02-requirements/BOPEN-PRD-P35-002.md) — 10 requirements, each with the mutation that must break it.
* **Key Execution Outline**:
  1. **WP-P35-06 Placement routing** — carried forward from Phase 3.5, generalized from shard routing. Resolve a tenant to a connection target that may be a dedicated database or a shared pool.
  2. **WP-P36-01 Plane assignment and cross-plane integrity** — the hard one. Twelve foreign keys reference `tenants` or `principals` and cannot survive the split.
  3. **WP-P36-02 Control-plane telemetry and credential boundary** — aggregates pushed outward; the control plane holds no credential for any tenant database.
  4. **WP-P36-03 Disclosure and migration uniformity** — a tenant can see its placement kind and what is held about it; a placement behind on migrations is refused service.
* **Entry gate**: Security and Privacy review of `DEC-P35-CONTROL-PLANE`, which must resolve two questions the PRD found — that the control plane necessarily holds personal data (`principals.email` is globally unique), and where audit records carrying business identifiers should live.
* **What it keeps**: row-level security remains the live mechanism for the shared pool, so the 16 policy-bearing tables and all 38 executed isolation tests retain their meaning. This is why Option D was preferred to database-per-tenant everywhere.

---

### Phase 4 — Common Business Foundations & Satellite Products
**Authorization**: **AUTHORIZED 2026-08-03 — MILE-4.1 and MILE-4.2 (Money & Currency)** (operator `BizEra`, [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §7). Precondition (Phase 3.5 closed/verified/demonstrated) met. In scope: **MILE-4.1** (Party) and **MILE-4.2 Money & Currency**. The other MILE-4.2 foundations (Document, Location, UOM, Calendar, Asset, Workflow, Notification) and all of **MILE-4.3** remain gated and enter on their own operator dispositions.
**Verification**: not started

* **Objective**: Build reusable business foundation microservices and integrate initial satellite products.
* **Key Execution Outline**:
  1. **MILE-4.1 Party & Relationship Foundation (`BOPEN-PARTY-001`)**: Person, organization, vendor, supplier, customer graph models.
  2. **MILE-4.2 Reusable Business Foundations**:
     - *Document Management*: File uploads, signatures, versioning, document access control.
     - *Location & Geography*: Physical sites, addresses, geofencing, GPS tracking.
     - *Money & Currency*: Multi-currency, exchange rates, financial rounding.
     - *Measurement & UOM*: Unit of measure conversions and specifications.
     - *Calendar & Operating Hours*: Shifts, schedules, holiday calendars.
     - *Asset Baseline*: Physical/digital asset lifecycle management.
     - *Workflow State Engine*: Task approvals and business process execution.
     - *Notification Engine*: Email, SMS, Push, and Webhook dispatching.
  3. **MILE-4.3 Satellite Product Composition**:
     - **bPro**: Practice & professional services management.
     - **bFleet**: Fleet management, logistics & route optimization.
     - **PropTech**: Real estate, property management & tenant leasing.
     - **bERP**: Enterprise resource planning core.
     - **LDM**: Logistics & distribution management.
