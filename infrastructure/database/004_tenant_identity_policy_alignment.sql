-- Migration: 004_tenant_identity_policy_alignment.sql
-- Description: Align migration 002's row-level security policies with the tenant identity
--              semantics used by 001 and 003, closing a demonstrated silent isolation defect.
-- Version: 1.0.0
-- Work package: BOPEN-P35-001
-- Governing artifacts: BOPEN-TENANT-001, AGENTS.md section 8, section 14, section 16
-- Rollback: 004_tenant_identity_policy_alignment.down.sql
--
-- =============================================================================
-- The defect, demonstrated rather than argued
-- =============================================================================
-- Migration 002 compares tenant identity as TEXT:
--
--     USING (tenant_id = current_setting('app.current_tenant_id', true))
--
-- Migrations 001 and 003 compare it as UUID:
--
--     USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
--
-- A text comparison is case-sensitive. A UUID comparison is not, because the type normalises
-- case. Migration 003's shape constraint uses `~*`, which is case-INsensitive, so mixed-case
-- UUID text is admissible into the 002 columns in the first place.
--
-- Executed against PostgreSQL 17.10 on 2026-07-30, one tenant identifier stored uppercase:
--
--     context                002 table (text)     003 table (uuid)
--     lowercase              0 rows               1 row
--     uppercase              1 row                1 row
--
-- The same tenant, in the same request, sees its own data in one family of tables and not in
-- the other, and no error is raised. The failure presents as missing data, not as a fault.
--
-- Why that is worse than it first appears: `FeatureRolloutEvaluator.is_feature_enabled` returns
-- `True` when it finds no toggle. A tenant whose toggle rows are invisible because of a case
-- mismatch is therefore granted every feature. A silent isolation defect on the read path
-- becomes a fail-open on the entitlement path.
--
-- =============================================================================
-- Why a new migration rather than an edit
-- =============================================================================
-- AGENTS.md section 14: migrations are append-only after merge. 002 is merged. Its policies are
-- therefore replaced here rather than corrected in place.
--
-- This is a change to a security boundary. It is recorded as a decision request under
-- AGENTS.md section 16 ("two approved artifacts conflict") rather than treated as a routine
-- fix, and the direction of the change is stated plainly: every policy below is at least as
-- restrictive as the one it replaces, never less.

-- =============================================================================
-- 1. Replace the five isolation policies from migration 002
-- =============================================================================
-- `tenant_id::uuid` casts the column rather than the session variable. That is deliberate: the
-- alternative — comparing `tenant_id = (setting)::text` — would preserve the index but keep the
-- case-sensitive semantics this migration exists to remove. Correctness before index usage on
-- tables that hold one row per tenant per capability.
--
-- The cast is safe because migration 003 already constrains every one of these columns to
-- UUID-shaped text (chk_*_tenant_id_is_uuid). Without those constraints in place this migration
-- would fail on any malformed row, which is the correct outcome: it would mean data exists that
-- cannot be reconciled with the tenant registry.
--
-- WITH CHECK is stated explicitly on every policy. PostgreSQL defaults it to the USING
-- expression when omitted, which is what 002 relied on. Stating it means the write-side
-- constraint survives any later edit to the read-side expression — the same reasoning recorded
-- in migration 003 section 1.

