-- Migration: 015_placement_identity.sql
-- Description: A database's declaration of the single tenant it serves. Empty in the shared pool;
--              one row in a dedicated database. Read by placement.verify_connection_serves to turn
--              a mis-configured dedicated route into a loud refusal instead of a silent empty read.
-- Version: 1.0.0
-- Work package: BOPEN-P35-001 (WP-P35-06 dedicated-database provisioning)
-- Governing artifacts: DEC-P35-TENANCY-MODEL §8 (Option D), §10; PLAN-P35-06-DEDICATED-DB §2.2
-- Rollback: 015_placement_identity.down.sql
--
-- =============================================================================
-- Why this table, and why one row at most
-- =============================================================================
-- The placement seam resolves a dedicated tenant to a database URL, but a URL can be mis-configured.
-- `verify_connection_serves` closes that: after connecting, it reads this table and refuses the
-- connection unless the database declares it serves EXACTLY the tenant that was resolved for. A wrong
-- ref then fails loudly rather than opening a correctly-tenant-scoped session onto a database that
-- holds someone else's data (or none), which row-level security cannot catch — inside the wrong
-- database the session simply finds no rows and reads "no data" instead of "refused".
--
-- The single-row constraint makes "this database serves two tenants" unrepresentable. A provisioning
-- bug that tried to declare a second tenant would be refused by the primary key, so a dedicated
-- database can never silently become shared-by-accident.
--
-- This table is applied to EVERY database (uniform schema). It stays empty in the shared pool and
-- control database, where verify_connection_serves returns early and never reads it.

CREATE TABLE IF NOT EXISTS placement_identity (
    tenant_id UUID NOT NULL,
    -- `singleton` is always true and is the primary key, so the table admits at most one row.
    singleton BOOLEAN NOT NULL DEFAULT true,
    declared_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_placement_identity PRIMARY KEY (singleton),
    CONSTRAINT chk_placement_identity_singleton CHECK (singleton = true)
);

-- Row-level security is ENABLED and FORCED like every other table in the schema, so this table is
-- structurally protected and cannot be left open by omission — the discipline
-- `test_every_table_in_the_schema_is_classified_and_protected` enforces after the 007 disclosure.
--
-- The policy is TENANT-MATCHING, the same shape the tenant-scoped tables use. `verify_connection_
-- serves` reads this table WHILE the resolved tenant's scope is in force, so a matching policy still
-- admits the declaration for the tenant a correctly-routed connection serves, and it makes a
-- mis-route return zero rows — the verification then refuses on the empty read. This REINFORCES
-- verify_connection_serves rather than relying on it alone, and it does not expose the served-tenant
-- id to any other tenant's scope.
--
-- (An earlier revision used `USING (true)` with a comment claiming a tenant-matching policy would
-- hide the row from verification. The verifier disproved that by execution — a tenant-matching
-- policy still admits the served tenant and still refuses a mis-route, and is strictly tighter — so
-- the policy was narrowed to this. Recorded rather than quietly changed.)
--
-- SELECT and INSERT only — no UPDATE or DELETE policy — so the declaration is write-once: a
-- provisioned identity cannot be silently re-pointed. The single-row primary key makes a second
-- declaration unrepresentable regardless of scope.
ALTER TABLE placement_identity ENABLE ROW LEVEL SECURITY;
ALTER TABLE placement_identity FORCE ROW LEVEL SECURITY;
CREATE POLICY placement_identity_read ON placement_identity
    FOR SELECT
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
CREATE POLICY placement_identity_declare ON placement_identity
    FOR INSERT
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
