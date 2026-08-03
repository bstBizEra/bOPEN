"""MILE-4.1 party foundation — tenant isolation and integrity, executed against PostgreSQL.

Governed by DEC-P4-ENTRY, BOPEN-PARTY-001, BOPEN-TENANT-001, AGENTS.md section 8.
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed SQL), R4 (adversarial negative probes), R5 (loud).

Every assertion runs real SQL against the live database with migration 010 applied. None would
still pass if the party isolation policies or the integrity constraints were dropped — a party
created in one tenant is unreadable in another, a cross-tenant party or relationship is refused by
the database, and a party cannot relate to itself. This is the first test that the Phase 3.5
tenant-isolation boundary holds for real business data, not only kernel entities.
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


class TestPartyEvidenceCanBeProduced(unittest.TestCase):
    """EBIV R5 — a check that cannot run reports failure, never silent success."""

    def test_party_isolation_evidence_can_be_produced(self):
        reason = _unavailable_reason()
        self.assertIsNone(reason, msg=f"Party isolation cannot be verified: {reason}")


@unittest.skipIf(_unavailable_reason() is not None, "database unavailable — reported by the guard test")
class TestPartyIsolation(unittest.TestCase):
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

    # -- isolation ---------------------------------------------------------------------

    def test_a_party_created_in_one_tenant_is_invisible_to_another(self):
        """INV-PARTY-TENANT-ISOLATION-01. Fails if tenant_isolation_parties is dropped."""
        self._make_party(self.tenant_a, "Acme A")
        with self.db.tenant_session(self.tenant_b, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM parties")
            visible_to_b = cur.fetchone()[0]
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM parties")
            visible_to_a = cur.fetchone()[0]
        self.assertEqual(visible_to_a, 1, "tenant A cannot see its own party")
        self.assertEqual(visible_to_b, 0, "tenant B read tenant A's party; isolation is not in force")

    def test_a_cross_tenant_party_insert_is_refused(self):
        """INV-PARTY-TENANT-WRITE-01. The WITH CHECK clause refuses writing another tenant's row."""
        with self.db.tenant_session(self.tenant_b, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute(
                    "INSERT INTO parties (tenant_id, party_type, display_name) VALUES (%s, %s, %s)",
                    (self.tenant_a, "organization", "smuggled into A"),
                )

    # -- integrity ---------------------------------------------------------------------

    def test_an_unknown_party_type_is_refused(self):
        """INV-PARTY-TYPE-01. chk_party_type refuses anything but person/organization."""
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.CheckViolation):
                cur.execute(
                    "INSERT INTO parties (tenant_id, party_type, display_name) VALUES (%s, %s, %s)",
                    (self.tenant_a, "alien", "not a valid type"),
                )

    def test_a_party_cannot_relate_to_itself(self):
        """INV-RELATIONSHIP-NO-SELF-01. chk_no_self_relationship refuses from == to."""
        p = self._make_party(self.tenant_a, "Self")
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.CheckViolation):
                cur.execute(
                    "INSERT INTO party_relationships (tenant_id, from_party_id, to_party_id, "
                    "relationship_type) VALUES (%s, %s, %s, 'owns')",
                    (self.tenant_a, p, p),
                )

    def test_a_relationship_cannot_cross_tenants(self):
        """INV-RELATIONSHIP-SAME-TENANT-01. The composite FK to parties(tenant_id, id) refuses a
        relationship whose other endpoint is a party of another tenant."""
        a_party = self._make_party(self.tenant_a, "A org")
        b_party = self._make_party(self.tenant_b, "B org")
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute(
                    "INSERT INTO party_relationships (tenant_id, from_party_id, to_party_id, "
                    "relationship_type) VALUES (%s, %s, %s, 'supplies')",
                    (self.tenant_a, a_party, b_party),
                )

    def test_a_valid_same_tenant_relationship_is_accepted(self):
        """Positive control — a relationship between two parties of the same tenant is created."""
        buyer = self._make_party(self.tenant_a, "Buyer")
        seller = self._make_party(self.tenant_a, "Seller")
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO party_relationships (tenant_id, from_party_id, to_party_id, "
                "relationship_type) VALUES (%s, %s, %s, 'supplies') RETURNING id",
                (self.tenant_a, seller, buyer),
            )
            self.assertIsNotNone(cur.fetchone()[0])


if __name__ == "__main__":
    unittest.main()