DROP POLICY IF EXISTS tenant_entitlement_plans_isolation ON tenant_entitlement_plans;
CREATE POLICY tenant_entitlement_plans_isolation ON tenant_entitlement_plans
    FOR ALL
    USING (tenant_id::uuid = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id::uuid = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

DROP POLICY IF EXISTS tenant_entitlement_overrides_isolation ON tenant_entitlement_overrides;
CREATE POLICY tenant_entitlement_overrides_isolation ON tenant_entitlement_overrides
    FOR ALL
    USING (tenant_id::uuid = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id::uuid = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

DROP POLICY IF EXISTS usage_meter_balances_isolation ON usage_meter_balances;
CREATE POLICY usage_meter_balances_isolation ON usage_meter_balances
    FOR ALL
    USING (tenant_id::uuid = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id::uuid = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

DROP POLICY IF EXISTS quota_reservations_isolation ON quota_reservations;
CREATE POLICY quota_reservations_isolation ON quota_reservations
    FOR ALL
    USING (tenant_id::uuid = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id::uuid = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

DROP POLICY IF EXISTS usage_outbox_isolation ON usage_outbox;
CREATE POLICY usage_outbox_isolation ON usage_outbox
    FOR ALL
    USING (tenant_id::uuid = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id::uuid = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- =============================================================================
-- 2. Normalise identifiers already stored
-- =============================================================================
-- Replacing the policy does not fix rows written under the old semantics. A row stored
-- uppercase becomes visible to the lowercase context after this migration — which is the
-- intended repair — but leaving mixed case in the column means the eventual conversion of these
-- columns to a real UUID type has cleanup to do, and it means `ORDER BY tenant_id` and any
-- future unique index behave inconsistently with the 001/003 family.
--
-- This UPDATE is not destructive: `lower()` on UUID-shaped text is information-preserving,
-- because a UUID's canonical form is lowercase and the two spellings denote the same value.

UPDATE tenant_entitlement_plans      SET tenant_id = lower(tenant_id) WHERE tenant_id <> lower(tenant_id);
UPDATE tenant_entitlement_overrides  SET tenant_id = lower(tenant_id) WHERE tenant_id <> lower(tenant_id);
UPDATE usage_meter_balances          SET tenant_id = lower(tenant_id) WHERE tenant_id <> lower(tenant_id);
UPDATE quota_reservations            SET tenant_id = lower(tenant_id) WHERE tenant_id <> lower(tenant_id);
UPDATE usage_outbox                  SET tenant_id = lower(tenant_id) WHERE tenant_id <> lower(tenant_id);

-- =============================================================================
-- 3. Tighten the shape constraint to canonical lowercase
-- =============================================================================
-- Migration 003 used `~*` (case-insensitive), which is what admitted mixed case. The policies
-- above no longer care about case, so this is defence in depth rather than the primary control:
-- it keeps the column in canonical form so that the future type conversion is a pure cast with
-- no data cleanup, and so that text-level operations behave predictably.
--
-- 003's constraints are dropped and replaced rather than edited, for the same append-only
-- reason this whole migration exists.

ALTER TABLE tenant_entitlement_plans DROP CONSTRAINT IF EXISTS chk_plans_tenant_id_is_uuid;
ALTER TABLE tenant_entitlement_plans
    ADD CONSTRAINT chk_plans_tenant_id_is_uuid
    CHECK (tenant_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');

ALTER TABLE tenant_entitlement_overrides DROP CONSTRAINT IF EXISTS chk_overrides_tenant_id_is_uuid;
ALTER TABLE tenant_entitlement_overrides
    ADD CONSTRAINT chk_overrides_tenant_id_is_uuid
    CHECK (tenant_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');

ALTER TABLE usage_meter_balances DROP CONSTRAINT IF EXISTS chk_balances_tenant_id_is_uuid;
ALTER TABLE usage_meter_balances
    ADD CONSTRAINT chk_balances_tenant_id_is_uuid
    CHECK (tenant_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');

ALTER TABLE quota_reservations DROP CONSTRAINT IF EXISTS chk_reservations_tenant_id_is_uuid;
ALTER TABLE quota_reservations
    ADD CONSTRAINT chk_reservations_tenant_id_is_uuid
    CHECK (tenant_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');

ALTER TABLE usage_outbox DROP CONSTRAINT IF EXISTS chk_outbox_tenant_id_is_uuid;
ALTER TABLE usage_outbox
    ADD CONSTRAINT chk_outbox_tenant_id_is_uuid
    CHECK (tenant_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');

-- =============================================================================
-- What this migration does NOT do
-- =============================================================================
-- The columns remain VARCHAR(64) with no foreign key to tenants(id). A row in any of these five
-- tables may still reference a tenant that does not exist, and every join to the 001/003 family
-- still needs a cast. Converting the columns to UUID and adding the foreign keys is a
-- destructive change requiring a staged rollout plan, and migration 003 section 3 already
-- raised it as a decision rather than a task. It stays raised.
--
-- What changes here is only that the two policy families now agree on what a tenant identifier
-- is. That was the part producing silent wrong answers.
