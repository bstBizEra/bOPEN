-- Rollback for 012_exchange_rates.sql.

DROP POLICY IF EXISTS tenant_isolation_exchange_rates ON exchange_rates;
DROP TABLE IF EXISTS exchange_rates;
