# WP-P35-06 — Dedicated-database provisioning, design & first-slice plan

**Document ID:** `PLAN-P35-06-DEDICATED-DB`
**Version:** `1.0.0`
**Status:** **Design — advisory. Buildable on operator authorization.** Extends the disposed WP-P35-06 placement seam ([`EVD-P35-06-DISPOSITION`](../evidence/phase-3.5/wp-p35-06-disposition.md)) with the carried "no dedicated DB provisioned" item.
**Issued:** 2026-08-03
**Raised by:** Claude (agent, Motor role) — advisory only
**Governing:** [`DEC-P35-TENANCY-MODEL`](../decisions/DEC-P35-TENANCY-MODEL.md) §8 (Option D hybrid), §9 (Option C strict); `AGENTS.md` §8

---

## 1. Where this picks up

The placement **seam** is built and disposed: `db.tenant_session` resolves every tenant through
`placement.resolve_placement` fail-closed, and `verify_connection_serves` is ready to refuse a
mis-routed dedicated connection. What does **not** exist yet is any way to *create* a dedicated
database for a tenant to be routed to. Two facts establish the gap precisely:

1. `placement_identity` — the table `verify_connection_serves` reads to confirm a dedicated database
   serves exactly one named tenant — is created by **no migration and no tool**. It exists only as a
   name in `placement.py`.
2. Every test today configures a dedicated placement with a **fake** URL (`postgresql://x/y`) and
   asserts only the *resolution*. **No real second database has ever held a tenant's row.**

