-- bOPEN WP-P35-06 (placement seam) — DEC-P35-TENANCY-MODEL Option D (hybrid placement).
-- Governed by DEC-P35-TENANCY-MODEL §8, AGENTS.md §8 (approved physical isolation).
--
-- Records WHERE each tenant's data lives, so the kernel resolves a tenant to the right database
-- rather than assuming one shared instance. Placement is a column on the tenant registry row, not a
-- separate table: the tenant registry is the natural authority for it, and every existing tenant is
-- backfilled to the shared pool by the column default with no data migration.
--
-- Default is the shared RLS pool. A paying/production tenant is moved to 'dedicated' with a
-- placement_ref that names its database; the constraint below refuses a dedicated placement with no
-- ref, so a tenant can never be marked dedicated without saying where.

ALTER TABLE tenants ADD COLUMN placement_kind VARCHAR(50) NOT NULL DEFAULT 'shared_pool';
ALTER TABLE tenants ADD COLUMN placement_ref VARCHAR(255);

ALTER TABLE tenants
    ADD CONSTRAINT chk_tenant_placement_kind CHECK (placement_kind IN ('shared_pool', 'dedicated'));

-- A dedicated placement must name where it lives; a shared placement must not carry a stale ref.
ALTER TABLE tenants
    ADD CONSTRAINT chk_tenant_placement_ref CHECK (
        (placement_kind = 'shared_pool' AND placement_ref IS NULL)
        OR (placement_kind = 'dedicated' AND placement_ref IS NOT NULL)
    );
