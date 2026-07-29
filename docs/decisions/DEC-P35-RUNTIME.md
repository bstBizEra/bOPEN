# DEC-P35-RUNTIME — Runtime Realization Gate and Evidence Anchoring Correction

**Decision ID:** `DEC-P35-RUNTIME`
**Version:** `1.0.0`
**Status:** **Proposed — decision request raised under `AGENTS.md` §16**
**Issued:** 2026-07-30
**Owner:** Architecture Authority & Engineering Authority
**Due date:** Before any Phase 4 work package is opened
**Governing artifacts:** `AGENTS.md` §4, §11, §14, §16, §19.6; `BOPEN-ARCH-PLAN-001`; `BOPEN-TENANT-001`
**Raised by:** Claude (agent, Cortex role) — advisory only, no execution authority

---

## 1. Why this record exists

`AGENTS.md` §16 requires an agent to stop and create a decision request when
*a required normative artifact is absent* or *two approved artifacts conflict*.
Both conditions are currently met. This record raises them; it does not resolve them.

No approval authority is claimed here. Per the BST-SA authority model, an agent may
analyse and recommend; it may not self-authorize execution or declare a gate realized.

---

## 2. Question

Phases 0–3 are recorded as completed. `BOPEN-ARCH-PLAN-001` §2 defines a five-layer
production blueprint. Four of those five layers have no implementation in the repository.

Should Phase 4 (Common Business Foundations & Satellite Products) open on the current
baseline, or should a **Phase 3.5 Runtime Realization** work package be inserted first?

---

## 3. Findings of fact

### 3.1 Blueprint conformance

`BOPEN-ARCH-PLAN-001` §2 and §3 bind the production stack. Measured against the tree at
`3f53fa294296afdb2cbdd1f8f3521df5ef483689`:

| Blueprint layer | Bound technology | Implementation present |
| :--- | :--- | :--- |
| 1. API Gateway | TypeScript / Node.js + Hono + Zod | **None.** `package.json` declares no dependencies |
| 2. Enterprise SSO / IdP Bridge | BoxyHQ Jackson, SAML 2.0 / OIDC / SCIM 2.0 | **Simulated.** `idp_bridge.py` performs no network or protocol operation |
| 3. Platform Kernel Core | Python 3.12 + FastAPI + Pydantic v2 | **None.** No FastAPI or Pydantic import exists |
| 4. Database & Persistence | PostgreSQL 16 + RLS + psycopg3 | **Unexecuted.** DDL exists; no driver, connection or migration runner exists |
| 5. Event Microservices | Go 1.22 + Gin / Fiber | **None.** No Go source file exists |

The kernel is presently 3,864 lines of in-process Python holding state in approximately
60 in-memory dictionaries. It is a behavioural model of the specification, not a runtime.

### 3.2 Consequence for tenant isolation

`AGENTS.md` §8 requires *database enforcement, not only application filtering*, and §14
requires that *database security policies must be tested as database behavior*.

`tests/isolation/test_tenant_isolation.py` satisfies neither. Its fixture is a Python list
and its query function is a list comprehension. It establishes that Python filtering works.
It establishes nothing about the Row-Level Security policies in
`001_tenant_isolation_baseline.sql`, which have never been executed by any automated check.

Tenant isolation — the primary security property of a multi-tenant kernel — is therefore
**asserted but unverified** across all three completed phases.

### 3.3 Evidence anchoring defect

`docs/evidence/phase-3/manifest.json` and `docs/evidence/phase-3/completion-decision.md`
both bind candidate commit `f59bbd289196b02a2818967b2d5a32b0728c306d`.

That object does not exist in the repository. The actual implementation commit is
`f59bbd23bb82e3f42a80c6b41c6f40c47bd4245e`. The two values share only the seven-character
prefix `f59bbd2`; the remaining 33 characters of the recorded value are unsourced.

A completion decision bound to a non-existent object cannot be re-verified, which defeats
the purpose of the manifest.

### 3.4 Conflicting approved artifacts

| Artifact | Assertion |
| :--- | :--- |
| `AGENTS.md` §3.1 | "Phase 2 code mutation is NOT yet authorized" — names `membership.py`, `idp_bridge.py`, `context.ts`, `context.py` as files that must not be created before the gate |
| `DECISION-REGISTER` DEC-0009..DEC-0011 | Records the same gate items as **Approved** via `DEC-P2-DOCKET` |
| Repository state | All four named files exist |
| `PHASE-OUTLINE-SPEC.md` | Phase 2 "NEXT IMMEDIATE FOCUS", Phase 3 "FUTURE MILESTONE" |
| `docs/evidence/phase-3/completion-decision.md` | Phase 3 "COMPLETED" |

`AGENTS.md` is rank 1 in the §4 source-of-truth hierarchy. It has drifted out of agreement
with the decision register and with the tree. On the evidence of `DEC-P2-DOCKET` the
underlying authorization does exist; the defect is that the rank-1 artifact was never
updated to reflect it. Any agent following §5 step 1 today reads a prohibition that the
authorities have already lifted.

### 3.5 Root cause — §19.6 has no evidence-quality floor

`AGENTS.md` §19.6 realizes gate authorization through "100% passing automated test suites,
contract schema validation, repository validation tools, clean-room checks, and evidence
packages", explicitly in place of human sign-off.

The clause places full gate authority on the test suite but constrains neither the strength
of that suite nor its independence from the implementer. In practice the same agent authors
the implementation, the tests that judge it, and the evidence package that records the
verdict. A suite that exercises only in-memory behaviour will pass at 100% while the
governing invariant is unimplemented.

