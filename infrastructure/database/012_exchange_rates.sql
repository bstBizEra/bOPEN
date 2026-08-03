-- bOPEN MILE-4.2 — Money & Currency: tenant exchange rates.
-- Governed by DEC-P4-ENTRY (MILE-4.2), AGENTS.md section 8, BOPEN-TENANT-001.
--
-- A tenant sets the exchange rate it uses to convert between currencies (its booking rate). Rates
-- are tenant-scoped by row-level security — one tenant's rates are private to it, isolated the same
-- way its parties and resources are. The rate is NUMERIC (exact decimal), never a float, matching
-- the money value type's integer-minor-units discipline; conversion arithmetic stays exact.

CREATE TABLE IF NOT EXISTS exchange_rates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    from_currency VARCHAR(3) NOT NULL,
    to_currency VARCHAR(3) NOT NULL,
    rate NUMERIC(24, 10) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_rate_positive CHECK (rate > 0),
    CONSTRAINT chk_currencies_differ CHECK (from_currency <> to_currency),
    CONSTRAINT unq_tenant_currency_pair UNIQUE (tenant_id, from_currency, to_currency)
);

ALTER TABLE exchange_rates ENABLE ROW LEVEL SECURITY;
ALTER TABLE exchange_rates FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_exchange_rates ON exchange_rates
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
