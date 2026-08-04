"""WP-P35-06 dedicated-database placement — "one tenant, one database", proven across two real
PostgreSQL databases.

Governed by DEC-P35-TENANCY-MODEL §8 (Option D), §10 (provisioning authorized), PLAN-P35-06-DEDICATED-DB.
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed SQL across two databases), R4 (the refusals — a
mis-route and an unconfigured dedicated tenant — are the point), R5 (loud: skips report the missing
admin credential rather than passing hollow).

This is the first proof that a dedicated tenant's data physically lives in its own database and is
absent from the shared pool — not just that resolution picks a URL. The keystone is
`test_a_misdeclared_dedicated_database_is_refused`: a database that does not declare it serves the
tenant is refused, so a mis-configured ref is a loud failure, not the invisible cross-tenant read
row-level security cannot catch.

Provisions a real second database in setUpClass and drops it in tearDownClass, so it needs the admin
credential; without it the class skips and the guard test reports why.
"""

from __future__ import annotations

import os
import re
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))
sys.path.insert(0, str(ROOT))


def _unavailable_reason() -> str | None:
    try:
        import psycopg  # noqa: F401
    except ImportError:
        return "psycopg is not installed."
    if not os.environ.get("BOPEN_DATABASE_URL", "").strip():
        return "BOPEN_DATABASE_URL is not set."
    if not os.environ.get("BOPEN_ADMIN_DATABASE_URL", "").strip():
        return "BOPEN_ADMIN_DATABASE_URL is not set; a second database cannot be provisioned."
    return None


def _sibling_url(app_url: str, database: str) -> str:
    """Return app_url with its database name replaced — the dedicated database, same host and role."""
    return re.sub(r"/[^/?]+(\?|$)", f"/{database}\\1", app_url, count=1)


class TestDedicatedEvidenceCanBeProduced(unittest.TestCase):
    """EBIV R5 — a check that cannot run reports failure, never silent success."""

    def test_dedicated_placement_evidence_can_be_produced(self):
        reason = _unavailable_reason()
        self.assertIsNone(reason, msg=f"Dedicated placement cannot be verified: {reason}")


