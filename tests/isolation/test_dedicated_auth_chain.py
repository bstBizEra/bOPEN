"""Option A — a dedicated tenant's auth chain works end to end (DEC-P35-TENANCY-MODEL §11).

Governed by DEC-P35-TENANCY-MODEL §11, PLAN-P35-06-DEDICATED-DB.
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed SQL across two databases), R4 (the chain that used to
be refused now completes, and the principal stays where it belongs), R5 (loud skip without admin).

The §10 slice proved a dedicated tenant's DOMAIN data routes to its own database, but a dedicated
tenant could not be *used*: `memberships`/`active_contexts`/`audit_events` foreign-key `principal_id`
to the global `principals`, and that FK cannot hold across the control/dedicated database split, so
membership creation raised ForeignKeyViolation. Migration 016 drops those three FKs (the migration-009
"survives its referent" pattern). These probes prove the chain now completes — membership and context
land in the dedicated database — while the principal stays global in control (not copied), which is
what makes principals multi-tenant.

The membership creation happens in setUpClass, so before migration 016 the whole class fails there
(loudly), which is the tests-first red: the onboarding cannot even be set up until the FK is dropped.
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
    return re.sub(r"/[^/?]+(\?|$)", f"/{database}\\1", app_url, count=1)


def corr() -> str:
    return f"corr_{uuid.uuid4()}"


class TestDedicatedAuthChainEvidenceCanBeProduced(unittest.TestCase):
    def test_dedicated_auth_chain_evidence_can_be_produced(self):
        reason = _unavailable_reason()
        self.assertIsNone(reason, msg=f"Dedicated auth chain cannot be verified: {reason}")


@unittest.skipIf(_unavailable_reason() is not None, "database unavailable — reported by the guard test")
class TestDedicatedAuthChain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from platform_kernel import db, repositories as repo
        from tools import provision_dedicated_db as prov

        cls.db = db
        cls.prov = prov
        cls.principals = repo.PrincipalRepository()
        cls.memberships = repo.MembershipRepository()
        cls.contexts = repo.ContextRepository()

        cls.control_url = os.environ["BOPEN_DATABASE_URL"]
        cls.admin_url = os.environ["BOPEN_ADMIN_DATABASE_URL"]
        cls.dedicated_db = f"bopen_dediauth_{uuid.uuid4().hex[:8]}"
        cls.dedicated_url = _sibling_url(cls.control_url, cls.dedicated_db)
        cls.tenant = str(uuid.uuid4())
        cls.ref = f"auth{uuid.uuid4().hex[:8]}"
        cls.env_key = f"BOPEN_DEDICATED_DB__{cls.ref}"

        prov.provision_dedicated_database(
            tenant_id=cls.tenant, tenant_name="Dedicated Auth Co", ref=cls.ref,
            target_url=cls.dedicated_url, admin_url=cls.admin_url, control_url=cls.control_url,
        )
        os.environ[cls.env_key] = cls.dedicated_url

        # Principal in the control database (global registry), as always. The membership then routes
        # to the dedicated database — the step that raised ForeignKeyViolation before migration 016.
        cls.principal = cls.principals.create(email=f"owner-{uuid.uuid4().hex[:8]}@example.com")
        cls.membership = cls.memberships.create(
            tenant_id=cls.tenant, principal_id=cls.principal.id, role="owner", state="active"
        )

    @classmethod
    def tearDownClass(cls):
        os.environ.pop(cls.env_key, None)
        try:
            cls.prov.drop_database(cls.dedicated_db, cls.admin_url)
        except Exception:
            pass
        try:
            with cls.db.system_session() as cur:
                cur.execute("DELETE FROM tenants WHERE id = %s", (cls.tenant,))
                cur.execute("DELETE FROM principals WHERE id = %s", (cls.principal.id,))
        except Exception:
            pass

    def test_a_dedicated_tenants_membership_lands_in_its_database(self):
        """INV-DEDI-AUTHCHAIN-01. The membership creation that used to raise ForeignKeyViolation now
        succeeds (in setUpClass) and lands in the dedicated database. Fails if migration 016 is rolled
        back — the FK would refuse the membership and setUpClass would error."""
        self.assertIsNotNone(self.membership.id)
        conn = self.db.connect(self.dedicated_url, autocommit=True)
        try:
            with self.db.tenant_session(self.tenant, connection=conn) as cur:
                cur.execute("SELECT count(*) FROM memberships WHERE id = %s", (self.membership.id,))
                self.assertEqual(cur.fetchone()[0], 1, "the membership is not in the dedicated DB")
        finally:
            conn.close()

    def test_the_principal_stays_global_in_control_and_is_not_copied(self):
        """INV-DEDI-AUTHCHAIN-02. Dropping the FK keeps principals global: the principal is in the
        control database and was NOT replicated into the dedicated database (which would break the
        multi-tenant principal model). Confirms Option A, not Option B."""
        conn_ctl = self.db.connect(self.control_url, autocommit=True)
        conn_ded = self.db.connect(self.dedicated_url, autocommit=True)
        try:
            with conn_ctl.cursor() as cur:
                cur.execute("SELECT count(*) FROM principals WHERE id = %s", (self.principal.id,))
                in_control = cur.fetchone()[0]
            with conn_ded.cursor() as cur:
                cur.execute("SELECT count(*) FROM principals WHERE id = %s", (self.principal.id,))
                in_dedicated = cur.fetchone()[0]
        finally:
            conn_ctl.close()
            conn_ded.close()
        self.assertEqual(in_control, 1, "the principal is not in the control registry")
        self.assertEqual(in_dedicated, 0, "the principal was copied into the dedicated DB (Option B)")

    def test_a_dedicated_tenant_can_establish_a_context(self):
        """INV-DEDI-AUTHCHAIN-03. With the membership in place, a context is established for the
        dedicated tenant — the full onboarding chain (principal -> membership -> context) completes,
        the context living in the dedicated database. active_contexts also FK'd principal_id before
        migration 016, so this is a second table the drop unblocks."""
        stored = self.contexts.establish(
            tenant_id=self.tenant,
            principal_id=self.principal.id,
            membership_id=self.membership.id,
            correlation_id=corr(),
        )
        self.assertIsNotNone(stored.id)
        conn = self.db.connect(self.dedicated_url, autocommit=True)
        try:
            with self.db.tenant_session(self.tenant, connection=conn) as cur:
                cur.execute("SELECT count(*) FROM active_contexts WHERE id = %s", (stored.id,))
                self.assertEqual(cur.fetchone()[0], 1, "the context is not in the dedicated DB")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
