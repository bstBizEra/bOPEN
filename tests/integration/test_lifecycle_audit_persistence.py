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

    def _emit(self, tenant_id, **overrides):
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

        A producer that cannot resolve a tenant declares `tenant_scope="unknown"`. 005's only
        INSERT policy required `tenant_id` to equal the session tenant, and `NULL = anything` is
        never true, so the record could not be written at all.

        These are precisely the audit records a post-incident review needs: the ones describing a
        failure that happened before anyone knew whose tenant it was.

        This test used to read the row back through an administrative connection, because
        `db.system_session` runs as the unprivileged application role and is subject to FORCE ROW
        LEVEL SECURITY like every other role — so before migration 008 it could not read this row
        either, and only a connection bypassing the policies could confirm the write. That was
        the administrative gap migration 005 recorded and 006 restated, and it is what made the
        unscoped bucket a place evidence could be hidden. 008 closes it: unscoped rows are
        readable from a session that is itself unscoped. Reading through `system_session` here is
        the assertion that it did.
        """
        event = self._emit(
            None, tenant_scope="unknown", outcome="failure", reason_code="SSO_ASSERTION_INVALID"
        )

        with self.db.system_session() as cur:
            cur.execute(
                "SELECT tenant_id, tenant_scope, outcome FROM lifecycle_events "
                "WHERE event_id = %s",
                (event["event_id"],),
            )
            row = cur.fetchone()

        self.assertIsNotNone(
            row,
            "an unscoped lifecycle event was not readable from an unscoped session; migration "
            "008 is what makes this bucket reachable at all",
        )
        self.assertIsNone(row[0], "an unscoped event was stored with a tenant identifier")
        self.assertEqual(row[1], "unknown")
        self.assertEqual(row[2], "failure")

    def test_an_unscoped_event_is_invisible_to_every_tenant(self):
        """Durable and unreadable is the intended state, not an accident.

        A pre-resolution event belongs to no tenant. Returning it to whichever tenant asked would
        be inventing an owner. Migration 008 makes these rows readable from an unscoped session
        and deliberately not from a tenant one, so this assertion is what keeps 008 from having
        widened anything: it would fail if the new SELECT policy had omitted its unscoped-session
        condition and exposed every deployment-wide authentication failure to every tenant.
        """
        self._emit(None, tenant_scope="scoped", outcome="deny", reason_code="CONTEXT_REVOKED")

        for tenant_id in (self.tenant_a, self.tenant_b):
            rows = self.sink.list_for_tenant(tenant_id)
            self.assertTrue(
                all(row["reason_code"] != "CONTEXT_REVOKED" for row in rows),
                "an unscoped event was visible to a tenant",
            )

    def test_a_tenant_value_that_is_not_an_identifier_is_refused_not_rerouted(self):
        """Silence here would be the worst outcome available.

        A sink that swallowed what it could not write would produce a trail that looks complete.
        Rerouting is the second-worst: the sink used to send anything matching `unknown` or
        `scoped` to the unscoped bucket, and on the context-switch denial path that value is
        request body, so a caller could pick the destination of their own denial. Refusing loudly
        is the behaviour that leaves a producer defect visible.
        """
        with self.assertRaises(self.PersistenceError) as caught:
            self._emit("tnt_alpha")

        self.assertIn("tnt_alpha", str(caught.exception))

    def test_the_old_sentinel_string_no_longer_buys_a_different_destination(self):
        """The evasion, asserted directly.

        `unknown` in the tenant position, with the scope left at its default, must now be treated
        exactly like any other non-identifier: refused. It is one unresolvable string among
        infinitely many and has no special power. Declaring the scope is the only way to reach
        the unscoped bucket, and a request body cannot declare it.
        """
        for value in ("unknown", "scoped", "tnt_alpha", "not-a-uuid"):
            with self.subTest(value=value):
                with self.assertRaises(self.PersistenceError):
                    self._emit(value)

    def test_the_scope_vocabulary_is_identical_in_all_three_places_that_define_it(self):
        """
        The producer, the sink and the table each hold a copy of the same three values.

        Three copies are acceptable only while something proves they agree. If the producer
        gained a fourth scope the sink did not know, every event carrying it would fail to
        persist; if the table's CHECK constraint disagreed, it would fail at the INSERT instead.
        Both are outages in the audit path, which is the component least able to afford one.
        """
        from kernel_core.audit import TENANT_SCOPES
        from platform_kernel.audit_repositories import ALLOWED_TENANT_SCOPES

        self.assertEqual(set(TENANT_SCOPES), set(ALLOWED_TENANT_SCOPES))

        with self.db.system_session() as cur:
            cur.execute(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conname = 'chk_lifecycle_scope'"
            )
            row = cur.fetchone()

        self.assertIsNotNone(row, "chk_lifecycle_scope is missing from lifecycle_events")
        for scope in TENANT_SCOPES:
            self.assertIn(
                f"'{scope}'", row[0],
                f"the producer can emit {scope!r} but the table's CHECK constraint does not "
                f"permit it; every such event would fail to persist",
            )

    def test_an_event_built_without_a_declared_scope_is_refused(self):
        """
        `emit_lifecycle_event` always sets `tenant_scope`, so reaching the sink without one means
        something constructed the envelope by hand and bypassed the producer's checks. The sink
        refuses rather than assuming, because the assumption it would have to make is the routing
        decision that this whole change exists to take away from the caller.
        """
        event = self._emit(self.tenant_a)
        for missing in (None, "", "Tenant", "admin"):
            with self.subTest(scope=missing):
                raw = dict(event, event_id=str(uuid.uuid4()))
                if missing is None:
                    raw.pop("tenant_scope")
                else:
                    raw["tenant_scope"] = missing
                with self.assertRaises(self.PersistenceError):
                    self.sink.record(raw)

    def test_a_denied_switch_for_a_real_tenant_stays_in_that_tenants_trail(self):
        """
        The attack path itself, driven through the service rather than the sink.

        `ContextSwitchService._deny` audits with `command.tenant_id`, which is request body. It
        used to pass that value into the tenant position, and the sink routed on it — so naming
        your tenant `unknown` filed your own denial where no SELECT policy reached. The scope is
        now decided here by parsing, so both halves have to be asserted together: a denial naming
        a real tenant must land in that tenant's trail, and a denial naming an unresolvable one
        must land in the operator bucket and be readable there.

        Asserting only the second would pass against a producer that filed everything as
        unscoped, which is what made this the mutation that survived the first run.
        """
        from kernel_core.membership import InMemoryMembershipRepository
        from platform_kernel.context_service import (
            ContextDenied,
            ContextSwitchService,
            DeterministicTestSigner,
            InMemorySessionStore,
            SwitchContextCommand,
        )

        service = ContextSwitchService(
            memberships=InMemoryMembershipRepository(),
            sessions=InMemorySessionStore(),
            signer=DeterministicTestSigner(),
            audit=self.dispatcher,
            issuer="https://bopen.local/kernel",
            audience="https://bopen.local/api",
        )

        keys = {}
        for label, requested in (("real", self.tenant_a), ("magic", "unknown")):
            keys[label] = f"f3-{label}-{uuid.uuid4().hex[:10]}"
            with self.assertRaises(ContextDenied):
                service.switch(SwitchContextCommand(
                    session_id="sess-does-not-exist",
                    tenant_id=requested,
                    idempotency_key=keys[label],
                ))

        with self.db.tenant_session(self.tenant_a) as cur:
            cur.execute(
                "SELECT correlation_id, tenant_scope FROM lifecycle_events "
                "WHERE correlation_id IN (%s, %s)",
                (keys["real"], keys["magic"]),
            )
            in_tenant = dict(cur.fetchall())

        with self.db.system_session() as cur:
            cur.execute(
                "SELECT correlation_id, tenant_scope FROM lifecycle_events "
                "WHERE correlation_id IN (%s, %s)",
                (keys["real"], keys["magic"]),
            )
            in_operator = dict(cur.fetchall())

        self.assertEqual(
            in_tenant.get(keys["real"]), "tenant",
            "a denial naming a real tenant did not reach that tenant's audit trail; the "
            "producer is filing resolvable tenants as unscoped",
        )
        self.assertNotIn(
            keys["magic"], in_tenant,
            "an event with no resolvable tenant was shown to a tenant, which invents an owner",
        )
        self.assertEqual(
            in_operator.get(keys["magic"]), "unknown",
            "the denial the caller tried to file away is readable by nobody; this is the "
            "evasion, and migration 008 is what closes it",
        )

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
