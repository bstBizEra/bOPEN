-- Migration: 020_location_foundation.sql
-- Description: Location foundation (BOPEN-LOC-001) — a tenant-scoped Location Registry that separates a
--              stable, immutable place identity from its versioned addresses, its point geometry
--              observations (each an explicit candidate that must be ACCEPTED, never auto-accepted from
--              an HTTP 200), its external identifiers, and a bounded `contains` relationship. Every
--              child is same-tenant at the database by a composite foreign key to its parent's
--              (tenant_id, id); every table is isolated by forced row-level security; the history table
--              is append-only.
-- Version: 1.0.0
-- Work package: BOPEN-LOC-001 (MILE-4.2 Location foundation)
-- Governing artifacts: DEC-P4-ENTRY §11 (+ LOC-D resolutions); RESEARCH-MILE-4.2-LOCATION §§5,7,12;
--                      AGENTS.md §8; BOPEN-TENANT-001; BOPEN-GOV-EBIV-001
-- Rollback: 020_location_foundation.down.sql
--
-- Load-bearing decisions this migration encodes (each a lesson of the built foundations):
--
--   Same-tenant integrity (mirrors party_relationships / party_contact_points). Every child references
--   its parent BY (tenant_id, parent_id) → parent(tenant_id, id), so a child attached to another
--   tenant's location is impossible at the database, not merely in application logic. Each parent
--   therefore declares UNIQUE (tenant_id, id).
--
--   Durable referents are ON DELETE RESTRICT, not CASCADE (LOC-D-12 + the migration-014 lesson). A
--   location that owns any address version, geometry observation, external identifier, relationship, or
--   history row cannot be deleted — retire it (lifecycle_state='retired') instead. This closes, in
--   advance, the cascade path that erased append-only workflow_history in migration 014: deleting a
--   location (or, through the tenant cascade, a whole tenant) that carries append-only history is
--   refused rather than silently erasing the evidence.
--
--   Coordinate validity is a database keystone (LOC-INV-04). chk_geo_lon / chk_geo_lat pin longitude to
--   [-180,180] and latitude to [-90,90]; because PostgreSQL orders NUMERIC 'NaN' above every number, a
--   NaN also fails the upper bound and is refused. The repository re-checks NaN/∞/range before insert
--   as belt-and-braces, but the constraint holds whatever SQL is issued.

-- 1. locations — a stable, immutable, tenant-owned identity for a named place/site. Identity is never
-- derived from an address, coordinate, or provider id; a lifecycle change keeps the same id (LOC-INV-03).
CREATE TABLE IF NOT EXISTS locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    code VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    location_type VARCHAR(32) NOT NULL,
    lifecycle_state VARCHAR(16) NOT NULL DEFAULT 'proposed',
    -- Soft references (no FK): they point into child tables that point back by composite FK, so a hard
    -- FK either way would create a chicken-and-egg cycle. The repository keeps them consistent.
    current_address_version_id UUID,
    current_geometry_observation_id UUID,
    revision INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Small governed versioned vocabularies via CHECK (LOC-D-02), not arbitrary strings.
    CONSTRAINT chk_location_type CHECK (
        location_type IN ('site', 'building', 'depot', 'office', 'warehouse', 'other')
    ),
    CONSTRAINT chk_location_lifecycle CHECK (
        lifecycle_state IN ('proposed', 'active', 'inactive', 'retired')
    ),
    -- (tenant_id, id) unique so children can reference a location BY TENANT.
    CONSTRAINT unq_location_tenant_id UNIQUE (tenant_id, id),
    -- Tenant-scoped unique code.
    CONSTRAINT unq_location_code UNIQUE (tenant_id, code)
);

