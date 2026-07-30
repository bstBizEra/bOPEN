"""
The Phase 2 lifecycle audit envelope, made durable.

Work package: BOPEN-P35-001
Table: migration 005 `lifecycle_events`, plus the unscoped INSERT policy from 006
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed), R4 (adversarial), R5 (fails loudly)

`AuditDispatcher` appended to a Python list. Every Phase 2 audit record — invitation, membership
transition, SCIM provisioning, context switch, delegation — was therefore lost on restart and
differed per worker. An audit trail that does not survive the process it describes is not an
audit trail, and it is half the reason Phase 2 is undeployable rather than merely unverified.

The assertions worth reading are the ones about what happens at the edges: an event whose tenant
is not yet known, an event whose tenant value is neither a UUID nor a recognised sentinel, and
the append-only guarantee. The happy path proves the least.
"""

from __future__ import annotations

import os
import sys
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))
sys.path.insert(0, str(ROOT / "packages" / "kernel-core" / "python"))


def _unavailable_reason() -> str | None:
    try:
        import psycopg  # noqa: F401
    except ImportError:
        return "psycopg is not installed. Run: python -m pip install -r requirements.txt"
    if not os.environ.get("BOPEN_DATABASE_URL", "").strip():
        return "BOPEN_DATABASE_URL is not set. Run: python tools/db_bootstrap.py --apply"
    return None


class TestLifecycleAuditEvidenceAvailability(unittest.TestCase):
    """EBIV R5 — audit durability cannot be checked without a database, and this says so."""

    def test_lifecycle_audit_evidence_can_be_produced(self):
        reason = _unavailable_reason()
        self.assertIsNone(
            reason,
            msg=(
                "Lifecycle audit durability cannot be verified in this environment.\n\n"
                f"{reason}\n\nThis failure is intentional under BOPEN-GOV-EBIV-001 R5."
            ),
        )


