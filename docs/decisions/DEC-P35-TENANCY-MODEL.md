# DEC-P35-TENANCY-MODEL — Should tenant isolation move from row-level security to database-per-tenant?

**Decision ID:** `DEC-P35-TENANCY-MODEL`
**Version:** `1.0.0`
**Status:** **Approved — Option D adopted 2026-07-31 (see §8, which supersedes §7)**
**Issued:** 2026-07-31
**Owner:** Architecture Authority
**Required concurrence:** Engineering Authority, Security Authority, Data Authority
**Raised by:** Claude (agent, Motor role) — advisory only, no approval authority
**Governing artifacts:** `BOPEN-ARCH-001`; `BOPEN-TENANT-001`; `ADR-0005`; `BOPEN-ARCH-TECH-001` (technology matrix); `AGENTS.md` §6, §7, §8, §14, §16
**Trigger:** operator request of 2026-07-31 to adopt an ERPNext/Frappe-style tenancy model *"to avoid overload on one database system"*

---

## 1. Why this record exists rather than an implementation

`AGENTS.md` §16 requires a decision request when a change would alter an approved tenant
isolation strategy. Three approved artifacts currently bind the present model:

| Artifact | Binding |
| :--- | :--- |
| `BOPEN-ARCH-001` §Phase 1 | code *"must enforce deny-by-default access, PostgreSQL Row-Level Security"* |
| `ADR-0005` / technology matrix | PostgreSQL + RLS scored **9.25/10**, recorded **SELECTED CANDIDATE** |
| `AGENTS.md` §7 invariant 10 | tenant-owned data requires an **approved** ownership and isolation strategy |

An agent changing these by writing code would be resolving reserved architecture by
implementation default, which `DEC-P35-RUNTIME` exists to prevent.

## 2. Clean-room constraint on the request as phrased

The request says *"clone the ERPNext (Frappe)"*. `AGENTS.md` §6 prohibits copying or translating
upstream source into bOPEN code, renaming upstream tables or classes and treating them as
original design, and importing upstream migrations into production zones.

**Adopting the pattern is permitted; cloning the source is not.** The allowed route is the §6
flow — `Observation → Evidence → Finding → Requirement/ADR → Contract → Independent
implementation`. Every option below assumes independent implementation. None assumes Frappe
source enters this repository outside `research/upstream/`.

Note also that Frappe runs on MariaDB, which the technology matrix records as **rejected** for
this platform on the specific ground of *"weak native RLS"*. Adopting Frappe's model wholesale
would reverse that too.

## 3. The stated driver, examined

The reason given is load: avoiding overload on one database system. That concern is legitimate
and worth designing for. The question is whether database-per-tenant is what addresses it.

**Finding 3.1 — separate databases do not distribute load; separate *instances* do.**
Fifty databases on one PostgreSQL server share one buffer pool, one WAL writer, one CPU
allocation and one connection limit. Splitting a schema into fifty databases on that server does
not reduce its work. It adds per-database overhead: fifty catalogs, fifty autovacuum targets,
fifty connection pools, fifty migration runs and fifty backup streams. Under most load profiles
this is **more** total resource use, not less.

**Finding 3.2 — the lever that does address load is orthogonal to the isolation mechanism.**
Placing tenants on different database instances distributes load. That works with row-level
security exactly as well as with separate databases: shard tenants across N PostgreSQL clusters
and keep RLS inside each. The choice of "RLS or separate database" and the choice of "one
instance or many" are independent axes, and only the second one is about load.

**Finding 3.3 — Frappe's site model is not primarily a load design.**
Each Frappe site carries its own installed apps, custom fields and schema mutations, so a site
needs its own database because tenants can have *structurally different schemas*. bOPEN's
premise is the opposite: `BOPEN-MOD-001` composes products from versioned capability contracts
against one governed schema. Adopting the site model would import a constraint that exists to
solve a problem bOPEN has deliberately designed out.

**Finding 3.4 — there is no measured load.**
bOPEN has no production deployment and no observed throughput. This repository has already set
a precedent on exactly this question: `DEC-P35-RUNTIME` §5 deferred Go event microservices
because introducing a runtime *"before layers 1–4 exist adds operational cost against no
measured load"*, and recommended revisiting *"when metering throughput is observed rather than
projected"*. The same standard applied here argues against re-architecting isolation now.

