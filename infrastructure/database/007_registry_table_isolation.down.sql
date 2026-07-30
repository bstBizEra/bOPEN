-- Rollback for: 007_registry_table_isolation.sql
--
-- Restores the pre-007 state exactly: no row security and no policies on the three registry
-- and infrastructure tables.
--
-- Applying this reopens the cross-tenant disclosure that 007 closed — every tenant session
-- regains read access to the full tenant list and every principal email on the deployment.
-- It exists because a migration whose rollback has never been executed is a migration whose
-- rollback does not work, and the round trip is verified on every apply. It is not a
-- remediation step.

DROP POLICY IF EXISTS schema_migrations_write ON schema_migrations;
DROP POLICY IF EXISTS schema_migrations_read ON schema_migrations;
DROP POLICY IF EXISTS principals_administer ON principals;
DROP POLICY IF EXISTS principals_provision ON principals;
DROP POLICY IF EXISTS principals_read ON principals;
DROP POLICY IF EXISTS tenants_administer ON tenants;
DROP POLICY IF EXISTS tenants_provision ON tenants;
DROP POLICY IF EXISTS tenants_read ON tenants;

ALTER TABLE schema_migrations NO FORCE ROW LEVEL SECURITY;
ALTER TABLE schema_migrations DISABLE ROW LEVEL SECURITY;
ALTER TABLE principals NO FORCE ROW LEVEL SECURITY;
ALTER TABLE principals DISABLE ROW LEVEL SECURITY;
ALTER TABLE tenants NO FORCE ROW LEVEL SECURITY;
ALTER TABLE tenants DISABLE ROW LEVEL SECURITY;