ALTER TABLE locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE locations FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_locations ON locations
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- 2. location_address_versions — an effective-dated postal/civic description. Original input is
-- preserved separately from the normalized components and the rendered form (LOC-D-03). At most one
-- CURRENT version per location is enforced by a partial unique index (LOC-INV-07).
CREATE TABLE IF NOT EXISTS location_address_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    location_id UUID NOT NULL,
    version_number INT NOT NULL,
    country_code CHAR(2) NOT NULL,
    -- Owned structured components (ISO 19160-1 / UPU S42 informed) plus a JSONB escape for country
    -- variation. Every explicit component is nullable; a place may have no postal address.
    premise VARCHAR(255),
    thoroughfare VARCHAR(255),
    locality VARCHAR(255),
    admin_area VARCHAR(255),
    postal_code VARCHAR(32),
    recipient VARCHAR(255),
    components JSONB,
    original_input TEXT NOT NULL,
    rendered TEXT,
    language_tag VARCHAR(32),
    script_tag VARCHAR(32),
    template_profile VARCHAR(64),
    verification_state VARCHAR(16) NOT NULL DEFAULT 'unverified',
    confidence NUMERIC,
    effective_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    effective_to TIMESTAMPTZ,
    revision INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_addr_verification_state CHECK (
        verification_state IN ('unverified', 'verified', 'failed')
    ),
    CONSTRAINT unq_addr_tenant_id UNIQUE (tenant_id, id),
    -- Same-tenant, durable-referent integrity: ON DELETE RESTRICT (LOC-D-12). A location with an
    -- address version cannot be deleted.
    CONSTRAINT fk_addr_location FOREIGN KEY (tenant_id, location_id)
        REFERENCES locations(tenant_id, id) ON DELETE RESTRICT
);

ALTER TABLE location_address_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE location_address_versions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_location_address_versions ON location_address_versions
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- At most one CURRENT (effective_to IS NULL) address version per location — LOC-INV-07.
CREATE UNIQUE INDEX unq_addr_current
    ON location_address_versions (tenant_id, location_id)
    WHERE effective_to IS NULL;

-- 3. location_geometry_observations — a point plus CRS, accuracy, provenance, and an acceptance state.
-- No observation is accepted on creation; acceptance is a distinct authorized action (LOC-INV-06).
CREATE TABLE IF NOT EXISTS location_geometry_observations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    location_id UUID NOT NULL,
    -- Exact decimal longitude/latitude, never float (LOC-D-04). NUMERIC(9,6) round-trips to the metre.
    longitude NUMERIC(9,6) NOT NULL,
    latitude NUMERIC(9,6) NOT NULL,
    crs VARCHAR(32) NOT NULL DEFAULT 'OGC:CRS84',
    -- Accuracy radius carried as a UOM length Quantity (m/km, exact Decimal), validated in the repo and
    -- recorded separately from the coordinate's numeric precision (LOC-D-04).
    accuracy_radius_value NUMERIC(38,18),
    accuracy_radius_unit VARCHAR(64),
    capture_method VARCHAR(64),
    source VARCHAR(255),
    confidence NUMERIC,
    observed_at TIMESTAMPTZ,
    received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acceptance_state VARCHAR(16) NOT NULL DEFAULT 'candidate',
    accepted_by VARCHAR(64),
    rejected_reason VARCHAR(255),
    revision INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_geo_crs CHECK (crs = 'OGC:CRS84'),
    CONSTRAINT chk_geo_acceptance_state CHECK (
        acceptance_state IN ('received', 'candidate', 'accepted', 'rejected', 'superseded')
    ),
    -- The coordinate-validity keystone (LOC-INV-04). BETWEEN also rejects NaN, which PostgreSQL orders
    -- above all numbers, so a NaN fails the upper bound.
    CONSTRAINT chk_geo_lon CHECK (longitude BETWEEN -180 AND 180),
    CONSTRAINT chk_geo_lat CHECK (latitude BETWEEN -90 AND 90),
    CONSTRAINT unq_geo_tenant_id UNIQUE (tenant_id, id),
    CONSTRAINT fk_geo_location FOREIGN KEY (tenant_id, location_id)
        REFERENCES locations(tenant_id, id) ON DELETE RESTRICT
);

