"""MILE-4.2 Notification foundation (Stage 1) — tenant isolation, same-tenant composite-FK integrity,
append-only attempt/receipt evidence, per-tenant idempotency, and cross-provider receipt dedup, executed
against PostgreSQL (BOPEN-NOTIFY-001, DEC-P4-ENTRY §12).

Governed by DEC-P4-ENTRY §12, PLAN-NOTIFY-MIGRATE, ADR-NOTIFY-WQ v2.1 §1, BOPEN-TENANT-001, AGENTS.md
section 8. Admissibility: BOPEN-GOV-EBIV-001 R1 (executed SQL), R4 (adversarial negative probes), R5 (loud).

Every assertion runs real SQL against the live database with migration 021 applied. None would still
pass if the notification isolation policies, the composite foreign keys, the ON DELETE RESTRICT actions,
the append-only attempt/receipt policies, or the uniqueness constraints were dropped: a notification of
one tenant is unreadable in another, a cross-tenant dispatch/attempt/receipt attachment is refused by the
database, a recorded attempt/receipt resists direct mutation and a parent cascade, a notification with a
dispatch cannot be deleted, a duplicate idempotency_key per tenant is refused, and a redelivered
provider receipt collapses on the deterministic dedup key.

Stage 1 scope only: the tables, standard tenant RLS, and the append-only discipline. The elevated
worker/callback roles, the content-free USING(true) claim policy, the callback tables, and the
worker/adapter/endpoint runtime are DEFERRED to later stages and are not exercised here.
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


class TestNotificationEvidenceCanBeProduced(unittest.TestCase):
    """EBIV R5 — a check that cannot run reports failure, never silent success."""

    def test_notification_isolation_evidence_can_be_produced(self):
        reason = _unavailable_reason()
        self.assertIsNone(reason, msg=f"Notification isolation cannot be verified: {reason}")


@unittest.skipIf(_unavailable_reason() is not None, "database unavailable — reported by the guard test")
class TestNotificationIsolation(unittest.TestCase):
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

    # -- helpers -----------------------------------------------------------------------

    def _make_notification(
        self,
        tenant_id: str,
        idempotency_key: str | None = None,
        purpose: str = "transactional",
        channel: str = "email",
    ) -> str:
        key = idempotency_key or f"idem-{uuid.uuid4().hex}"
        with self.db.tenant_session(tenant_id, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO notifications (tenant_id, purpose, channel, idempotency_key) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (tenant_id, purpose, channel, key),
            )
            return str(cur.fetchone()[0])

    def _make_dispatch(self, tenant_id: str, notification_id: str) -> str:
        with self.db.tenant_session(tenant_id, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO notification_dispatch (tenant_id, notification_id, provider_id) "
                "VALUES (%s, %s, 'fake') RETURNING id",
                (tenant_id, notification_id),
            )
            return str(cur.fetchone()[0])

    def _make_attempt(self, tenant_id: str, dispatch_id: str, attempt_no: int = 1) -> None:
        with self.db.tenant_session(tenant_id, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO notification_attempt "
                "(tenant_id, dispatch_id, attempt_no, classified_outcome) "
                "VALUES (%s, %s, %s, 'provider_accepted')",
                (tenant_id, dispatch_id, attempt_no),
            )

    def _make_receipt(
        self,
        tenant_id: str,
        dispatch_id: str,
        provider_id: str = "fake",
        provider_message_id: str | None = None,
        dedup_key: str | None = None,
    ) -> None:
        # The dedup uniqueness is global (provider_id, provider_message_id, dedup_key) and rows persist
        # across tests on the disposable instance, so default to unique values; the dedup-collision test
        # passes explicit repeating values of its own.
        provider_message_id = provider_message_id or f"pm-{uuid.uuid4().hex}"
        dedup_key = dedup_key or f"dk-{uuid.uuid4().hex}"
        with self.db.tenant_session(tenant_id, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO notification_receipt "
                "(tenant_id, dispatch_id, provider_id, provider_message_id, normalized_status, dedup_key) "
                "VALUES (%s, %s, %s, %s, 'delivered', %s)",
                (tenant_id, dispatch_id, provider_id, provider_message_id, dedup_key),
            )

    # -- isolation ---------------------------------------------------------------------

    def test_a_notification_created_in_one_tenant_is_invisible_to_another(self):
        """NOTIFY-INV-01. Fails if tenant_isolation_notifications is dropped."""
        self._make_notification(self.tenant_a)
        with self.db.tenant_session(self.tenant_b, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM notifications")
            visible_to_b = cur.fetchone()[0]
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM notifications")
            visible_to_a = cur.fetchone()[0]
        self.assertEqual(visible_to_a, 1, "tenant A cannot see its own notification")
        self.assertEqual(visible_to_b, 0, "tenant B read tenant A's notification; isolation is off")

    def test_a_cross_tenant_notification_insert_is_refused(self):
        """NOTIFY-INV-01, write side. The WITH CHECK clause refuses writing another tenant's row."""
        with self.db.tenant_session(self.tenant_b, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute(
                    "INSERT INTO notifications (tenant_id, purpose, channel, idempotency_key) "
                    "VALUES (%s, 'transactional', 'email', 'x')",
                    (self.tenant_a,),
                )

    def test_a_dispatch_is_invisible_across_tenants(self):
        """NOTIFY-INV-01, dispatch surface."""
        n = self._make_notification(self.tenant_a)
        self._make_dispatch(self.tenant_a, n)
        with self.db.tenant_session(self.tenant_b, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM notification_dispatch")
            self.assertEqual(cur.fetchone()[0], 0, "tenant B read tenant A's dispatch")

    # -- cross-tenant composite-FK refusal ---------------------------------------------

    def test_a_dispatch_cannot_attach_to_another_tenants_notification(self):
        """Composite FK fk_dispatch_notification (tenant_id, notification_id) refuses a dispatch whose
        notification belongs to another tenant, at the database."""
        b_notif = self._make_notification(self.tenant_b)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute(
                    "INSERT INTO notification_dispatch (tenant_id, notification_id) VALUES (%s, %s)",
                    (self.tenant_a, b_notif),
                )

    def test_an_attempt_cannot_attach_to_another_tenants_dispatch(self):
        """Composite FK fk_attempt_dispatch refuses a cross-tenant attempt at the database."""
        b_notif = self._make_notification(self.tenant_b)
        b_dispatch = self._make_dispatch(self.tenant_b, b_notif)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute(
                    "INSERT INTO notification_attempt "
                    "(tenant_id, dispatch_id, attempt_no, classified_outcome) "
                    "VALUES (%s, %s, 1, 'provider_accepted')",
                    (self.tenant_a, b_dispatch),
                )

    def test_a_receipt_cannot_attach_to_another_tenants_dispatch(self):
        """Composite FK fk_receipt_dispatch refuses a cross-tenant receipt at the database."""
        b_notif = self._make_notification(self.tenant_b)
        b_dispatch = self._make_dispatch(self.tenant_b, b_notif)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute(
                    "INSERT INTO notification_receipt "
                    "(tenant_id, dispatch_id, provider_id, provider_message_id, normalized_status, "
                    " dedup_key) VALUES (%s, %s, 'fake', 'm', 'delivered', 'd')",
                    (self.tenant_a, b_dispatch),
                )

    # -- vocabulary CHECKs -------------------------------------------------------------

    def test_an_unknown_channel_is_refused(self):
        """chk_notification_channel refuses anything but email/phone."""
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.CheckViolation):
                cur.execute(
                    "INSERT INTO notifications (tenant_id, purpose, channel, idempotency_key) "
                    "VALUES (%s, 'transactional', 'carrier_pigeon', 'ck')",
                    (self.tenant_a,),
                )

    def test_an_unknown_dispatch_status_is_refused(self):
        """chk_dispatch_status refuses a status outside the closed state machine."""
        n = self._make_notification(self.tenant_a)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.CheckViolation):
                cur.execute(
                    "INSERT INTO notification_dispatch (tenant_id, notification_id, status) "
                    "VALUES (%s, %s, 'teleported')",
                    (self.tenant_a, n),
                )

    def test_an_unknown_attempt_outcome_is_refused(self):
        """chk_attempt_outcome enforces the closed four-class classifier vocabulary. terminal_unknown
        is a dispatch lifecycle floor, not an attempt outcome, so it too is refused here."""
        n = self._make_notification(self.tenant_a)
        d = self._make_dispatch(self.tenant_a, n)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.CheckViolation):
                cur.execute(
                    "INSERT INTO notification_attempt "
                    "(tenant_id, dispatch_id, attempt_no, classified_outcome) "
                    "VALUES (%s, %s, 1, 'terminal_unknown')",
                    (self.tenant_a, d),
                )

    # -- idempotency uniqueness (NOTIFY-INV-06) ----------------------------------------

    def test_a_duplicate_idempotency_key_per_tenant_is_refused(self):
        """unq_notification_idempotency refuses the same idempotency_key twice within one tenant."""
        self._make_notification(self.tenant_a, idempotency_key="same-key")
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.UniqueViolation):
                cur.execute(
                    "INSERT INTO notifications (tenant_id, purpose, channel, idempotency_key) "
                    "VALUES (%s, 'transactional', 'email', 'same-key')",
                    (self.tenant_a,),
                )

    def test_the_same_idempotency_key_is_allowed_in_a_different_tenant(self):
        """Positive control — idempotency uniqueness is per tenant, so the same key in tenant B is fine."""
        self._make_notification(self.tenant_a, idempotency_key="shared-key")
        n_b = self._make_notification(self.tenant_b, idempotency_key="shared-key")
        self.assertIsNotNone(n_b)

    # -- receipt dedup uniqueness (NOTIFY-INV-06/-10) -----------------------------------

    def test_a_duplicate_receipt_dedup_key_is_refused(self):
        """unq_receipt_dedup (provider_id, provider_message_id, dedup_key) is cross-tenant/cross-provider
        unique on purpose, so a redelivered callback collapses without depending on a nullable replay id.
        A second receipt with the same triple — even for a different dispatch — is refused."""
        pm = f"pm-{uuid.uuid4().hex}"
        dk = f"dk-{uuid.uuid4().hex}"
        n1 = self._make_notification(self.tenant_a)
        d1 = self._make_dispatch(self.tenant_a, n1)
        self._make_receipt(self.tenant_a, d1, provider_message_id=pm, dedup_key=dk)
        n2 = self._make_notification(self.tenant_a)
        d2 = self._make_dispatch(self.tenant_a, n2)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.UniqueViolation):
                cur.execute(
                    "INSERT INTO notification_receipt "
                    "(tenant_id, dispatch_id, provider_id, provider_message_id, normalized_status, "
                    " dedup_key) VALUES (%s, %s, 'fake', %s, 'delivered', %s)",
                    (self.tenant_a, d2, pm, dk),
                )

    # -- append-only attempt / receipt (NOTIFY-INV-12) ---------------------------------

    def test_a_recorded_attempt_cannot_be_updated_or_deleted(self):
        """notification_attempt grants SELECT and INSERT only, so UPDATE/DELETE reach zero rows whatever
        SQL is issued — the append-only discipline of workflow_history and the audit trail."""
        n = self._make_notification(self.tenant_a)
        d = self._make_dispatch(self.tenant_a, n)
        self._make_attempt(self.tenant_a, d)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("UPDATE notification_attempt SET classified_outcome = 'terminal_failed'")
            self.assertEqual(cur.rowcount, 0, "an attempt was updatable")
            cur.execute("DELETE FROM notification_attempt")
            self.assertEqual(cur.rowcount, 0, "an attempt was deletable")
            cur.execute("SELECT classified_outcome FROM notification_attempt WHERE dispatch_id = %s", (d,))
            self.assertEqual(cur.fetchone()[0], "provider_accepted", "the recorded attempt was altered")

    def test_a_recorded_receipt_cannot_be_updated_or_deleted(self):
        """notification_receipt is append-only the same way."""
        n = self._make_notification(self.tenant_a)
        d = self._make_dispatch(self.tenant_a, n)
        self._make_receipt(self.tenant_a, d)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("UPDATE notification_receipt SET normalized_status = 'bounced'")
            self.assertEqual(cur.rowcount, 0, "a receipt was updatable")
            cur.execute("DELETE FROM notification_receipt")
            self.assertEqual(cur.rowcount, 0, "a receipt was deletable")
            cur.execute("SELECT normalized_status FROM notification_receipt WHERE dispatch_id = %s", (d,))
            self.assertEqual(cur.fetchone()[0], "delivered", "the recorded receipt was altered")

    def test_a_recorded_attempt_survives_an_attempt_to_delete_its_dispatch(self):
        """NOTIFY-INV-12, the migration-014 lesson applied in advance. fk_attempt_dispatch is ON DELETE
        RESTRICT, so deleting a dispatch that has an attempt is refused and the evidence is untouched."""
        n = self._make_notification(self.tenant_a)
        d = self._make_dispatch(self.tenant_a, n)
        self._make_attempt(self.tenant_a, d)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute("DELETE FROM notification_dispatch WHERE id = %s", (d,))
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM notification_attempt WHERE dispatch_id = %s", (d,))
            self.assertEqual(cur.fetchone()[0], 1, "the recorded attempt was erased")

    def test_a_recorded_receipt_survives_an_attempt_to_delete_its_dispatch(self):
        """NOTIFY-INV-12. fk_receipt_dispatch is ON DELETE RESTRICT."""
        n = self._make_notification(self.tenant_a)
        d = self._make_dispatch(self.tenant_a, n)
        self._make_receipt(self.tenant_a, d)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute("DELETE FROM notification_dispatch WHERE id = %s", (d,))
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM notification_receipt WHERE dispatch_id = %s", (d,))
            self.assertEqual(cur.fetchone()[0], 1, "the recorded receipt was erased")

    # -- ON DELETE RESTRICT on the notification ----------------------------------------

    def test_a_notification_with_a_dispatch_cannot_be_deleted(self):
        """fk_dispatch_notification is ON DELETE RESTRICT: a notification that owns a dispatch cannot be
        deleted out from under it — retire it instead. Deleting a notification would otherwise cascade
        toward the dispatch and, through it, the append-only attempt/receipt evidence."""
        n = self._make_notification(self.tenant_a)
        self._make_dispatch(self.tenant_a, n)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute("DELETE FROM notifications WHERE id = %s", (n,))
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM notifications WHERE id = %s", (n,))
            self.assertEqual(cur.fetchone()[0], 1, "the notification was deleted out from under its dispatch")

    # -- tenant-scoped control tables --------------------------------------------------

    def test_control_rows_are_isolated_across_tenants(self):
        """Quota / suspension / fairness control rows are tenant-scoped by RLS like the rest."""
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO notification_quota (tenant_id, purpose, window_start, tokens_limit) "
                "VALUES (%s, 'transactional', date_trunc('minute', now()), 100)",
                (self.tenant_a,),
            )
            cur.execute("INSERT INTO notification_fairness (tenant_id) VALUES (%s)", (self.tenant_a,))
        with self.db.tenant_session(self.tenant_b, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM notification_quota")
            self.assertEqual(cur.fetchone()[0], 0, "tenant B read tenant A's quota row")
            cur.execute("SELECT count(*) FROM notification_fairness")
            self.assertEqual(cur.fetchone()[0], 0, "tenant B read tenant A's fairness cursor")


@unittest.skipIf(_unavailable_reason() is not None, "database unavailable — reported by the guard test")
class TestNotificationR5Guard(unittest.TestCase):
    """BOPEN-GOV-EBIV-001 R5 — the notification substrate is present and forced-RLS, so the isolation
    evidence above is real rather than vacuous. If migration 021 were not applied, these reads fail
    loudly rather than skipping into a false green."""

    @classmethod
    def setUpClass(cls):
        from platform_kernel import db

        cls.db = db

    def setUp(self):
        self.conn = self.db.connect(autocommit=True)

    def tearDown(self):
        self.conn.close()

    def test_every_notification_table_has_forced_row_level_security(self):
        """R5 / A-04. ENABLE alone leaves the table owner unconstrained; FORCE is what makes the
        isolation probes meaningful for the application role. Asserts the whole Stage 1 table set —
        the tenant-scoped tables and the platform provider-health control-plane table."""
        tables = (
            "notifications",
            "notification_dispatch",
            "notification_attempt",
            "notification_receipt",
            "notification_quota",
            "notification_quota_suspend",
            "notification_fairness",
            "notification_provider_health",
        )
        with self.db.system_session(connection=self.conn) as cur:
            for table in tables:
                enabled, forced = self.db.rls_is_active(cur, table)
                self.assertTrue(enabled, f"{table} does not have row level security enabled")
                self.assertTrue(forced, f"{table} does not FORCE row level security")


if __name__ == "__main__":
    unittest.main()