**Finding 3.5 — what the change would cost.**
16 tables under `ROW LEVEL SECURITY`, 5 migrations that define policies, and 38 isolation tests
that execute against them. Under database-per-tenant these become provisioning code and
per-database migration orchestration. The 38 executed isolation tests — currently the strongest
evidence bOPEN has of anything — would be testing a mechanism that no longer exists.

## 4. Options

**Option A — keep RLS on a single instance (status quo).**
No change. Adequate until measured load says otherwise. Does not address the operator's concern
if load is genuinely anticipated.

**Option B — database-per-tenant, Frappe-style, independently implemented.**
Strongest blast-radius isolation: a policy bug cannot cross a database boundary. Costs: reverses
`ADR-0005` and `BOPEN-ARCH-001`; discards 16 tables of policy and 38 executed isolation tests;
adds per-tenant migration orchestration, connection-pool multiplication, and cross-tenant
reporting difficulty; makes tenant provisioning a heavyweight operation. Per Finding 3.1 it does
not by itself reduce load on one server.

**Option C — shard tenants across PostgreSQL instances, RLS within each shard.** *(recommended)*
Directly addresses the stated driver. Tenants are routed to one of N instances by a tenant→shard
map; each instance keeps the existing schema, policies and tests unchanged. Load is distributed
by adding instances. `ADR-0005` stands. All 38 isolation tests keep their meaning and keep
running. Cost: a routing layer and a shard map, plus care that `db.tenant_session` resolves the
right instance. This is the smallest change that solves the problem actually stated.

**Option D — hybrid: RLS by default, dedicated database for named tenants.**
Most tenants share an RLS instance; large, regulated or noisy tenants get their own database.
`AGENTS.md` §8 already contemplates this — it requires *"explicit tenant ownership field **or
approved physical isolation**"* — so the invariant does not need amending. Gives Option B's
isolation exactly where it is worth paying for, without paying for it everywhere. Cost: two
provisioning paths and a placement decision per tenant.

## 5. Recommendation

**Adopt Option C now, and Option D when a tenant's requirements justify it.** Option B should be
adopted only if the driver turns out to be regulatory or blast-radius isolation rather than
load — in which case the honest framing is a security decision, not a scaling one, and it should
be argued on those terms.

If the authorities prefer Option B regardless, this record should be superseded by an ADR that
explicitly retires `ADR-0005`, restates `BOPEN-ARCH-001`'s isolation clause, and schedules
replacement of the 38 isolation tests before the old ones are deleted — never after.

## 6. What would unblock a decision

One measurement, which does not exist yet: projected tenant count, and read/write throughput per
tenant at the intended scale. Finding 3.1 turns on whether the bottleneck is CPU, connections or
IO, and that is measurable rather than arguable. This repository priced the identifier-format
decision by measurement rather than argument; the same is available here.

## 7. Decision and approver

| Field | Value |
| :--- | :--- |
| **Decision** | **ACCEPT — Option C.** Tenants are sharded across PostgreSQL instances; row-level security is retained within each shard. `ADR-0005` and `BOPEN-ARCH-001`'s isolation clause stand unchanged |
| **Driver recorded** | **Load and scale headroom** — not regulatory or blast-radius isolation. This matters: had the driver been isolation, Option B would have been stronger and Security Authority concurrence would have been required |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — acting as Architecture Authority |
| **Decision timestamp** | 2026-07-31 |
| **Security review** | Not separately required. Option C **retains** every existing isolation control and adds no new trust boundary inside a shard. The routing layer it introduces is a new *correctness* surface, which §7.2 addresses |
| **Recorded by** | Claude (agent, Motor role), transcribing an operator decision. `execution_authority: false`, `approval_authority: false` |

Option D remains available per case without a further architecture decision, because
`AGENTS.md` §8 already permits *"explicit tenant ownership field or approved physical
isolation"*. A tenant needing its own database can be placed on a single-tenant shard.

Option B is **not** adopted. Nothing in this record retires `ADR-0005`, amends `BOPEN-ARCH-001`,
or authorizes removing an isolation policy or test.

