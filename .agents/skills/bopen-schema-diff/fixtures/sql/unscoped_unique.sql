CREATE TABLE tenant_documents (
 id uuid PRIMARY KEY,
 tenant_id uuid NOT NULL REFERENCES tenants(id),
 external_id text NOT NULL,
 UNIQUE (external_id)
);
ALTER TABLE tenant_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_documents FORCE ROW LEVEL SECURITY;
CREATE POLICY doc_policy ON tenant_documents USING (tenant_id = current_setting('app.tenant_id')::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);
