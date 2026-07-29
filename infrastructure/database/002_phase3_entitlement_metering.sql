-- Migration: 002_phase3_entitlement_metering.sql
-- Description: Phase 3 Commercial Entitlement, Usage Metering & Transactional Outbox Baseline
-- Version: 1.0.0

-- 1. Tenant Entitlement Plans Table
CREATE TABLE IF NOT EXISTS tenant_entitlement_plans (
    tenant_id VARCHAR(64) PRIMARY KEY,
    plan_id VARCHAR(64) NOT NULL DEFAULT 'plan_free',
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tenant Entitlement Overrides Table
CREATE TABLE IF NOT EXISTS tenant_entitlement_overrides (
    override_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    capability_id VARCHAR(64) NOT NULL,
    rule_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_tenant_capability_override UNIQUE (tenant_id, capability_id)
);

-- 3. Usage Meter Balances Table
CREATE TABLE IF NOT EXISTS usage_meter_balances (
    balance_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    capability_id VARCHAR(64) NOT NULL,
    used_quantity BIGINT NOT NULL DEFAULT 0,
    quota_limit BIGINT NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_tenant_capability_window UNIQUE (tenant_id, capability_id, window_start)
);

-- 4. Transactional Usage Outbox Table
CREATE TABLE IF NOT EXISTS usage_outbox (
    outbox_id VARCHAR(64) PRIMARY KEY,
    event_id VARCHAR(64) UNIQUE NOT NULL,
    tenant_id VARCHAR(64) NOT NULL,
    principal_id VARCHAR(64) NOT NULL,
    capability_id VARCHAR(64) NOT NULL,
    quantity INT NOT NULL,
    unit VARCHAR(32) NOT NULL,
    correlation_id VARCHAR(64) NOT NULL,
    idempotency_key VARCHAR(128) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dispatched_at TIMESTAMPTZ NULL
);

-- Row-Level Security (RLS) Policies for Tenant Isolation
ALTER TABLE tenant_entitlement_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_entitlement_overrides ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_meter_balances ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_outbox ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_entitlement_plans_isolation ON tenant_entitlement_plans
    USING (tenant_id = current_setting('app.current_tenant_id', true));

CREATE POLICY tenant_entitlement_overrides_isolation ON tenant_entitlement_overrides
    USING (tenant_id = current_setting('app.current_tenant_id', true));

CREATE POLICY usage_meter_balances_isolation ON usage_meter_balances
    USING (tenant_id = current_setting('app.current_tenant_id', true));

CREATE POLICY usage_outbox_isolation ON usage_outbox
    USING (tenant_id = current_setting('app.current_tenant_id', true));
