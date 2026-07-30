-- Migration: 007_registry_table_isolation.sql
-- Description: Put row-level security on the three tables that never had it. Closes a
--              cross-tenant disclosure of the whole customer list and every user email.
-- Version: 1.0.0
-- Work package: BOPEN-P35-001
-- Governing artifacts: BOPEN-TENANT-001; AGENTS.md §8; BOPEN-GOV-EBIV-001
-- Rollback: 007_registry_table_isolation.down.sql
--
-- =============================================================================
-- What was open
-- =============================================================================
-- Migration 001 created five tables and enabled RLS on two of them. `tenants`, `principals`
-- and `schema_migrations` were left with `relrowsecurity = false` and zero policies, and six
-- migrations went by without anyone noticing, because every isolation test asserts against a
-- table that has a policy. Found by security review on 2026-07-30 and measured:
--
--     a session scoped to one tenant read     7631 rows from tenants
--                                             6657 rows from principals, including emails
--                                                1 row  from tenant_resources   (correct)
--
-- The contrast in that third line is the whole finding. The isolation model was working
-- exactly as designed on every table it had been applied to, and the registry — the list of
-- who the customers are and what every user's email address is — sat beside it in the open.
-- Any tenant could enumerate the entire customer base of the deployment.
--
-- =============================================================================
-- Why these tables were skipped, and why that reasoning does not survive
-- =============================================================================
-- `tenants` and `principals` are not tenant-scoped: they carry no `tenant_id`, and both
-- precede the boundary. A tenant row *defines* a boundary rather than sitting inside one, and
-- a principal exists before any membership places it in one. `repositories.py` says so in both
-- docstrings, and both are read and written exclusively through `system_session`.
--
-- All of that is true, and none of it implies "therefore no policy". It implies the policy is
-- not `tenant_id = current_tenant`; it does not imply the table should be world-readable to
-- every tenant on the deployment. The absent `tenant_id` column made the usual policy
-- inexpressible, and inexpressible was treated as inapplicable.
--
-- So this migration names a second class of table with its own rule, rather than adding an
-- exception to the first:
--
--   tenant-scoped  carries tenant_id. Policy: tenant_id = current. Unscoped reads nothing.
--                  (memberships, tenant_resources, active_contexts, entitlements, metering…)
--
--   registry       defines or precedes the boundary. Reachable unscoped, because provisioning
--                  necessarily runs before the tenant it is creating exists. Within a tenant
--                  scope, restricted to what that tenant is already entitled to know.
--                  (tenants, principals)
--
--   infrastructure not data. Readable unscoped only. (schema_migrations)
--
-- =============================================================================
-- Reads
-- =============================================================================
-- A tenant sees its own row, and nothing else on the deployment.
--
-- The alternative was to show a tenant session nothing at all, which is simpler and would also
-- have closed the finding, since no code reads these tables under a tenant scope today. It is
-- rejected because of where it pushes future callers. A satellite product that wants to display
-- its own tenant's name would have to reach for `system_session` to get it — and a codebase
-- where ordinary reads are done from the unscoped path is one bug away from a much larger
-- disclosure than the one being fixed here. The narrow read is the safe habit to make available.

CREATE POLICY tenants_read ON tenants
    FOR SELECT
    USING (
        NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL
        OR id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
    );

-- A tenant sees the principals it already has a membership relationship with — the people it
-- invited — and no others. The subquery is itself subject to the `memberships` policy, so it
-- is filtered to the current tenant before this predicate ever applies; the explicit
-- `m.tenant_id = ...` is redundant today and stated anyway, so that a future change to the
-- memberships policy cannot silently widen this one.
--
-- No recursion: the memberships policy references `current_setting` only, never `principals`.

CREATE POLICY principals_read ON principals
    FOR SELECT
    USING (
        NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL
        OR EXISTS (
            SELECT 1 FROM memberships m
            WHERE m.principal_id = principals.id
              AND m.tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
    );

CREATE POLICY schema_migrations_read ON schema_migrations
    FOR SELECT
    USING (NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL);

-- =============================================================================
-- Writes
-- =============================================================================
-- Every write to the registry is unscoped-only. Reads and writes are separate policies rather
-- than one `FOR ALL`, and that split is the security-critical half of this migration.
--
-- `FOR ALL` with a single `USING` reuses that expression as the `WITH CHECK`. Written that way,
-- a tenant permitted to read its own row would also have been permitted to UPDATE it — and the
-- `status` column on `tenants` is the column that carries 'suspended' and 'terminated'. A
-- suspended tenant could have set itself back to 'active'. Closing a disclosure by opening a
-- privilege escalation is not a fix.

CREATE POLICY tenants_provision ON tenants
    FOR INSERT
    WITH CHECK (NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL);

CREATE POLICY tenants_administer ON tenants
    FOR UPDATE
    USING (NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL)
    WITH CHECK (NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL);

CREATE POLICY principals_provision ON principals
    FOR INSERT
    WITH CHECK (NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL);

CREATE POLICY principals_administer ON principals
    FOR UPDATE
    USING (NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL)
    WITH CHECK (NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL);

CREATE POLICY schema_migrations_write ON schema_migrations
    FOR ALL
    USING (NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL)
    WITH CHECK (NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL);

-- No DELETE policy on `tenants` or `principals`, so the application role cannot delete a
-- registry row through any session. Nothing in the kernel deletes one — the status vocabulary
-- carries 'terminated' and 'purged' precisely so that the row survives the relationship. A
-- deployment that needs erasure for a data-protection request performs it administratively,
-- where it is a deliberate act with a superuser behind it rather than a reachable code path.

ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenants FORCE ROW LEVEL SECURITY;
ALTER TABLE principals ENABLE ROW LEVEL SECURITY;
ALTER TABLE principals FORCE ROW LEVEL SECURITY;
ALTER TABLE schema_migrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE schema_migrations FORCE ROW LEVEL SECURITY;

-- FORCE matters as much as ENABLE here and for the usual reason: without it the table owner
-- bypasses every policy above, and the kernel connects as the owner in development, so the
-- whole migration would be inert in exactly the environment where it is tested.

-- =============================================================================
-- What this does not close
-- =============================================================================
-- 1. The unscoped path itself. `system_session` still sees the entire registry, and it is
--    reachable from request handling — `PrincipalRepository.create` and `TenantRepository.get`
--    are called from API handlers. What constrains those is the repository surface, which
--    takes an identifier and returns one row; it is not the database. This migration stops
--    tenant-scoped code from wandering into the registry, which is what was measured. It does
--    not turn the unscoped path into a safe one.
--
-- 2. Constraint-check disclosure. PostgreSQL evaluates referential-integrity and uniqueness
--    checks with row security bypassed, by design, so that a policy cannot be used to corrupt
--    data. The consequence is a covert channel: a failed insert can reveal that a row exists
--    which the caller cannot see. `principals.email` is UNIQUE, so this is an email-existence
--    oracle at the database layer. It is not reachable from a tenant session here, because
--    every write policy above is unscoped-only and an unscoped caller can read the row anyway.
--    Its API-level counterpart is a separate finding and stays open.
