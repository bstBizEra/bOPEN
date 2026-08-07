# Notification migration, rollback & compensation plan (DRAFT)

**STATUS: DRAFT / PROPOSED — NOT AUTHORIZED, NOT IN FORCE. Notification remains gated by DEC-P4-ENTRY §9. This document plans a migration; it authorizes none, writes no `.sql`, runs no migration, and records no completion. A build — and the migration it plans — requires a separate operator authorization recorded first.**

---

## Controlled-document metadata

| Field | Value |
|---|---|
| **Document ID** | `PLAN-NOTIFY-MIGRATE` (proposed; pending governance ID-registry ratification) |
| **Version** | 1.0.0-draft |
| **Owner** | bOPEN Agentic SE — Notification (Motor authoring; Codex independent reviewer) |
| **Issued** | 2026-08-06 |
| **Status** | DRAFT / PROPOSED — gated by DEC-P4-ENTRY §9 |
| **Governing artifacts** | DEC-P4-ENTRY §9; `ADR-NOTIFY-WQ` v2.1 (table/state source of truth); `ADR-NOTIFY-PROVIDER` v2.1; RESEARCH-MILE-4.2-NOTIFICATION §§9–10, §12(3); AGENTS.md §6 (clean-room) |
| **Dependent artifacts** | `BOPEN-NOTIFY-001`; operations runbooks; backup/restore runbook; test matrix; EBIV invariant-traceability |
| **Evidence refs** | `infrastructure/database/014_workflow_history_survives_its_instance.sql` (ON DELETE RESTRICT lesson); `infrastructure/database/020_location_foundation.sql` (forced-RLS + composite-FK pattern); `tools/migrate_tenant_to_dedicated.py` (`COPY_ORDER`); `tests/isolation/test_rls_database_behavior.py` (`TENANT_SCOPED_TABLES`, classification test); `tests/isolation/test_trial_to_paid.py`; `services/platform-kernel/python/platform_kernel/db.py` (`tenant_session`, `TenantMigratingError`, `_verify_placement`, `_reject_conflicting_scope`) |

`ready_for_operator_review: false`

This plan is **consistent with** the v2.1 ADRs and does not re-decide them. It sequences *how* the `notification_*` substrate reaches a database, how it is unwound, and how it survives backup, restore, and the trial→paid migration — not *whether* it is built.

---

## 1. Migration shape and sequencing

The substrate lands as one forward migration in the kernel's numbered series — provisionally **`021_notification_foundation.sql`**, following `020_location_foundation.sql` — with its paired **`021_notification_foundation.down.sql`** and, where the tables have accrued committed evidence, a **`.compensate.sql`** rather than a destructive down (§5). It follows the exact discipline migrations 013/014/019/020 encode: every tenant-owned table gets `ENABLE` + `FORCE ROW LEVEL SECURITY`, a default-deny tenant policy, `UNIQUE (tenant_id, id)` on every parent so children reference it **by tenant**, tenant-inclusive composite foreign keys, and `ON DELETE RESTRICT` on the append-only tables so no cascade — nor the tenant cascade above it — can silently erase evidence (the migration-014 lesson, applied in advance the way Location did).

Two migration concerns are new to Notification and are called out because the kernel has never had them: **elevated non-`bopen_app` roles with cross-tenant policies** (the claim and callback planes), and **tables that are not ordinary tenant-scoped rows** (a platform-level provider-health table and a *tenantless* quarantine table). Both interact directly with the classification and copy-coverage invariants (§4) and must be resolved before the migration is written, not discovered during it.

## 2. The tables — columns, constraints, RLS, grants

Column sets are the v2.1 worker ADR's (§1, §4, §7, §8); this plan fixes their DDL-level constraints, RLS policies, and role grants. Parents precede children throughout.

