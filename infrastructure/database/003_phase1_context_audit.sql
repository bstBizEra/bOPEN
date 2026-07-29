-- Migration: 003_phase1_context_audit.sql
-- Description: Phase 1 active-context and audit-event persistence, plus tenant identity
--              reconciliation between migrations 001 and 002.
-- Version: 1.0.0
-- Work package: BOPEN-P35-001 (WP-P35-01, deliverable D-01)
-- Governing artifacts: BOPEN-TENANT-001, BOPEN-AUTHZ-001, AGENTS.md section 8 and section 14
-- Rollback: 003_phase1_context_audit.down.sql
--
-- Why this migration exists
-- -------------------------
-- The Phase 1 execution chain is:
--     register principal -> provision tenant -> create owner membership
--     -> establish context -> authorize -> emit audit event
--
-- Migration 001 persists principals, tenants and memberships. It persists neither the
-- active context nor the audit event, so the last two links of the chain have no storage
-- at all. Invariant 6 of AGENTS.md section 7 requires active context to be explicit,
-- validated AND auditable; invariant 11 requires audit events to be distinct from domain
-- events but correlated with them. Neither is satisfiable without these tables.

-- =============================================================================
-- 1. Active context
-- =============================================================================
-- A context binds a principal to exactly one tenant for the duration of a request. It is
-- tenant-scoped and therefore subject to row-level security like any other tenant-owned
-- relation.

CREATE TABLE IF NOT EXISTS active_contexts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    principal_id UUID NOT NULL REFERENCES principals(id) ON DELETE CASCADE,
    membership_id UUID NOT NULL REFERENCES memberships(id) ON DELETE CASCADE,
    correlation_id VARCHAR(64) NOT NULL,
    established_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ NULL,

    -- A context that expires before it is established is never valid. Rejecting it here
    -- means no application path can create one, including a buggy one.
    CONSTRAINT chk_context_window CHECK (expires_at > established_at),

    -- Revocation cannot predate establishment.
    CONSTRAINT chk_context_revocation CHECK (revoked_at IS NULL OR revoked_at >= established_at)
);

-- Uniqueness is tenant-scoped per AGENTS.md section 14: the same principal may hold a live
-- context in several tenants simultaneously, but only one per tenant.
CREATE UNIQUE INDEX IF NOT EXISTS unq_live_context_per_tenant_principal
    ON active_contexts (tenant_id, principal_id)
    WHERE revoked_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_active_contexts_correlation
    ON active_contexts (correlation_id);

ALTER TABLE active_contexts ENABLE ROW LEVEL SECURITY;
ALTER TABLE active_contexts FORCE ROW LEVEL SECURITY;

-- USING governs which rows are visible to SELECT, UPDATE and DELETE.
-- WITH CHECK governs which rows may be written by INSERT and UPDATE.
-- Both are stated explicitly rather than relying on WITH CHECK defaulting to USING, so
-- that the write-side constraint survives any later edit to the read-side expression.
CREATE POLICY active_contexts_isolation ON active_contexts
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- =============================================================================
-- 2. Audit events
-- =============================================================================
-- Audit events are append-only. Append-only is enforced by granting SELECT and INSERT
-- policies and deliberately granting no UPDATE or DELETE policy: under row-level security
-- a command with no permissive policy sees no rows, so UPDATE and DELETE can never reach
-- an existing record.

CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    principal_id UUID NULL REFERENCES principals(id) ON DELETE SET NULL,
    context_id UUID NULL REFERENCES active_contexts(id) ON DELETE SET NULL,
    correlation_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    action VARCHAR(128) NOT NULL,
    resource_type VARCHAR(128) NOT NULL,
    resource_id VARCHAR(255) NULL,
    decision VARCHAR(16) NULL,
    reason_code VARCHAR(64) NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Deny-by-default is an invariant of BOPEN-AUTHZ-001. Constraining the column to the
    -- decision vocabulary keeps an unrecognised third value from being read as "not denied".
    CONSTRAINT chk_audit_decision CHECK (decision IS NULL OR decision IN ('allow', 'deny')),

    -- An authorization audit record without a reason code cannot be reviewed later.
    CONSTRAINT chk_audit_reason_present CHECK (decision IS NULL OR reason_code IS NOT NULL)
);