@unittest.skipIf(
    _unavailable_reason() is not None,
    "database unavailable — reported as a failure by TestLifecycleAuditEvidenceAvailability",
)
class LifecycleAuditPersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from kernel_core.audit import AuditDispatcher
        from platform_kernel import db
        from platform_kernel.audit_repositories import (
            LifecycleEventPersistenceError,
            PostgresLifecycleEventSink,
        )

        cls.db = db
        cls.AuditDispatcher = AuditDispatcher
        cls.PersistenceError = LifecycleEventPersistenceError
        cls.sink = PostgresLifecycleEventSink()

    def setUp(self):
        self.tenant_a = str(uuid.uuid4())
        self.tenant_b = str(uuid.uuid4())
        with self.db.system_session() as cur:
            for tenant_id, name in ((self.tenant_a, "A"), (self.tenant_b, "B")):
                cur.execute(
                    "INSERT INTO tenants (id, name, status) VALUES (%s, %s, 'active')",
                    (tenant_id, name),
                )
        self.dispatcher = self.AuditDispatcher(self.sink)

    @staticmethod
    def _database_name() -> str:
        """The database the application connects to, taken from the application URL.

        Derived rather than hardcoded so this test follows a relocated verification database
        instead of silently probing the wrong one and reporting a missing table as a defect.
        """
        import re

        match = re.search(r"/([^/?]+)(?:\?.*)?$", os.environ["BOPEN_DATABASE_URL"])
        return match.group(1) if match else "bopen_dev"

    def _emit(self, tenant_id: str, **overrides):
        params = dict(
            event_type="invitation.issued",
            correlation_id=f"corr-{uuid.uuid4().hex[:12]}",
            actor_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            subject_type="invitation",
            subject_id=f"inv_{uuid.uuid4()}",
            outcome="success",
            reason_code="INVITATION_ISSUED",
        )
        params.update(overrides)
        return self.dispatcher.emit_lifecycle_event(**params)

    # -- durability ---------------------------------------------------------------

    def test_an_emitted_event_survives_the_dispatcher(self):
        """The whole point. Previously the record existed only in `dispatcher.logs`."""
        event = self._emit(self.tenant_a)

        stored = self.sink.list_for_tenant(self.tenant_a)
        matching = [row for row in stored if row["event_id"] == event["event_id"]]

        self.assertEqual(len(matching), 1, "the emitted event was not persisted")
        self.assertEqual(matching[0]["event_type"], "invitation.issued")
        self.assertEqual(matching[0]["outcome"], "success")
        self.assertEqual(matching[0]["reason_code"], "INVITATION_ISSUED")

    def test_a_tenant_cannot_read_another_tenants_audit_trail(self):
        """`list_for_tenant` has no tenant predicate; the policy scopes it.

        If this fails, the policy is not in force — and no care taken in the repository would
        compensate, because the query contains nothing to compensate with.
        """
        mine = self._emit(self.tenant_a)
        theirs = self._emit(self.tenant_b)

        visible = {row["event_id"] for row in self.sink.list_for_tenant(self.tenant_a)}

        self.assertIn(mine["event_id"], visible)
        self.assertNotIn(theirs["event_id"], visible, "tenant A read tenant B's audit record")

    # -- the edge migration 005 got wrong ----------------------------------------

    def test_an_event_with_no_resolved_tenant_is_still_written(self):
        """Migration 005 refused these rows outright and this test is why 006 exists.

        The producer emits `unknown` in the tenant position on paths that run before a tenant is
        resolved — a failed SSO assertion, for instance. 005's only INSERT policy required
        `tenant_id` to equal the session tenant, and `NULL = anything` is never true, so the
        record could not be written at all.

        These are precisely the audit records a post-incident review needs: the ones describing a
        failure that happened before anyone knew whose tenant it was.
        """
        event = self._emit("unknown", outcome="failure", reason_code="SSO_ASSERTION_INVALID")

        # Verified through an administrative connection, and that detail is the finding rather
        # than a test convenience. `db.system_session` runs as the unprivileged application role,
        # which is subject to FORCE ROW LEVEL SECURITY like every other role — so it cannot read
        # this row either. Only a connection that bypasses the policies can confirm the write.
        #
        # That is exactly the administrative path migration 005 records as not yet existing. The
        # first draft of this test read through `system_session` and failed, which is how the
        # limitation stopped being a sentence in a migration comment and became something the
        # suite demonstrates.
        admin_url = os.environ.get("BOPEN_ADMIN_DATABASE_URL", "").strip()
        if not admin_url:
            self.skipTest(
                "BOPEN_ADMIN_DATABASE_URL is not set; an unscoped row is unreadable without it"
            )

        import re

        import psycopg

        # The admin URL points at the maintenance database, because that is where CREATE DATABASE
        # has to run. Swapping the database name is the same thing `tools/db_bootstrap.py` does
        # for the same reason.
        target = re.sub(r"/[^/]*$", "/" + self._database_name(), admin_url)

        with psycopg.connect(target, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT tenant_id, tenant_scope, outcome FROM lifecycle_events "
                    "WHERE event_id = %s",
                    (event["event_id"],),
                )
                row = cur.fetchone()

        self.assertIsNotNone(row, "an unscoped lifecycle event was not written")
        self.assertIsNone(row[0], "an unscoped event was stored with a tenant identifier")
        self.assertEqual(row[1], "unknown")
        self.assertEqual(row[2], "failure")

    def test_an_unscoped_event_is_invisible_to_every_tenant(self):
        """Durable and unreadable is the intended state, not an accident.

        A pre-resolution event belongs to no tenant. Returning it to whichever tenant asked would
        be inventing an owner. Reading them needs an administrative path that does not exist yet,
        and that gap is recorded rather than closed by a policy that would guess.
        """
        self._emit("scoped", outcome="deny", reason_code="CONTEXT_REVOKED")

        for tenant_id in (self.tenant_a, self.tenant_b):
            rows = self.sink.list_for_tenant(tenant_id)
            self.assertTrue(
                all(row["reason_code"] != "CONTEXT_REVOKED" for row in rows),
                "an unscoped event was visible to a tenant",
            )

    def test_a_tenant_value_that_is_neither_uuid_nor_sentinel_is_refused(self):
        """Silence here would be the worst outcome available.

        A sink that swallowed what it could not write would produce a trail that looks complete.
        The refusal names the offending value and the recognised sentinels, because a caller
        hitting this needs to know which of the two mistakes it made.
        """
        with self.assertRaises(self.PersistenceError) as caught:
            self._emit("tnt_alpha")

        self.assertIn("tnt_alpha", str(caught.exception))

    # -- append-only --------------------------------------------------------------

    def test_a_persisted_audit_record_cannot_be_altered_or_removed(self):
        """Append-only by construction: migration 005 grants SELECT and INSERT and no others.

        UPDATE and DELETE reach zero rows whatever SQL is issued, so this asserts the outcome
        rather than the absence of a method.
        """
        event = self._emit(self.tenant_a)

        with self.db.tenant_session(self.tenant_a) as cur:
            cur.execute(
                "UPDATE lifecycle_events SET reason_code = 'TAMPERED' WHERE event_id = %s",
                (event["event_id"],),
            )
            self.assertEqual(cur.rowcount, 0, "an audit record was modified")

            cur.execute("DELETE FROM lifecycle_events WHERE event_id = %s", (event["event_id"],))
            self.assertEqual(cur.rowcount, 0, "an audit record was deleted")

    def test_the_producers_contract_checks_still_run_before_anything_is_written(self):
        """`AuditContractError` must fire before the sink sees the event.

        A record rejected by the producer must not reach storage, or the table would hold events
        the catalogue does not contain and the enum on `event_type` would be the only thing
        standing between the two.
        """
        from kernel_core.audit import AuditContractError

        before = len(self.sink.list_for_tenant(self.tenant_a))

        with self.assertRaises(AuditContractError):
            self._emit(self.tenant_a, event_type="not.a.real.event")
        with self.assertRaises(AuditContractError):
            self._emit(self.tenant_a, outcome="SUCCESS")

        self.assertEqual(
            len(self.sink.list_for_tenant(self.tenant_a)),
            before,
            "a contract-rejected event still reached storage",
        )

    def test_prohibited_metadata_is_refused_before_storage(self):
        """`AGENTS.md` §13. The dispatcher raises on credential-shaped keys; nothing is written.

        This is the guard that keeps a bearer token out of a queryable table, and it has to fire
        before the sink rather than after, because after is too late.
        """
        from kernel_core.audit import AuditContractError

        with self.assertRaises(AuditContractError):
            self._emit(self.tenant_a, metadata={"access_token": "eyJhbGciOiJI"})


if __name__ == "__main__":
    unittest.main()