| Table | Class | Key columns | FK / constraints | RLS policies + role grants |
|---|---|---|---|---|
| `notifications` | tenant-scoped (parent) | `id`, `tenant_id`, `purpose`, `channel`, template-version ref, recipient-snapshot ref, `lifecycle_state`, `revision`, `correlation_id`, `idempotency_key` | `tenant_id → tenants ON DELETE CASCADE`; `UNIQUE (tenant_id, id)`; **`UNIQUE (tenant_id, idempotency_key)`** (NOTIFY-INV-06) | forced RLS; `FOR ALL` tenant policy `TO bopen_app` (`USING/WITH CHECK tenant_id = NULLIF(current_setting('app.current_tenant_id',true),'')::uuid`). No claimer/callback grant. |
| `notification_dispatch` | tenant-scoped (child) | `dispatch_id`, `tenant_id`, `status`, `attempt_no`, `send_key`, `send_started_at`, `available_at`, `lease_owner`, `lease_expires_at`, `lease_fence BIGINT`, `next_visible_at`, `dead_lettered_at`, `provider_id`, `provider_profile_version` — **content-free** | composite FK **`(tenant_id, notification_id) → notifications(tenant_id, id)`**; `UNIQUE (tenant_id, dispatch_id)`; `CHECK status IN (...)` | forced RLS; **two** policies — tenant `FOR ALL TO bopen_app`, plus a second `TO bopen_notify_claimer FOR SELECT, UPDATE USING (true)` (cross-tenant by design), confined by **column GRANTs** to ids + lease/scheduling scalars only (WQ-SEC-02). |
| `notification_attempt` | tenant-scoped, **append-only** | `attempt_id`, `tenant_id`, `attempt_no`, `provider_profile`, request fingerprint, `provider_idempotency_ref`, `started_at`/`ended_at`, `classified_outcome`, `safe_code`, `provider_message_id` | composite FK `(tenant_id, dispatch_id) → notification_dispatch(...)` **`ON DELETE RESTRICT`**; `CHECK classified_outcome IN (provider_accepted, retryable_failed, terminal_failed, unknown)` | forced RLS; **SELECT + INSERT policies only**, no UPDATE/DELETE (013/014). `bopen_app` writes it under `tenant_session`. Callback plane gets a **column-restricted SELECT** on binding scalars only (CB-SEC-01b). |
| `notification_receipt` | tenant-scoped, **append-only** | provider event id, provider-observed time, normalized transport status, raw-payload integrity ref, `applied\|superseded\|conflicting` | composite FK to attempt/dispatch **`ON DELETE RESTRICT`** | forced RLS; SELECT+INSERT only. |
| `notification_callback_event` | tenant-scoped, **append-only** | `dedup_key`, `provider_id`, `provider_message_id`, `provider_event_id`, `payload_signature_digest`, `replay_id` (evidence only) | **`UNIQUE (provider_id, provider_message_id, dedup_key)`** (NOTIFY-INV-06); FK to bound attempt `ON DELETE RESTRICT` | forced RLS; SELECT+INSERT only; callback plane holds `INSERT` here (CB-SEC-01). |
| `notification_callback_quarantine` | **tenantless / content-free** (append-only) | verified-but-unbound early-callback ids, no `tenant_id` binding yet | no tenant composite FK (tenant unknown at insert) | forced RLS with a **role-scoped `TO bopen_notify_callback`** policy; no tenant policy — needs an explicit **classification decision** (§4). |
| `notification_quota` | tenant-scoped (control) | `(tenant_id, purpose, window_start)`, `tokens_used`, `tokens_limit` | `PK (tenant_id, purpose, window_start)`; tenant FK | forced RLS; tenant policy `TO bopen_app`; claimer gets `SELECT,UPDATE` on content-free counter only. |
| `notification_quota_suspend` | tenant-scoped (control) | `tenant_id`, `active` | tenant FK | forced RLS; tenant policy; claimer `SELECT`. |
| `notification_fairness` | tenant-scoped (control) | `tenant_id PK`, `last_served_at` (+ optional `inflight_reserved`) | tenant FK | forced RLS; claimer `SELECT,UPDATE` (interleave cursor / slot serialization). |
| `notification_provider_health` | **platform control-plane (NOT tenant-scoped)** | `provider_id`, `state`, `failure_count`, `opened_at`, `half_open_at`, `probe_fence BIGINT`, `probe_owner`, `probe_lease_expires_at`, per-provider callback-rate counter | keyed on `provider_id`, no `tenant_id` | needs **REGISTRY/INFRASTRUCTURE classification** (§4); claimer `SELECT`; callback plane `SELECT,UPDATE` on the rate counter only. |

**Elevated roles (cluster-level, granted per database).** The migration provisions `bopen_notify_claimer` and `bopen_notify_callback` — neither `bopen_app`, superuser, nor table owner — with **zero grant on any content table**. The claimer's only writes are the content-free dispatch/lease and control-row columns; the callback principal's only writes are the append-only callback tables and the provider-rate counter. Two governed service principals (`principals.type='service'`: `notify-worker`, `notify-callback`) are seeded for audit identity (WQ-SEC-04 / CB-SEC-01d). Revocation levers (`ALTER ROLE … NOLOGIN`, principal suspension, `DROP POLICY … TO …`) degrade each plane to **zero-visibility, never open-visibility** (WQ-SEC-05 / CB-SEC-01e) — a property the migration must preserve by keeping the ordinary tenant policy present alongside the elevated one.

