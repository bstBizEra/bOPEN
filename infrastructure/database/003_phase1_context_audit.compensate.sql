-- Compensation: 003_phase1_context_audit.compensate.sql
-- Companion to: 003_phase1_context_audit.sql / .down.sql
-- Version: 1.0.0
-- Work package: BOPEN-P35-001 (WP-P35-01, acceptance criterion A-06)
--
-- Why this file exists
-- --------------------
-- Migration 003 adds CHECK constraints. Its rollback drops them. That pair is not
-- round-trippable on its own, and the gap was found by executing the rollback rather than
-- assuming it worked:
--
--   1. rollback 003        -> the constraints are gone
--   2. the system runs     -> rows that violate them are now accepted and committed
--   3. re-apply 003        -> FAILS: "check constraint ... is violated by some row"
--
-- The forward migration cannot fix this, because at the moment it runs the offending rows
-- already exist. AGENTS.md section 14 requires every migration to have a forward, rollback or
-- compensating strategy; for a constraint-adding migration the rollback alone is not a
-- strategy, and this file is the missing third part.
--
-- Observed concretely on 2026-07-30: with the constraints dropped, the negative test suite
-- inserted six rows that the constraints exist to forbid — a zero-quantity reservation, an
-- already-expired reservation, and a balance exceeding its quota — and every one of them
-- committed successfully. Those six rows then blocked re-application.
--
-- THIS SCRIPT DELETES DATA
-- ------------------------
-- It removes exactly the rows that could not have been written while migration 003 was in
-- force. On a development or verification database those rows are artefacts of the rollback
-- window. On any database holding real tenant data they are evidence of an incident, and
-- deleting them destroys that evidence.
--
-- `tools/db_bootstrap.py --compensate 003` therefore refuses to run unless
-- BOPEN_DB_NON_PRODUCTION=1 is set. For a production recovery, quarantine these rows into a
-- side table under an approved incident procedure instead of running this file.

-- Quota reservations that were created with a non-positive quantity or already expired.
DELETE FROM quota_reservations
 WHERE reserved_quantity <= 0
    OR expires_at <= created_at
    OR status NOT IN ('pending', 'committed', 'released', 'expired');

-- Meter balances that are negative, exceed their quota, carry a non-positive quota, or hold an
-- inverted window.
DELETE FROM usage_meter_balances
 WHERE used_quantity < 0
    OR quota_limit <= 0
    OR used_quantity > quota_limit
    OR window_end <= window_start;

-- Outbox entries with a non-positive quantity.
DELETE FROM usage_outbox
 WHERE quantity <= 0;

-- Rows whose tenant identifier is not UUID-shaped. These cannot be reconciled with the UUID
-- columns in migration 001 and would block the tenant identity convergence recorded in
-- migration 003 section 3.
DELETE FROM quota_reservations
 WHERE tenant_id !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
DELETE FROM usage_meter_balances
 WHERE tenant_id !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
DELETE FROM usage_outbox
 WHERE tenant_id !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
DELETE FROM tenant_entitlement_overrides
 WHERE tenant_id !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
DELETE FROM tenant_entitlement_plans
 WHERE tenant_id !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
