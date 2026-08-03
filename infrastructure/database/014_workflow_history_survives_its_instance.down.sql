-- Rollback for 014_workflow_history_survives_its_instance.sql.
-- Restores the original ON DELETE CASCADE from migration 013. Note this reopens the append-only
-- bypass the forward migration closes; it exists only to make 014 reversible in a controlled way.

ALTER TABLE workflow_history DROP CONSTRAINT fk_wf_instance;

ALTER TABLE workflow_history ADD CONSTRAINT fk_wf_instance
    FOREIGN KEY (tenant_id, instance_id)
    REFERENCES workflow_instances(tenant_id, id) ON DELETE CASCADE;
