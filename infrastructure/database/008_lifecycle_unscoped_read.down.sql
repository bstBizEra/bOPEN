-- Rollback for: 008_lifecycle_unscoped_read.sql
--
-- Restores the pre-008 state: unscoped lifecycle events remain writable and become unreadable
-- through any session again.
--
-- Applying this returns the audit trail to the condition that made the evasion worth
-- attempting — evidence that lands in the unscoped bucket goes back to having no reader. It
-- exists because a rollback that has never been executed is a rollback that does not work, and
-- the round trip is verified on every apply. It is not a remediation step.

DROP POLICY IF EXISTS lifecycle_events_read_unscoped ON lifecycle_events;
