-- bOPEN Multi-Tenant PostgreSQL Database Isolation DDL Baseline v1.0
-- Governed by AGENTS.md Section 8 & BOPEN-TENANT-001

-- 1. Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Tenants Table
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_tenant_status CHECK (status IN ('draft', 'pending_verification', 'approved', 'provisioning', 'active', 'restricted', 'suspended', 'cancellation_pending', 'terminated', 'retention', 'purged'))
);

-- 3. Principals Table
CREATE TABLE IF NOT EXISTS principals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(50) NOT NULL DEFAULT 'human',
    email VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_principal_type CHECK (type IN ('human', 'service', 'application', 'device', 'agent'))
);

-- 4. Tenant-Scoped Memberships Table
CREATE TABLE IF NOT EXISTS memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    principal_id UUID NOT NULL REFERENCES principals(id) ON DELETE CASCADE,
    state VARCHAR(50) NOT NULL DEFAULT 'invited',
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unq_tenant_principal UNIQUE (tenant_id, principal_id),
    CONSTRAINT chk_membership_state CHECK (state IN ('invited', 'active', 'suspended', 'declined', 'expired', 'revoked', 'left', 'removed'))
);

-- Enable RLS on Memberships
ALTER TABLE memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE memberships FORCE ROW LEVEL SECURITY;

-- Create Tenant Isolation Policy on Memberships
CREATE POLICY tenant_isolation_memberships ON memberships
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- 5. Tenant-Scoped Data Domain Resource Example
CREATE TABLE IF NOT EXISTS tenant_resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    resource_name VARCHAR(255) NOT NULL,
    payload JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Enable RLS on Tenant Resources
ALTER TABLE tenant_resources ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_resources FORCE ROW LEVEL SECURITY;

-- Create Strict RLS Policy on Tenant Resources
CREATE POLICY tenant_isolation_resources ON tenant_resources
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
