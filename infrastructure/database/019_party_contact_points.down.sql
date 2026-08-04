-- Rollback for 019_party_contact_points.sql.
-- Children before parents: the verification-events table references party_contact_points.

DROP POLICY IF EXISTS party_cp_verification_events_insert ON party_contact_point_verification_events;
DROP POLICY IF EXISTS party_cp_verification_events_read ON party_contact_point_verification_events;
DROP TABLE IF EXISTS party_contact_point_verification_events;

DROP INDEX IF EXISTS unq_cp_primary;
DROP POLICY IF EXISTS tenant_isolation_party_contact_points ON party_contact_points;
DROP TABLE IF EXISTS party_contact_points;
