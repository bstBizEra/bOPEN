-- bOPEN MILE-4.2 — Workflow State Engine (authorized DEC-P4-ENTRY §8).
-- Governed by DEC-P4-ENTRY, AGENTS.md section 8, BOPEN-TENANT-001.
--
-- A generic, tenant-scoped state machine for business processes: a definition names the states and
-- the transitions allowed between them; an instance carries a current state for one subject; and a
-- transition moves an instance from one state to another ONLY along an edge the definition allows.
-- History is append-only, the same discipline as the audit trail. All three tables are isolated by
-- row-level security. Used by every satellite product (CAPABILITY-MATRIX).

-- 1. Definitions — the state machine specification.
CREATE TABLE IF NOT EXISTS workflow_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    initial_state VARCHAR(64) NOT NULL,
    states JSONB NOT NULL,        -- e.g. ["draft","submitted","approved","rejected"]
    transitions JSONB NOT NULL,   -- e.g. [["draft","submitted"],["submitted","approved"]]
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- (tenant_id, id) unique so an instance can reference a definition BY TENANT.
    CONSTRAINT unq_wf_def_tenant_id UNIQUE (tenant_id, id)
);
ALTER TABLE workflow_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_definitions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_workflow_definitions ON workflow_definitions
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- 2. Instances — one running process, carrying a current state for a subject.
CREATE TABLE IF NOT EXISTS workflow_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    definition_id UUID NOT NULL,
    current_state VARCHAR(64) NOT NULL,
    subject_ref VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- The composite FK makes an instance of another tenant's definition impossible at the database.
    CONSTRAINT fk_wf_definition FOREIGN KEY (tenant_id, definition_id)
        REFERENCES workflow_definitions(tenant_id, id) ON DELETE CASCADE,
    CONSTRAINT unq_wf_instance_tenant_id UNIQUE (tenant_id, id)
);
ALTER TABLE workflow_instances ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_instances FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_workflow_instances ON workflow_instances
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- 3. History — append-only record of every transition.
CREATE TABLE IF NOT EXISTS workflow_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    instance_id UUID NOT NULL,
    from_state VARCHAR(64) NOT NULL,
    to_state VARCHAR(64) NOT NULL,
    actor_principal_id VARCHAR(64),
    at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_wf_instance FOREIGN KEY (tenant_id, instance_id)
        REFERENCES workflow_instances(tenant_id, id) ON DELETE CASCADE
);
ALTER TABLE workflow_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_history FORCE ROW LEVEL SECURITY;
-- Read and insert only — no UPDATE or DELETE policy, so history is append-only the way the audit
-- trail is: a recorded transition cannot be altered or erased through any tenant session.
CREATE POLICY workflow_history_read ON workflow_history
    FOR SELECT
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
CREATE POLICY workflow_history_insert ON workflow_history
    FOR INSERT
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