## 3. Content-free claim plane at migration time

The column GRANTs are the load-bearing migration artifact, not a runtime convenience: because `bopen_notify_claimer` is *granted* only ids and lease/scheduling scalars, a coding error that tries to write content on the claim connection fails on **privilege**, not on reviewer vigilance (WQ-SEC-03). The migration therefore issues explicit `GRANT SELECT (col, …), UPDATE (col, …)` column lists — never table-level grants — and the test matrix asserts a fully-compromised claimer sees only opaque `(dispatch_id, tenant_id, notification_id, provider_id)` tuples.

## 4. Two-place registration obligation (INV-MIGRATE-COVERAGE-01)

Every tenant-owned table must be registered in **both** inventories, or the kernel's own coverage guard fails the build:

1. **`TENANT_SCOPED_TABLES`** in `tests/isolation/test_rls_database_behavior.py` — the RLS classification. `test_every_table_in_the_schema_is_classified_and_protected` enumerates the **live schema** and fails on any table absent from all three classes (TENANT_SCOPED / REGISTRY / INFRASTRUCTURE) — the mechanism that caught the 007 disclosure.
2. **`COPY_ORDER`** in `tools/migrate_tenant_to_dedicated.py` — the trial→paid copy manifest, **parents before children**: `notifications` first, then `notification_dispatch`, `notification_attempt`, `notification_receipt`, `notification_callback_event`, the tenant-scoped control rows (`notification_quota`, `notification_quota_suspend`, `notification_fairness`), append-only tables last.

`test_copy_order_covers_every_tenant_scoped_table` asserts `set(COPY_ORDER) == set(TENANT_SCOPED_TABLES)` — a tenant-scoped table added to one inventory but not the other is **silent data loss on cutover**, and this equality test is what makes it loud instead. This is **INV-MIGRATE-COVERAGE-01**.

**Two tables force an explicit pre-build decision here.** `notification_provider_health` is keyed on `provider_id` with no `tenant_id`; it is **not** tenant-owned and must be classified REGISTRY/INFRASTRUCTURE and kept **out** of `COPY_ORDER` (it is not copied per-tenant). `notification_callback_quarantine` is *tenantless by construction* (the tenant is unknown until re-resolution) — it can carry no ordinary tenant policy and no tenant composite FK, so it needs a bespoke classification (role-scoped, content-free) that satisfies the enumerate-don't-miss test without pretending to be tenant-scoped. Leaving either unclassified fails the schema-classification test; misclassifying provider-health *into* `COPY_ORDER` would try to copy a non-tenant table by `tenant_id` and fail at copy. Both decisions are recorded here as **required before the migration is authored**, not deferred into it.

## 5. Rollback, compensation, forward-only

The kernel ships a `.down.sql` per migration, but Notification's append-only evidence changes the calculus. A down migration is safe **only before any evidence commits**: once `notification_attempt`/`_receipt`/`_callback_event` rows exist, dropping the tables is exactly the cascade-erasure the `ON DELETE RESTRICT` discipline forbids. The plan is therefore:

- **Pre-evidence down migration** (`021_*.down.sql`): drops policies, column grants, tables (children→parents), and the two roles/principals — valid only while the substrate is empty of committed attempts/receipts. Used to unwind a failed *install*, never a running queue.
- **Forward-only compensation** once evidence exists: an in-flight or drained queue is retired by **forward** state transitions (dead-letter drain, `terminal_unknown` floor, lifecycle retirement) and, if the feature is withdrawn, a compensating migration that revokes the roles (`NOLOGIN`, `DROP POLICY … TO bopen_notify_*`) and **quarantines** the tables read-only rather than dropping them — preserving the append-only trail (mirroring `003_*.compensate.sql`). Destroying committed delivery evidence is an operator act with its own authorization, never a rollback side effect.

## 6. Dedicated-DB queue topology — **must resolve before build (reviewer-flagged)**

The worker ADR's Consequences and Explicitly-deferred sections both flag this as unresolved: for dedicated-DB tenants the tenant-scoped dispatch/attempt/receipt tables live **in each placement database** (copied by `COPY_ORDER` at cutover), but the **control plane** (`notification_provider_health`, and arguably fairness/quota) and the **worker process and roles** admit two topologies:

