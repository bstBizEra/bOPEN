-- Rollback for 021_notification_foundation.sql — Stage 1 substrate only.
-- Children before parents: every child references its parent by a composite foreign key.
--
-- Per PLAN-NOTIFY-MIGRATE §5, this pre-evidence down migration is valid ONLY while the substrate is
-- empty of committed attempts/receipts. Once append-only delivery evidence exists, dropping these
-- tables is exactly the cascade-erasure the ON DELETE RESTRICT discipline forbids; a running/drained
-- queue is retired by forward compensation (revoke + read-only quarantine), never by this down.

-- Platform control-plane (no tenant dependency).
DROP TABLE IF EXISTS notification_provider_health;

-- Tenant-scoped control tables (no children).
DROP POLICY IF EXISTS tenant_isolation_notification_fairness ON notification_fairness;
DROP TABLE IF EXISTS notification_fairness;

DROP POLICY IF EXISTS tenant_isolation_notification_quota_suspend ON notification_quota_suspend;
DROP TABLE IF EXISTS notification_quota_suspend;

DROP POLICY IF EXISTS tenant_isolation_notification_quota ON notification_quota;
DROP TABLE IF EXISTS notification_quota;

-- Append-only evidence (children of notification_dispatch).
DROP POLICY IF EXISTS notification_receipt_insert ON notification_receipt;
DROP POLICY IF EXISTS notification_receipt_read ON notification_receipt;
DROP TABLE IF EXISTS notification_receipt;

DROP POLICY IF EXISTS notification_attempt_insert ON notification_attempt;
DROP POLICY IF EXISTS notification_attempt_read ON notification_attempt;
DROP TABLE IF EXISTS notification_attempt;

-- Mutable dispatch (child of notifications).
DROP POLICY IF EXISTS tenant_isolation_notification_dispatch ON notification_dispatch;
DROP TABLE IF EXISTS notification_dispatch;

-- Parent orchestration record.
DROP POLICY IF EXISTS tenant_isolation_notifications ON notifications;
DROP TABLE IF EXISTS notifications;
