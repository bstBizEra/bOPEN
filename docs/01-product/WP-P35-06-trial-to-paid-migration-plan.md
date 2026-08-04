# WP-P35-06 — Trial→paid tenant migration, design & slice plan

**Document ID:** `PLAN-P35-06-TRIAL-TO-PAID`
**Version:** `1.0.0`
**Status:** **Design — advisory. Buildable on operator authorization.** The last open item of the hybrid tenancy model ([`DEC-P35-TENANCY-MODEL`](../decisions/DEC-P35-TENANCY-MODEL.md) §8 Option D), deferred through the §10 and §11 slices.
**Issued:** 2026-08-04
**Raised by:** Claude (agent, Motor role) — advisory only
**Governing:** [`DEC-P35-TENANCY-MODEL`](../decisions/DEC-P35-TENANCY-MODEL.md) §8, §10, §11; `AGENTS.md` §8

---

## 1. Where this picks up

Hybrid placement is now usable for a **new** dedicated tenant: provisioning (§10) creates its
database, and Option A (§11) lets it be onboarded end to end. What is missing is the flow the model
was named for — *"trial account shares the pool; when it pays, it gets its own database"*: moving an
**existing** shared-pool tenant's data into a fresh dedicated database.

This is the hard half, for one reason that shapes the whole design: **PostgreSQL cannot run a single
ACID transaction across two databases.** The shared pool and the dedicated database are separate
databases, so "copy the tenant's rows over and switch" cannot be one atomic commit. The design's job
is to reach *no data loss and no split-brain reads* without that guarantee — by sequencing, not by a
distributed transaction.

## 2. The shape: freeze → copy → verify → cutover → clean up

A migration is an operator-initiated action on one tenant. The steps, and what each guarantees:

1. **Provision (no cutover).** Create the dedicated database and its `placement_identity`, exactly as
   §10 does — but **do not flip the control registry yet**. The tenant keeps serving from the shared
   pool. (`provision_dedicated_db` grows a "prepare only" mode, or the cutover is split out.)
2. **Freeze.** Mark the tenant `migrating` in the control registry. While migrating, the kernel
   **refuses** the tenant's requests with a retriable error ("migration in progress") — the simplest
   safe freeze, and acceptable because a trial→paid upgrade is an operator action on a low-traffic
   tenant, not a hot production cutover. A freeze is what makes the copy a complete snapshot: no write
   can land in the shared pool after it is read.
3. **Copy.** Copy the tenant's rows from the shared pool into the dedicated database, under the
   tenant's own scope (RLS yields exactly that tenant's rows), in foreign-key dependency order
   (`parties` before `party_relationships`, `workflow_definitions` before instances before history,
   …). The table list is **derived from the RLS classification** (`TENANT_SCOPED_TABLES`), never
   hard-coded, so a tenant-scoped table added later is copied automatically — a missing table would be
   silent data loss, and this is the control against it (the same enumerate-don't-list discipline as
   `test_every_table_in_the_schema_is_classified_and_protected`). Principals are **not** copied — they
   are global and stay in control (Option A).
4. **Verify.** Per table, the dedicated row count for the tenant equals the shared snapshot count
   (and a content checksum, optionally). The migration does not proceed to cutover unless every table
   reconciles.
5. **Cutover.** In the **control** database — a single database, so this *is* atomic — one row update
   flips `tenants.placement_kind` to `dedicated`, sets `placement_ref`, and clears the `migrating`
   state. `BOPEN_DEDICATED_DB__<ref>` is set. Before this update, every read resolves to the shared
   pool; after it, to the dedicated database. There is no instant where reads are split.
6. **Clean up.** After a verified cutover, delete the tenant's now-stale rows from the shared pool.
   This is what prevents duplication. If cleanup fails, the only residue is unread rows in the shared
   pool (routing now goes to dedicated) — recoverable, not data loss.

## 3. Why this is "atomic enough", stated precisely

There is no distributed transaction, and the design does not pretend otherwise. The guarantees come
from where the irreversibles sit:

- **No lost write:** the freeze refuses writes for the duration, so nothing changes in the shared pool
  between the snapshot and the cutover.
- **No split-brain read:** the cutover is a single-row update in one database (control), so reads flip
  from shared to dedicated at one instant; there is no window where half the reads go each way.
