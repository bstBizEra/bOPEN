"""Trial→paid tenant migration — moving an existing shared-pool tenant to a dedicated database.

Governed by DEC-P35-TENANCY-MODEL §12, PLAN-P35-06-TRIAL-TO-PAID.
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed SQL across two databases), R4 (the negatives — the
freeze refuses, a verification mismatch refuses cutover, no row is left behind or duplicated), R5.

The pair `test_migration_moves_all_rows...` + `test_migrated_rows_are_gone_from_the_shared_pool`
together mean *moved, not copied and not lost*. `test_a_verification_mismatch_leaves_the_tenant_on_
the_shared_pool` is the one that makes the operation safe to attempt. `test_copy_order_covers_every_
tenant_scoped_table` is the control against silent data loss: a tenant-scoped table added later but
not to the migrate tool fails here.
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


class TestTrialToPaidEvidenceCanBeProduced(unittest.TestCase):
    def test_trial_to_paid_evidence_can_be_produced(self):
        reason = _unavailable_reason()
        self.assertIsNone(reason, msg=f"Trial→paid migration cannot be verified: {reason}")


class TestCopyOrderCoverage(unittest.TestCase):
    """No database needed — a structural control that the migrate tool copies every tenant-scoped
    table. This is the guard against silent data loss and runs even without the admin credential."""

    def test_copy_order_covers_every_tenant_scoped_table(self):
        from tools import migrate_tenant_to_dedicated as migrate
        from tests.isolation.test_rls_database_behavior import TENANT_SCOPED_TABLES

        self.assertEqual(
            set(migrate.COPY_ORDER), set(TENANT_SCOPED_TABLES),
            "the migrate tool's COPY_ORDER and the RLS-classified tenant-scoped tables disagree; a "
            "tenant-scoped table added without being added to COPY_ORDER would be silently left "
            "behind in the shared pool (data loss), or a non-tenant table would be wrongly copied",
        )


@unittest.skipIf(_unavailable_reason() is not None, "database unavailable — reported by the guard test")
class TestTrialToPaidMigration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from platform_kernel import db, repositories as repo
        from tools import migrate_tenant_to_dedicated as migrate
        from tools import provision_dedicated_db as prov

        cls.db = db
        cls.migrate = migrate
        cls.prov = prov
        cls.control_url = os.environ["BOPEN_DATABASE_URL"]
        cls.admin_url = os.environ["BOPEN_ADMIN_DATABASE_URL"]
        cls.dedicated_db = f"bopen_t2p_{uuid.uuid4().hex[:8]}"
        cls.dedicated_url = _sibling_url(cls.control_url, cls.dedicated_db)
        cls.tenant = str(uuid.uuid4())
        cls.ref = f"t2p{uuid.uuid4().hex[:8]}"
        cls.env_key = f"BOPEN_DEDICATED_DB__{cls.ref}"

        # A shared-pool tenant with data across several tables.
        with db.system_session() as cur:
            cur.execute(
                "INSERT INTO tenants (id, name, status) VALUES (%s, 'Upgrading Co', 'active')",
                (cls.tenant,),
            )
        cls.principal = repo.PrincipalRepository().create(
            email=f"owner-{uuid.uuid4().hex[:8]}@example.com"
        )
        cls.membership = repo.MembershipRepository().create(
            tenant_id=cls.tenant, principal_id=cls.principal.id, role="owner", state="active"
        )
        with db.tenant_session(cls.tenant) as cur:  # routes to shared (tenant is shared_pool)
            cur.execute(
                "INSERT INTO parties (tenant_id, party_type, display_name) "
                "VALUES (%s, 'organization', 'A Customer') RETURNING id",
                (cls.tenant,),
            )
            cls.party_id = str(cur.fetchone()[0])
            cur.execute(
                "INSERT INTO exchange_rates (tenant_id, from_currency, to_currency, rate) "
                "VALUES (%s, 'USD', 'THB', 34.50)",
                (cls.tenant,),
            )

        # Snapshot the per-table shared counts before migrating.
        cls.snapshot = {}
        conn = db.connect(cls.control_url)
        try:
            with db.tenant_session(cls.tenant, connection=conn) as cur:
                for table in migrate.COPY_ORDER:
                    cur.execute(f"SELECT count(*) FROM {table}")
                    cls.snapshot[table] = cur.fetchone()[0]
        finally:
            conn.close()

        # Migrate.
        cls.result = migrate.migrate_tenant_to_dedicated(
            tenant_id=cls.tenant, tenant_name="Upgrading Co", ref=cls.ref,
            target_url=cls.dedicated_url, admin_url=cls.admin_url, control_url=cls.control_url,
        )
        os.environ[cls.env_key] = cls.dedicated_url

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

    def test_migration_moves_all_rows_to_the_dedicated_database(self):
        """INV-MIGRATE-COMPLETE-01. Every tenant-scoped row is in the dedicated database — per-table
        counts equal the pre-migration snapshot."""
        conn = self.db.connect(self.dedicated_url)
        try:
            with self.db.tenant_session(self.tenant, connection=conn) as cur:
                for table, expected in self.snapshot.items():
                    cur.execute(f"SELECT count(*) FROM {table}")
                    self.assertEqual(
                        cur.fetchone()[0], expected,
                        f"{table}: dedicated has a different row count than the shared snapshot",
                    )
        finally:
            conn.close()
        # Sanity: the tenant actually had data to move.
        self.assertGreaterEqual(self.snapshot["parties"], 1)
        self.assertGreaterEqual(self.snapshot["memberships"], 1)

    def test_migrated_rows_are_gone_from_the_shared_pool(self):
        """INV-MIGRATE-NO-DUPLICATION-01. After cleanup, the tenant's rows are gone from the shared
        pool — no row exists in both databases."""
        conn = self.db.connect(self.control_url)
        try:
            with self.db.tenant_session(self.tenant, connection=conn) as cur:
                for table in self.migrate.COPY_ORDER:
                    cur.execute(f"SELECT count(*) FROM {table}")
                    self.assertEqual(
                        cur.fetchone()[0], 0,
                        f"{table}: the tenant's rows are still in the shared pool (duplication)",
                    )
        finally:
            conn.close()

    def test_after_cutover_the_tenant_routes_to_the_dedicated_database(self):
        """INV-MIGRATE-CUTOVER-ROUTES-01. A tenant_session now resolves to the dedicated database and
        reads the migrated data — the cutover flipped the routing."""
        with self.db.tenant_session(self.tenant) as cur:  # resolves placement — must be dedicated now
            cur.execute("SELECT display_name FROM parties WHERE id = %s", (self.party_id,))
            row = cur.fetchone()
        self.assertIsNotNone(row, "the migrated party is not readable through the routed session")
        self.assertEqual(row[0], "A Customer")

    def test_the_principal_stays_in_control_and_is_not_moved(self):
        """INV-MIGRATE-PRINCIPALS-UNTOUCHED-01. The principal is global: it stays in control and is
        not moved or duplicated into the dedicated database (Option A holds through a migration)."""
        conn_ctl = self.db.connect(self.control_url)
        conn_ded = self.db.connect(self.dedicated_url)
        try:
            with conn_ctl.cursor() as cur:
                cur.execute("SELECT count(*) FROM principals WHERE id = %s", (self.principal.id,))
                self.assertEqual(cur.fetchone()[0], 1, "principal missing from control")
            with conn_ded.cursor() as cur:
                cur.execute("SELECT count(*) FROM principals WHERE id = %s", (self.principal.id,))
                self.assertEqual(cur.fetchone()[0], 0, "principal was moved/copied to the dedicated DB")
        finally:
            conn_ctl.close()
            conn_ded.close()


@unittest.skipIf(_unavailable_reason() is not None, "database unavailable — reported by the guard test")
class TestMigrationFreezeAndRollback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from platform_kernel import db
        from tools import migrate_tenant_to_dedicated as migrate

        cls.db = db
        cls.migrate = migrate
        cls.control_url = os.environ["BOPEN_DATABASE_URL"]

    def _shared_tenant_with_a_party(self):
        from platform_kernel import repositories as repo

        tenant = str(uuid.uuid4())
        with self.db.system_session() as cur:
            cur.execute(
                "INSERT INTO tenants (id, name, status) VALUES (%s, 'Freeze Co', 'active')",
                (tenant,),
            )
        with self.db.tenant_session(tenant) as cur:
            cur.execute(
                "INSERT INTO parties (tenant_id, party_type, display_name) "
                "VALUES (%s, 'organization', 'Before Migration')",
                (tenant,),
            )
        return tenant

    def test_a_verification_mismatch_leaves_the_tenant_on_the_shared_pool(self):
        """INV-MIGRATE-ROLLBACK-SAFE-01. A failure before cutover (here, verification) leaves the
        tenant fully on the shared pool with its data intact and the freeze cleared."""
        tenant = self._shared_tenant_with_a_party()
        try:
            # Force verification to fail — the migration must abort before cutover.
            original = self.migrate._verify_counts
            self.migrate._verify_counts = lambda *a, **k: (_ for _ in ()).throw(
                RuntimeError("injected verification mismatch")
            )
            dedicated_db = f"bopen_rb_{uuid.uuid4().hex[:8]}"
            dedicated_url = _sibling_url(self.control_url, dedicated_db)
            try:
                with self.assertRaises(RuntimeError):
                    self.migrate.migrate_tenant_to_dedicated(
                        tenant_id=tenant, tenant_name="Freeze Co", ref=f"rb{uuid.uuid4().hex[:6]}",
                        target_url=dedicated_url,
                        admin_url=os.environ["BOPEN_ADMIN_DATABASE_URL"],
                        control_url=self.control_url,
                    )
            finally:
                self.migrate._verify_counts = original
                try:
                    self.migrate.prov.drop_database(dedicated_db, os.environ["BOPEN_ADMIN_DATABASE_URL"])
                except Exception:
                    pass

            # The tenant is still on the shared pool, unfrozen, with its data.
            with self.db.system_session() as cur:
                cur.execute(
                    "SELECT placement_kind, placement_state FROM tenants WHERE id = %s", (tenant,)
                )
                kind, state = cur.fetchone()
            self.assertEqual(kind, "shared_pool", "the tenant was cut over despite a failure")
            self.assertEqual(state, "stable", "the freeze was left on after a failed migration")
            with self.db.tenant_session(tenant) as cur:  # still routes to shared
                cur.execute("SELECT count(*) FROM parties")
                self.assertEqual(cur.fetchone()[0], 1, "the tenant's data was lost on a failed migration")
        finally:
            with self.db.system_session() as cur:
                cur.execute("DELETE FROM tenants WHERE id = %s", (tenant,))

    def test_the_freeze_covers_the_data_chokepoint_not_just_http(self):
        """INV-MIGRATE-FREEZE-DATA-PATH-01. The freeze is enforced at `db.tenant_session` — the
        chokepoint every write path passes through — not only at the HTTP layer. A verifier reproduced
        a data loss on candidate 2a253a5 where a `tenant_session` write that bypassed the HTTP-only
        freeze committed to the shared pool after the copy and was then deleted by cleanup, leaving
        zero copies in either database. This asserts a migrating tenant's `tenant_session` is now
        refused, closing that path; the migrate tool is unaffected because it uses superuser raw
        connections, not `tenant_session`."""
        from platform_kernel import db as dbmod

        tenant = self._shared_tenant_with_a_party()
        try:
            with self.db.system_session() as cur:
                cur.execute("UPDATE tenants SET placement_state = 'migrating' WHERE id = %s", (tenant,))

            # Branch 1 — the resolved-connection path (connection is None).
            with self.assertRaises(dbmod.TenantMigratingError):
                with self.db.tenant_session(tenant) as cur:
                    cur.execute(
                        "INSERT INTO parties (tenant_id, party_type, display_name) "
                        "VALUES (%s, 'person', 'late write via resolution path')",
                        (tenant,),
                    )

            # Branch 2 — the SUPPLIED-connection path (connection=X). This is the path a verifier
            # reproduced on candidate 6fdb8e9: it skipped a freeze placed only in the resolution
            # branch. entitlement_repositories and others pass connection=X, so it must be frozen too.
            supplied = self.db.connect(self.control_url, autocommit=True)
            try:
                with self.assertRaises(dbmod.TenantMigratingError):
                    with self.db.tenant_session(tenant, connection=supplied) as cur:
                        cur.execute(
                            "INSERT INTO parties (tenant_id, party_type, display_name) "
                            "VALUES (%s, 'person', 'late write via supplied connection')",
                            (tenant,),
                        )
            finally:
                supplied.close()
        finally:
            with self.db.system_session() as cur:
                cur.execute("UPDATE tenants SET placement_state = 'stable' WHERE id = %s", (tenant,))
                cur.execute("DELETE FROM tenants WHERE id = %s", (tenant,))

    def test_a_migrating_tenant_is_frozen_at_the_request_path(self):
        """INV-MIGRATE-FREEZE-REFUSES-01. While a tenant is `migrating`, the kernel refuses its
        requests with 503, so no write lands in the source database after the snapshot."""
        if not os.environ.get("BOPEN_CONTEXT_TOKEN_KEY", "").strip():
            self.skipTest("BOPEN_CONTEXT_TOKEN_KEY not set; the HTTP freeze path cannot be exercised")
        from fastapi.testclient import TestClient
        from platform_kernel.api import app

        client = TestClient(app, raise_server_exceptions=False)

        def hdr(token=None):
            h = {"X-Correlation-ID": f"corr_{uuid.uuid4()}"}
            if token:
                h["Authorization"] = f"Bearer {token}"
            return h

        p = client.post("/v1/principals", json={"email": f"f-{uuid.uuid4().hex[:8]}@e.com", "type": "human"}, headers=hdr())
        pid = p.json()["principal_id"]
        t = client.post("/v1/tenants", json={"name": "FreezeHttp", "owner_principal_id": pid}, headers=hdr())
        tid = t.json()["tenant_id"]
        ctx = client.post(
            "/v1/contexts",
            json={"principal_id": pid, "membership_id": t.json()["owner_membership_id"]},
            headers={**hdr(), "X-Tenant-ID": tid},
        )
        token = ctx.json()["access_token"]

        # Before the freeze: a bearer-gated request works.
        ok = client.post("/v1/parties", json={"party_type": "person", "display_name": "ok"}, headers=hdr(token))
        self.assertEqual(ok.status_code, 201, ok.text)

        # Freeze the tenant, then the same request is refused with 503.
        with self.db.system_session() as cur:
            cur.execute("UPDATE tenants SET placement_state = 'migrating' WHERE id = %s", (tid,))
        try:
            frozen = client.post(
                "/v1/parties", json={"party_type": "person", "display_name": "blocked"}, headers=hdr(token)
            )
            self.assertEqual(frozen.status_code, 503, f"a migrating tenant's request was not frozen: {frozen.text}")
        finally:
            with self.db.system_session() as cur:
                cur.execute("UPDATE tenants SET placement_state = 'stable' WHERE id = %s", (tid,))
                cur.execute("DELETE FROM tenants WHERE id = %s", (tid,))
                cur.execute("DELETE FROM principals WHERE id = %s", (pid,))


if __name__ == "__main__":
    unittest.main()
