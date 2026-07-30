-- Rollback: 006_lifecycle_unscoped_append.down.sql
-- Reverses: 006_lifecycle_unscoped_append.sql
-- Version: 1.0.0
-- Work package: BOPEN-P35-001
--
-- Rolling this back restores the state where a lifecycle event with no resolved tenant cannot be
-- written at all. Rows already inserted are untouched — dropping a policy does not remove data,
-- and the table is append-only in any case.
--
-- The effect is that any producer emitting a pre-resolution event begins failing on insert.
-- Whether that surfaces as an error or as a swallowed exception depends on the caller, which is
-- the reason this is worth stating: the failure mode of the state this restores is silent loss
-- of the audit records that describe failures occurring before a tenant is known.

DROP POLICY IF EXISTS lifecycle_events_append_unscoped ON lifecycle_events;