### 7.1 What this authorizes

Implementation of tenant→shard routing under a new work package, `WP-P35-06`. No migration is
altered. No RLS policy is removed. The 38 isolation tests keep running unchanged, and are now
required to run **per shard**.

### 7.2 The risk this introduces, stated before any code exists

Sharding moves a class of failure from "policy is wrong" to "routing is wrong". A tenant whose
requests reach the wrong shard is a **tenant isolation failure** — precisely what this platform
exists to prevent — and row-level security cannot catch it, because within the wrong shard the
session is correctly scoped to a tenant that has no data there. Silent wrong answers, not
refusals.

This is why implementation is specified before it is started, and why `WP-P35-06`'s acceptance
criteria require that mis-routing be *impossible* rather than *unlikely*.

Nothing in this record changes a contract, migration, specification or production source.

---

## 8. Amendment 2026-07-31 — Option D adopted, superseding §7

> **Change note (extend-only, per BST rule 5).** §7 is retained for provenance and **must not be
> read as the current decision**. §8 governs.
> **Reason**: §7 recorded the driver as *load, not isolation*, and said in terms that had the
> driver been isolation, Option B would have been stronger and Security Authority concurrence
> would have been required. The operator then stated a **privacy** requirement — tenant data is
> private, no cross-tenant data accessible. The premise of §7 no longer holds.
> **Benefit of the prior decision**: Option C was the cheapest way to answer a load question and
> preserved every existing control unchanged.
> **Expected outcome**: tenant privacy becomes a structural property rather than a policy
> promise, while row-level security survives where it is still the right tool.

### 8.1 Decision

**Option D — hybrid placement.**

| Placement | Who | Isolation mechanism |
| :--- | :--- | :--- |
| **Dedicated database** *(default)* | Every paying/production tenant | Physical separation. A policy bug cannot cross a database boundary |
| **Shared RLS pool** | Trial, free-tier and evaluation tenants, **who must be told so** | PostgreSQL row-level security, exactly as today |

Both placements distribute across instances, so §7's load answer is retained rather than
discarded — Option D is a superset of Option C, not a replacement for it.

### 8.2 What this does and does not retire

`ADR-0005` and `BOPEN-ARCH-001`'s row-level-security clause **stand**. RLS remains the mechanism
for the shared pool, so the 16 policy-bearing tables and the 38 executed isolation tests keep
their meaning and keep running. This is the principal advantage of Option D over Option B: no
evidence is discarded to gain the isolation.

`AGENTS.md` §8 already permits *"explicit tenant ownership field **or** approved physical
isolation"*, so no invariant is amended.

### 8.3 Security and privacy concurrence — recorded as NOT obtained

The tenancy change is a **tightening** and is ratified on that basis. The control-plane data
collection it requires is **not** a tightening: it is a new data flow out of tenant boundaries,
and it is privacy-bearing.

That boundary is specified separately in [`DEC-P35-CONTROL-PLANE`](DEC-P35-CONTROL-PLANE.md) and
**requires Security and Privacy Authority review before implementation**. It is not ratified
here, and an agent must not treat this record as authorizing it.

### 8.4 Consequence for `WP-P35-06`

Not withdrawn — **generalized**. Shard routing becomes *placement routing*: resolve a tenant to a
connection target, which may be a dedicated database or a shared pool. Every acceptance criterion
survives, and `A-09` (an unresolvable tenant is refused, never defaulted) becomes more important,
not less: under hybrid placement a wrong default could route a private tenant into the shared
pool.

### 8.5 Approver

| Field | Value |
| :--- | :--- |
| **Decision** | **ACCEPT — Option D.** Dedicated database per tenant by default; shared RLS pool for trial and free tier, disclosed to those tenants |
| **Driver** | **Tenant privacy**, with load retained as a secondary driver |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — acting as Architecture Authority |
| **Decision timestamp** | 2026-07-31 |
| **Security review** | **NOT OBTAINED.** Required for `DEC-P35-CONTROL-PLANE` before any collection is implemented |
| **Recorded by** | Claude (agent, Motor role). `execution_authority: false`, `approval_authority: false` |

---

## 9. Amendment 2026-08-03 — A-09 wiring interpretation (Option C, strict)

