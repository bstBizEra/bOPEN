"""MILE-4.2 Location foundation — tenant isolation, integrity, coordinate validity, cycle refusal, and
append-only history, executed against PostgreSQL (BOPEN-LOC-001, DEC-P4-ENTRY §11).

Governed by DEC-P4-ENTRY §11, RESEARCH-MILE-4.2-LOCATION, BOPEN-TENANT-001, AGENTS.md section 8.
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed SQL), R4 (adversarial negative probes), R5 (loud).

Every assertion runs real SQL against the live database with migration 020 applied. None would still
pass if the location isolation policies, the composite foreign keys, the ON DELETE RESTRICT actions, the
coordinate-validity CHECK constraints, the partial unique indexes, or the append-only history policies
were dropped: a location of one tenant is unreadable in another, a cross-tenant child attachment is
refused by the database, an out-of-range or NaN coordinate is refused, a self-link and a containment
cycle are refused, at most one current address version and one live scheme/value and one active parent
hold, a recorded history event resists direct mutation and a parent cascade, and a location with any
child cannot be deleted.
"""

from __future__ import annotations

import os
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))


def _unavailable_reason() -> str | None:
    try:
        import psycopg  # noqa: F401
    except ImportError:
        return "psycopg is not installed. Run: python -m pip install -r requirements.txt"
    if not os.environ.get("BOPEN_DATABASE_URL", "").strip():
        return "BOPEN_DATABASE_URL is not set. Provision with `python tools/db_bootstrap.py --apply`."
    return None


class TestLocationEvidenceCanBeProduced(unittest.TestCase):
    """EBIV R5 — a check that cannot run reports failure, never silent success."""

    def test_location_isolation_evidence_can_be_produced(self):
        reason = _unavailable_reason()
        self.assertIsNone(reason, msg=f"Location isolation cannot be verified: {reason}")


