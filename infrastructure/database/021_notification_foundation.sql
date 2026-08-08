-- Migration: 021_notification_foundation.sql
-- Description: Notification foundation (BOPEN-NOTIFY-001) — Stage 1 substrate: the tenant-scoped
--              `notification_*` table set that a later worker/callback stage leases, sends, and
--              reconciles against. Stage 1 lands the tables, the standard tenant-isolation RLS, the
--              append-only evidence discipline, the tenant-inclusive composite foreign keys, and the
--              per-tenant idempotency / cross-provider dedup uniqueness. It provisions NO elevated
--              worker/callback roles, NO content-free `USING(true)` claim policy, NO repositories, NO
--              worker runtime, NO adapter, NO callback ingest plane, and NO endpoints — each is a later
--              stage with its own build.
-- Version: 1.0.0
-- Work package: BOPEN-NOTIFY-001 (MILE-4.2 Notification foundation)
-- Governing artifacts: DEC-P4-ENTRY §12 (Stage 1 authorization); PLAN-NOTIFY-MIGRATE (migration plan);
--                      ADR-NOTIFY-WQ v2.1 §1 (table/state source of truth); BOPEN-NOTIFY-001 §1;
--                      AGENTS.md §8; BOPEN-TENANT-001; BOPEN-GOV-EBIV-001
-- Rollback: 021_notification_foundation.down.sql
--
-- Load-bearing decisions this migration encodes (each a lesson of the built foundations 013/014/019/020):
--
--   Same-tenant integrity (mirrors party_contact_points / location_*). Every child references its
--   parent BY (tenant_id, parent_id) → parent(tenant_id, id), so a dispatch/attempt/receipt attached to
--   another tenant's parent is impossible at the database, not merely in application logic. Each parent
--   therefore declares UNIQUE (tenant_id, id).
--
--   Append-only evidence is ON DELETE RESTRICT, not CASCADE (the migration-014 lesson applied in
--   advance). `notification_attempt` and `notification_receipt` carry SELECT + INSERT policies only (no
--   UPDATE/DELETE policy) AND their composite FK to `notification_dispatch` is ON DELETE RESTRICT, so a
--   recorded attempt/receipt survives BOTH a direct UPDATE/DELETE AND a parent cascade — a dispatch (or,
--   through the tenant cascade above it, a whole tenant) that carries committed delivery evidence cannot
--   be deleted out from under that append-only trail. The mutable current-state row + separate
--   append-only history split is the `workflow_instances`↔`workflow_history` pattern (013/014).
--
--   Idempotency and dedup keystones. `UNIQUE (tenant_id, idempotency_key)` on `notifications`
--   (NOTIFY-INV-06) collapses a retried request per tenant; the receipt dedup key
--   `UNIQUE (provider_id, provider_message_id, dedup_key)` is deliberately CROSS-tenant/cross-provider so
--   a redelivered provider callback collapses without depending on a nullable/mutable replay id.

-- 1. notifications — the durable tenant-owned orchestration record and the unit of logical identity.
-- Mutable state row (analogue of workflow_instances). One notification = one recipient, one channel.
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    purpose VARCHAR(32) NOT NULL,
    channel VARCHAR(16) NOT NULL,
    -- References into the tenant's template/recipient evidence; soft (no FK) — resolved by the worker
    -- orchestrator per attempt (ADR-NOTIFY-WQ §10), not a hard referent here.
    template_version_ref UUID,
    recipient_snapshot_ref UUID,
    -- The tenant-facing monotonic lifecycle projection (BOPEN-NOTIFY-001 §2); never regresses.
    lifecycle_state VARCHAR(32) NOT NULL DEFAULT 'accepted',
    revision INT NOT NULL DEFAULT 1,
    correlation_id VARCHAR(64),
    idempotency_key VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Small governed vocabularies via CHECK, not arbitrary strings. Channel: email now; phone modeled,
    -- deferred (BOPEN-NOTIFY-001 §1 D-03). Lifecycle: the projection states of §2.
    CONSTRAINT chk_notification_channel CHECK (channel IN ('email', 'phone')),
    CONSTRAINT chk_notification_lifecycle CHECK (
        lifecycle_state IN (
            'accepted', 'dispatching', 'suppressed', 'cancelled', 'provider_accepted',
            'delivered', 'delayed', 'failed', 'unknown', 'terminal_unknown'
        )
    ),
    -- (tenant_id, id) unique so children reference a notification BY TENANT.
    CONSTRAINT unq_notification_tenant_id UNIQUE (tenant_id, id),
    -- NOTIFY-INV-06: a retried request collides per tenant and returns the existing record.
    CONSTRAINT unq_notification_idempotency UNIQUE (tenant_id, idempotency_key)
);

ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_notifications ON notifications
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- 2. notification_dispatch — the claimable send-window record and the whole dispatch state machine
-- (analogue of workflow_instances for the send). Mutable / claimable current-state row. Content-free by
-- construction: ids, scheduling, and lease/send control columns only — never a body, subject, or
-- recipient value (WQ-SEC-02). One-to-one with `notifications` in the first slice.
CREATE TABLE IF NOT EXISTS notification_dispatch (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    notification_id UUID NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    attempt_no INT NOT NULL DEFAULT 0,
    -- Deterministic per-attempt provider idempotency key, stamped before send (ADR-NOTIFY-WQ §3/D-EV-3).
    send_key VARCHAR(255),
    send_started_at TIMESTAMPTZ,
    available_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    lease_owner VARCHAR(128),
    lease_expires_at TIMESTAMPTZ,
    -- Monotonic DB-clock fence for claim concurrency (fenced CAS).
    lease_fence BIGINT NOT NULL DEFAULT 0,
    next_visible_at TIMESTAMPTZ,
    dead_lettered_at TIMESTAMPTZ,
    -- Enqueue-time provider binding so the claim can join provider health before spending a slot.
    provider_id VARCHAR(64),
    provider_profile_version VARCHAR(64),
    revision INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_dispatch_status CHECK (
        status IN ('pending', 'leased', 'sending', 'reconciling', 'done', 'dead')
    ),
    CONSTRAINT unq_dispatch_tenant_id UNIQUE (tenant_id, id),
    -- Same-tenant, durable-referent integrity: ON DELETE RESTRICT. A notification with a dispatch
    -- cannot be deleted; the composite FK also makes a cross-tenant dispatch impossible at the database.
    CONSTRAINT fk_dispatch_notification FOREIGN KEY (tenant_id, notification_id)
        REFERENCES notifications(tenant_id, id) ON DELETE RESTRICT
);