ALTER TABLE location_geometry_observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE location_geometry_observations FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_location_geometry_observations ON location_geometry_observations
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- 4. location_external_identifiers — a scheme/value reference issued by a provider or external
-- registry. A live (effective_to IS NULL) scheme/value collision within a tenant is refused (LOC-INV-08).
CREATE TABLE IF NOT EXISTS location_external_identifiers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    location_id UUID NOT NULL,
    scheme VARCHAR(64) NOT NULL,
    value VARCHAR(255) NOT NULL,
    issuer VARCHAR(255),
    effective_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    effective_to TIMESTAMPTZ,
    is_primary BOOLEAN NOT NULL DEFAULT false,
    provenance VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_extid_location FOREIGN KEY (tenant_id, location_id)
        REFERENCES locations(tenant_id, id) ON DELETE RESTRICT
);

ALTER TABLE location_external_identifiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE location_external_identifiers FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_location_external_identifiers ON location_external_identifiers
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- One live (scheme, value) per tenant — LOC-INV-08.
CREATE UNIQUE INDEX unq_extid_live
    ON location_external_identifiers (tenant_id, scheme, value)
    WHERE effective_to IS NULL;

-- 5. location_relationships — a typed, effective-dated `contains` edge between two same-tenant
-- locations. Self-links, cross-tenant targets, duplicate live edges, and second live parents are
-- refused here; a containment CYCLE is refused in the repository by a WITH RECURSIVE walk (a row CHECK
-- cannot see a cycle) — LOC-INV-09, LOC-D-05.
CREATE TABLE IF NOT EXISTS location_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    from_location_id UUID NOT NULL,
    to_location_id UUID NOT NULL,
    relationship_type VARCHAR(32) NOT NULL DEFAULT 'contains',
    effective_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    effective_to TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_rel_type CHECK (relationship_type = 'contains'),
    -- A location cannot contain itself (LOC-INV-09).
    CONSTRAINT chk_rel_no_self CHECK (from_location_id <> to_location_id),
    -- Both endpoints must be locations of THIS tenant; ON DELETE RESTRICT so a related location cannot
    -- be deleted out from under the edge.
    CONSTRAINT fk_rel_from FOREIGN KEY (tenant_id, from_location_id)
        REFERENCES locations(tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_rel_to FOREIGN KEY (tenant_id, to_location_id)
        REFERENCES locations(tenant_id, id) ON DELETE RESTRICT
);

ALTER TABLE location_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE location_relationships FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_location_relationships ON location_relationships
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- No duplicate live edge — LOC-INV-09.
CREATE UNIQUE INDEX unq_rel_live_edge
    ON location_relationships (tenant_id, from_location_id, to_location_id, relationship_type)
    WHERE effective_to IS NULL;

-- One active parent per child in a hierarchy — LOC-D-05. A second live `contains` edge INTO the same
-- child is refused.
CREATE UNIQUE INDEX unq_rel_one_active_parent
    ON location_relationships (tenant_id, to_location_id, relationship_type)
    WHERE effective_to IS NULL;

-- 6. location_history — append-only record of every material mutation. detail carries SAFE metadata
-- only (never precise coordinates — LOC-INV-14). SELECT and INSERT policies only, and ON DELETE
-- RESTRICT to its location, so a recorded event survives both direct mutation and a parent cascade —
-- the migration-014 discipline applied in advance (LOC-INV-12).
CREATE TABLE IF NOT EXISTS location_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    location_id UUID NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    detail JSONB,
    at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_history_location FOREIGN KEY (tenant_id, location_id)
        REFERENCES locations(tenant_id, id) ON DELETE RESTRICT
);

ALTER TABLE location_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE location_history FORCE ROW LEVEL SECURITY;
-- Read and insert only — no UPDATE or DELETE policy, so a recorded event is append-only the way the
-- audit trail and workflow_history are.
CREATE POLICY location_history_read ON location_history
    FOR SELECT
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
CREATE POLICY location_history_insert ON location_history
    FOR INSERT
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
