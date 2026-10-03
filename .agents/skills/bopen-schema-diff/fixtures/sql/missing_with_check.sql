CREATE TABLE workspace_items (
 id uuid PRIMARY KEY,
 tenant_id uuid NOT NULL REFERENCES tenants(id),
 code text NOT NULL,
 UNIQUE (tenant_id, code)
);
ALTER TABLE workspace_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_items FORCE ROW LEVEL SECURITY;
CREATE POLICY item_policy ON workspace_items USING (tenant_id = current_setting('app.tenant_id')::uuid);
