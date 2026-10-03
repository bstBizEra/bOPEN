CREATE TABLE project_tasks (
  id uuid PRIMARY KEY,
  tenant_id uuid REFERENCES tenants(id),
  code text NOT NULL,
  UNIQUE (tenant_id, code)
);
ALTER TABLE project_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_tasks FORCE ROW LEVEL SECURITY;
CREATE POLICY tasks_policy ON project_tasks
USING (tenant_id = current_setting('app.tenant_id')::uuid)
WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);