- **Fail-safe before cutover:** any failure during provision/copy/verify leaves the tenant fully on
  the shared pool with its data untouched — the dedicated database is a discardable work-in-progress.
- **Recoverable after cutover:** the only post-cutover step is deleting stale shared rows; its failure
  leaves unread duplicates, not loss.

The alternative — PostgreSQL two-phase commit (`PREPARE TRANSACTION`) across both databases — is
recorded as considered and **not** chosen for the first slice: it needs a coordinator that survives
crashes to resolve prepared transactions, and a stuck prepared transaction holds locks and blocks
vacuum. Freeze-and-cutover is simpler, and its failure modes are all either safe or recoverable.

## 4. What this slice needs that does not exist yet

| New piece | Why |
| :--- | :--- |
| A tenant **`migrating`** state + the kernel refusing a migrating tenant's requests | The freeze in step 2 — the write path must fail closed while a tenant is mid-migration |
| Provisioning **without cutover** (prepare vs activate split) | Step 1 — the DB is stood up while the tenant still serves from shared |
| A **migrate tool** (`migrate_tenant_to_dedicated`) driving copy/verify/cutover/cleanup, table list from `TENANT_SCOPED_TABLES` | Steps 3–6 |
| A **cutover** operation (the atomic control-row flip) | Step 5 |

## 5. Scope

| In scope | Out of scope (later) |
| :--- | :--- |
| Migrate **one existing shared-pool tenant** to a dedicated database, operator-initiated, with a brief freeze | **Zero-downtime / online** migration (no freeze) — needs change-data-capture and is a different design |
| Freeze via a `migrating` state that refuses the tenant's requests | Automatic/scheduled migration, bulk migration of many tenants |
| Copy derived from `TENANT_SCOPED_TABLES`, verify by row count, atomic cutover, post-cutover cleanup | Migrating a tenant **back** (dedicated→shared) |
| Principals stay global (untouched) | Cross-region / different-host dedicated databases |

## 6. Invariants to verify (R4 negative probes, drafted early)

Executed across two real databases; each carries a test and a traced row before any ballot:

- `INV-MIGRATE-COMPLETE-01` — after migration, every one of the tenant's rows is in the dedicated
  database: per-table counts equal the pre-freeze snapshot.
- `INV-MIGRATE-NO-DUPLICATION-01` — after cleanup, the tenant's rows are **gone from the shared pool**
  (no row exists in both).
- `INV-MIGRATE-CUTOVER-ROUTES-01` — after cutover, `tenant_session` resolves the tenant to the
  dedicated database and reads the migrated data.
- `INV-MIGRATE-FREEZE-REFUSES-01` — while `migrating`, a write for the tenant is refused (the freeze
  holds; no write is lost).
- `INV-MIGRATE-ROLLBACK-SAFE-01` — a failure injected before cutover leaves the tenant fully on the
  shared pool, its data intact and readable, no partial dedicated state serving.
- `INV-MIGRATE-PRINCIPALS-UNTOUCHED-01` — the tenant's principals remain the global control rows and
  are neither moved nor duplicated (Option A holds through a migration).

`INV-MIGRATE-COMPLETE-01` and `INV-MIGRATE-NO-DUPLICATION-01` are the pair that together mean "moved,
not copied and not lost"; `INV-MIGRATE-ROLLBACK-SAFE-01` is the one that makes the operation safe to
attempt.

## 7. The maker cycle (same governance)

Design (this doc) → operator authorization recorded **before build** → tests-first (the migration
probes, red before the tool and the freeze exist) → the `migrating` state + prepare/cutover split +
migrate tool → execute across **two live databases** → trace invariants (R2) → maker submission →
**Codex** ballot → operator disposition under `EBIV` §6.5.

## 8. Why design-first, and why it is the right last tenancy build

A migration touches the one thing that is unrecoverable if done wrong — the tenant's own data — and
it does so without a transaction to fall back on. The failure modes have to be reasoned *before*
code: which step is safe to fail at, which is not, and where the single irreversible instant sits.
Improvising it would risk a half-migrated tenant serving from neither database or both. Designing the
freeze, the verified copy, and the atomic cutover first is what lets the probes assert the properties
that matter — completeness, no duplication, and rollback safety — against the real mechanism.

It is the right last build because it closes the hybrid tenancy model end to end: a trial tenant
lives in the shared pool, and when it pays, its data moves into its own database with no loss and no
split read — the sentence the model was written to make true.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
