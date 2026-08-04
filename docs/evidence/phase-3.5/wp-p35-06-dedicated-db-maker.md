# EVD-P35-06-DEDICATED-DB-MAKER — Dedicated-database provisioning

**Document ID:** `EVD-P35-06-DEDICATED-DB-MAKER`
**Version:** `1.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision
**Issued:** 2026-08-04
**Implements:** [`DEC-P35-TENANCY-MODEL`](../../decisions/DEC-P35-TENANCY-MODEL.md) §10 (authorized); [`PLAN-P35-06-DEDICATED-DB`](../../01-product/WP-P35-06-dedicated-db-provisioning-plan.md)
**Candidate:** `d8dd023` (supersedes `ec14c53`, whose permissive RLS the verifier narrowed — see §5)
**Blob — `015_placement_identity.sql`:** `3d4f230c43f35fc5db3dbc6b9d9346a448c8dffc`
**Blob — `provision_dedicated_db.py`:** `38d69d47d8da676c477942ea29f71342427ff5e9`
**Blob — `db_bootstrap.py`:** `fdc61fe7092d7ceac5abc9044260e889c43d0fec`
**Blob — `test_dedicated_placement.py`:** `05c4f04e1e630be68ac1dcf2e96190369f4eb357`
**Blob — `invariant-traceability.csv`:** `2b8dc5c7a51fcb489a372a94edb9fcd14aa1eb47`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifier:** Codex
**Suites:** canonical **547/547** against PostgreSQL, with a **second real database** provisioned (8 dedicated probes added)

---

## 1. What this is — and the one property it defends

The provisioning that makes "one tenant, one database" real. The placement seam already *resolved* a
dedicated tenant to a URL and stood ready to *verify* it; nothing *created* the database it routes to
(`placement_identity` was created by no migration or tool, and every test used a fake URL). This
slice provisions a real dedicated database and proves the routing end to end across **two** live
PostgreSQL databases.

The defended property: **a dedicated tenant's data physically lives in its own database and is
absent from the shared pool, and a mis-configured route is refused loudly rather than read as
empty.** The keystone is `INV-DEDI-MISROUTE-REFUSED-01` — the one failure row-level security cannot
catch (in the wrong database the session is correctly scoped to a tenant with no rows, so it reads
"no data" instead of "refused") becomes a loud refusal via `verify_connection_serves`.

**Clean-room (`AGENTS.md` §6):** independently designed hybrid-placement provisioning; no upstream
multi-tenant framework's provisioning code was adapted.

## 2. Defensive verification

Every proposition asserts the platform **routes** a dedicated tenant to its own database and
**refuses** a mis-route or an unconfigured dedicated tenant. No offensive objective; the two
databases are local verification instances.

## 3. Propositions (traced in `invariant-traceability.csv`)

`tests/isolation/test_dedicated_placement.py`, executed SQL across two databases:

| ID | The kernel must… | Test |
| :--- | :--- | :--- |
| `P4-DEDI-01` | write a dedicated tenant's data into its own database | `test_a_dedicated_tenants_write_lands_in_its_own_database` |
| `P4-DEDI-02` | keep that data physically absent from the shared pool | `test_that_write_is_absent_from_the_shared_pool` |
| `P4-DEDI-03` | keep a shared tenant from reaching dedicated data through the kernel | `test_a_shared_tenant_cannot_reach_dedicated_data_through_the_kernel` |
| `P4-DEDI-04` | **refuse a database that does not declare it serves the tenant** (keystone) | `test_a_misdeclared_dedicated_database_is_refused` |
| `P4-DEDI-05` | refuse a dedicated tenant with no configured connection | `test_an_unconfigured_dedicated_tenant_is_refused` |
| `P4-DEDI-06` | refuse a dedicated database declaring a second tenant | `test_the_dedicated_database_cannot_declare_a_second_tenant` |
| `P4-DEDI-07` | keep the identity declaration invisible to another tenant's scope | `test_the_identity_is_invisible_to_another_tenants_scope` |

**Attack angle for the verifier:** point a second dedicated tenant's `BOPEN_DEDICATED_DB__<ref2>` at
the existing dedicated database (which declares tenant A) and open a session for that second tenant —
it must raise `PlacementUnresolved`, not silently read A's empty-to-it database; provision, then
query the dedicated database directly for the party and confirm it is there and **not** in the
shared pool; try to insert a second `placement_identity` row (must be refused by the singleton PK).

## 4. Execution

```text
python tools/run_tests.py     547/547 OK   (live PostgreSQL, a second DB provisioned)
```

- **Migration 015** adds `placement_identity` (single-row: `singleton` PK + `CHECK singleton=true`),
  the declaration `verify_connection_serves` reads.
- **`tools/provision_dedicated_db.py`** creates the target database, applies the **full ledger** via
  the same `db_bootstrap.apply_ledger_to` the shared pool uses (a dedicated DB is the same schema,
  not a variant), marks the control registry row `dedicated`, and seeds the dedicated database's
  single `tenants` row and `placement_identity`. The connection URL is never written to a table.
- **`db_bootstrap`** gains `apply_ledger_to(target_url, …)`, extracted from `cmd_apply` so the
  shared-pool bootstrap and dedicated provisioning apply the same migrations by the same code. The
  shared-pool bootstrap is behaviourally unchanged (re-verified by re-running `--apply`).

## 5. `placement_identity` carries a tenant-matching RLS policy (corrected after verifier refutation)

`PLAN-P35-06-DEDICATED-DB` §2.1–§2.2 said `placement_identity` would carry **no** row-level security
because it is not tenant data. Building it, the structural test
`test_every_table_in_the_schema_is_classified_and_protected` correctly refused a new table with no
RLS — every table must be ENABLE + FORCE, so absence can never be a silent open door (the control
that would have caught the 007 disclosure).

The first candidate `ec14c53` then carried **permissive** policies (`SELECT USING (true)`), with a
maker rationale that a tenant-matching policy "would hide the row from the very check that needs it".
**The verifier disproved that by execution** (candidate `ec14c53` keystone ballot): a tenant-matching
policy still admits the served tenant (so `verify_connection_serves` works), still makes a mis-route
return zero rows and refuse, **and** additionally stops another tenant's scope from reading the
served-tenant id that `USING (true)` exposed. The permissive policy was broader than necessary and
the rationale was wrong.

So the policy is now **tenant-matching** (`USING`/`WITH CHECK tenant_id = current_setting(...)`, no
UPDATE/DELETE — write-once), seeded under the served tenant's scope by the provisioning tool. It
reinforces `verify_connection_serves` rather than relying on it alone, and exposes the identity to no
other tenant's scope. The new probe `INV-DEDI-IDENTITY-SCOPED-01` asserts that invisibility. The
correction is recorded here and in the migration rather than quietly swapped.

## 6. What this does NOT establish (disclosed)

1. **The auth chain is not yet usable for a dedicated tenant — a cross-database foreign-key gap,
   reproduced.** `principals` and the `tenants` registry are *global* (`system_session`, control
   database), while `memberships` and `contexts` are *routed* (`tenant_session`, the dedicated
   database). `memberships.principal_id` has a foreign key to `principals(id)` (migration 001). So
   creating a membership for a dedicated tenant inserts into the dedicated database a row that
   references a principal present only in the control database, and PostgreSQL raises
   `ForeignKeyViolation: memberships_principal_id_fkey` (reproduced 2026-08-04). **A dedicated tenant
   therefore cannot yet be given a membership, hence no context, hence no working auth chain.** This
   slice provisions the database and proves *domain-data* routing and mis-route refusal; it does not
   establish a usable dedicated tenant end to end. Resolving this is the next slice — the options
   are: drop the `memberships→principals` FK (the migration-009 "survives its referent" pattern),
   replicate the needed principals into each dedicated database, or route principals too (which
   conflicts with principals being global/multi-tenant). This is an **architecture decision** for the
   operator, not a maker choice.
2. **"One tenant, one database" here means the tenant's *domain* data.** Parties, workflow, money,
   resources, memberships and contexts route to the dedicated database; the *global* registry
   (principals, and the tenant's own registry row that is the routing authority) stays in the control
   database by design. The claim proven is physical placement and isolation of the tenant's domain
   data, not that every byte naming the tenant lives in one database.
3. **New dedicated tenants only.** The **trial→paid data migration** (moving an existing shared-pool
   tenant's rows into a fresh dedicated database) is deferred — cross-database, its own atomicity
   design (`PLAN` §2.4). Note this interacts with gap 1: a trial→paid move must also carry or
   reconcile the tenant's principals.
4. **No connection pooling** per dedicated database; each `tenant_session` opens and closes a
   connection (the seam's existing behaviour).
5. **No deprovisioning / backup / DR** for dedicated databases yet.
6. **One verifier, not two** (two-agent profile).

## 7. Authority

A maker's submission. `EBIV` §8: a passing suite carries no verdict weight.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
