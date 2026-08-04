-- Rollback for 016_principal_reference_survives_placement.sql.
-- Restores the three principal_id foreign keys. Note this reopens the cross-database gap the forward
-- migration closes: a dedicated tenant's membership/context/audit rows would again fail the FK.
-- Restoring is only sound on a database whose principal rows are all present locally (the shared
-- pool / control database).

ALTER TABLE memberships
    ADD CONSTRAINT memberships_principal_id_fkey
    FOREIGN KEY (principal_id) REFERENCES principals(id) ON DELETE CASCADE;
ALTER TABLE active_contexts
    ADD CONSTRAINT active_contexts_principal_id_fkey
    FOREIGN KEY (principal_id) REFERENCES principals(id) ON DELETE CASCADE;
ALTER TABLE audit_events
    ADD CONSTRAINT audit_events_principal_id_fkey
    FOREIGN KEY (principal_id) REFERENCES principals(id) ON DELETE SET NULL;
