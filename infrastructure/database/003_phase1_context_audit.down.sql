-- Rollback: 003_phase1_context_audit.down.sql
-- Reverses: 003_phase1_context_audit.sql
-- Version: 1.0.0
-- Work package: BOPEN-P35-001 (WP-P35-01, deliverable D-01)
--
-- Required by AGENTS.md section 14: every migration must have a forward, rollback or
-- compensating strategy.
--
-- Reversal order is the inverse of application. Constraints added to pre-existing tables
-- are dropped before the new tables, so that a partially applied 003 can still be rolled
-- back cleanly. Every statement is IF EXISTS for that reason.

-- =============================================================================
-- 4. Quota and metering integrity constraints (reverse of section 4)
-- =============================================================================

ALTER TABLE IF EXISTS usage_outbox
    DROP CONSTRAINT IF EXISTS chk_outbox_quantity_positive;

ALTER TABLE IF EXISTS usage_meter_balances
    DROP CONSTRAINT IF EXISTS chk_balance_within_quota;

ALTER TABLE IF EXISTS usage_meter_balances
    DROP CONSTRAINT IF EXISTS chk_balance_quota_positive;

ALTER TABLE IF EXISTS usage_meter_balances
    DROP CONSTRAINT IF EXISTS chk_balance_window_order;

ALTER TABLE IF EXISTS quota_reservations
    DROP CONSTRAINT IF EXISTS chk_reservation_expiry_future;

ALTER TABLE IF EXISTS quota_reservations
    DROP CONSTRAINT IF EXISTS chk_reservation_status;

ALTER TABLE IF EXISTS quota_reservations
    DROP CONSTRAINT IF EXISTS chk_reservation_quantity_positive;

-- =============================================================================
-- 3. Tenant identity reconciliation (reverse of section 3)
-- =============================================================================

ALTER TABLE IF EXISTS usage_outbox
    DROP CONSTRAINT IF EXISTS chk_outbox_tenant_id_is_uuid;

ALTER TABLE IF EXISTS quota_reservations
    DROP CONSTRAINT IF EXISTS chk_reservations_tenant_id_is_uuid;

ALTER TABLE IF EXISTS usage_meter_balances
    DROP CONSTRAINT IF EXISTS chk_balances_tenant_id_is_uuid;

ALTER TABLE IF EXISTS tenant_entitlement_overrides
    DROP CONSTRAINT IF EXISTS chk_overrides_tenant_id_is_uuid;

ALTER TABLE IF EXISTS tenant_entitlement_plans
    DROP CONSTRAINT IF EXISTS chk_plans_tenant_id_is_uuid;

-- =============================================================================
-- 2. Audit events (reverse of section 2)
-- =============================================================================
-- Dropping audit_events destroys an audit trail. This rollback is safe only in a
-- development or verification database. Executing it against an environment holding real
-- audit records requires an approved retention decision first; the migration runner
-- refuses rollback unless the target is explicitly marked non-production.

DROP POLICY IF EXISTS audit_events_append_isolation ON audit_events;
DROP POLICY IF EXISTS audit_events_read_isolation ON audit_events;
DROP INDEX IF EXISTS idx_audit_events_correlation;
DROP INDEX IF EXISTS idx_audit_events_tenant_time;
DROP TABLE IF EXISTS audit_events;

-- =============================================================================
-- 1. Active context (reverse of section 1)
-- =============================================================================

DROP POLICY IF EXISTS active_contexts_isolation ON active_contexts;
DROP INDEX IF EXISTS idx_active_contexts_correlation;
DROP INDEX IF EXISTS unq_live_context_per_tenant_principal;
DROP TABLE IF EXISTS active_contexts;