-- ON DELETE RESTRICT on tenant_id is deliberate and differs from the CASCADE used
-- elsewhere: deleting a tenant must not silently erase its audit trail. Retention and
-- purge are governed decisions, not a side effect of a foreign key.

CREATE INDEX IF NOT EXISTS idx_audit_events_tenant_time
    ON audit_events (tenant_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_events_correlation
    ON audit_events (correlation_id);

ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events FORCE ROW LEVEL SECURITY;

CREATE POLICY audit_events_read_isolation ON audit_events
    FOR SELECT
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY audit_events_append_isolation ON audit_events
    FOR INSERT
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- No UPDATE policy and no DELETE policy: this is the append-only enforcement, and it is
-- intentional. Do not add one without an approved ADR.

-- =============================================================================
-- 3. Tenant identity reconciliation between 001 and 002
-- =============================================================================
-- Migration 001 models tenant_id as UUID with a foreign key to tenants(id).
-- Migration 002 models tenant_id as VARCHAR(64) with no foreign key, and its row-level
-- security policies compare that text directly against current_setting(...).
--
-- The same logical column therefore has two types and two isolation semantics in one
-- database. Consequences:
--   a) a row in a 002 table may reference a tenant that does not exist;
--   b) the 002 policies compare text to text, so a session variable that is not a valid
--      UUID still matches rows, whereas the 001 policies would raise on the cast;
--   c) joining a 001 table to a 002 table requires a cast that defeats index usage.
--
-- Migrations are append-only after merge (AGENTS.md section 14), so 002 is not edited.
-- Converting the 002 columns to UUID is a destructive change requiring a staged rollout
-- plan, which is out of scope for this migration and is raised instead as a decision.
--
-- What this migration does now is close the weakest gap without a type change: it makes
-- the 002 tenant identifiers structurally valid UUID text, so that the reconciliation can
-- later be performed as a pure type change with no data cleanup.

ALTER TABLE tenant_entitlement_plans
    ADD CONSTRAINT chk_plans_tenant_id_is_uuid
    CHECK (tenant_id ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');

ALTER TABLE tenant_entitlement_overrides
    ADD CONSTRAINT chk_overrides_tenant_id_is_uuid
    CHECK (tenant_id ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');

ALTER TABLE usage_meter_balances
    ADD CONSTRAINT chk_balances_tenant_id_is_uuid
    CHECK (tenant_id ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');

ALTER TABLE quota_reservations
    ADD CONSTRAINT chk_reservations_tenant_id_is_uuid
    CHECK (tenant_id ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');

ALTER TABLE usage_outbox
    ADD CONSTRAINT chk_outbox_tenant_id_is_uuid
    CHECK (tenant_id ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');

-- =============================================================================
-- 4. Quota and metering integrity constraints missing from 002
-- =============================================================================
-- The independent review of 2026-07-30 recorded that quota reservation accepts a
-- non-positive quantity and an already-expired window, and that neither is refused by the
-- database. Application-level guards were added in Phase 3 but AGENTS.md section 8 requires
-- database enforcement, not only application filtering. These constraints make the invalid
-- states unrepresentable regardless of which service writes the row.

ALTER TABLE quota_reservations
    ADD CONSTRAINT chk_reservation_quantity_positive
    CHECK (reserved_quantity > 0);

ALTER TABLE quota_reservations
    ADD CONSTRAINT chk_reservation_status
    CHECK (status IN ('pending', 'committed', 'released', 'expired'));

ALTER TABLE quota_reservations
    ADD CONSTRAINT chk_reservation_expiry_future
    CHECK (expires_at > created_at);

ALTER TABLE usage_meter_balances
    ADD CONSTRAINT chk_balance_window_order
    CHECK (window_end > window_start);

ALTER TABLE usage_meter_balances
    ADD CONSTRAINT chk_balance_quota_positive
    CHECK (quota_limit > 0);

-- Usage may not exceed the entitled quota, and may not go negative. This is the database
-- expression of the quota guarantee that the in-memory implementation could not provide,
-- because it held no balance to check against.
ALTER TABLE usage_meter_balances
    ADD CONSTRAINT chk_balance_within_quota
    CHECK (used_quantity >= 0 AND used_quantity <= quota_limit);

ALTER TABLE usage_outbox
    ADD CONSTRAINT chk_outbox_quantity_positive
    CHECK (quantity > 0);
