-- Rollback for 018_uom_custom_units.sql.

DROP POLICY IF EXISTS tenant_isolation_uom_custom_units ON uom_custom_units;
DROP TABLE IF EXISTS uom_custom_units;
