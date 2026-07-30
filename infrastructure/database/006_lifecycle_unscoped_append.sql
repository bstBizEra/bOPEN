-- Migration: 006_lifecycle_unscoped_append.sql
-- Description: Allow pre-resolution lifecycle events to be written. Closes a gap migration 005
--              created and recorded but did not fix.
-- Version: 1.0.0
-- Work package: BOPEN-P35-001
-- Governing artifacts: BOPEN-P1-001-EXECUTION-PLAN §10.2; AGENTS.md §8
-- Rollback: 006_lifecycle_unscoped_append.down.sql
--
-- =============================================================================
-- The gap
-- =============================================================================
-- Migration 005 modelled the tenant position as a nullable UUID plus a `tenant_scope` column,
-- because the producer emits the literal strings `unknown` and `scoped` on paths that run before
-- a tenant is resolved — a failed SSO assertion, a context revocation sweep.
--
-- It then gave the table one INSERT policy:
--
--     WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
--
-- `NULL = anything` is never true, so a row with no tenant satisfies neither that policy nor any
-- other. Migration 005's own comment records that such rows are unreadable and calls it
-- deliberate. It is — for reads. For writes it means the events cannot be inserted at all, which
-- is not a limitation but a defect: the audit records that describe a failure occurring before a
-- tenant is known are exactly the ones a post-incident review needs, and they were the ones the
-- schema silently refused.
--
-- Found by attempting to wire the dispatcher to the table rather than by reading the migration
-- back. Recorded here rather than repaired in 005, which is append-only after merge.

CREATE POLICY lifecycle_events_append_unscoped ON lifecycle_events
    FOR INSERT
    WITH CHECK (tenant_id IS NULL AND tenant_scope IN ('unknown', 'scoped'));

-- =============================================================================
-- What this deliberately does not do
-- =============================================================================
-- It adds no SELECT policy. Unscoped rows stay unreadable through any tenant session, which is
-- the property migration 005 chose and this migration keeps: a pre-resolution event belongs to
-- no tenant, so showing it to whichever tenant asked would be inventing an owner.
--
-- Reading them needs an administrative path that does not exist yet. That gap is real and stays
-- recorded — but a durable record nobody has yet built a reader for is strictly better than an
-- insert that fails, because the second loses the evidence permanently.
--
-- The `tenant_scope` restriction in the WITH CHECK matters. Without it the policy would read
-- `tenant_id IS NULL`, and the CHECK constraint from 005 that keeps scope and identifier in
-- agreement would be the only thing stopping a caller from writing a row that claims tenant
-- scope with no tenant. Stating both here means the policy refuses it too, so a future edit to
-- one constraint cannot silently widen the other.
