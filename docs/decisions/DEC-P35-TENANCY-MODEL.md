# DEC-P35-TENANCY-MODEL — Should tenant isolation move from row-level security to database-per-tenant?

**Decision ID:** `DEC-P35-TENANCY-MODEL`
**Version:** `1.0.0`
**Status:** **Proposed — decision request raised under `AGENTS.md` §16**
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
| **Decision** | *Pending* |
| **Approver** | *Not assigned — Architecture Authority* |
| **Security review** | *Not assigned* |
| **Agent authority** | Advisory only. `execution_authority: false`, `approval_authority: false` |

Nothing in this record changes a contract, migration, specification or production source.
