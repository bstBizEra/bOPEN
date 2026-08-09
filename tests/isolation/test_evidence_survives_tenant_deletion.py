"""
A tenant holding append-only evidence cannot be deleted.

Work package: WP-P35-08 (Refusal Matrix R-1, R-2)
Governing artifacts: DEC-P4-NOTIFY-TENANT-CASCADE §6, §7; AGENTS.md §8, §14;
                     BOPEN-GOV-EBIV-001

Eleven tables across four foundations rely on an `ON DELETE RESTRICT` foreign key to their parent
row to make their evidence append-only. Every one of them also declares
`tenant_id REFERENCES tenants(id) ON DELETE CASCADE`. PostgreSQL performs foreign-key actions with
row security bypassed and follows the tenant edge first, so the RESTRICT edge is never consulted
and the evidence is erased.

Reproduced live by an independent verifier on the notification tables: the tenant delete
**succeeded** and `notification_attempt` and `notification_receipt` went to zero rows.

These tests are written BEFORE migration 022 and are expected to fail. They assert the behaviour the
migration must produce, one probe per table — R-1 requires eleven, not one representative. A single
table would prove the pattern works somewhere and say nothing about the other ten, which is how the
defect reached four foundations in the first place.

**R-2 is the safety valve and is not optional.** A migration that made *all* tenant deletion
impossible would satisfy R-1 completely and be wrong. The fix must refuse deletion only where
evidence exists.

Every tenant created here is disposable and is removed in teardown. Where a test leaves a tenant
undeletable by design, teardown removes the evidence first — otherwise this suite would accumulate
tenants it has itself made permanent.
"""

from __future__ import annotations

import os
import re
import sys
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))


@contextmanager
def cur_ctx(conn):
    with conn.cursor() as c:
        yield c


def _superuser_url() -> str | None:
    """Superuser credentials from the admin URL, pointed at the application database.

    The defect under test is reachable only by a role that bypasses row security. `bopen_app`
    cannot delete a tenant at all — `tenants` has no DELETE policy, so the statement reaches zero
    rows silently — which means a probe run as the application role would pass trivially and prove
    nothing (WP-P35-08 §11). The admin URL names the superuser but targets the administrative
    database, so the database name is taken from the application URL.
    """
    app = os.environ.get("BOPEN_DATABASE_URL", "").strip()
    adm = os.environ.get("BOPEN_ADMIN_DATABASE_URL", "").strip()
    pat = r"^(?P<scheme>\w+)://(?P<user>[^:]+):(?P<pw>[^@]+)@(?P<host>[^/]+)/(?P<db>[^?]+)"
    a, u = re.match(pat, app), re.match(pat, adm)
    if not (a and u):
        return None
    return f"{u['scheme']}://{u['user']}:{u['pw']}@{u['host']}/{a['db']}"


def _unavailable_reason() -> str | None:
    try:
        import psycopg  # noqa: F401
    except ImportError:
        return "psycopg is not installed. Run: python -m pip install -r requirements.txt"
    if not os.environ.get("BOPEN_DATABASE_URL", "").strip():
        return "BOPEN_DATABASE_URL is not set. Provision with `python tools/db_bootstrap.py --apply`."
    if _superuser_url() is None:
        return ("BOPEN_ADMIN_DATABASE_URL is not set or unparseable. The tenant-deletion path is "
                "reachable only by a superuser; without it this check cannot run.")
    return None


class TestTenantDeletionEvidenceCanBeProduced(unittest.TestCase):
    """EBIV R5 — a check that cannot run reports failure, never silent success."""

    def test_tenant_deletion_evidence_can_be_produced(self):
        reason = _unavailable_reason()
        self.assertIsNone(reason, msg=f"Tenant-deletion isolation cannot be verified: {reason}")


