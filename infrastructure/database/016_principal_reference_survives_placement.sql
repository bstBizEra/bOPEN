-- Migration: 016_principal_reference_survives_placement.sql
-- Description: Drop the three principal_id foreign keys on routed tables, so a dedicated tenant's
--              membership, context and audit rows can reference a principal that lives in another
--              database. Makes a dedicated tenant usable end to end.
-- Version: 1.0.0
-- Work package: BOPEN-P35-001 (WP-P35-06, Option A)
-- Governing artifacts: DEC-P35-TENANCY-MODEL §11; AGENTS.md §8; BOPEN-GOV-EBIV-001
-- Rollback: 016_principal_reference_survives_placement.down.sql
--
-- =============================================================================
-- Why the foreign key has to go for dedicated placement
-- =============================================================================
-- `principals` is a GLOBAL registry: a principal can hold memberships in several tenants, some on the
-- shared pool and some on their own dedicated database, so it lives once in the control database and
-- is never routed (`repositories.py`: principals use `system_session`). `memberships`,
-- `active_contexts` and `audit_events` are tenant-scoped and ROUTED: for a dedicated tenant they are
-- written into that tenant's own database via `tenant_session`. Each of the three declared
-- `principal_id REFERENCES principals(id)`.
--
-- A foreign key cannot span two databases. So a dedicated tenant's routed row references a principal
-- that is not in its database, and PostgreSQL raises
-- `ForeignKeyViolation: memberships_principal_id_fkey` — reproduced 2026-08-04. The effect is that a
-- dedicated tenant cannot be given a membership, hence no context, hence no working auth chain.
--
-- This is the exact shape migration 009 resolved for `audit_events.context_id`: "an audit record is a
-- historical statement… it has to outlive the row it describes". Here the referent does not disappear
-- — it lives in another database by design. The column stays as a soft reference; only the
-- referential action goes. The relationship is still enforced where it can be: the application reads
-- the principal from the control registry (`principals.get`) and `POST /v1/contexts` checks that the
-- membership names the caller's principal. What the database can no longer guarantee across databases,
-- the application still checks.

ALTER TABLE memberships DROP CONSTRAINT IF EXISTS memberships_principal_id_fkey;
ALTER TABLE active_contexts DROP CONSTRAINT IF EXISTS active_contexts_principal_id_fkey;
ALTER TABLE audit_events DROP CONSTRAINT IF EXISTS audit_events_principal_id_fkey;

COMMENT ON COLUMN memberships.principal_id IS
    'Principal that holds this membership. Deliberately carries no foreign key: principals are a '
    'global registry in the control database, while a dedicated tenant''s memberships live in its own '
    'database, and a foreign key cannot span two databases. Validated in the application. Migration 016.';
COMMENT ON COLUMN active_contexts.principal_id IS
    'Principal this context is for. No foreign key, for the same reason as memberships.principal_id — '
    'the principal is global and the context may be in a dedicated database. Migration 016.';
COMMENT ON COLUMN audit_events.principal_id IS
    'Actor principal. No foreign key: the principal is global and a dedicated tenant''s audit rows are '
    'in its own database. This also removes the ON DELETE SET NULL that migration 009 left in place. '
    'Migration 016.';

-- =============================================================================
-- What this deliberately does not do
-- =============================================================================
-- It does not add orphan handling for principal deletion. The application role has no DELETE policy on
-- `principals` after migration 007 and no code path deletes one, so a dangling `principal_id` is not
-- reachable today; if principal deletion is ever built, the cleanup for these three columns becomes
-- its concern and is recorded there. It does not move any data: existing shared-pool tenants are
-- unaffected (their rows and principals are in the same database), and the trial->paid migration of an
-- existing tenant to a dedicated database remains a separate, deferred slice.
