-- Migration: 014_workflow_history_survives_its_instance.sql
-- Description: Stop a recorded workflow transition from being erased by deleting its instance.
--              Closes a reachable deletion of the append-only history.
-- Version: 1.0.0
-- Work package: BOPEN-P35-001 (MILE-4.2 Workflow State Engine)
-- Governing artifacts: DEC-P4-ENTRY §8; AGENTS.md §8; BOPEN-GOV-EBIV-001
-- Rollback: 014_workflow_history_survives_its_instance.down.sql
--
-- =============================================================================
-- What was reachable
-- =============================================================================
-- Migration 013 states the basis for calling `workflow_history` append-only: it has SELECT and
-- INSERT policies and deliberately no UPDATE or DELETE policy, so those commands reach zero rows
-- whatever SQL is issued. That is true, and the isolation suite asserts it directly.
--
-- It is not the whole guarantee. PostgreSQL performs foreign-key actions with row security
-- bypassed — migration 009 closed exactly this carve-out for the audit trail. `workflow_history`
-- declared its instance foreign key `ON DELETE CASCADE`, and `workflow_instances` carries a
-- `FOR ALL` policy, which grants DELETE. So the history was erasable from inside an ordinary
-- tenant session, using only the application role, without any DELETE on `workflow_history` itself.
-- Reproduced live by the verifier on candidate a09022d:
--
--     transition recorded          workflow_history has 1 row      (append-only holds directly)
--     direct DELETE on history     0 rows                          (append-only holds directly)
--     DELETE the parent instance   1 row (permitted by FOR ALL) -> history cascades 1 -> 0
--
-- A recorded transition erased, every direct-DELETE test still green while it happened. That is
-- the void-if-broken failure migration 009 names: an append-only claim that a cascade quietly voids.
--
-- =============================================================================
-- The fix, and why RESTRICT rather than dropping the key
-- =============================================================================
-- Migration 009 faced the same shape and chose by what the referent *is*. `audit_events.context_id`
-- lost its foreign key entirely, because a context lives five minutes and is expected to be reaped —
-- the audit record must outlive a referent that is meant to disappear. `audit_events.tenant_id`
-- instead is `ON DELETE RESTRICT`, because a tenant is not meant to silently vanish under its own
-- trail.
--
-- A workflow instance is the second case, not the first. It is durable business state, there is no
-- reaper for it, and its identifier in a history row still names a live thing. So the key stays and
-- only the action changes: `ON DELETE RESTRICT`. An instance that has recorded a transition can no
-- longer be deleted out from under its history — the history is protected in place, referential
-- integrity intact, no orphan rows.
--
-- This also closes the two longer paths without further change. Deleting a definition cascades to
-- its instances (013), and deleting a tenant cascades to its definitions; either now fails if any
-- of those instances has history, because the cascade reaches an instance the RESTRICT protects.
-- The same discipline as `audit_events.tenant_id`, which already refuses to let a tenant with an
-- audit trail be deleted.

ALTER TABLE workflow_history DROP CONSTRAINT fk_wf_instance;

ALTER TABLE workflow_history ADD CONSTRAINT fk_wf_instance
    FOREIGN KEY (tenant_id, instance_id)
    REFERENCES workflow_instances(tenant_id, id) ON DELETE RESTRICT;

COMMENT ON CONSTRAINT fk_wf_instance ON workflow_history IS
    'ON DELETE RESTRICT, not CASCADE: a recorded transition is append-only and must survive, so an '
    'instance that has history cannot be deleted. Migration 014 — closes the cascade bypass 013 left '
    'open, the same carve-out migration 009 closed for the audit trail.';