This is observable in the current baseline: 169 of 169 tests pass while
`RateLimitDecision.to_dict()` violates its own frozen schema
(`contracts/schemas/rate-limit-decision.schema.json`). The schema is loaded by the contract
suite but `jsonschema.validate()` is never applied to a `RateLimitDecision` instance.
The suite passes because it does not look, not because the contract holds.

§19.6 is not wrong to remove the human quorum. It is incomplete: it never states what makes
evidence admissible. Until it does, every future phase can be realized against evidence of
arbitrary weakness, and this outcome will recur.

---

## 4. Options

**Option A — Open Phase 4 on the current baseline.**
Satellite products (bPro, bFleet, PropTech, bERP, LDM) would integrate by importing
`kernel_core` in-process. Each product would then hold its own copy of tenant, membership
and entitlement state. The kernel would stop being a boundary and become a shared library,
which contradicts invariant §7.2 (tenant as isolation boundary) and forfeits the reason
bOPEN exists. Rejected on architectural grounds.

**Option B — Retro-fit the runtime during Phase 4.**
Defers the same work while adding five product surfaces that depend on it. The persistence
contract would be set by whichever product lands first rather than by the kernel. Rejected
on sequencing grounds.

**Option C — Insert Phase 3.5 Runtime Realization before Phase 4.** *(recommended)*
Convert the specification model into a running system, layer by layer, with each layer
proven by evidence that executes against the real dependency. Phase 4 opens on a kernel
that satellite products can actually call over a network boundary.

---

## 5. Recommendation

Adopt **Option C**, sequenced by dependency:

| ID | Deliverable | Rationale |
| :--- | :--- | :--- |
| `WP-P35-01` | PostgreSQL persistence and tenant-scoped session layer (psycopg3) | Removes the in-memory substrate. Quota balance, transactional outbox and RLS become structural properties rather than claims |
| `WP-P35-02` | Kernel HTTP surface (FastAPI + Pydantic v2) | The point at which bOPEN becomes callable by anything other than itself |
| `WP-P35-03` | Signed context token (`sub`, `tid`, `mid`, `roles`, `scopes`) | Without it, active context cannot survive a process boundary and cross-service tenancy is unenforceable |
| `WP-P35-04` | API gateway header and schema validation (Hono + Zod) | Binds `sdk/headers/HTTP_HEADER_SPEC.md` to executable behaviour |
| `WP-P35-05` | Enterprise IdP bridge integration | Replaces the simulated SSO surface |

Go microservices (blueprint layer 5) are **deferred**, not cancelled. Introducing a third
language runtime before layers 1–4 exist adds operational cost against no measured load.
Recommend a `DEC` record when metering throughput is observed rather than projected.

### 5.1 Companion amendment to §19.6

Runtime work alone does not close the root cause in §3.5. Recommend amending §19.6 to
define an admissibility floor for evidence. Suggested minimum:

1. **Executed, not simulated.** Evidence for an infrastructure-enforced invariant must be
   produced by executing against that infrastructure. A test that substitutes an in-process
   fake for the governing mechanism is inadmissible for that invariant.
2. **Traced.** Every normative invariant in scope carries a named test ID in the phase
   invariant-traceability record. An untraced invariant counts as unverified, not as passed.
3. **Machine-anchored.** Commit and tree OIDs in an evidence manifest are emitted by a tool
   that reads them from git, never transcribed by an agent. A manifest whose OIDs do not
   resolve is rejected before its test results are read.
4. **Adversarial.** Each security-relevant invariant carries at least one negative probe
   asserting that the violating operation is refused.

These four rules are mechanically checkable and preserve §19.6's removal of human quorum.
They constrain evidence quality, not who signs.

---

## 6. Impact

- Phase 4 entry is deferred until `WP-P35-01`..`WP-P35-03` report admissible evidence.
- No approved normative specification changes. `BOPEN-MOD-001`, `BOPEN-ENT-001`,
  `BOPEN-TENANT-001` and `BOPEN-AUTHZ-001` are implemented, not amended.
- Migrations remain append-only per §14. `001` and `002` are not edited.
- Phase 1–3 completion records require status correction, not retraction of the work. The
  implementations exist and are specification-shaped; what is absent is execution and
  admissible proof. Recommended status for all three: `IMPLEMENTED_UNVERIFIED` pending
  re-verification under §5.1.

---

## 7. Residual risk if not adopted

Satellite product teams would build against a kernel whose isolation guarantee has never
been executed. The first execution of that guarantee would then occur in production, on
multi-tenant customer data, across five products at once.

---

## 8. Decision and approver

| Field | Value |
| :--- | :--- |
| **Decision** | *Pending* |
| **Approver** | *Not assigned — Architecture Authority & Engineering Authority* |
| **Security review** | *Not assigned* |
| **Agent authority** | Advisory only. `execution_authority: false`, `approval_authority: false` |

---

## 9. Provenance

Raised by Claude (agent, Cortex role) on 2026-07-30 against tree
`abb2badee27b3926ae0016aa9eeb98f00cecf63b` at commit
`3f53fa294296afdb2cbdd1f8f3521df5ef483689`, branch
`claude/BOPEN-P2-001-membership-onboarding`.

Findings in §3.1–§3.4 were established by direct inspection of the tree. §3.3 was
established by `git cat-file -t` against both the recorded and the actual object.
