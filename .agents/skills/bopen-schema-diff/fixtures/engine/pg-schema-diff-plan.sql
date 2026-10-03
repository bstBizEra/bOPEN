-- pg-schema-diff generated plan fixture
ALTER TABLE public.projects ADD COLUMN description text;
CREATE INDEX CONCURRENTLY idx_projects_tenant ON public.projects (tenant_id);
