-- Rollback for 015_placement_identity.sql.

DROP POLICY IF EXISTS placement_identity_declare ON placement_identity;
DROP POLICY IF EXISTS placement_identity_read ON placement_identity;
DROP TABLE IF EXISTS placement_identity;
