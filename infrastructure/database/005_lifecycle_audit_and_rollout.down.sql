-- Rollback: 005_lifecycle_audit_and_rollout.down.sql
-- Reverses: 005_lifecycle_audit_and_rollout.sql
-- Version: 1.0.0
-- Work package: BOPEN-P35-001
--
-- THIS DESTROYS AN AUDIT TRAIL.
--
-- `lifecycle_events` is append-only by policy precisely so that no application path can remove a
-- record. This script removes all of them, because a table cannot be dropped selectively. That
-- is the same asymmetry migration 003's rollback carries for `audit_events`, and the same
-- warning applies: safe on a development or verification database, and requiring an approved
-- retention decision anywhere else.
--
-- `tools/db_bootstrap.py --rollback` refuses to run without BOPEN_DB_NON_PRODUCTION=1 for this
-- reason.
--
-- Reversal order is the inverse of creation, so a partially applied 005 still rolls back.

-- =============================================================================
-- 3. Rate limiting
-- =============================================================================

DROP POLICY IF EXISTS rate_limit_counters_isolation ON rate_limit_counters;
DROP INDEX IF EXISTS idx_rate_limit_counters_window;
DROP TABLE IF EXISTS rate_limit_counters;

DROP POLICY IF EXISTS rate_limit_policies_isolation ON rate_limit_policies;
DROP TABLE IF EXISTS rate_limit_policies;

-- =============================================================================
-- 2. Feature rollout
-- =============================================================================

DROP POLICY IF EXISTS tenant_feature_toggles_isolation ON tenant_feature_toggles;
DROP TABLE IF EXISTS tenant_feature_toggles;

-- =============================================================================
-- 1. Lifecycle audit
-- =============================================================================

DROP POLICY IF EXISTS lifecycle_events_append_isolation ON lifecycle_events;
DROP POLICY IF EXISTS lifecycle_events_read_isolation ON lifecycle_events;
DROP INDEX IF EXISTS idx_lifecycle_events_type_time;
DROP INDEX IF EXISTS idx_lifecycle_events_correlation;
DROP INDEX IF EXISTS idx_lifecycle_events_tenant_time;
DROP TABLE IF EXISTS lifecycle_events;
