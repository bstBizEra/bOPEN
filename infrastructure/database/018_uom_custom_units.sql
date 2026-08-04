-- Migration: 018_uom_custom_units.sql
-- Description: Tenant custom units of measure — the tenant-scoped half of the UOM foundation. Standard
--              units (SI + common + Thai land units) are a code constant in platform_kernel/uom.py;
--              this table holds units a tenant defines for itself (e.g. "pallet" = 48 each), isolated
--              by row-level security exactly as exchange_rates is.
-- Version: 1.0.0
-- Work package: BOPEN-P35-001 (MILE-4.2 UOM)
-- Governing artifacts: DEC-P4-ENTRY §9; RESEARCH-MILE-4.2-UOM §6; AGENTS.md §8; BOPEN-TENANT-001
--
-- A custom unit belongs to one of the multiplicative dimensions and carries an exact factor to that
-- dimension's base unit, so it converts through the same base as the standard units. Full CRUD is
-- supported by a FOR ALL policy under the tenant's own scope. Temperature is excluded: it is affine
-- (needs an offset, not a factor) and refused in this slice.

CREATE TABLE IF NOT EXISTS uom_custom_units (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    unit_code VARCHAR(64) NOT NULL,
    dimension VARCHAR(32) NOT NULL,
    -- Exact factor to the dimension's base unit. NUMERIC (not float) so the value never drifts.
    factor_to_base NUMERIC(38, 18) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unq_uom_custom_unit UNIQUE (tenant_id, unit_code),
    -- A factor must be positive; a zero or negative factor is a nonsensical unit.
    CONSTRAINT chk_uom_factor_positive CHECK (factor_to_base > 0),
    -- Multiplicative dimensions only. Temperature (affine) is deliberately excluded in this slice.
    CONSTRAINT chk_uom_dimension CHECK (dimension IN ('mass', 'length', 'area', 'volume', 'time', 'count'))
);

ALTER TABLE uom_custom_units ENABLE ROW LEVEL SECURITY;
ALTER TABLE uom_custom_units FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_uom_custom_units ON uom_custom_units
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
