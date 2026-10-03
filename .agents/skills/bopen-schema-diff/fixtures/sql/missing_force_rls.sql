CREATE TABLE project_memberships (
 id uuid PRIMARY KEY,
 tenant_id uuid NOT NULL REFERENCES tenants(id),
 code text NOT NULL,
 UNIQUE (tenant_id, code)
);
ALTER TABLE project_memberships ENABLE ROW LEVEL SECURITY;
CREATE POLICY pm_policy ON project_memberships USING (tenant_id = current_setting('app.tenant_id')::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);
