-- Rollback for 011_tenant_placement.sql.

ALTER TABLE tenants DROP CONSTRAINT IF EXISTS chk_tenant_placement_ref;
ALTER TABLE tenants DROP CONSTRAINT IF EXISTS chk_tenant_placement_kind;
ALTER TABLE tenants DROP COLUMN IF EXISTS placement_ref;
ALTER TABLE tenants DROP COLUMN IF EXISTS placement_kind;