> **Change note (extend-only).** Trigger: implementing `WP-P35-06` surfaced that the entitlement
> tables (`002`) use `tenant_id VARCHAR(64)` with **no foreign key** to `tenants`, so some tenants
> have no registry row and a fail-closed resolver refuses them. This decides how A-09 ("an
> unresolvable tenant is refused, never defaulted") applies to them. An **independent immune review**
> (2026-08-03) found that defaulting unregistered tenants to the shared pool (the tempting small
> change) converts the resolver from *fail-closed* to *fail-open-to-shared* and re-opens the exact
> silent mis-route A-09 exists to close, resting tenant isolation on an unenforced cross-subsystem
> invariant. The operator ratified the strict option **for safety**.

### 9.1 Decision

**A-09 stays STRICT — an unresolvable tenant is refused, never defaulted.** Concretely (Option C):

1. **`resolve_placement` never defaults.** An unregistered tenant, an unknown placement kind, or an
   unroutable dedicated placement is refused. (The resolver as built already does this.)
2. **Placement is resolved once at the request/context boundary**, where the tenant has just
   authenticated and is therefore known-registered, and the resolved connection is threaded down via
   the existing `connection=` parameter — **not** re-resolved inside every `db.tenant_session` call.
   This keeps the fail-closed gate in one place and off the per-call hot path.
3. **Every tenant with tenant-scoped data must have a `tenants` registry row.** The 41 entitlement/
   metering test fixtures that deliberately skipped it are corrected to provision it; the
   entitlement→`tenants` foreign key (already raised as deferred in migration `004`) is scheduled so
   the database enforces this rather than a convention. Under this rule an orphan entitlement tenant
   becomes unreachable through the kernel — the strict gate delivers FK-grade integrity at the
   routing boundary.

### 9.2 Approver

| Field | Value |
| :--- | :--- |
| **Decision** | **ACCEPT — Option C (strict).** A-09 unconditional; resolve at the request boundary; every tenant registered (FK scheduled). Option B (default unregistered → shared) is **rejected** as a security-gate weakening |
| **Driver** | **Tenant isolation** — a mis-route is a silent wrong answer RLS cannot catch, so refuse-vs-default must be structural and unconditional |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — acting as Architecture Authority |
| **Decision timestamp** | 2026-08-03 |
| **Independent review** | Immune agent (advisory) recommended this option and flagged Option B as fail-open-to-shared; a Codex ballot on the implementation follows per `WP-P35-06` §6.5 |
| **Recorded by** | Claude (agent, Motor role), transcribing an operator decision. `execution_authority: false`, `approval_authority: false` |

### 9.3 Implementation note (2026-08-03)

The strict fail-closed resolution is now **wired into `db.tenant_session`** and the full canonical
suite passes (488/488) with every entitlement/metering test tenant registered per §9.1.3. The
security property in §9.1 — A-09 unconditional, no default, dedicated verified — is delivered and
proved by two new probes (`test_tenant_session_refuses_an_unregistered_tenant`,
`test_tenant_session_serves_a_registered_shared_pool_tenant`).

**Deviation from §9.1.2, disclosed:** resolution is currently done **per `tenant_session` call**, not
once at the request boundary. This delivers the identical security property (each call resolves
fail-closed and verifies a dedicated connection) but runs one extra placement read per tenant-scoped
call and surfaces a refusal inside a repository operation rather than at request admission.
Resolving once at the boundary and threading the connection down (`repositories.py` methods would
gain a `connection=` parameter, as `entitlement_repositories.py` already has) is a **tracked
refinement** in `WP-P35-06`, not a security gap. This maker note is subject to the Codex ballot.

---

## 10. Amendment 2026-08-04 — dedicated-database provisioning authorized

> **Change note (extend-only).** §8.4 recorded that `WP-P35-06` carries the placement seam and that
> actually *provisioning* a dedicated database was a disclosed, accepted follow-on. This authorizes
> that follow-on build, recorded **before any build** per the `DEC-P4-ENTRY` §7/§8 sequencing lesson.
> The design it authorizes is [`PLAN-P35-06-DEDICATED-DB`](../01-product/WP-P35-06-dedicated-db-provisioning-plan.md).

### 10.1 Decision

**The dedicated-database provisioning slice is AUTHORIZED**, exactly as scoped in
`PLAN-P35-06-DEDICATED-DB` §2 and §2.4. In scope: migration 015 (`placement_identity`, single-row),
a `provision_dedicated_db` tool that applies the full migration ledger to a target database and seeds
the identity, parameterizing the `db_bootstrap` applier by target database, and an end-to-end
cross-database isolation test proving a dedicated tenant's data lives in its own database and is
invisible to the shared pool — with the keystone probe `INV-DEDI-MISROUTE-REFUSED-01` (a wrong route
becomes a loud refusal, never a silent empty read). **Explicitly out of scope and deferred:** the
trial→paid cross-database data migration (`PLAN` §2.4), and any change to the disposed request path.

| Field | Value |
| :--- | :--- |
| **Decision** | **AUTHORIZE the dedicated-database provisioning slice** per `PLAN-P35-06-DEDICATED-DB`. Trial→paid data migration stays deferred |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — Architecture Authority |
| **Decision timestamp** | 2026-08-04 |
| **Recorded by** | Claude (agent, Motor role), transcribing an operator decision. `execution_authority: false`, `approval_authority: false` |

### 10.2 How it runs (governed, same loop)

Tests-first (the cross-database `INV-DEDI-*` probes, red before migration 015 and the tool exist) →
migration 015 + provisioning tool → execute against **two live PostgreSQL databases** → trace
invariants in `invariant-traceability.csv` (R2) → maker submission → **Codex** independent ballot
(defensive framing) → operator disposition under `EBIV` §6.5. No request-path kernel code changes.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```

---

## 11. Amendment 2026-08-04 — Option A: make a dedicated tenant usable end to end

> **Change note (extend-only).** §10's disposition disclosed, and the operator acknowledged, that a
> dedicated tenant cannot yet be given a membership: three routed tables foreign-key `principal_id`
> to the global `principals`, and that FK cannot be satisfied across databases. This authorizes the
> fix. Recorded **before any build** per the §7/§8 sequencing lesson.

### 11.1 The gap, precisely

`memberships` (001), `active_contexts` (003) and `audit_events` (003) each declare
`principal_id → principals(id)`. All three route to a dedicated tenant's database via
`tenant_session`, while `principals` is global in the control database (`system_session`). PostgreSQL
cannot enforce a foreign key across databases, so a dedicated tenant's routed rows raise
`ForeignKeyViolation` — reproduced 2026-08-04. A principal is deliberately multi-tenant, so it stays
global (routing it, or replicating it per dedicated database, both break that); the foreign key is
what must change.

### 11.2 Decision

**Option A is AUTHORIZED.** Drop the three `principal_id → principals` foreign keys (keeping the
columns as soft references), the same reasoning migration 009 applied to `audit_events.context_id`
("an audit record must survive its referent" — here, a routed row references a principal that lives
in another database by design). The application already validates principal existence
(`principals.get` in control; `POST /v1/contexts` checks the membership's principal), so the
integrity the database can no longer enforce across databases is still checked where it can be.

| Field | Value |
| :--- | :--- |
| **Decision** | **AUTHORIZE Option A** — a migration dropping the `principal_id` FKs on `memberships`, `active_contexts`, `audit_events` (columns kept), plus a test proving a dedicated tenant onboards end to end (principal in control, membership + context in its dedicated database, authorize succeeds) |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — Architecture Authority |
| **Decision timestamp** | 2026-08-04 |
| **Recorded by** | Claude (agent, Motor role), transcribing an operator decision. `execution_authority: false`, `approval_authority: false` |

### 11.3 Scope and how it runs

In scope: the FK-dropping migration; an end-to-end dedicated-tenant onboarding test (the "usable
dedicated tenant" proof the §10 slice lacks); the reproduction that the FK gap is closed. **Out of
scope:** orphan handling on principal deletion (principals have no DELETE policy after migration 007,
so it is not reachable today — recorded, not built); the trial→paid cross-database data migration
(still deferred). Governed cycle: tests-first → migration 016 → execute across two databases → trace
invariants (R2) → maker submission → **Codex** ballot → operator disposition.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
