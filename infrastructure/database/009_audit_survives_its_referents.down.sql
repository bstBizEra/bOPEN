-- Rollback for: 009_audit_survives_its_referents.sql
--
-- Restores the pre-009 state: the foreign key from audit_events.context_id back onto
-- active_contexts with ON DELETE SET NULL, and the single FOR ALL policy on active_contexts.
--
-- Applying this reopens the mutation 009 closed — a tenant regains the ability to delete its own
-- context row and thereby null the context binding on its own audit records, using only the
-- application role. It exists because a rollback that has never been executed is a rollback that
-- does not work, and the round trip is verified on every apply. It is not a remediation step.
--
-- The foreign key is recreated as NOT VALID and then validated, so that rolling back cannot fail
-- on audit rows whose context has since been reaped — rows that only exist because 009 made them
-- possible. Without this the rollback would be untestable the moment it became useful.

DROP POLICY IF EXISTS active_contexts_revoke ON active_contexts;
DROP POLICY IF EXISTS active_contexts_establish ON active_contexts;
DROP POLICY IF EXISTS active_contexts_read ON active_contexts;

CREATE POLICY active_contexts_isolation ON active_contexts
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- Any audit row whose context no longer exists is detached first; the pre-009 schema could not
-- have held it.
UPDATE audit_events a
   SET context_id = NULL
 WHERE a.context_id IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM active_contexts c WHERE c.id = a.context_id);

ALTER TABLE audit_events
    ADD CONSTRAINT audit_events_context_id_fkey
    FOREIGN KEY (context_id) REFERENCES active_contexts(id) ON DELETE SET NULL;

COMMENT ON COLUMN audit_events.context_id IS NULL;
