-- Migration: 009_audit_survives_its_referents.sql
-- Description: Stop an audit record from being altered by the deletion of something it
--              references. Closes a reachable mutation of the append-only trail.
-- Version: 1.0.0
-- Work package: BOPEN-P35-001
-- Governing artifacts: BOPEN-AUTHZ-001; AGENTS.md §8; BOPEN-GOV-EBIV-001
-- Rollback: 009_audit_survives_its_referents.down.sql
--
-- =============================================================================
-- What was reachable
-- =============================================================================
-- Migration 003 states the basis for calling `audit_events` append-only: it has SELECT and
-- INSERT policies and deliberately no UPDATE or DELETE policy, so those commands reach zero
-- rows whatever SQL is issued. That is true, and it is what the isolation suite asserts.
--
-- It is also not the whole guarantee. PostgreSQL documents three ways past an RLS policy, and
-- one of them is referential integrity: foreign-key actions are performed by the system and are
-- not subject to row security. `audit_events.context_id` was declared
-- `REFERENCES active_contexts(id) ON DELETE SET NULL`, and `active_contexts` carried a `FOR ALL`
-- policy — which grants DELETE.
--
-- So the trail was mutable from inside an ordinary tenant session, using only the application
-- role, without any write to `audit_events`. Reproduced end to end on 2026-07-30:
--
--     audit record written    context_id=e0615e21-…  action=delete
--     direct DELETE on audit  0 rows                 (append-only holds)
--     DELETE own context      1 row                  (permitted by the FOR ALL policy)
--     audit record now reads  context_id=NULL        action=delete
--
-- The same probe confirmed the other two carve-outs are already closed: the application role has
-- no TRUNCATE privilege, and `audit_events.tenant_id` is `ON DELETE RESTRICT` — migration 003
-- reasoned about exactly this hazard for the tenant column and said so in a comment. It did not
-- carry that reasoning to the two adjacent columns.
--
-- =============================================================================
-- Why this matters more than the attack does
-- =============================================================================
-- Nothing in the kernel deletes a context today, so this is not being exploited. The reason to
-- fix it now is that a context lives five minutes. Something must eventually reap expired ones,
-- and on the day that job is written it will strip `context_id` from every audit row referencing
-- what it reaps. Not an attack — routine housekeeping, quietly destroying evidence, and passing
-- every existing test while doing it.
--
-- An audit record is a historical statement, not a live relationship. It has to outlive the row
-- it describes, because the whole point is to still be there afterwards.

-- 1. The audit record keeps the identifier, and stops being editable by the referent's deletion.
ALTER TABLE audit_events DROP CONSTRAINT audit_events_context_id_fkey;

-- The column stays. Only the referential action goes.
--
-- This is deliberately the opposite of the reasoning in finding F10, which prices the *absence*
-- of a foreign key at 6,537 orphaned rows in the metering tables. The distinction is what the
-- column means. A metering row's `tenant_id` names a live relationship and an orphan there is a
-- defect. An audit row's `context_id` names something that happened; the referent is expected to
-- disappear, and the record is worth less, not more, once it has been edited to agree.

COMMENT ON COLUMN audit_events.context_id IS
    'Context in force when the event occurred. Deliberately carries no foreign key: contexts are '
    'five-minute-lived and will be reaped, and an audit record must survive its referent. '
    'Migration 009.';

-- 2. Remove the DELETE capability nothing uses.
--
-- `repositories.py` performs INSERT, SELECT and UPDATE on this table and never DELETE. The
-- FOR ALL policy granted a fourth command that no caller needs and that made the mutation above
-- reachable. Splitting by command is the same shape migration 007 uses for the registry tables.

DROP POLICY active_contexts_isolation ON active_contexts;

CREATE POLICY active_contexts_read ON active_contexts
    FOR SELECT
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY active_contexts_establish ON active_contexts
    FOR INSERT
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- Revocation is an UPDATE setting `revoked_at`, so UPDATE stays.
--
-- USING and WITH CHECK are both stated, and the reason is legibility rather than force. An
-- earlier draft of this comment claimed that omitting WITH CHECK would let an update move a row
-- to another tenant; that is wrong, and mutation testing caught it. PostgreSQL supplies an
-- identical WITH CHECK when one is omitted, so dropping it here changes nothing — the mutation
-- that removes it is a semantic no-op and correctly survives the suite. Migration 003 states the
-- real reason for writing both: so the write-side constraint survives a later edit to the
-- read-side expression, rather than silently inheriting it.
CREATE POLICY active_contexts_revoke ON active_contexts
    FOR UPDATE
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- No DELETE policy. A context is retired by setting `revoked_at`, which is what the code does
-- and what leaves the audit trail able to explain itself.

-- =============================================================================
-- What this deliberately does not do
-- =============================================================================
-- `audit_events.principal_id` remains `ON DELETE SET NULL`, so deleting a principal still erases
-- the actor from existing audit records. That is left alone because it is not clearly a defect:
-- nulling the actor on erasure is one of the recognised reconciliations between an append-only
-- trail and a data-subject erasure request, and migration 003 does not say whether it was
-- intended as one. The two readings lead to opposite changes — `RESTRICT` if it was an oversight,
-- keep it if it is the erasure path — so it is a decision, and it is recorded as one rather than
-- taken here. It is also far less reachable than the context case: the application role has no
-- DELETE policy on `principals` after migration 007, and no code path deletes one.
--
-- Nor does this add a reaper for expired contexts. It makes the trail safe for one to exist.
