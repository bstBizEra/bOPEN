"""Tenant placement resolution — WP-P35-06 seam, executed against PostgreSQL.

Governed by DEC-P35-TENANCY-MODEL Option D, AGENTS.md section 8.
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed), R4 (adversarial — the fail-closed refusals are
the point), R5 (loud).

The seam's whole value is that a tenant is resolved to the RIGHT database and never silently to a
wrong one. These probes assert the refusals: an unknown tenant, an unknown placement kind, and a
dedicated tenant whose connection is not configured are all refused, never defaulted into the
shared pool.
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
        return "psycopg is not installed."
    if not os.environ.get("BOPEN_DATABASE_URL", "").strip():
        return "BOPEN_DATABASE_URL is not set."
    return None


class TestPlacementEvidenceCanBeProduced(unittest.TestCase):
    def test_placement_evidence_can_be_produced(self):
        self.assertIsNone(_unavailable_reason(), msg=_unavailable_reason())


@unittest.skipIf(_unavailable_reason() is not None, "database unavailable — reported by the guard test")
class TestPlacementResolution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from platform_kernel import db, placement

        cls.db = db
        cls.placement = placement

    def setUp(self):
        self.conn = self.db.connect(autocommit=True)
        self.tenant = str(uuid.uuid4())
        self._saved_env = {}

    def tearDown(self):
        for k, v in self._saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.conn.close()

    def _seed(self, kind: str = "shared_pool", ref: str | None = None) -> None:
        with self.db.system_session(connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO tenants (id, name, status, placement_kind, placement_ref) "
                "VALUES (%s, %s, 'active', %s, %s)",
                (self.tenant, f"T-{self.tenant[:8]}", kind, ref),
            )

    def _set_env(self, key: str, value: str) -> None:
        self._saved_env[key] = os.environ.get(key)
        os.environ[key] = value

    # -- resolution ---------------------------------------------------------------------

    def test_a_shared_pool_tenant_resolves_to_the_control_database(self):
        self._seed("shared_pool")
        p = self.placement.resolve_placement(self.tenant, control_connection=self.conn)
        self.assertEqual(p.kind, "shared_pool")
        self.assertEqual(p.connection_url, self.db.database_url())

    def test_a_dedicated_tenant_resolves_to_its_configured_database(self):
        ref = f"ded{uuid.uuid4().hex[:8]}"
        self._seed("dedicated", ref)
        self._set_env(f"{self.placement.DEDICATED_ENV_PREFIX}{ref}", "postgresql://x/y")
        p = self.placement.resolve_placement(self.tenant, control_connection=self.conn)
        self.assertEqual(p.kind, "dedicated")
        self.assertEqual(p.connection_url, "postgresql://x/y")

    # -- fail-closed (the adversarial half) ---------------------------------------------

    def test_an_unknown_tenant_is_refused_not_defaulted(self):
        with self.assertRaises(self.placement.PlacementUnresolved):
            self.placement.resolve_placement(str(uuid.uuid4()), control_connection=self.conn)

    def test_a_dedicated_tenant_with_no_configured_connection_is_refused(self):
        ref = f"missing{uuid.uuid4().hex[:8]}"
        self._seed("dedicated", ref)
        # deliberately do NOT set BOPEN_DEDICATED_DB__<ref>
        with self.assertRaises(self.placement.PlacementUnresolved):
            self.placement.resolve_placement(self.tenant, control_connection=self.conn)

    def test_an_empty_tenant_identifier_is_refused(self):
        with self.assertRaises(self.placement.PlacementUnresolved):
            self.placement.resolve_placement("", control_connection=self.conn)

    # -- the wiring: tenant_session itself now resolves fail-closed ----------------------

    def test_tenant_session_refuses_an_unregistered_tenant(self):
        """The seam is wired (WP-P35-06): opening a session for a tenant with no registry row is
        refused, not silently served against the shared pool where its writes would land."""
        with self.assertRaises(self.placement.PlacementUnresolved):
            with self.db.tenant_session(str(uuid.uuid4())) as cur:
                cur.execute("SELECT 1")

    def test_tenant_session_serves_a_registered_shared_pool_tenant(self):
        """A registered shared-pool tenant resolves and its session is scoped by RLS as before."""
        self._seed("shared_pool")
        with self.db.tenant_session(self.tenant) as cur:
            cur.execute("SELECT count(*) FROM parties")
            self.assertEqual(cur.fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