@unittest.skipIf(_unavailable_reason() is not None, "database unavailable — reported by the guard test")
class TestLocationIsolation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from platform_kernel import db

        cls.db = db

    def setUp(self):
        import psycopg

        self.psycopg = psycopg
        self.conn = self.db.connect(autocommit=True)
        self.tenant_a = str(uuid.uuid4())
        self.tenant_b = str(uuid.uuid4())
        with self.db.system_session(connection=self.conn) as cur:
            for tenant_id, name in ((self.tenant_a, "Tenant A"), (self.tenant_b, "Tenant B")):
                cur.execute(
                    "INSERT INTO tenants (id, name, status) VALUES (%s, %s, 'active')",
                    (tenant_id, name),
                )

    def tearDown(self):
        self.conn.close()

    def _make_location(
        self, tenant_id: str, code: str, name: str = "Site", location_type: str = "site"
    ) -> str:
        with self.db.tenant_session(tenant_id, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO locations (tenant_id, code, name, location_type) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (tenant_id, code, name, location_type),
            )
            return str(cur.fetchone()[0])

    def _make_geometry(
        self, tenant_id: str, location_id: str, lon="100.5", lat="13.7"
    ) -> str:
        with self.db.tenant_session(tenant_id, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO location_geometry_observations "
                "(tenant_id, location_id, longitude, latitude) VALUES (%s, %s, %s, %s) RETURNING id",
                (tenant_id, location_id, lon, lat),
            )
            return str(cur.fetchone()[0])

    def _add_contains(self, tenant_id: str, from_id: str, to_id: str) -> None:
        with self.db.tenant_session(tenant_id, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO location_relationships (tenant_id, from_location_id, to_location_id) "
                "VALUES (%s, %s, %s)",
                (tenant_id, from_id, to_id),
            )

    # -- isolation ---------------------------------------------------------------------

    def test_a_location_created_in_one_tenant_is_invisible_to_another(self):
        """LOC-INV-01. Fails if tenant_isolation_locations is dropped."""
        self._make_location(self.tenant_a, "A-1")
        with self.db.tenant_session(self.tenant_b, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM locations")
            visible_to_b = cur.fetchone()[0]
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM locations")
            visible_to_a = cur.fetchone()[0]
        self.assertEqual(visible_to_a, 1, "tenant A cannot see its own location")
        self.assertEqual(visible_to_b, 0, "tenant B read tenant A's location; isolation is off")

    def test_a_cross_tenant_location_insert_is_refused(self):
        """LOC-INV-01, write side. The WITH CHECK clause refuses writing another tenant's row."""
        with self.db.tenant_session(self.tenant_b, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute(
                    "INSERT INTO locations (tenant_id, code, name, location_type) "
                    "VALUES (%s, 'X', 'X', 'site')",
                    (self.tenant_a,),
                )

    # -- cross-tenant composite-FK refusal ---------------------------------------------

    def test_an_address_version_cannot_attach_to_another_tenants_location(self):
        """LOC-INV-09/composite FK. fk_addr_location (tenant_id, location_id) refuses a child whose
        location belongs to another tenant, at the database."""
        b_loc = self._make_location(self.tenant_b, "B-1")
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute(
                    "INSERT INTO location_address_versions "
                    "(tenant_id, location_id, version_number, country_code, original_input) "
                    "VALUES (%s, %s, 1, 'TH', 'raw')",
                    (self.tenant_a, b_loc),
                )

    def test_a_geometry_observation_cannot_attach_to_another_tenants_location(self):
        b_loc = self._make_location(self.tenant_b, "B-2")
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute(
                    "INSERT INTO location_geometry_observations "
                    "(tenant_id, location_id, longitude, latitude) VALUES (%s, %s, '10', '10')",
                    (self.tenant_a, b_loc),
                )

    def test_a_relationship_cannot_target_another_tenants_location(self):
        a_loc = self._make_location(self.tenant_a, "A-2")
        b_loc = self._make_location(self.tenant_b, "B-3")
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute(
                    "INSERT INTO location_relationships (tenant_id, from_location_id, to_location_id) "
                    "VALUES (%s, %s, %s)",
                    (self.tenant_a, a_loc, b_loc),
                )

    # -- coordinate validity (LOC-INV-04) ----------------------------------------------

    def test_out_of_range_longitude_is_refused(self):
        loc = self._make_location(self.tenant_a, "GEO-1")
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.CheckViolation):
                cur.execute(
                    "INSERT INTO location_geometry_observations "
                    "(tenant_id, location_id, longitude, latitude) VALUES (%s, %s, '200', '10')",
                    (self.tenant_a, loc),
                )

    def test_out_of_range_latitude_is_refused(self):
        loc = self._make_location(self.tenant_a, "GEO-2")
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.CheckViolation):
                cur.execute(
                    "INSERT INTO location_geometry_observations "
                    "(tenant_id, location_id, longitude, latitude) VALUES (%s, %s, '10', '95')",
                    (self.tenant_a, loc),
                )

    def test_nan_coordinate_is_refused(self):
        """PostgreSQL orders NUMERIC 'NaN' above every number, so BETWEEN -180 AND 180 rejects it."""
        loc = self._make_location(self.tenant_a, "GEO-3")
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.CheckViolation):
                cur.execute(
                    "INSERT INTO location_geometry_observations "
                    "(tenant_id, location_id, longitude, latitude) VALUES (%s, %s, 'NaN', '10')",
                    (self.tenant_a, loc),
                )

    # -- relationship integrity (LOC-INV-09) -------------------------------------------

    def test_a_self_link_is_refused(self):
        """chk_rel_no_self refuses a location containing itself."""
        loc = self._make_location(self.tenant_a, "SELF-1")
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.CheckViolation):
                cur.execute(
                    "INSERT INTO location_relationships (tenant_id, from_location_id, to_location_id) "
                    "VALUES (%s, %s, %s)",
                    (self.tenant_a, loc, loc),
                )

    def test_a_containment_cycle_is_refused(self):
        """LOC-INV-09. A contains B, B contains C, then C contains A closes a cycle and is refused by
        the repository's WITH RECURSIVE walk."""
        from platform_kernel import location_repositories as location_repo

        repo = location_repo.LocationRepository()
        # Use tenant sessions on the module's own connections; the repo opens its own connection.
        a = self._make_location(self.tenant_a, "CY-A")
        b = self._make_location(self.tenant_a, "CY-B")
        c = self._make_location(self.tenant_a, "CY-C")
        repo.add_contains(self.tenant_a, a, b)
        repo.add_contains(self.tenant_a, b, c)
        with self.assertRaises(location_repo.RelationshipCycleError):
            repo.add_contains(self.tenant_a, c, a)

    def test_a_duplicate_live_edge_is_refused(self):
        """unq_rel_live_edge refuses the same live (from, to, type) twice."""
        a = self._make_location(self.tenant_a, "DUP-A")
        b = self._make_location(self.tenant_a, "DUP-B")
        self._add_contains(self.tenant_a, a, b)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.UniqueViolation):
                cur.execute(
                    "INSERT INTO location_relationships (tenant_id, from_location_id, to_location_id) "
                    "VALUES (%s, %s, %s)",
                    (self.tenant_a, a, b),
                )

    def test_a_second_active_parent_is_refused(self):
        """LOC-D-05. unq_rel_one_active_parent refuses a second live `contains` into one child."""
        parent1 = self._make_location(self.tenant_a, "P1")
        parent2 = self._make_location(self.tenant_a, "P2")
        child = self._make_location(self.tenant_a, "CHILD")
        self._add_contains(self.tenant_a, parent1, child)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.UniqueViolation):
                cur.execute(
                    "INSERT INTO location_relationships (tenant_id, from_location_id, to_location_id) "
                    "VALUES (%s, %s, %s)",
                    (self.tenant_a, parent2, child),
                )

    # -- address integrity (LOC-INV-07) ------------------------------------------------

    def test_at_most_one_current_address_version_per_location(self):
        """unq_addr_current refuses a second version with effective_to IS NULL for one location."""
        loc = self._make_location(self.tenant_a, "ADDR-1")
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO location_address_versions "
                "(tenant_id, location_id, version_number, country_code, original_input) "
                "VALUES (%s, %s, 1, 'TH', 'raw1')",
                (self.tenant_a, loc),
            )
            with self.assertRaises(self.psycopg.errors.UniqueViolation):
                cur.execute(
                    "INSERT INTO location_address_versions "
                    "(tenant_id, location_id, version_number, country_code, original_input) "
                    "VALUES (%s, %s, 2, 'TH', 'raw2')",
                    (self.tenant_a, loc),
                )

    # -- identifier integrity (LOC-INV-08) ---------------------------------------------

    def test_a_live_scheme_value_collision_is_refused(self):
        """unq_extid_live refuses the same live (scheme, value) within a tenant."""
        loc1 = self._make_location(self.tenant_a, "EID-1")
        loc2 = self._make_location(self.tenant_a, "EID-2")
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO location_external_identifiers (tenant_id, location_id, scheme, value) "
                "VALUES (%s, %s, 'osm', 'node/42')",
                (self.tenant_a, loc1),
            )
            with self.assertRaises(self.psycopg.errors.UniqueViolation):
                cur.execute(
                    "INSERT INTO location_external_identifiers "
                    "(tenant_id, location_id, scheme, value) VALUES (%s, %s, 'osm', 'node/42')",
                    (self.tenant_a, loc2),
                )

    # -- append-only history (LOC-INV-12) ----------------------------------------------

    def _record_history(self, tenant_id: str, location_id: str) -> None:
        with self.db.tenant_session(tenant_id, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO location_history (tenant_id, location_id, event_type, detail) "
                "VALUES (%s, %s, 'location.registered', '{\"safe\": true}'::jsonb)",
                (tenant_id, location_id),
            )

    def test_recorded_history_cannot_be_updated_or_deleted(self):
        """LOC-INV-12. location_history grants SELECT and INSERT only, so UPDATE/DELETE reach zero
        rows whatever SQL is issued — the audit-trail discipline."""
        loc = self._make_location(self.tenant_a, "HIST-1")
        self._record_history(self.tenant_a, loc)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("UPDATE location_history SET event_type = 'tampered'")
            self.assertEqual(cur.rowcount, 0, "a history event was updatable")
            cur.execute("DELETE FROM location_history")
            self.assertEqual(cur.rowcount, 0, "a history event was deletable")
            cur.execute("SELECT event_type FROM location_history WHERE location_id = %s", (loc,))
            self.assertEqual(cur.fetchone()[0], "location.registered", "the recorded event was altered")

    def test_recorded_history_survives_an_attempt_to_delete_its_location(self):
        """LOC-INV-12, the migration-014 lesson applied in advance. fk_history_location is ON DELETE
        RESTRICT, so deleting a location that has history is refused and the event is untouched."""
        loc = self._make_location(self.tenant_a, "HIST-2")
        self._record_history(self.tenant_a, loc)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute("DELETE FROM locations WHERE id = %s", (loc,))
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM location_history WHERE location_id = %s", (loc,))
            self.assertEqual(cur.fetchone()[0], 1, "the recorded history was erased")

    def test_a_location_with_children_cannot_be_deleted(self):
        """LOC-D-12. fk_geo_location is ON DELETE RESTRICT: a location with a geometry observation
        cannot be deleted — retire it instead."""
        loc = self._make_location(self.tenant_a, "CHILD-DEL")
        self._make_geometry(self.tenant_a, loc)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute("DELETE FROM locations WHERE id = %s", (loc,))
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM locations WHERE id = %s", (loc,))
            self.assertEqual(cur.fetchone()[0], 1, "the location was deleted out from under its child")

    # -- immutable identity (LOC-INV-03) -----------------------------------------------

    def test_a_lifecycle_change_keeps_the_same_id(self):
        """LOC-INV-03. A transition mutates lifecycle_state, never the immutable id."""
        from platform_kernel import location_repositories as location_repo

        repo = location_repo.LocationRepository()
        loc = repo.create(self.tenant_a, "IDN-1", "Site", "site")
        moved = repo.transition(self.tenant_a, loc.id, "active", actor="p")
        self.assertEqual(moved.id, loc.id, "the location id changed across a lifecycle transition")
        self.assertEqual(moved.lifecycle_state, "active")


if __name__ == "__main__":
    unittest.main()
