"""MILE-4.2 Party ContactPoint extension — tenant isolation, integrity and append-only verification
history, executed against PostgreSQL (BOPEN-PARTY-002, DEC-P4-ENTRY §10).

Governed by DEC-P4-ENTRY, RESEARCH-MILE-4.2-PARTY-CONTACTPOINT, BOPEN-TENANT-001, AGENTS.md section 8.
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed SQL), R4 (adversarial negative probes), R5 (loud).

Every assertion runs real SQL against the live database with migration 019 applied. None would still
pass if the contact-point isolation policy, the composite foreign key, the ON DELETE RESTRICT actions,
the append-only verification-event policies, or the one-live-primary index were dropped — a contact
point of one tenant is unreadable in another, a cross-tenant attachment is refused by the database, a
recorded verification event resists both direct mutation and a parent cascade (the migration-014
lesson), a second primary of the same (party, type) is refused, and a Party with contact points cannot
be deleted.
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


class TestContactPointEvidenceCanBeProduced(unittest.TestCase):
    """EBIV R5 — a check that cannot run reports failure, never silent success."""

    def test_contact_point_isolation_evidence_can_be_produced(self):
        reason = _unavailable_reason()
        self.assertIsNone(reason, msg=f"ContactPoint isolation cannot be verified: {reason}")


@unittest.skipIf(_unavailable_reason() is not None, "database unavailable — reported by the guard test")
class TestContactPointIsolation(unittest.TestCase):
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

    def _make_party(self, tenant_id: str, name: str, party_type: str = "organization") -> str:
        with self.db.tenant_session(tenant_id, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO parties (tenant_id, party_type, display_name) VALUES (%s, %s, %s) "
                "RETURNING id",
                (tenant_id, party_type, name),
            )
            return str(cur.fetchone()[0])

    def _make_contact_point(
        self,
        tenant_id: str,
        party_id: str,
        endpoint_type: str = "email",
        endpoint_value: str = "a@example.com",
        purpose: str = "transactional",
        is_primary: bool = False,
    ) -> str:
        with self.db.tenant_session(tenant_id, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO party_contact_points "
                "(tenant_id, party_id, endpoint_type, endpoint_value, purpose, is_primary) "
                "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (tenant_id, party_id, endpoint_type, endpoint_value, purpose, is_primary),
            )
            return str(cur.fetchone()[0])

    # -- isolation ---------------------------------------------------------------------

    def test_a_contact_point_created_in_one_tenant_is_invisible_to_another(self):
        """CP-INV-01. Fails if tenant_isolation_party_contact_points is dropped."""
        p = self._make_party(self.tenant_a, "Acme A")
        self._make_contact_point(self.tenant_a, p)
        with self.db.tenant_session(self.tenant_b, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM party_contact_points")
            visible_to_b = cur.fetchone()[0]
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM party_contact_points")
            visible_to_a = cur.fetchone()[0]
        self.assertEqual(visible_to_a, 1, "tenant A cannot see its own contact point")
        self.assertEqual(visible_to_b, 0, "tenant B read tenant A's contact point; isolation is off")

    def test_a_cross_tenant_contact_point_insert_is_refused(self):
        """CP-INV-01, write side. The WITH CHECK clause refuses writing another tenant's row."""
        p = self._make_party(self.tenant_a, "Acme A")
        with self.db.tenant_session(self.tenant_b, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute(
                    "INSERT INTO party_contact_points "
                    "(tenant_id, party_id, endpoint_type, endpoint_value, purpose) "
                    "VALUES (%s, %s, 'email', 'x@example.com', 'general')",
                    (self.tenant_a, p),
                )

    # -- same-tenant integrity ---------------------------------------------------------

    def test_a_contact_point_cannot_attach_to_another_tenants_party(self):
        """CP-INV-02. The composite FK (tenant_id, party_id) -> parties(tenant_id, id) refuses a
        contact point whose Party belongs to another tenant, at the database."""
        b_party = self._make_party(self.tenant_b, "B org")
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute(
                    "INSERT INTO party_contact_points "
                    "(tenant_id, party_id, endpoint_type, endpoint_value, purpose) "
                    "VALUES (%s, %s, 'email', 'x@example.com', 'general')",
                    (self.tenant_a, b_party),
                )

    def test_an_unknown_endpoint_type_is_refused(self):
        """CP-INV-11. chk_cp_endpoint_type refuses anything but email/phone."""
        p = self._make_party(self.tenant_a, "Acme")
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.CheckViolation):
                cur.execute(
                    "INSERT INTO party_contact_points "
                    "(tenant_id, party_id, endpoint_type, endpoint_value, purpose) "
                    "VALUES (%s, %s, 'fax', 'x', 'general')",
                    (self.tenant_a, p),
                )

    def test_an_unknown_purpose_is_refused(self):
        """CP-INV-11. chk_cp_purpose refuses an ungoverned purpose."""
        p = self._make_party(self.tenant_a, "Acme")
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.CheckViolation):
                cur.execute(
                    "INSERT INTO party_contact_points "
                    "(tenant_id, party_id, endpoint_type, endpoint_value, purpose) "
                    "VALUES (%s, %s, 'email', 'x@example.com', 'marketing')",
                    (self.tenant_a, p),
                )

    def test_a_duplicate_endpoint_for_one_party_is_refused(self):
        """CP-INV-08. unq_cp_party_endpoint refuses the same endpoint twice for one party."""
        p = self._make_party(self.tenant_a, "Acme")
        self._make_contact_point(self.tenant_a, p, endpoint_value="dup@example.com")
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.UniqueViolation):
                cur.execute(
                    "INSERT INTO party_contact_points "
                    "(tenant_id, party_id, endpoint_type, endpoint_value, purpose) "
                    "VALUES (%s, %s, 'email', 'dup@example.com', 'billing')",
                    (self.tenant_a, p),
                )

    # -- one live primary per (party, type) --------------------------------------------

    def test_at_most_one_live_primary_per_party_and_type(self):
        """CP-INV-08 / CP-D-04. The partial unique index unq_cp_primary refuses a second primary of
        the same (tenant, party, endpoint_type)."""
        p = self._make_party(self.tenant_a, "Acme")
        self._make_contact_point(
            self.tenant_a, p, endpoint_value="primary1@example.com", is_primary=True
        )
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.UniqueViolation):
                cur.execute(
                    "INSERT INTO party_contact_points "
                    "(tenant_id, party_id, endpoint_type, endpoint_value, purpose, is_primary) "
                    "VALUES (%s, %s, 'email', 'primary2@example.com', 'general', true)",
                    (self.tenant_a, p),
                )

    def test_a_second_primary_of_a_different_type_is_allowed(self):
        """Positive control — the primary scope is (party, type), so a primary email and a primary
        phone coexist."""
        p = self._make_party(self.tenant_a, "Acme")
        self._make_contact_point(
            self.tenant_a, p, endpoint_type="email", endpoint_value="e@example.com", is_primary=True
        )
        cp = self._make_contact_point(
            self.tenant_a, p, endpoint_type="phone", endpoint_value="+15551234567", is_primary=True
        )
        self.assertIsNotNone(cp)

    # -- append-only verification history ----------------------------------------------

    def _record_verification_event(self, tenant_id: str, contact_point_id: str) -> None:
        with self.db.tenant_session(tenant_id, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO party_contact_point_verification_events "
                "(tenant_id, contact_point_id, from_state, to_state, method) "
                "VALUES (%s, %s, 'unverified', 'verified', 'administrative_assertion')",
                (tenant_id, contact_point_id),
            )

    def test_recorded_verification_events_cannot_be_updated_or_deleted(self):
        """CP-INV-07. The events table grants SELECT and INSERT only, so an UPDATE or DELETE reaches
        zero rows whatever SQL is issued — the same discipline as workflow_history and the audit
        trail."""
        p = self._make_party(self.tenant_a, "Acme")
        cp = self._make_contact_point(self.tenant_a, p)
        self._record_verification_event(self.tenant_a, cp)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("UPDATE party_contact_point_verification_events SET to_state = 'failed'")
            self.assertEqual(cur.rowcount, 0, "a verification event was updatable")
            cur.execute("DELETE FROM party_contact_point_verification_events")
            self.assertEqual(cur.rowcount, 0, "a verification event was deletable")
            cur.execute("SELECT to_state FROM party_contact_point_verification_events")
            self.assertEqual(cur.fetchone()[0], "verified", "the recorded event was altered")

    def test_recorded_verification_survives_an_attempt_to_delete_its_contact_point(self):
        """CP-INV-07, the migration-014 lesson applied in advance. A direct DELETE on the events table
        reaches zero rows (no DELETE policy), but a parent cascade is the path that erased
        workflow_history. fk_cpve_cp is ON DELETE RESTRICT, so deleting a contact point that has a
        recorded verification event is refused and the event is untouched."""
        p = self._make_party(self.tenant_a, "Acme")
        cp = self._make_contact_point(self.tenant_a, p)
        self._record_verification_event(self.tenant_a, cp)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute("DELETE FROM party_contact_points WHERE id = %s", (cp,))
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute(
                "SELECT to_state FROM party_contact_point_verification_events "
                "WHERE contact_point_id = %s",
                (cp,),
            )
            self.assertEqual(cur.fetchone()[0], "verified", "the recorded event was erased")

    # -- ON DELETE RESTRICT on the party (CP-D-03) -------------------------------------

    def test_a_party_with_a_contact_point_cannot_be_deleted(self):
        """CP-INV-07 / CP-D-03. fk_cp_party is ON DELETE RESTRICT: deleting a Party with contact
        points is refused — retire, do not delete. Deleting a Party would otherwise cascade its
        contact points and, through them, the append-only verification history."""
        p = self._make_party(self.tenant_a, "Acme")
        self._make_contact_point(self.tenant_a, p)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute("DELETE FROM parties WHERE id = %s", (p,))
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM parties WHERE id = %s", (p,))
            self.assertEqual(cur.fetchone()[0], 1, "the party was deleted out from under its contact point")


if __name__ == "__main__":
    unittest.main()