So "one tenant, one database" is decided, wired for resolution, and unproven end to end. This plan is
the slice that makes it real and demonstrable — and it is **isolation-critical**, because a
mis-route is the one tenant-isolation failure row-level security cannot catch (in the wrong database
the session is correctly scoped to a tenant that simply has no rows there, so the caller reads "no
data" instead of a refusal). That is why it is designed before it is built.

## 2. The design decisions this slice commits to

### 2.1 A dedicated database is the *same schema*, single-tenant

A dedicated database is provisioned with the **identical migration set** the shared pool runs — same
tables, same `FORCE ROW LEVEL SECURITY`, same policies, same foreign keys. It is not a stripped
variant. The only differences are *data*:

- its `tenants` table holds exactly **one** row — the tenant it serves — so the foreign keys every
  tenant-scoped table declares (`tenant_id → tenants(id)`) and the RLS policies remain intact and
  identical to the shared pool. Nothing about a table's definition changes by placement.
- it carries a `placement_identity` row naming that one tenant.

The **authority** for placement stays in the control connection (`BOPEN_DATABASE_URL`): the control
`tenants` row is what `resolve_placement` reads and what carries `placement_kind='dedicated'` and the
`placement_ref`. The dedicated database's own single `tenants` row exists only to keep its local
schema self-consistent (FKs, RLS), not to route. This matches the seam's rule — "only tenant *data*
moves to a dedicated database" — with the minimum a self-contained schema needs to stand up.

### 2.2 `placement_identity` becomes migration 015 (uniform schema, seeded per placement)

Rather than a dedicated-only DDL that would make the two schemas diverge, `placement_identity` is a
normal migration applied everywhere:

```sql
-- 015: a database's declaration of the single tenant it serves (empty in the shared pool).
CREATE TABLE placement_identity (
    tenant_id UUID NOT NULL,
    singleton BOOLEAN NOT NULL DEFAULT true,
    CONSTRAINT pk_placement_identity PRIMARY KEY (singleton),   -- at most one row, ever
    CONSTRAINT chk_placement_identity_singleton CHECK (singleton = true)
);
```

- In the **shared pool / control** database it stays **empty** — `verify_connection_serves` never
  reads it there (it returns early for `SHARED_POOL`), so an empty table is correct and inert.
- In a **dedicated** database the provisioning tool inserts exactly one row: the served tenant. The
  single-row constraint makes "this database serves two tenants" unrepresentable, so a provisioning
  bug cannot silently produce a shared-by-accident dedicated database.

### 2.3 The provisioning tool

A new retained utility, `tools/provision_dedicated_db.py` (Rule 13; monitoring/deployment class),
that given `--tenant-id`, `--ref`, `--target-url` (and admin credentials):

1. creates the target database (idempotent; refuses to clobber a non-empty one);
2. applies the **full migration ledger** to it, reusing `db_bootstrap`'s applier parameterized by
   target database (the applier is currently hard-coded to `bopen_dev` — this slice parameterizes it,
   which also lets the shared pool keep using it unchanged);
3. seeds the one `tenants` row (id, name, `placement_kind='dedicated'`, `placement_ref=<ref>`) and
   the one `placement_identity` row;
4. marks the **control** `tenants` row `placement_kind='dedicated', placement_ref=<ref>` (the routing
   authority);
5. prints the `BOPEN_DEDICATED_DB__<ref>` line to export, and never writes the URL to any table
   (the seam keeps the connection secret in the environment, not the registry).

### 2.4 Scope line — new dedicated tenants only

| In scope | Out of scope (later slices) |
| :--- | :--- |
| Provision a **new** dedicated tenant into its own database | **Trial→paid data migration** — copying an existing shared-pool tenant's rows into a fresh dedicated DB (cross-database, needs its own atomicity design; the harder half) |
| `placement_identity` (migration 015) + the provisioning tool | Automated deprovisioning / tenant deletion across databases |
| End-to-end cross-database isolation test + a demo | Connection pooling / per-dedicated-DB pool management |
| `verify_connection_serves` proven against a real mis-declared DB | Dedicated-DB backup/DR wiring |

The trial→paid migration is explicitly deferred and named, because attempting it in the same slice
would couple a routing feature to a cross-database data-move with its own failure modes.

## 3. Invariants to verify (R4 negative probes, drafted early)

Each carries an executed test and a row in `invariant-traceability.csv` before any ballot. These run
against **two real databases** (guarded on `BOPEN_ADMIN_DATABASE_URL`, skipping loud if absent):

- `INV-DEDI-ROUTE-01` — a dedicated tenant's write lands in **its** database: after the write, the
  row is present when the dedicated DB is queried directly.
- `INV-DEDI-ISOLATION-01` — that same row is **absent** from the shared pool, queried directly —
  the data physically is not there.
- `INV-DEDI-CROSS-DB-01` — a shared-pool tenant B cannot read the dedicated tenant A's data through
  the kernel (404), across the physical database boundary.
- `INV-DEDI-MISROUTE-REFUSED-01` — a dedicated database whose `placement_identity` is absent or
  names a **different** tenant is **refused** by `verify_connection_serves`, not used — a
  mis-configured `BOPEN_DEDICATED_DB__<ref>` is a loud failure, not a silent empty read.
- `INV-DEDI-UNCONFIGURED-REFUSED-01` — a dedicated tenant with no `BOPEN_DEDICATED_DB__<ref>` set is
  refused, never defaulted into the shared pool (already covered by placement resolution; re-asserted
  end to end here).
- `INV-DEDI-SINGLETON-01` — the dedicated database cannot be made to declare a second served tenant
  (the single-row constraint on `placement_identity`).

`INV-DEDI-MISROUTE-REFUSED-01` is the keystone: it is the test that a wrong route becomes a refusal
rather than the invisible cross-tenant read this whole seam exists to prevent.

## 4. How it plugs into the proven seam (reuse, not reinvent)

- **Resolution**: unchanged — `resolve_placement` already reads the control registry and returns the
  dedicated URL from the environment. This slice only makes the target it returns real.
- **Verification**: unchanged — `verify_connection_serves` already queries `placement_identity`; this
  slice creates and seeds that table so the query has something true to read.
- **Schema**: one new migration (015) applied by the same applier to every database.
- **Kernel code**: **none changed** on the request path. The seam is disposed; this slice provisions
  the databases it routes to and proves the routing. (The one code change is parameterizing
  `db_bootstrap`'s applier by target database — a tool, not the kernel.)

## 5. The maker cycle (same governance)

Design (this doc) → operator authorization recorded **before build** (the §7/§8 lesson) →
tests-first (the cross-database probes, red before migration 015 and the tool exist) → migration 015
+ provisioning tool → execute against **two live PostgreSQL databases** → trace invariants (R2) →
maker submission → **Codex** independent ballot (defensive framing: confirm the kernel *refuses* a
mis-route and *routes* a valid one) → operator disposition under EBIV §6.5.

## 6. Why design-first, and why this is the right next placement build

A mis-route is the isolation failure RLS cannot catch, and provisioning is where a mis-route is
introduced — a wrong `placement_identity` seed, a dedicated DB pointed at the wrong URL, a data table
provisioned without its RLS policy. Improvising this inside a test fixture would create an unofficial
provisioning path that does not match how a real dedicated tenant is stood up, and would prove the
fixture rather than the mechanism. Designing the provisioning tool and the `placement_identity`
contract first means the test exercises the **real** path, and the keystone probe
(`INV-DEDI-MISROUTE-REFUSED-01`) is meaningful.

It is the right next placement build because it converts "one tenant, one database" from a decided-
and-wired promise into a demonstrated, adversarially-verified property — the tangible proof of the
hybrid tenancy model the platform is committed to — without touching the disposed request path.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
