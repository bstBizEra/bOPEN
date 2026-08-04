-- Rollback for 017_tenant_placement_state.sql.

ALTER TABLE tenants DROP CONSTRAINT IF EXISTS chk_tenant_placement_state;
ALTER TABLE tenants DROP COLUMN IF EXISTS placement_state;
