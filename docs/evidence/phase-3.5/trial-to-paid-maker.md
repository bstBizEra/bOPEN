# EVD-TRIAL-TO-PAID-MAKER — trial→paid tenant migration

**Document ID:** `EVD-TRIAL-TO-PAID-MAKER`
**Version:** `1.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision
**Issued:** 2026-08-04
**Implements:** [`DEC-P35-TENANCY-MODEL`](../../decisions/DEC-P35-TENANCY-MODEL.md) §12 (authorized); [`PLAN-P35-06-TRIAL-TO-PAID`](../../01-product/WP-P35-06-trial-to-paid-migration-plan.md)
**Candidate:** `2a253a5`
**Blob — `017_tenant_placement_state.sql`:** `3cfcf9ed6fb296538023a24d70e7bc8538ad443a`
**Blob — `migrate_tenant_to_dedicated.py`:** `65e173e33bb755a445b0e1d2e9b9700b90c2b3b6`
**Blob — `api.py`:** `58aa9170965a5163cd41d291767d7d72c06da773`
**Blob — `test_trial_to_paid.py`:** `5eb9578427e12ebb62fa5015410100975c999bec`
**Blob — `invariant-traceability.csv`:** `14cbb8f94fbac60bafe1bcd4191c223580b975bc`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifier:** Codex
**Suites:** canonical **560/560** against PostgreSQL, with a second real database provisioned

---

## 1. What this is — and the properties it defends

The last piece of the hybrid tenancy model: moving an **existing shared-pool tenant** into its own
dedicated database — *"trial shares the pool; when it pays, it gets its own database."* There is no
ACID transaction across two databases, so the guarantee is by sequencing: **freeze → prepare → copy →
verify → cutover → cleanup** (`PLAN-P35-06-TRIAL-TO-PAID`).

The properties defended, together: the tenant's data is **moved, not copied and not lost**
(complete in the dedicated database *and* gone from the shared pool), the routing **flips atomically**
at cutover, the tenant is **frozen** during the move so no write is lost, a **failure before cutover
is safe** (the tenant stays on the shared pool), and the tenant's **global principals are untouched**.

**Clean-room (`AGENTS.md` §6):** the freeze/verified-copy/atomic-cutover sequence and the choice
against two-phase commit were reasoned from this schema and PostgreSQL's cross-database limits, not
adapted from an external migration framework.

## 2. Defensive verification

Every proposition asserts a safety property of an irreversible operation — that nothing is lost,
nothing is duplicated, a mis-step before cutover is recoverable, and a migrating tenant is refused.
No offensive objective; two local verification databases.

## 3. Propositions (traced in `invariant-traceability.csv`)

`tests/isolation/test_trial_to_paid.py`, executed across two databases (except coverage, structural):

| ID | The migration must… | Test |
| :--- | :--- | :--- |
| `P4-MIGRATE-01` | move every one of the tenant's rows into the dedicated database | `test_migration_moves_all_rows_to_the_dedicated_database` |
| `P4-MIGRATE-02` | leave none behind in the shared pool (no duplication) | `test_migrated_rows_are_gone_from_the_shared_pool` |
| `P4-MIGRATE-03` | route the tenant to the dedicated database after cutover | `test_after_cutover_the_tenant_routes_to_the_dedicated_database` |
| `P4-MIGRATE-04` | refuse a migrating tenant's request at the HTTP layer (the freeze) | `test_a_migrating_tenant_is_frozen_at_the_request_path` |
| `P4-MIGRATE-08` | refuse a migrating tenant at `db.tenant_session` — the data chokepoint, every write path (keystone, added after refutation) | `test_the_freeze_covers_the_data_chokepoint_not_just_http` |
| `P4-MIGRATE-05` | leave the tenant safely on the shared pool if it fails before cutover | `test_a_verification_mismatch_leaves_the_tenant_on_the_shared_pool` |
| `P4-MIGRATE-06` | not move or duplicate the tenant's global principals | `test_the_principal_stays_in_control_and_is_not_moved` |
| `P4-MIGRATE-07` | copy **every** tenant-scoped table (no silent data loss) | `test_copy_order_covers_every_tenant_scoped_table` |

**Attack angle for the verifier:** after a migration, query the shared pool directly for the tenant's
rows — every tenant-scoped table must be empty; query the dedicated database — the counts must equal
the pre-migration snapshot, with the **same ids** (binary COPY preserves them). Force verification to
fail and confirm the tenant is left on `shared_pool`, `stable`, data intact. Mark a tenant `migrating`
and confirm a bearer-gated request returns 503. Add a table to `TENANT_SCOPED_TABLES` without adding
it to the tool's `COPY_ORDER` and confirm `P4-MIGRATE-07` fails.

## 4. Execution

```text
python tools/run_tests.py     560/560 OK   (live PostgreSQL, a second DB provisioned)
```

- **Migration 017** adds `tenants.placement_state` (`stable` | `migrating`).
- **The freeze** is enforced at **`db.tenant_session`** (`_connect_for_tenant`) — the data-access
  chokepoint every write path passes through — raising `TenantMigratingError` for a migrating tenant,
  with `api._load_validated_context` additionally returning a clean retriable 503 on the HTTP path.
  The migrate tool uses superuser raw connections, not `tenant_session`, so it is not frozen. (The
  first candidate froze *only* at HTTP; see §7.)
- **`provision_dedicated_db`** gains `activate=False` (prepare without flipping the control registry).
- **`tools/migrate_tenant_to_dedicated.py`** drives freeze → prepare → copy → verify → cutover →
  cleanup. The copy is **binary COPY as the superuser** — because `COPY FROM` is refused on an RLS
  table, the superuser bypasses RLS and the tenant scope is supplied explicitly as
  `WHERE tenant_id = <tenant>` on the source; binary format preserves ids/timestamps/JSONB exactly.
  The table list `COPY_ORDER` is asserted equal to the RLS-classified `TENANT_SCOPED_TABLES`, so no
  tenant-scoped table can be silently missed. Cleanup deletes the tenant's shared rows **as the
  superuser** because the append-only tables (`audit_events`, `workflow_history`, `lifecycle_events`)
  have no DELETE policy for the application role — a controlled post-cutover move of rows already
  copied and verified, not an application-reachable deletion.

## 5. Why "atomic enough" without a distributed transaction (disclosed)

There is no two-phase commit (recorded as considered and rejected — `PLAN` §3). The guarantees sit at
the irreversibles: the **freeze** stops writes during the copy; the **cutover** is a single row
update in the control database (atomic there), so reads flip from shared to dedicated at one instant;
a failure **before** cutover leaves the tenant fully on the shared pool (the half-built dedicated
database is discardable); a failure of **cleanup after** cutover leaves only unread stale rows in the
shared pool — recoverable, not loss.

## 6. What this does NOT establish (disclosed)

1. **Not zero-downtime.** The freeze refuses the tenant's requests for the copy+cutover window — a
   brief unavailability, acceptable for an operator-run trial→paid upgrade, not an online migration.
2. **A cutover-step failure is not auto-repaired.** A failure exactly at/after the cutover UPDATE can
   leave the tenant `migrating` (frozen) needing a manual clear; the data is safe (in shared, or in
   dedicated post-flip), but the state is not self-healing. Recorded as a known edge, not built.
3. **No reverse (dedicated→shared) or bulk/scheduled migration.**
4. **The freeze adds one control read per context resolution.** The same per-call cost class as the
   placement resolution refinement already tracked in §9.3; not a new architectural cost.
5. **One verifier, not two** (two-agent profile).

## 7. Verification history — one refutation, closed

The first candidate `2a253a5` was verified by Codex, which **CONFIRMED 6 of 7** propositions and
**REFUTED `INV-MIGRATE-COMPLETE-01`** by execution: the freeze was placed at the HTTP layer only, so a
write via `db.tenant_session` that bypassed it committed to the shared pool after the migration's copy
and was then deleted by cleanup — leaving **zero copies in either database** (data loss). The freeze
was at the wrong layer.

Fixed at root cause: the freeze moved to **`db.tenant_session`** (`TenantMigratingError` in
`_connect_for_tenant`), the chokepoint every write path passes through — the HTTP 503 remains for a
clean error. The reproduction is now proposition `P4-MIGRATE-08`
(`test_the_freeze_covers_the_data_chokepoint_not_just_http`). This candidate re-submits with that fix
for re-ballot. The verifier catching a data-loss window the maker's HTTP-layer freeze left open is the
two-agent governance working on the slice where it matters most.

## 8. Authority

A maker's submission. `EBIV` §8: a passing suite carries no verdict weight.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
