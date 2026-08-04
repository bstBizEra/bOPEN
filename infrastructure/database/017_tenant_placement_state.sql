-- Migration: 017_tenant_placement_state.sql
-- Description: A tenant's placement state — stable, or migrating between databases. The kernel
--              refuses a migrating tenant's requests (the freeze) so a trial->paid migration can copy
--              its data without a concurrent write landing in the source database after the snapshot.
-- Version: 1.0.0
-- Work package: BOPEN-P35-001 (WP-P35-06, trial->paid migration)
-- Governing artifacts: DEC-P35-TENANCY-MODEL §12; PLAN-P35-06-TRIAL-TO-PAID §2; AGENTS.md §8
-- Rollback: 017_tenant_placement_state.down.sql
--
-- `placement_kind` (migration 011) says WHERE a tenant's data lives; `placement_state` says whether it
-- is settled there. A migration sets `migrating` before it copies and clears it to `stable` at the
-- atomic cutover. While `migrating`, the request path fails closed for that tenant — the freeze — so
-- the copy is a complete snapshot. Every existing tenant is `stable` by the column default; no data
-- migration is needed to add it.

ALTER TABLE tenants ADD COLUMN placement_state VARCHAR(20) NOT NULL DEFAULT 'stable';

ALTER TABLE tenants
    ADD CONSTRAINT chk_tenant_placement_state CHECK (placement_state IN ('stable', 'migrating'));
