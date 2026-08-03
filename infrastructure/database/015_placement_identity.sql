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
-- Its policies are deliberately PERMISSIVE, unlike the tenant-scoped tables, and the reason is what
-- this table is and when it is read. It is not tenant *data*: it is the database's own declaration
-- of the single tenant it serves, and it is read by `verify_connection_serves` WHILE a tenant scope
-- is already in force (right after the session sets it) precisely to check that declaration against
-- the resolved tenant. A tenant-matching policy would hide the row from the verification step that
-- has to see it. The one value it exposes is the served-tenant id, which the connecting caller
-- already supplies — not a secret. The real mis-route defence is verify_connection_serves comparing
-- this row to the resolved tenant, plus the single-row primary key; the SELECT/INSERT-only policies
-- (no UPDATE, no DELETE) make the declaration write-once, so a provisioned identity cannot be
-- silently re-pointed.
ALTER TABLE placement_identity ENABLE ROW LEVEL SECURITY;
ALTER TABLE placement_identity FORCE ROW LEVEL SECURITY;
CREATE POLICY placement_identity_read ON placement_identity FOR SELECT USING (true);
CREATE POLICY placement_identity_declare ON placement_identity FOR INSERT WITH CHECK (true);
