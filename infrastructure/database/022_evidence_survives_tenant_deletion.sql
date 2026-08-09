-- Migration: 022_evidence_survives_tenant_deletion.sql
-- Description: Stop a recorded evidence row from being erased by deleting its tenant.
--              Closes the last reachable deletion of the append-only evidence tables.
-- Version: 1.0.0
-- Work package: WP-P35-08
-- Governing artifacts: DEC-P4-NOTIFY-TENANT-CASCADE §6, §7; AGENTS.md §8, §14;
--                      BOPEN-GOV-EBIV-001
-- Rollback: 022_evidence_survives_tenant_deletion.down.sql
--
-- =============================================================================
-- What was reachable
-- =============================================================================
-- Eleven tables across four foundations are append-only by two mechanisms: RLS policies granting
-- SELECT and INSERT but no UPDATE or DELETE, and an `ON DELETE RESTRICT` foreign key to the parent
-- row. Migration 009 records why the second is needed — *PostgreSQL performs foreign-key actions
-- with row security bypassed* — and migration 014 applied it to `workflow_history` after a verifier
-- reproduced a live erasure through the parent edge.
--
-- Both mechanisms were in place and neither defended the row, because each table also declared
-- `tenant_id REFERENCES tenants(id) ON DELETE CASCADE`. The tenant edge reaches the row first, so
-- the RESTRICT edge is never consulted. Reproduced live by an independent verifier on the
-- notification tables (ballot bd42b2e):
--
--     attempt and receipt recorded    2 rows
--     DELETE the tenant               succeeds
--     attempt and receipt             0 rows        -- erased, no error, no test red
--
-- The same shape was then found on ten further tables. Migration 014 is itself on that list: it
-- closed the instance edge and left the tenant edge CASCADE, so the migration written to teach this
-- lesson carried the gap it teaches about.
--
-- =============================================================================
-- Why RESTRICT on the tenant edge, and why it is the mechanism that binds
-- =============================================================================
-- The path is reachable only by a superuser or table owner: `tenants` has SELECT, INSERT and UPDATE
-- policies and no DELETE policy, so `bopen_app` deleting a tenant reaches zero rows silently. Row
-- security does not constrain a superuser. Foreign-key constraints do.
--
-- `ON DELETE RESTRICT` is therefore effective on exactly the path that is exposed, and it is the
-- only one of the two mechanisms that binds the role able to trigger the defect.
--
-- `audit_events` (003) and `lifecycle_events` (005) already declare `tenant_id ... ON DELETE
-- RESTRICT`. This migration applies the pattern the repository already uses rather than inventing
-- one.
--
-- =============================================================================
-- Consequence, accepted deliberately
-- =============================================================================
-- A tenant holding evidence can no longer be deleted until that evidence is archived or released.
-- Tenant offboarding becomes an operation with a prerequisite. That is a product consequence and it
-- is the point: a future offboarding capability must confront evidence retention rather than
-- silently destroy it. Separating retention from tenant lifetime (Option 3 of the decision) remains
-- open; RESTRICT is the floor that makes its absence loud instead of silent.
--
-- A tenant holding NO evidence remains deletable. That is asserted by R-2 of the Refusal Matrix and
-- is not incidental: a migration that made all tenant deletion impossible would satisfy every R-1
-- probe and be wrong.
--
-- Only the delete action changes. No policy, grant, column, index or table definition is touched.
-- =============================================================================

BEGIN;

-- Workflow (013/014)
ALTER TABLE workflow_history DROP CONSTRAINT workflow_history_tenant_id_fkey;
ALTER TABLE workflow_history ADD CONSTRAINT workflow_history_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT;

-- Party ContactPoint (019)
ALTER TABLE party_contact_points DROP CONSTRAINT party_contact_points_tenant_id_fkey;
ALTER TABLE party_contact_points ADD CONSTRAINT party_contact_points_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT;

ALTER TABLE party_contact_point_verification_events
    DROP CONSTRAINT party_contact_point_verification_events_tenant_id_fkey;
ALTER TABLE party_contact_point_verification_events
    ADD CONSTRAINT party_contact_point_verification_events_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT;

-- Location (020)
ALTER TABLE location_address_versions DROP CONSTRAINT location_address_versions_tenant_id_fkey;
ALTER TABLE location_address_versions ADD CONSTRAINT location_address_versions_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT;

ALTER TABLE location_geometry_observations DROP CONSTRAINT location_geometry_observations_tenant_id_fkey;
ALTER TABLE location_geometry_observations ADD CONSTRAINT location_geometry_observations_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT;

ALTER TABLE location_external_identifiers DROP CONSTRAINT location_external_identifiers_tenant_id_fkey;
ALTER TABLE location_external_identifiers ADD CONSTRAINT location_external_identifiers_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT;

ALTER TABLE location_relationships DROP CONSTRAINT location_relationships_tenant_id_fkey;
ALTER TABLE location_relationships ADD CONSTRAINT location_relationships_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT;

ALTER TABLE location_history DROP CONSTRAINT location_history_tenant_id_fkey;
ALTER TABLE location_history ADD CONSTRAINT location_history_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT;

-- Notification (021)
ALTER TABLE notification_dispatch DROP CONSTRAINT notification_dispatch_tenant_id_fkey;
ALTER TABLE notification_dispatch ADD CONSTRAINT notification_dispatch_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT;

ALTER TABLE notification_attempt DROP CONSTRAINT notification_attempt_tenant_id_fkey;
ALTER TABLE notification_attempt ADD CONSTRAINT notification_attempt_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT;

ALTER TABLE notification_receipt DROP CONSTRAINT notification_receipt_tenant_id_fkey;
ALTER TABLE notification_receipt ADD CONSTRAINT notification_receipt_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT;

COMMENT ON CONSTRAINT workflow_history_tenant_id_fkey ON workflow_history IS
    'ON DELETE RESTRICT, not CASCADE: recorded evidence is append-only and must survive, so a '
    'tenant that holds it cannot be deleted until the evidence is archived or released. '
    'WP-P35-08 / DEC-P4-NOTIFY-TENANT-CASCADE.';

COMMIT;
