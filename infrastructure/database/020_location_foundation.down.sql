-- Rollback for 020_location_foundation.sql.
-- Children before parents: every child references locations by a composite foreign key.

DROP POLICY IF EXISTS location_history_insert ON location_history;
DROP POLICY IF EXISTS location_history_read ON location_history;
DROP TABLE IF EXISTS location_history;

DROP INDEX IF EXISTS unq_rel_one_active_parent;
DROP INDEX IF EXISTS unq_rel_live_edge;
DROP POLICY IF EXISTS tenant_isolation_location_relationships ON location_relationships;
DROP TABLE IF EXISTS location_relationships;

DROP INDEX IF EXISTS unq_extid_live;
DROP POLICY IF EXISTS tenant_isolation_location_external_identifiers ON location_external_identifiers;
DROP TABLE IF EXISTS location_external_identifiers;

DROP POLICY IF EXISTS tenant_isolation_location_geometry_observations ON location_geometry_observations;
DROP TABLE IF EXISTS location_geometry_observations;

DROP INDEX IF EXISTS unq_addr_current;
DROP POLICY IF EXISTS tenant_isolation_location_address_versions ON location_address_versions;
DROP TABLE IF EXISTS location_address_versions;

DROP POLICY IF EXISTS tenant_isolation_locations ON locations;
DROP TABLE IF EXISTS locations;