ALTER TABLE notification_dispatch ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_dispatch FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_notification_dispatch ON notification_dispatch
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- DEFERRED to worker stage: the elevated content-free claim policy. A later stage provisions the
-- `bopen_notify_claimer` role and attaches a SECOND policy here — `TO bopen_notify_claimer FOR
-- SELECT, UPDATE USING (true)` (cross-tenant by design), confined by column-level GRANTs to ids and
-- lease/scheduling scalars only (ADR-NOTIFY-WQ §8 WQ-SEC-02). Stage 1 carries the ordinary tenant
-- policy above ONLY; the ordinary policy must always remain alongside the elevated one so revocation
-- (DROP POLICY … TO bopen_notify_claimer) degrades the claim plane to zero-visibility, never open.

-- 3. notification_attempt — append-only, once-written-at-finalization per-attempt evidence (analogue of
-- workflow_history). SELECT + INSERT policies only, composite FK ON DELETE RESTRICT: a recorded attempt
-- survives both direct mutation and a parent cascade (the migration-014 lesson, NOTIFY-INV-12).
CREATE TABLE IF NOT EXISTS notification_attempt (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    dispatch_id UUID NOT NULL,
    attempt_no INT NOT NULL,
    provider_profile VARCHAR(64),
    request_fingerprint VARCHAR(128),
    -- Sourced from the mutable dispatch send_key; recomputable, never random.
    provider_idempotency_ref VARCHAR(255),
    -- The closed four-class classifier outcome (ADR-NOTIFY-WQ §5). terminal_unknown is a dispatch
    -- lifecycle floor, NOT an attempt outcome, so it is deliberately absent here.
    classified_outcome VARCHAR(32) NOT NULL,
    safe_code VARCHAR(64),
    provider_message_id VARCHAR(255),
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_attempt_outcome CHECK (
        classified_outcome IN ('provider_accepted', 'retryable_failed', 'terminal_failed', 'unknown')
    ),
    CONSTRAINT unq_attempt_tenant_id UNIQUE (tenant_id, id),
    CONSTRAINT fk_attempt_dispatch FOREIGN KEY (tenant_id, dispatch_id)
        REFERENCES notification_dispatch(tenant_id, id) ON DELETE RESTRICT
);

ALTER TABLE notification_attempt ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_attempt FORCE ROW LEVEL SECURITY;
-- Read and insert only — no UPDATE or DELETE policy, so a recorded attempt is append-only.
CREATE POLICY notification_attempt_read ON notification_attempt
    FOR SELECT
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
CREATE POLICY notification_attempt_insert ON notification_attempt
    FOR INSERT
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- 4. notification_receipt — append-only provider-observed transport truth (a candidate, never
-- self-promoting). SELECT + INSERT only, composite FK ON DELETE RESTRICT. The deterministic dedup key is
-- CROSS-tenant/cross-provider unique on purpose: a redelivered callback collapses without depending on a
-- nullable/mutable replay id (NOTIFY-INV-06/-10). replay_id, when present, is evidence only.
CREATE TABLE IF NOT EXISTS notification_receipt (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    dispatch_id UUID NOT NULL,
    provider_id VARCHAR(64) NOT NULL,
    provider_event_id VARCHAR(255),
    provider_message_id VARCHAR(255) NOT NULL,
    provider_observed_at TIMESTAMPTZ,
    normalized_status VARCHAR(32) NOT NULL,
    -- Integrity ref for the raw payload; the raw bytes themselves live behind the adapter facade, never
    -- in this row (INV-13).
    raw_payload_integrity_ref VARCHAR(255),
    -- digest(provider_id ‖ provider_message_id ‖ provider_event_id ‖ payload_signature_digest).
    dedup_key VARCHAR(128) NOT NULL,
    -- Computed at insert against the current projection; a stale/contradicting receipt is inserted
    -- superseded/conflicting and does not advance the mutable lifecycle (NOTIFY-INV-11).
    projection_marker VARCHAR(16) NOT NULL DEFAULT 'applied',
    replay_id VARCHAR(255),
    received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_receipt_projection CHECK (
        projection_marker IN ('applied', 'superseded', 'conflicting')
    ),
    CONSTRAINT unq_receipt_tenant_id UNIQUE (tenant_id, id),
    -- NOTIFY-INV-06: deterministic replay dedup, independent of a nullable replay_id. Cross-tenant by
    -- construction because a callback arrives with no tenant context.
    CONSTRAINT unq_receipt_dedup UNIQUE (provider_id, provider_message_id, dedup_key),
    CONSTRAINT fk_receipt_dispatch FOREIGN KEY (tenant_id, dispatch_id)
        REFERENCES notification_dispatch(tenant_id, id) ON DELETE RESTRICT
);

