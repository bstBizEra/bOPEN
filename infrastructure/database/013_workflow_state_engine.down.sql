-- Rollback for 013_workflow_state_engine.sql. Drop in dependency order.

DROP POLICY IF EXISTS workflow_history_insert ON workflow_history;
DROP POLICY IF EXISTS workflow_history_read ON workflow_history;
DROP TABLE IF EXISTS workflow_history;

DROP POLICY IF EXISTS tenant_isolation_workflow_instances ON workflow_instances;
DROP TABLE IF EXISTS workflow_instances;

DROP POLICY IF EXISTS tenant_isolation_workflow_definitions ON workflow_definitions;
DROP TABLE IF EXISTS workflow_definitions;