@unittest.skipIf(_unavailable_reason() is not None, "database unavailable — reported by the guard test")
class TestDedicatedPlacement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg

        from platform_kernel import db, placement
        from tools import provision_dedicated_db as prov

        cls.psycopg = psycopg
        cls.db = db
        cls.placement = placement
        cls.prov = prov

        cls.control_url = os.environ["BOPEN_DATABASE_URL"]
        cls.admin_url = os.environ["BOPEN_ADMIN_DATABASE_URL"]
        cls.dedicated_db = f"bopen_dedi_{uuid.uuid4().hex[:10]}"
        cls.dedicated_url = _sibling_url(cls.control_url, cls.dedicated_db)

        cls.tenant_dedi = str(uuid.uuid4())
        cls.ref = f"ded{uuid.uuid4().hex[:8]}"
        cls.env_key = f"{placement.DEDICATED_ENV_PREFIX}{cls.ref}"

        # Provision the dedicated database end to end: control registry row (dedicated), the database
        # itself with the full ledger, its single tenants row and its placement_identity declaration.
        prov.provision_dedicated_database(
            tenant_id=cls.tenant_dedi,
            tenant_name="Dedicated Co",
            ref=cls.ref,
            target_url=cls.dedicated_url,
            admin_url=cls.admin_url,
            control_url=cls.control_url,
        )
        os.environ[cls.env_key] = cls.dedicated_url

        # A shared-pool tenant, for the cross-placement isolation probe.
        cls.tenant_shared = str(uuid.uuid4())
        with db.system_session() as cur:
            cur.execute(
                "INSERT INTO tenants (id, name, status) VALUES (%s, 'Shared Co', 'active') "
                "ON CONFLICT (id) DO NOTHING",
                (cls.tenant_shared,),
            )

    @classmethod
    def tearDownClass(cls):
        os.environ.pop(cls.env_key, None)
        # Drop the dedicated database and remove the control rows this class created.
        try:
            cls.prov.drop_database(cls.dedicated_db, cls.admin_url)
        except Exception:
            pass
        try:
            with cls.db.system_session() as cur:
                cur.execute("DELETE FROM tenants WHERE id = ANY(%s)",
                            ([cls.tenant_dedi, cls.tenant_shared],))
        except Exception:
            pass

    def _dedicated_conn(self):
        return self.db.connect(self.dedicated_url, autocommit=True)

    def _control_conn(self):
        return self.db.connect(self.control_url, autocommit=True)

    # -- routing: the write goes to the right database -----------------------------------

    def test_a_dedicated_tenants_write_lands_in_its_own_database(self):
        """INV-DEDI-ROUTE-01. Through the kernel's real path (placement resolved), a dedicated
        tenant's party is written — and is found by querying the dedicated database directly."""
        with self.db.tenant_session(self.tenant_dedi) as cur:  # resolves to the dedicated DB
            cur.execute(
                "INSERT INTO parties (tenant_id, party_type, display_name) "
                "VALUES (%s, 'organization', 'Dedicated Customer') RETURNING id",
                (self.tenant_dedi,),
            )
            party_id = str(cur.fetchone()[0])

        conn = self._dedicated_conn()
        try:
            with self.db.tenant_session(self.tenant_dedi, connection=conn) as cur:
                cur.execute("SELECT display_name FROM parties WHERE id = %s", (party_id,))
                row = cur.fetchone()
        finally:
            conn.close()
        self.assertIsNotNone(row, "the party is not in the dedicated database it was routed to")
        self.assertEqual(row[0], "Dedicated Customer")

    def test_that_write_is_absent_from_the_shared_pool(self):
        """INV-DEDI-ISOLATION-01. The same tenant's data is physically absent from the shared pool —
        it is in the other database, not merely hidden by a policy."""
        with self.db.tenant_session(self.tenant_dedi) as cur:
            cur.execute(
                "INSERT INTO parties (tenant_id, party_type, display_name) "
                "VALUES (%s, 'organization', 'Only In Dedicated')",
                (self.tenant_dedi,),
            )
        conn = self._control_conn()
        try:
            with self.db.tenant_session(self.tenant_dedi, connection=conn) as cur:
                cur.execute("SELECT count(*) FROM parties")
                in_shared = cur.fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(in_shared, 0, "the dedicated tenant's data was found in the shared pool")

    def test_a_shared_tenant_cannot_reach_dedicated_data_through_the_kernel(self):
        """INV-DEDI-CROSS-DB-01. A shared-pool tenant, routed to the shared database, cannot read a
        dedicated tenant's rows — they are in a different database entirely."""
        with self.db.tenant_session(self.tenant_dedi) as cur:
            cur.execute(
                "INSERT INTO parties (tenant_id, party_type, display_name) "
                "VALUES (%s, 'organization', 'Private To Dedicated') RETURNING id",
                (self.tenant_dedi,),
            )
            party_id = str(cur.fetchone()[0])
        with self.db.tenant_session(self.tenant_shared) as cur:  # resolves to the shared pool
            cur.execute("SELECT count(*) FROM parties WHERE id = %s", (party_id,))
            self.assertEqual(cur.fetchone()[0], 0, "a shared tenant reached a dedicated tenant's row")

    # -- the refusals (R4) ---------------------------------------------------------------

    def test_a_misdeclared_dedicated_database_is_refused(self):
        """INV-DEDI-MISROUTE-REFUSED-01 (keystone). A dedicated tenant pointed at a database whose
        placement_identity names a DIFFERENT tenant is refused by verify_connection_serves — a
        mis-configured ref becomes a loud failure, never a silent empty read from the wrong database."""
        other_tenant = str(uuid.uuid4())
        other_ref = f"mis{uuid.uuid4().hex[:8]}"
        with self.db.system_session() as cur:
            cur.execute(
                "INSERT INTO tenants (id, name, status, placement_kind, placement_ref) "
                "VALUES (%s, 'Misrouted Co', 'active', 'dedicated', %s)",
                (other_tenant, other_ref),
            )
        # Point this tenant's ref at the EXISTING dedicated database, which declares tenant_dedi.
        os.environ[f"{self.placement.DEDICATED_ENV_PREFIX}{other_ref}"] = self.dedicated_url
        try:
            with self.assertRaises(self.placement.PlacementUnresolved):
                with self.db.tenant_session(other_tenant) as cur:
                    cur.execute("SELECT 1")
        finally:
            os.environ.pop(f"{self.placement.DEDICATED_ENV_PREFIX}{other_ref}", None)
            with self.db.system_session() as cur:
                cur.execute("DELETE FROM tenants WHERE id = %s", (other_tenant,))

    def test_an_unconfigured_dedicated_tenant_is_refused(self):
        """INV-DEDI-UNCONFIGURED-REFUSED-01. A dedicated tenant with no BOPEN_DEDICATED_DB__<ref>
        configured is refused end to end, never defaulted into the shared pool."""
        lonely = str(uuid.uuid4())
        lonely_ref = f"non{uuid.uuid4().hex[:8]}"  # deliberately never set in the environment
        with self.db.system_session() as cur:
            cur.execute(
                "INSERT INTO tenants (id, name, status, placement_kind, placement_ref) "
                "VALUES (%s, 'Unconfigured Co', 'active', 'dedicated', %s)",
                (lonely, lonely_ref),
            )
        try:
            with self.assertRaises(self.placement.PlacementUnresolved):
                with self.db.tenant_session(lonely) as cur:
                    cur.execute("SELECT 1")
        finally:
            with self.db.system_session() as cur:
                cur.execute("DELETE FROM tenants WHERE id = %s", (lonely,))

    def test_the_dedicated_database_cannot_declare_a_second_tenant(self):
        """INV-DEDI-SINGLETON-01. placement_identity holds at most one row, so a provisioning bug
        cannot make a dedicated database claim to serve two tenants (a shared-by-accident dedicated
        database). The single-row primary key refuses the second declaration — asserted under the
        served tenant's own scope so it is the key, not the tenant-matching policy, that refuses."""
        conn = self._dedicated_conn()
        try:
            with self.assertRaises(self.psycopg.errors.Error):
                with self.db.tenant_session(self.tenant_dedi, connection=conn) as cur:
                    cur.execute(
                        "INSERT INTO placement_identity (tenant_id) VALUES (%s)",
                        (self.tenant_dedi,),
                    )
        finally:
            conn.close()

    def test_the_identity_is_invisible_to_another_tenants_scope(self):
        """INV-DEDI-IDENTITY-SCOPED-01. The tenant-matching policy (migration 015) keeps the
        declaration from being read under any scope but the served tenant's — so the served-tenant id
        is not exposed to another tenant's session. This is the tightening the verifier's adversarial
        probe on candidate ec14c53 established over the earlier permissive USING(true)."""
        conn = self._dedicated_conn()
        try:
            with self.db.tenant_session(self.tenant_dedi, connection=conn) as cur:
                cur.execute("SELECT count(*) FROM placement_identity")
                self.assertEqual(cur.fetchone()[0], 1, "the served tenant cannot read its own identity")
            other = str(uuid.uuid4())
            with self.db.tenant_session(other, connection=conn) as cur:
                cur.execute("SELECT count(*) FROM placement_identity")
                self.assertEqual(cur.fetchone()[0], 0, "another tenant's scope read the identity row")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