ALTER TABLE notification_receipt ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_receipt FORCE ROW LEVEL SECURITY;
CREATE POLICY notification_receipt_read ON notification_receipt
    FOR SELECT
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
CREATE POLICY notification_receipt_insert ON notification_receipt
    FOR INSERT
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- 5. notification_quota — per-tenant token-bucket admission control (ADR-NOTIFY-WQ §7 D3). Tenant-scoped
-- control row keyed on (tenant_id, purpose, window_start).
CREATE TABLE IF NOT EXISTS notification_quota (
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    purpose VARCHAR(32) NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    tokens_used INT NOT NULL DEFAULT 0,
    tokens_limit INT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_notification_quota PRIMARY KEY (tenant_id, purpose, window_start)
);

ALTER TABLE notification_quota ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_quota FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_notification_quota ON notification_quota
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- 6. notification_quota_suspend — emergency per-tenant suspension, never conflated with ordinary quota.
CREATE TABLE IF NOT EXISTS notification_quota_suspend (
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    active BOOLEAN NOT NULL DEFAULT false,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_notification_quota_suspend PRIMARY KEY (tenant_id)
);

ALTER TABLE notification_quota_suspend ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_quota_suspend FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_notification_quota_suspend ON notification_quota_suspend
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- 7. notification_fairness — the per-tenant interleave cursor for least-recently-served scheduling
-- (ADR-NOTIFY-WQ §7 D2). Tenant-scoped control row.
CREATE TABLE IF NOT EXISTS notification_fairness (
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    last_served_at TIMESTAMPTZ,
    inflight_reserved INT NOT NULL DEFAULT 0,
    CONSTRAINT pk_notification_fairness PRIMARY KEY (tenant_id)
);

ALTER TABLE notification_fairness ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_fairness FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_notification_fairness ON notification_fairness
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- 8. notification_provider_health — the platform circuit-breaker / probe-fence control-plane row. This
-- is NOT tenant business data: it is keyed on `provider_id` with no `tenant_id`, so the ordinary tenant
-- policy is inexpressible on it and it is NOT copied per-tenant (kept out of COPY_ORDER). It is
-- classified INFRASTRUCTURE in the isolation suite. Under ENABLE + FORCE ROW LEVEL SECURITY with no
-- policy it is deny-by-default to bopen_app; the elevated worker/callback roles receive their
-- SELECT/UPDATE grants and role-scoped policies in the later worker/callback stage.
CREATE TABLE IF NOT EXISTS notification_provider_health (
    provider_id VARCHAR(64) PRIMARY KEY,
    state VARCHAR(16) NOT NULL DEFAULT 'closed',
    failure_count INT NOT NULL DEFAULT 0,
    opened_at TIMESTAMPTZ,
    half_open_at TIMESTAMPTZ,
    probe_fence BIGINT NOT NULL DEFAULT 0,
    probe_owner VARCHAR(128),
    probe_lease_expires_at TIMESTAMPTZ,
    -- Per-provider callback-rate counter, keyed only on provider (CB-SEC-05).
    callback_rate_tokens INT NOT NULL DEFAULT 0,
    callback_rate_window_start TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_provider_health_state CHECK (state IN ('closed', 'open', 'half_open'))
);

ALTER TABLE notification_provider_health ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_provider_health FORCE ROW LEVEL SECURITY;
-- No tenant policy (platform control-plane, not tenant-owned). Deny-by-default under FORCE RLS.

-- DEFERRED to worker/callback stages (NOT built by Stage 1): the elevated DB roles
-- `bopen_notify_claimer` / `bopen_notify_callback` and their content-free cross-tenant policies + column
-- grants; the governed `notify-worker` / `notify-callback` service principals; the append-only
-- `notification_callback_event` (deterministic dedup ledger) and tenantless `notification_callback_quarantine`
-- tables; and the repositories/worker runtime/adapter/callback ingest/endpoints. Each is a later stage
-- with its own operator authorization.
