-- Rollback for 010_party_foundation.sql (MILE-4.1).
-- Drop in dependency order: relationships reference parties.

DROP POLICY IF EXISTS tenant_isolation_party_relationships ON party_relationships;
DROP TABLE IF EXISTS party_relationships;

DROP POLICY IF EXISTS tenant_isolation_parties ON parties;
DROP TABLE IF EXISTS parties;
