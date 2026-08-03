-- bOPEN MILE-4.1 — Party & Relationship Foundation (BOPEN-PARTY-001)
-- Governed by DEC-P4-ENTRY, AGENTS.md Section 8, BOPEN-TENANT-001.
--
-- A party is a business entity (person or organization) owned by a tenant — distinct from a
-- principal, which is an authentication identity. Party data is tenant-scoped by row-level security
-- from this first migration, the same mechanism that isolates tenant_resources; it is never global.

-- 1. Parties
CREATE TABLE IF NOT EXISTS parties (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    party_type VARCHAR(50) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_party_type CHECK (party_type IN ('person', 'organization')),
    CONSTRAINT chk_party_status CHECK (status IN ('active', 'archived')),
    -- (tenant_id, id) is unique because id is unique; declaring it lets a relationship reference a
    -- party BY TENANT, so the database refuses a relationship whose party lives in another tenant.
    CONSTRAINT unq_party_tenant_id UNIQUE (tenant_id, id)
);

ALTER TABLE parties ENABLE ROW LEVEL SECURITY;
ALTER TABLE parties FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_parties ON parties
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- 2. Party relationships — a typed, directed edge between two parties IN THE SAME TENANT.
CREATE TABLE IF NOT EXISTS party_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    from_party_id UUID NOT NULL,
    to_party_id UUID NOT NULL,
    relationship_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_relationship_type CHECK (relationship_type IN ('employs', 'supplies', 'bills', 'owns', 'member_of')),
    -- A party cannot relate to itself.
    CONSTRAINT chk_no_self_relationship CHECK (from_party_id <> to_party_id),
    CONSTRAINT unq_relationship UNIQUE (tenant_id, from_party_id, to_party_id, relationship_type),
    -- Both endpoints must be parties of THIS tenant. The composite foreign key to (tenant_id, id)
    -- is what makes a cross-tenant relationship impossible at the database, not application logic.
    CONSTRAINT fk_from_party FOREIGN KEY (tenant_id, from_party_id)
        REFERENCES parties(tenant_id, id) ON DELETE CASCADE,
    CONSTRAINT fk_to_party FOREIGN KEY (tenant_id, to_party_id)
        REFERENCES parties(tenant_id, id) ON DELETE CASCADE
);

ALTER TABLE party_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE party_relationships FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_party_relationships ON party_relationships
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
