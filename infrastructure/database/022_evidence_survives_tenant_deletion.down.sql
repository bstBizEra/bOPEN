-- Rollback: 022_evidence_survives_tenant_deletion.down.sql
-- Restores `tenant_id ... ON DELETE CASCADE` on the eleven append-only evidence tables.
--
-- Applying this REINTRODUCES the defect WP-P35-08 closed: deleting a tenant erases its recorded
-- workflow transitions, contact-point verifications, location history and delivery evidence,
-- silently and with every direct-delete test still green. It exists because AGENTS.md §14 requires
-- every migration to carry a rollback, not because reverting is expected to be safe.

BEGIN;

ALTER TABLE workflow_history DROP CONSTRAINT workflow_history_tenant_id_fkey;
ALTER TABLE workflow_history ADD CONSTRAINT workflow_history_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE party_contact_points DROP CONSTRAINT party_contact_points_tenant_id_fkey;
ALTER TABLE party_contact_points ADD CONSTRAINT party_contact_points_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE party_contact_point_verification_events
    DROP CONSTRAINT party_contact_point_verification_events_tenant_id_fkey;
ALTER TABLE party_contact_point_verification_events
    ADD CONSTRAINT party_contact_point_verification_events_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE location_address_versions DROP CONSTRAINT location_address_versions_tenant_id_fkey;
ALTER TABLE location_address_versions ADD CONSTRAINT location_address_versions_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE location_geometry_observations DROP CONSTRAINT location_geometry_observations_tenant_id_fkey;
ALTER TABLE location_geometry_observations ADD CONSTRAINT location_geometry_observations_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE location_external_identifiers DROP CONSTRAINT location_external_identifiers_tenant_id_fkey;
ALTER TABLE location_external_identifiers ADD CONSTRAINT location_external_identifiers_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE location_relationships DROP CONSTRAINT location_relationships_tenant_id_fkey;
ALTER TABLE location_relationships ADD CONSTRAINT location_relationships_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE location_history DROP CONSTRAINT location_history_tenant_id_fkey;
ALTER TABLE location_history ADD CONSTRAINT location_history_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE notification_dispatch DROP CONSTRAINT notification_dispatch_tenant_id_fkey;
ALTER TABLE notification_dispatch ADD CONSTRAINT notification_dispatch_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE notification_attempt DROP CONSTRAINT notification_attempt_tenant_id_fkey;
ALTER TABLE notification_attempt ADD CONSTRAINT notification_attempt_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE notification_receipt DROP CONSTRAINT notification_receipt_tenant_id_fkey;
ALTER TABLE notification_receipt ADD CONSTRAINT notification_receipt_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

COMMIT;