@unittest.skipIf(_unavailable_reason() is not None, "database unavailable — reported by the guard test")
class EvidenceSurvivesTenantDeletion(unittest.TestCase):
    """WP-P35-08 R-1 and R-2."""

    @classmethod
    def setUpClass(cls):
        from platform_kernel import db

        cls.db = db

    def setUp(self):
        import psycopg

        self.psycopg = psycopg
        self.conn = self.db.connect(autocommit=True)
        self.tenant = str(uuid.uuid4())
        self._evidence_tables: list[str] = []
        with psycopg.connect(_superuser_url(), autocommit=True) as c, c.cursor() as cur:
            cur.execute(
                "INSERT INTO tenants (id, name, status) VALUES (%s, %s, 'active')",
                (self.tenant, f"Disposable {self.tenant[:8]}"),
            )

    def tearDown(self):
        # Remove any evidence this test deliberately made undeletable, then the tenant itself.
        # Without this the suite would leave behind tenants it has made permanent by design.
        try:
            with self.psycopg.connect(_superuser_url(), autocommit=True) as c, cur_ctx(c) as cur:
                for table in reversed(self._evidence_tables):
                    cur.execute(f"DELETE FROM {table} WHERE tenant_id = %s", (self.tenant,))
                for table in ("notification_dispatch", "notifications", "workflow_instances",
                              "workflow_definitions",
                              "location_relationships", "location_history",
                              "location_address_versions", "location_geometry_observations",
                              "location_external_identifiers", "locations",
                              "party_contact_point_verification_events", "party_contact_points",
                              "parties"):
                    cur.execute(f"DELETE FROM {table} WHERE tenant_id = %s", (self.tenant,))
                cur.execute("DELETE FROM tenants WHERE id = %s", (self.tenant,))
        finally:
            self.conn.close()

    # -- parents -------------------------------------------------------------------------

    def _sys(self, sql: str, params: tuple):
        """Insert evidence through the ordinary tenant-scoped path, as the application would."""
        with self.db.tenant_session(self.tenant, connection=self.conn) as cur:
            cur.execute(sql, params)
            row = cur.fetchone() if cur.description else None
            return str(row[0]) if row else None

    def _party(self) -> str:
        return self._sys(
            "INSERT INTO parties (tenant_id, party_type, display_name) "
            "VALUES (%s, 'organization', 'Probe Co') RETURNING id", (self.tenant,))

    def _location(self, code: str = "L1") -> str:
        return self._sys(
            "INSERT INTO locations (tenant_id, code, name, location_type) "
            "VALUES (%s, %s, 'Probe Site', 'site') RETURNING id", (self.tenant, f"{code}-{uuid.uuid4().hex[:6]}"))

    def _notification(self) -> str:
        return self._sys(
            "INSERT INTO notifications (tenant_id, purpose, channel, idempotency_key) "
            "VALUES (%s, 'transactional', 'email', %s) RETURNING id",
            (self.tenant, f"idem-{uuid.uuid4().hex}"))

    def _dispatch(self) -> str:
        return self._sys(
            "INSERT INTO notification_dispatch (tenant_id, notification_id, provider_id) "
            "VALUES (%s, %s, 'probe') RETURNING id", (self.tenant, self._notification()))

    def _definition(self) -> str:
        return self._sys(
            "INSERT INTO workflow_definitions "
            "(tenant_id, name, initial_state, states, transitions) "
            "VALUES (%s, %s, 'open', %s, %s) RETURNING id",
            (self.tenant, f"probe-{uuid.uuid4().hex[:8]}",
             '["open","closed"]', '[{"from":"open","to":"closed"}]'))

    def _instance(self) -> str:
        return self._sys(
            "INSERT INTO workflow_instances (tenant_id, definition_id, current_state, subject_ref) "
            "VALUES (%s, %s, 'open', 'probe') RETURNING id", (self.tenant, self._definition()))

    def _contact_point(self) -> str:
        return self._sys(
            "INSERT INTO party_contact_points (tenant_id, party_id, endpoint_type, endpoint_value, purpose) "
            "VALUES (%s, %s, 'email', %s, 'transactional') RETURNING id",
            (self.tenant, self._party(), f"probe-{uuid.uuid4().hex[:8]}@example.invalid"))

    # -- evidence builders, one per protected table ---------------------------------------

    def _build(self, table: str) -> None:
        if table == "workflow_history":
            self._sys("INSERT INTO workflow_history (tenant_id, instance_id, from_state, to_state) "
                      "VALUES (%s, %s, 'open', 'closed')", (self.tenant, self._instance()))
        elif table == "party_contact_points":
            self._contact_point()
        elif table == "party_contact_point_verification_events":
            self._sys("INSERT INTO party_contact_point_verification_events "
                      "(tenant_id, contact_point_id, to_state, method) "
                      "VALUES (%s, %s, 'verified', 'administrative_assertion')",
                      (self.tenant, self._contact_point()))
        elif table == "location_address_versions":
            self._sys("INSERT INTO location_address_versions "
                      "(tenant_id, location_id, version_number, country_code, original_input) "
                      "VALUES (%s, %s, 1, 'TH', 'probe')", (self.tenant, self._location()))
        elif table == "location_geometry_observations":
            self._sys("INSERT INTO location_geometry_observations "
                      "(tenant_id, location_id, longitude, latitude) VALUES (%s, %s, 100.5, 13.7)",
                      (self.tenant, self._location()))
        elif table == "location_external_identifiers":
            self._sys("INSERT INTO location_external_identifiers (tenant_id, location_id, scheme, value) "
                      "VALUES (%s, %s, 'osm', %s)", (self.tenant, self._location(), f"w/{uuid.uuid4().hex[:6]}"))
        elif table == "location_relationships":
            self._sys("INSERT INTO location_relationships (tenant_id, from_location_id, to_location_id) "
                      "VALUES (%s, %s, %s)", (self.tenant, self._location("A"), self._location("B")))
        elif table == "location_history":
            self._sys("INSERT INTO location_history (tenant_id, location_id, event_type) "
                      "VALUES (%s, %s, 'created')", (self.tenant, self._location()))
        elif table == "notification_dispatch":
            self._dispatch()
        elif table == "notification_attempt":
            self._sys("INSERT INTO notification_attempt "
                      "(tenant_id, dispatch_id, attempt_no, classified_outcome) "
                      "VALUES (%s, %s, 1, 'provider_accepted')", (self.tenant, self._dispatch()))
        elif table == "notification_receipt":
            self._sys("INSERT INTO notification_receipt (tenant_id, dispatch_id, provider_id, "
                      "provider_message_id, normalized_status, dedup_key) "
                      "VALUES (%s, %s, 'probe', %s, 'delivered', %s)",
                      (self.tenant, self._dispatch(), uuid.uuid4().hex, uuid.uuid4().hex))
        else:  # pragma: no cover
            raise AssertionError(f"no builder for {table}")
        self._evidence_tables.append(table)

    def _delete_tenant(self):
        """Delete as superuser — the only role that can (WP-P35-08 §11)."""
        with self.psycopg.connect(_superuser_url(), autocommit=True) as c, c.cursor() as cur:
            cur.execute("DELETE FROM tenants WHERE id = %s", (self.tenant,))

    def _tenant_exists(self) -> bool:
        with self.psycopg.connect(_superuser_url(), autocommit=True) as c, c.cursor() as cur:
            cur.execute("SELECT count(*) FROM tenants WHERE id = %s", (self.tenant,))
            return cur.fetchone()[0] == 1

    # -- R-2: the safety valve -------------------------------------------------------------

    def test_R2_a_tenant_holding_no_evidence_is_still_deletable(self):
        """A fix that made all tenant deletion impossible would satisfy R-1 and be wrong."""
        self._delete_tenant()
        self.assertFalse(self._tenant_exists(), "a tenant with no evidence must remain deletable")


def _make_r1(table: str):
    def test(self):
        self._build(table)
        with self.assertRaises(
            self.psycopg.errors.ForeignKeyViolation,
            msg=f"deleting a tenant holding {table} rows must be refused, not silently cascade",
        ):
            self._delete_tenant()
        self.assertTrue(self._tenant_exists(), f"{table}: the tenant was deleted despite holding evidence")
    test.__doc__ = (
        f"R-1/{table}. The tenant edge must RESTRICT, not CASCADE. Fails while "
        f"{table}.tenant_id is ON DELETE CASCADE."
    )
    return test


# One probe per protected table. R-1 requires eleven; a representative would prove nothing
# about the other ten, which is how this defect reached four foundations.
for _t in (
    "workflow_history",
    "party_contact_points",
    "party_contact_point_verification_events",
    "location_address_versions",
    "location_geometry_observations",
    "location_external_identifiers",
    "location_relationships",
    "location_history",
    "notification_dispatch",
    "notification_attempt",
    "notification_receipt",
):
    setattr(EvidenceSurvivesTenantDeletion, f"test_R1_{_t}_blocks_tenant_deletion", _make_r1(_t))


if __name__ == "__main__":
    unittest.main()
