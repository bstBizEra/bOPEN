-- Migration: 019_party_contact_points.sql
-- Description: Party ContactPoint extension (BOPEN-PARTY-002) — the tenant-scoped, Party-owned registry
--              of typed, purpose-classified, verifiable communication endpoints that a future
--              NotificationRecipientResolver resolves a business recipient against, so a send never
--              falls back to principals.email. A contact point is attached to a Party of THIS tenant by
--              the same composite-foreign-key discipline that makes party_relationships same-tenant at
--              the database. Verification is state plus a seam here — the ceremony is deferred.
-- Version: 1.0.0
-- Work package: BOPEN-PARTY-002 (MILE-4.2 Party ContactPoint extension)
-- Governing artifacts: DEC-P4-ENTRY §10; RESEARCH-MILE-4.2-PARTY-CONTACTPOINT §§7,8,12; AGENTS.md §8;
--                      BOPEN-TENANT-001; BOPEN-GOV-EBIV-001
-- Rollback: 019_party_contact_points.down.sql
--
-- Two decisions this migration encodes, both load-bearing lessons of the built foundations:
--
--   CP-D-03 / the migration-014 lesson. Deleting a Party with contact points, or a contact point with
--   verification events, is REFUSED (ON DELETE RESTRICT), not cascaded. A cascade with row security
--   bypassed is exactly how migration 014 erased append-only workflow_history; that carve-out is
--   closed here in advance so a Party deletion can never silently erase its contact-point verification
--   evidence. Retire (effective_to / a retired state), do not delete.
--
--   CP-D-04 / one live primary per (party, type). A partial unique index enforces at most one primary
--   contact point per (tenant, party, endpoint_type) while it is live (is_primary = true).

-- 1. Contact points — a Party-owned, tenant-scoped, typed, purpose-classified, verifiable endpoint.
CREATE TABLE IF NOT EXISTS party_contact_points (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    party_id UUID NOT NULL,
    endpoint_type VARCHAR(32) NOT NULL,
    -- Sensitive tenant business data (CP-INV-06): redacted from logs, events and default status.
    endpoint_value VARCHAR(320) NOT NULL,
    purpose VARCHAR(32) NOT NULL,
    -- unverified is the only safe default: until the verification seam transitions it, the resolver
    -- refuses every endpoint (CP-INV-04). failed is DISTINCT from unverified — a prior verification
    -- was invalidated — and neither is ever treated as verified.
    verification_state VARCHAR(16) NOT NULL DEFAULT 'unverified',
    verification_method VARCHAR(64),
    verified_at TIMESTAMPTZ,
    effective_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    effective_to TIMESTAMPTZ,
    is_primary BOOLEAN NOT NULL DEFAULT false,
    provenance VARCHAR(64),
    revision INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Small governed versioned vocabularies (CP-INV-11): an arbitrary string is refused by CHECK.
    CONSTRAINT chk_cp_endpoint_type CHECK (endpoint_type IN ('email', 'phone')),
    CONSTRAINT chk_cp_purpose CHECK (
        purpose IN ('security_operational', 'transactional', 'billing', 'general')
    ),
    CONSTRAINT chk_cp_verification_state CHECK (
        verification_state IN ('unverified', 'verified', 'failed')
    ),
    -- (tenant_id, id) unique so the verification-events table can reference a contact point BY TENANT.
    CONSTRAINT unq_cp_tenant_id UNIQUE (tenant_id, id),
    -- The same endpoint is not recorded twice for one Party (CP-INV-08).
    CONSTRAINT unq_cp_party_endpoint UNIQUE (tenant_id, party_id, endpoint_type, endpoint_value),
    -- Same-tenant integrity at the database, mirroring party_relationships (CP-INV-02). ON DELETE
    -- RESTRICT (CP-D-03): a Party with contact points cannot be deleted — retire it instead. Relies on
    -- the existing unq_party_tenant_id UNIQUE (tenant_id, id) on parties.
    CONSTRAINT fk_cp_party FOREIGN KEY (tenant_id, party_id)
        REFERENCES parties(tenant_id, id) ON DELETE RESTRICT
);

ALTER TABLE party_contact_points ENABLE ROW LEVEL SECURITY;
ALTER TABLE party_contact_points FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_party_contact_points ON party_contact_points
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- One live primary endpoint per (party, type) — CP-INV-08 / CP-D-04. A partial unique index over the
-- rows where is_primary is true; a second primary of the same (tenant, party, type) is refused.
CREATE UNIQUE INDEX unq_cp_primary
    ON party_contact_points (tenant_id, party_id, endpoint_type)
    WHERE is_primary;

-- 2. Verification events — append-only history of every verification-state transition. The
-- migration-014 lesson applied in advance: it survives BOTH direct UPDATE/DELETE (no such policy for
-- the application role) AND a parent cascade (ON DELETE RESTRICT), so deleting a Party or a contact
-- point that carries verification history is refused rather than silently erasing the evidence.
CREATE TABLE IF NOT EXISTS party_contact_point_verification_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    contact_point_id UUID NOT NULL,
    from_state VARCHAR(16),
    to_state VARCHAR(16) NOT NULL,
    method VARCHAR(64) NOT NULL,
    actor_principal_id VARCHAR(64),
    at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- ON DELETE RESTRICT, not CASCADE: a contact point that has recorded a verification event cannot be
    -- deleted out from under its append-only history (CP-INV-07). The composite FK also makes a
    -- cross-tenant event impossible at the database.
    CONSTRAINT fk_cpve_cp FOREIGN KEY (tenant_id, contact_point_id)
        REFERENCES party_contact_points(tenant_id, id) ON DELETE RESTRICT
);

ALTER TABLE party_contact_point_verification_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE party_contact_point_verification_events FORCE ROW LEVEL SECURITY;
-- Read and insert only — no UPDATE or DELETE policy, so a recorded verification transition is
-- append-only the way the audit trail and workflow_history are.
CREATE POLICY party_cp_verification_events_read ON party_contact_point_verification_events
    FOR SELECT
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
CREATE POLICY party_cp_verification_events_insert ON party_contact_point_verification_events
    FOR INSERT
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
