# EVD-P35-06-DEDICATED-DB-MAKER — Dedicated-database provisioning

**Document ID:** `EVD-P35-06-DEDICATED-DB-MAKER`
**Version:** `1.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision
**Issued:** 2026-08-04
**Implements:** [`DEC-P35-TENANCY-MODEL`](../../decisions/DEC-P35-TENANCY-MODEL.md) §10 (authorized); [`PLAN-P35-06-DEDICATED-DB`](../../01-product/WP-P35-06-dedicated-db-provisioning-plan.md)
**Candidate:** the commit carrying this submission (filled on commit)
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifier:** Codex
**Suites:** canonical **546/546** against PostgreSQL, with a **second real database** provisioned (7 dedicated probes added)

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

**Attack angle for the verifier:** point a second dedicated tenant's `BOPEN_DEDICATED_DB__<ref2>` at
the existing dedicated database (which declares tenant A) and open a session for that second tenant —
it must raise `PlacementUnresolved`, not silently read A's empty-to-it database; provision, then
query the dedicated database directly for the party and confirm it is there and **not** in the
shared pool; try to insert a second `placement_identity` row (must be refused by the singleton PK).

## 4. Execution

```text
python tools/run_tests.py     546/546 OK   (live PostgreSQL, a second DB provisioned)
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

## 5. Disclosed deviation from the design — `placement_identity` carries RLS after all

`PLAN-P35-06-DEDICATED-DB` §2.1–§2.2 said `placement_identity` would carry **no** row-level security
because it is not tenant data. Building it, the structural test
`test_every_table_in_the_schema_is_classified_and_protected` correctly refused a new table with no
RLS — every table must be ENABLE + FORCE, so absence can never be a silent open door (the control
that would have caught the 007 disclosure). So `placement_identity` now carries ENABLE + FORCE RLS
with **permissive** policies (`SELECT USING (true)`, `INSERT WITH CHECK (true)`, no UPDATE/DELETE —
write-once). The permissiveness is deliberate and documented in the migration: the row holds only the
served-tenant id (which the caller already supplies, not a secret) and is read by
`verify_connection_serves` *while a tenant scope is in force*, so a tenant-matching policy would hide
the row from the very check that needs it. The mis-route defence remains the verification comparison
plus the single-row key; the FORCE RLS makes the table structurally protected rather than open by
omission. This is a strengthening the structural control forced, recorded rather than hidden.

## 6. What this does NOT establish (disclosed)

1. **New dedicated tenants only.** The **trial→paid data migration** (moving an existing shared-pool
   tenant's rows into a fresh dedicated database) is deferred — cross-database, its own atomicity
   design (`PLAN` §2.4).
2. **No connection pooling** per dedicated database; each `tenant_session` opens and closes a
   connection (the seam's existing behaviour).
3. **No deprovisioning / backup / DR** for dedicated databases yet.
4. **One verifier, not two** (two-agent profile).

## 7. Authority

A maker's submission. `EBIV` §8: a passing suite carries no verdict weight.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
