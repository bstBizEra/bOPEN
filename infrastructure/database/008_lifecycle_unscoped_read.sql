-- Migration: 008_lifecycle_unscoped_read.sql
-- Description: Give the unscoped lifecycle-audit bucket a reader. Closes the half of the
--              audit-evasion finding that the producer change alone cannot reach.
-- Version: 1.0.0
-- Work package: BOPEN-P35-001
-- Governing artifacts: BOPEN-P1-001-EXECUTION-PLAN §10.2; AGENTS.md §8; BOPEN-GOV-EBIV-001
-- Rollback: 008_lifecycle_unscoped_read.down.sql
--
-- =============================================================================
-- Why
-- =============================================================================
-- Migration 006 let pre-resolution events be written and deliberately added no SELECT policy,
-- reasoning that a row belonging to no tenant should not be shown to whichever tenant asked,
-- because that would be inventing an owner. That reasoning is correct and this migration does
-- not weaken it: no tenant session gains anything here.
--
-- What 006 also recorded, in its own words, was that "reading them needs an administrative path
-- that does not exist yet". Security review on 2026-07-30 found what that gap costs. The sink
-- decided whether an event was tenant-scoped by matching `tenant_id` against the strings
-- 'unknown' and 'scoped', and on the context-switch denial path `tenant_id` is the request
-- body's tenant field. So a caller could file their own denial into a bucket with no reader by
-- naming their tenant `unknown`. Reproduced end to end: of two identical denials, the one whose
-- requested tenant was that literal string vanished from the tenant's audit trail.
--
-- The producer side of that is fixed in the same change as this migration — scope is now stated
-- by the producer and reached by parsing, so `unknown` is one unresolvable string among
-- infinitely many and has no special power. But that alone does not close the finding, because
-- a genuinely unresolvable tenant still lands here, and a bucket nothing can read is a bucket
-- where evidence goes to be forgotten. Both halves are needed: the producer change stops the
-- caller choosing the destination, and this stops the destination being a hole.

CREATE POLICY lifecycle_events_read_unscoped ON lifecycle_events
    FOR SELECT
    USING (
        tenant_id IS NULL
        AND tenant_scope IN ('unknown', 'scoped')
        AND NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL
    );

-- The third condition is what keeps 006's reasoning intact. Without it the policy would expose
-- every pre-resolution event to every tenant session — failed authentications across the whole
-- deployment, readable by any tenant on it. That would be a worse disclosure than the one being
-- closed. Unscoped rows are readable only from a session that is itself unscoped, which is the
-- same shape migration 007 uses for the registry tables.
--
-- The first two conditions restate the row's own scope rather than relying on the CHECK
-- constraint from 005 to keep identifier and scope in agreement. Stating both means a future
-- edit to one cannot silently widen the other — the same reasoning migration 006 gives for the
-- `tenant_scope` restriction in its INSERT policy.
--
-- =============================================================================
-- What this does not do
-- =============================================================================
-- It does not build an operator console, an export, or a retention path. It makes the rows
-- reachable by a system session; something still has to read them, and deciding who may run
-- that query is an authorization question above this layer, not an RLS one.
--
-- It adds no UPDATE or DELETE policy. `lifecycle_events` stays append-only for the application
-- role, which is the property the audit trail rests on.
