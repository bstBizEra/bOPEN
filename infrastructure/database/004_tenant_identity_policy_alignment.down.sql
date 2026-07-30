-- Rollback: 004_tenant_identity_policy_alignment.down.sql
-- Reverses: 004_tenant_identity_policy_alignment.sql
-- Version: 1.0.0
-- Work package: BOPEN-P35-001
--
-- READ THIS BEFORE RUNNING IT.
--
-- This rollback restores a demonstrated isolation defect. Migration 004 exists because the
-- migration 002 policies compare tenant identity as case-sensitive text while 001 and 003
-- compare it as UUID, so one tenant can see its own rows in one family of tables and not the
-- other, silently. Running this script puts that behaviour back.
--
-- It is provided because AGENTS.md section 14 requires every migration to be reversible, and
-- because a policy change on a security boundary that cannot be undone is its own hazard: if
-- 004 turns out to break a caller in a way not anticipated here, an operator needs a way back.
-- Restoring a known defect deliberately, with it recorded, is preferable to being stuck.
--
-- The lowercase normalisation in 004 section 2 is NOT reversed. Re-uppercasing identifiers
-- would be destructive in the sense that matters — it would recreate the exact rows that
-- trigger the defect — and `lower()` on a UUID is information-preserving, so there is nothing
-- to restore. This is a deliberate asymmetry, not an omission.

-- =============================================================================
-- 3. Restore migration 003's case-insensitive shape constraints
-- =============================================================================

ALTER TABLE IF EXISTS usage_outbox DROP CONSTRAINT IF EXISTS chk_outbox_tenant_id_is_uuid;
ALTER TABLE IF EXISTS usage_outbox
    ADD CONSTRAINT chk_outbox_tenant_id_is_uuid
    CHECK (tenant_id ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');

ALTER TABLE IF EXISTS quota_reservations DROP CONSTRAINT IF EXISTS chk_reservations_tenant_id_is_uuid;
ALTER TABLE IF EXISTS quota_reservations
    ADD CONSTRAINT chk_reservations_tenant_id_is_uuid
    CHECK (tenant_id ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');

ALTER TABLE IF EXISTS usage_meter_balances DROP CONSTRAINT IF EXISTS chk_balances_tenant_id_is_uuid;
ALTER TABLE IF EXISTS usage_meter_balances
    ADD CONSTRAINT chk_balances_tenant_id_is_uuid
    CHECK (tenant_id ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');

ALTER TABLE IF EXISTS tenant_entitlement_overrides DROP CONSTRAINT IF EXISTS chk_overrides_tenant_id_is_uuid;
ALTER TABLE IF EXISTS tenant_entitlement_overrides
    ADD CONSTRAINT chk_overrides_tenant_id_is_uuid
    CHECK (tenant_id ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');

ALTER TABLE IF EXISTS tenant_entitlement_plans DROP CONSTRAINT IF EXISTS chk_plans_tenant_id_is_uuid;
ALTER TABLE IF EXISTS tenant_entitlement_plans
    ADD CONSTRAINT chk_plans_tenant_id_is_uuid
    CHECK (tenant_id ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');

-- =============================================================================
-- 1. Restore migration 002's text-comparison policies
-- =============================================================================
-- Reinstated exactly as 002 wrote them, WITH CHECK omitted included. PostgreSQL will default
-- the write-side check to the USING expression, which is what 002 relied on.

DROP POLICY IF EXISTS usage_outbox_isolation ON usage_outbox;
CREATE POLICY usage_outbox_isolation ON usage_outbox
    USING (tenant_id = current_setting('app.current_tenant_id', true));

DROP POLICY IF EXISTS quota_reservations_isolation ON quota_reservations;
CREATE POLICY quota_reservations_isolation ON quota_reservations
    USING (tenant_id = current_setting('app.current_tenant_id', true));

DROP POLICY IF EXISTS usage_meter_balances_isolation ON usage_meter_balances;
CREATE POLICY usage_meter_balances_isolation ON usage_meter_balances
    USING (tenant_id = current_setting('app.current_tenant_id', true));

DROP POLICY IF EXISTS tenant_entitlement_overrides_isolation ON tenant_entitlement_overrides;
CREATE POLICY tenant_entitlement_overrides_isolation ON tenant_entitlement_overrides
    USING (tenant_id = current_setting('app.current_tenant_id', true));

DROP POLICY IF EXISTS tenant_entitlement_plans_isolation ON tenant_entitlement_plans;
CREATE POLICY tenant_entitlement_plans_isolation ON tenant_entitlement_plans
    USING (tenant_id = current_setting('app.current_tenant_id', true));
