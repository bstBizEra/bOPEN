-- Atlas generated plan fixture
ALTER TABLE "public"."projects" ADD COLUMN "description" text NULL;
CREATE INDEX "idx_projects_tenant" ON "public"."projects" ("tenant_id");