- **Per-placement worker + per-placement control tables** — each dedicated DB runs its own claimer/callback roles, its own breaker/health, its own fairness cursor. Strong isolation; fragmented breaker state (a provider's health is re-learned per placement) and N workers to operate.
- **Shared control plane + fan-out worker** — one breaker/health/quota control set, a worker that fans out across placements re-entering `tenant_session` per content touch. Coherent provider health and fairness; a cross-placement actor that must be provisioned (`bopen_notify_claimer`, `bopen_notify_callback`) in **every** placement DB and must never let one placement's state leak into another's isolation.

This decision determines *which database* each control table's migration targets, whether `notification_provider_health` is global or per-placement, where callbacks land during and after cutover, and whether the roles are provisioned once or per placement. It is **explicitly out of scope to decide here** and is named a hard pre-build blocker.

## 7. Migrating-freeze interaction

Trial→paid migration sets the control registry `placement_state='migrating'`, and `tenant_session` raises `TenantMigratingError` for any tenant-scoped access during the freeze (`db.py`). Every worker **content touch** re-enters `tenant_session`, so it inherits the freeze and fails closed — correct, but wasteful if a lease is already spent. The plan therefore requires the **fair-claim query to skip migrating tenants** (join the placement state, exclude `migrating`) so a dispatch for a freezing tenant is never claimed and no lease is burned against a `TenantMigratingError`. The claim plane's `USING(true)` cross-tenant policy does **not** see the freeze on its own; skipping is an explicit claim-predicate obligation. Callbacks arriving mid-freeze verify (content-free) and **quarantine** rather than append, re-resolving after the freeze clears — the quarantine window absorbing the migration window. The copy manifest already carries the tenant-scoped queue/evidence rows, so a mid-flight dispatch migrates with its tenant; leases arrive stale (past `lease_expires_at`) and are safely reclaimed by fencing on the dedicated side (§8).

## 8. Backup / restore of queue + evidence

Backup must capture the queue **and** its evidence at one consistent point (PITR / single snapshot), so mutable `notification_dispatch` state and the append-only `notification_attempt`/`_receipt`/`_callback_event` trail never diverge across the boundary. On restore:

- **Leases are self-healing.** Restored `lease_expires_at` values are in the past, so every leased/sending row is reclaimable; the monotonic `lease_fence` guarantees a resumed pre-restore worker's late writes match nothing (fenced CAS).
- **No restore-driven resend.** A restored `status='sending'` row with a populated `send_key` and no finalized attempt is recovered to `reconciling`, never blind-resent (D-EV-5); the deterministic `send_key`/`provider_idempotency_ref` survive the restore, so a legitimate reconcile reuses the identical key.
- **Dedup and idempotency survive.** `UNIQUE (tenant_id, idempotency_key)` and the callback `dedup_key` uniqueness are restored with the rows, so replays after restore collapse exactly as before.
- **Secrets are not in the backup.** Provider signing secrets live as runtime config behind the adapter facade (NOTIFY-INV-13), so a database backup carries no credential; secret custody and rotation are an ops concern outside this dataset.

Restore correctness — leases stale-and-reclaimable, `sending`→`reconciling` with no resend, dedup preserved — is a named item on the build-time test matrix on live PostgreSQL (NOTIFY-INV-16), not asserted here.

---

## Clean-room note

Designed independently under AGENTS.md §6. No upstream migration or queue code was copied; the plan derives from the kernel's own forced-RLS + composite-FK + `ON DELETE RESTRICT` migrations (014/019/020), the `COPY_ORDER`/`TENANT_SCOPED_TABLES` two-place coverage discipline and its equality test, and the `tenant_session`/`TenantMigratingError`/placement freeze in `db.py`. Table shapes and role grants are the v2.1 worker/provider ADRs', referenced and not re-decided.

## Authority block

```yaml
document: notification-migration-rollback-compensation-plan
document_id: PLAN-NOTIFY-MIGRATE
version: 1.0.0-draft
status: DRAFT / PROPOSED
gated_by: DEC-P4-ENTRY §9
truth_status: partially_supported
authority_status: advisory_only
implementation_status: candidate
risk_class: high
execution_authority: false
approval_authority: false
production_activation_authority: false
migration_execution_authority: false
completion_claimed: false
self_certification:
  agent_id: claude-motor
  peer_agent_id: codex-reviewer
  certification_scope: advisory_only
  execution_authority: false
  approval_authority: false
  ready_for_operator_review: false
```

> This plan sequences a migration only. It authorizes nothing, writes no SQL, and runs no migration. The dedicated-DB queue topology (§6) and the two non-tenant-scoped table classifications (§4) are named pre-build blockers to be resolved by their own decision records. A build and its migration require a separate operator authorization recorded first; Notification remains gated by DEC-P4-ENTRY §9.
