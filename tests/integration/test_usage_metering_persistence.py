"""
Usage metering, transactional outbox and quota reservations executed against PostgreSQL.

Work package: BOPEN-P35-001
Governing findings: F-3 (the outbox was a Python list that `dispatch_outbox` cleared)
                    F-2 residue (a reservation held nothing, and expiry was never compared
                    to the present instant)
Governing artifacts: BOPEN-TENANT-001, BOPEN-ENT-001, AGENTS.md section 8
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed), R4 (adversarial), R5 (fails loudly)

Every assertion here runs real SQL against a real PostgreSQL instance with the migrations in
`infrastructure/database/` applied. Nothing simulates a policy or a constraint. The suite that
existed before this file asserted the same behaviours against Python dictionaries, where a
unique index, a CHECK constraint and a row-level security policy are all equally unfalsifiable.

Running:
    python tools/db_bootstrap.py --apply
    export BOPEN_DATABASE_URL="postgresql://bopen_app:<password>@127.0.0.1:5433/bopen_dev"
    python tools/run_tests.py

If BOPEN_DATABASE_URL is unset these tests FAIL rather than skip, for the reason recorded in
`tests/isolation/test_rls_database_behavior.py`: a skipped check and a passing check look
identical in a summary line.

Every test allocates fresh tenant UUIDs and never deletes or truncates, so the suite is safe to
run against a database shared with other work.
"""

from __future__ import annotations

import json
import os
import sys
import unittest
import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone
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
        return (
            "BOPEN_DATABASE_URL is not set. Provision a verification database with "
            "`python tools/db_bootstrap.py --apply` and export the URL it prints."
        )
    return None


class TestMeteringPersistenceAvailability(unittest.TestCase):
    """Guard test — an environment that cannot execute these checks produces a red suite."""

    def test_metering_evidence_can_be_produced(self):
        reason = _unavailable_reason()
        self.assertIsNone(
            reason,
            msg=(
                "Usage metering persistence cannot be verified in this environment, so no "
                f"admissible evidence exists for it.\n\n{reason}\n\n"
                "Under BOPEN-GOV-EBIV-001 R5 a check that cannot run reports failure."
            ),
        )


@unittest.skipIf(
    _unavailable_reason() is not None,
    "database unavailable — reported as a failure by TestMeteringPersistenceAvailability",
)
class UsageOutboxPersistenceTests(unittest.TestCase):
    """F-3. The outbox is a table with a unique constraint, not a list in one process."""

    @classmethod
    def setUpClass(cls):
        from platform_kernel import db
        from platform_kernel import metering

        cls.db = db
        cls.metering = metering

    def setUp(self):
        self.service = self.metering.UsageMeterService()
        # Canonical lowercase UUID text: migration 004 constrains these columns to exactly
        # that shape, and identifiers are passed through unchanged.
        self.tenant_a = str(uuid.uuid4())
        self.tenant_b = str(uuid.uuid4())
        # Fixed per test: a replay is the *same* request arriving twice, so varying the
        # principal between calls would exercise the payload-conflict guard instead.
        self.principal = str(uuid.uuid4())
        self.context = str(uuid.uuid4())

    def _record(self, tenant_id: str, key: str, **overrides):
        params = dict(
            tenant_id=tenant_id,
            principal_id=self.principal,
            context_id=self.context,
            capability_id="cap_monthly_leases",
            quantity=1,
            unit=self.metering.MeteredUnit.REQUESTS,
            correlation_id="corr-outbox-1",
            idempotency_key=key,
        )
        params.update(overrides)
        return self.service.record_event(**params)

    def test_event_is_written_to_the_outbox_table(self):
        key = f"idemp-{uuid.uuid4()}"
        event = self._record(self.tenant_a, key)

        stored = self.service.get_outbox_events(self.tenant_a)
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].event_id, event.event_id)
        self.assertEqual(stored[0].idempotency_key, key)
        self.assertIsNone(
            stored[0].dispatched_at, "a freshly recorded event has not been dispatched"
        )

    def test_replay_returns_the_stored_row_and_writes_no_second_row(self):
        """
        The replay guard is `UNIQUE (tenant_id, idempotency_key)`, so it holds across
        processes and across restarts. The dictionary it replaces held for the lifetime of one
        interpreter, which is why two workers behind a load balancer deduplicated nothing.
        """
        key = f"idemp-{uuid.uuid4()}"
        first = self._record(self.tenant_a, key)
        second = self._record(self.tenant_a, key)

        self.assertEqual(second.event_id, first.event_id)
        self.assertEqual(second.timestamp, first.timestamp, "a replay must not restamp time")
        self.assertEqual(len(self.service.get_outbox_events(self.tenant_a)), 1)

    def test_replay_with_a_different_payload_is_refused(self):
        key = f"idemp-{uuid.uuid4()}"
        self._record(self.tenant_a, key, quantity=1)

        with self.assertRaises(self.metering.IdempotencyPayloadConflictError):
            self._record(self.tenant_a, key, quantity=99)

        self.assertEqual(len(self.service.get_outbox_events(self.tenant_a)), 1)

    def test_a_second_tenant_may_use_the_same_key_and_neither_sees_the_other(self):
        """
        The former guard was a process-global dictionary keyed on the idempotency key alone.
        It made one tenant's write fail because of another tenant's data, and its message
        named the owning tenant — disclosing both that another tenant exists and which one.

        The unique constraint is on `(tenant_id, idempotency_key)`. Two tenants may hold the
        same key, each sees only its own row, and neither can learn that the other exists.
        This assertion would fail if the constraint were ever widened to the key alone.
        """
        key = f"idemp-{uuid.uuid4()}"
        event_a = self._record(self.tenant_a, key)
        event_b = self._record(self.tenant_b, key)

        self.assertNotEqual(event_a.event_id, event_b.event_id)

        visible_to_a = self.service.get_outbox_events(self.tenant_a)
        visible_to_b = self.service.get_outbox_events(self.tenant_b)
        self.assertEqual([r.event_id for r in visible_to_a], [event_a.event_id])
        self.assertEqual([r.event_id for r in visible_to_b], [event_b.event_id])

    def test_unset_tenant_context_reads_no_outbox_rows(self):
        """Deny-by-default. An absent tenant must not mean unrestricted access."""
        self._record(self.tenant_a, f"idemp-{uuid.uuid4()}")

        with self.db.system_session() as cur:
            cur.execute("SELECT count(*) FROM usage_outbox")
            self.assertEqual(cur.fetchone()[0], 0)

    def test_dispatch_marks_and_keeps(self):
        """
        F-3, stated as an assertion.

        The previous implementation called `self._outbox.clear()`. After that ran, "was this
        event delivered?" and "did this event ever exist?" had the same answer. Dispatch now
        stamps `dispatched_at` and deletes nothing.
        """
        key = f"idemp-{uuid.uuid4()}"
        event = self._record(self.tenant_a, key)

        dispatched = self.service.dispatch_outbox(self.tenant_a)
        self.assertEqual(dispatched, 1)

        retained = self.service.get_outbox_events(self.tenant_a)
        self.assertEqual(len(retained), 1, "dispatch must not delete the record it sent")
        self.assertEqual(retained[0].event_id, event.event_id)
        self.assertIsNotNone(retained[0].dispatched_at)

        self.assertEqual(
            len(self.service.get_pending_outbox_events(self.tenant_a)),
            0,
            "a dispatched row is no longer pending",
        )
        self.assertEqual(
            self.service.dispatch_outbox(self.tenant_a),
            0,
            "a second run must not re-send an already dispatched row",
        )

    def test_dispatch_only_touches_the_calling_tenants_rows(self):
        self._record(self.tenant_a, f"idemp-{uuid.uuid4()}")
        self._record(self.tenant_b, f"idemp-{uuid.uuid4()}")

        self.service.dispatch_outbox(self.tenant_a)

        self.assertEqual(len(self.service.get_pending_outbox_events(self.tenant_a)), 0)
        self.assertEqual(
            len(self.service.get_pending_outbox_events(self.tenant_b)),
            1,
            "one tenant's dispatch run marked another tenant's rows",
        )

    def test_a_failing_sink_leaves_the_rows_pending(self):
        """
        The stamping and the send share one transaction, so a sink that raises rolls the
        stamping back. The reverse order — send, then stamp separately — loses every event the
        process dies between.
        """
        class ExplodingDispatcher(self.metering.OutboxDispatcher):
            def dispatch(self, records):
                raise RuntimeError("downstream unavailable")

        service = self.metering.UsageMeterService(dispatcher=ExplodingDispatcher())
        service.record_event(
            tenant_id=self.tenant_a,
            principal_id=str(uuid.uuid4()),
            context_id=str(uuid.uuid4()),
            capability_id="cap_monthly_leases",
            quantity=2,
            unit=self.metering.MeteredUnit.REQUESTS,
            correlation_id="corr-sink-fail",
            idempotency_key=f"idemp-{uuid.uuid4()}",
        )

        with self.assertRaises(RuntimeError):
            service.dispatch_outbox(self.tenant_a)

        pending = service.get_pending_outbox_events(self.tenant_a)
        self.assertEqual(len(pending), 1, "a failed dispatch must not mark the row sent")
        self.assertIsNone(pending[0].dispatched_at)

    def test_non_positive_quantity_writes_nothing(self):
        with self.assertRaises(self.metering.InvalidQuantityError):
            self._record(self.tenant_a, f"idemp-{uuid.uuid4()}", quantity=0)
        with self.assertRaises(self.metering.InvalidQuantityError):
            self._record(self.tenant_a, f"idemp-{uuid.uuid4()}", quantity=-5)

        self.assertEqual(len(self.service.get_outbox_events(self.tenant_a)), 0)

    def test_a_non_uuid_tenant_identifier_is_refused_by_the_database(self):
        """
        Identifiers are passed through unchanged, so a caller still holding a `tnt_` prefixed
        identifier is refused rather than quietly accommodated. Normalising in the repository
        would hide the caller that is wrong.

        Two controls would each refuse this row: `chk_outbox_tenant_id_is_uuid` from migration
        003, and the isolation policy from migration 004, which casts the session variable with
        `NULLIF(current_setting('app.current_tenant_id', true), '')::uuid`. The policy fires
        first, which is worth pinning: the refusal comes from the isolation boundary, so it
        applies to every statement in the session and not only to inserts into this one table.
        """
        import psycopg

        with self.assertRaises(psycopg.errors.InvalidTextRepresentation):
            self._record("tnt_beta", f"idemp-{uuid.uuid4()}")


@unittest.skipIf(
    _unavailable_reason() is not None,
    "database unavailable — reported as a failure by TestMeteringPersistenceAvailability",
)
class QuotaReservationPersistenceTests(unittest.TestCase):
    """F-2 residue. A reservation now holds against a balance, and expiry is compared to now."""

    @classmethod
    def setUpClass(cls):
        from platform_kernel import db
        from platform_kernel import metering

        cls.db = db
        cls.metering = metering

    def setUp(self):
        self.service = self.metering.UsageMeterService()
        self.tenant = str(uuid.uuid4())
        self.other_tenant = str(uuid.uuid4())
        self.capability = "cap_monthly_leases"
        self.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    def _provision(self, quota_limit: int = 100):
        return self.service.provision_quota(self.tenant, self.capability, quota_limit)

    def _reserve(self, quantity: int = 5, **overrides):
        params = dict(
            tenant_id=self.tenant,
            capability_id=self.capability,
            reserved_quantity=quantity,
            expires_at=self.expires_at,
            correlation_id="corr-res-1",
        )
        params.update(overrides)
        return self.service.create_quota_reservation(**params)

    def _used(self) -> int:
        return self.service.get_quota_balance(self.tenant, self.capability).used_quantity

    def test_reservation_holds_against_the_balance(self):
        """
        The hold is what makes it a reservation. Before this change nothing was decremented,
        so no sequence of reservations could exceed a quota and the guarantee the type is named
        for was made nowhere.
        """
        self._provision(quota_limit=100)
        self.assertEqual(self._used(), 0)

        reservation = self._reserve(quantity=5)

        self.assertEqual(reservation.status, "pending")
        self.assertEqual(self._used(), 5)

    def test_reservation_without_a_provisioned_balance_is_refused(self):
        """A hold against nothing constrains nothing, so it is refused rather than created."""
        with self.assertRaises(self.metering.QuotaBalanceNotProvisionedError):
            self._reserve(quantity=5)

    def test_holds_cannot_exceed_the_entitled_quota(self):
        """
        `chk_balance_within_quota` refuses the increment. This is a database invariant, so it
        would refuse a writer that had never heard of this module.
        """
        self._provision(quota_limit=10)
        self._reserve(quantity=8)

        with self.assertRaises(self.metering.QuotaExceededError):
            self._reserve(quantity=5, correlation_id="corr-res-2")

        self.assertEqual(
            self._used(), 8, "a refused hold must roll back, leaving the earlier hold intact"
        )

    def test_no_reservation_row_survives_a_refused_hold(self):
        self._provision(quota_limit=10)
        self._reserve(quantity=10)

        with self.assertRaises(self.metering.QuotaExceededError):
            self._reserve(quantity=1, correlation_id="corr-res-3")

        with self.db.tenant_session(self.tenant) as cur:
            cur.execute("SELECT count(*) FROM quota_reservations")
            self.assertEqual(
                cur.fetchone()[0], 1, "the reservation row outlived the hold it depended on"
            )

    def test_commit_marks_the_row_and_keeps_the_hold(self):
        self._provision(quota_limit=100)
        reservation = self._reserve(quantity=5)

        committed = self.service.commit_reservation(reservation)

        self.assertEqual(committed.status, "committed")
        self.assertEqual(self.service.get_reservation(
            self.tenant, reservation.reservation_id
        ).status, "committed")
        self.assertEqual(self._used(), 5, "commit converts a hold to consumption, not to zero")

    def test_commit_preserves_every_field_but_status(self):
        """
        A transition must change the status and nothing else. Four of the eleven fields have
        no column, so they survive a transition only because the presented record carries
        them; this is the assertion that would fail if a transition rebuilt the record from
        the stored row and silently defaulted the rest.
        """
        self._provision(quota_limit=100)
        before = self._reserve(quantity=5).to_dict()
        after = self.service.commit_reservation(self._rebuild(before)).to_dict()

        self.assertEqual(after["status"], "committed")
        del before["status"], after["status"]
        self.assertEqual(before, after, "commit altered a field other than status")

    def _rebuild(self, payload: dict):
        """Rebuild the record a caller would be holding from its serialized form."""
        return self.metering.QuotaReservation(
            reservation_id=payload["reservation_id"],
            tenant_id=payload["tenant_id"],
            capability_id=payload["capability_id"],
            reserved_quantity=payload["reserved_quantity"],
            quota_window=self.metering.QuotaWindow(payload["quota_window"]),
            window_starts_at=datetime.fromisoformat(payload["window_starts_at"]),
            window_ends_at=datetime.fromisoformat(payload["window_ends_at"]),
            expires_at=datetime.fromisoformat(payload["expires_at"]),
            status=payload["status"],
            correlation_id=payload["correlation_id"],
            idempotency_key=payload["idempotency_key"],
        )

    def test_release_returns_the_hold(self):
        self._provision(quota_limit=100)
        reservation = self._reserve(quantity=5)
        self.assertEqual(self._used(), 5)

        released = self.service.release_reservation(reservation)

        self.assertEqual(released.status, "released")
        self.assertEqual(self._used(), 0)

    def test_a_released_reservation_cannot_be_released_again(self):
        """A second decrement would hand the tenant allowance it never gave back."""
        self._provision(quota_limit=100)
        reservation = self._reserve(quantity=5)
        self.service.release_reservation(reservation)

        with self.assertRaises(self.metering.ReservationNotPendingError):
            self.service.release_reservation(reservation)

        self.assertEqual(self._used(), 0)

    def test_a_committed_reservation_cannot_be_committed_again(self):
        self._provision(quota_limit=100)
        reservation = self._reserve(quantity=5)
        self.service.commit_reservation(reservation)

        with self.assertRaises(self.metering.ReservationNotPendingError):
            self.service.commit_reservation(reservation)

        self.assertEqual(self._used(), 5)

    def test_a_reservation_that_expired_after_creation_cannot_be_committed(self):
        """
        The F-2 residue, demonstrated rather than argued.

        `chk_reservation_expiry_future` compares `expires_at` to `created_at`. Both are fixed
        when the row is written, so the constraint can only reject a reservation that was born
        expired. It cannot reject one that lapsed while it was pending.

        This test backdates both timestamps together — which keeps the CHECK satisfied, and
        that is exactly the point: the database accepts the row and would accept the commit.
        Only the comparison of `expires_at` against `now()` in `commit_reservation` refuses it.
        """
        self._provision(quota_limit=100)
        reservation = self._reserve(quantity=5)
        self.assertEqual(self._used(), 5)

        with self.db.tenant_session(self.tenant) as cur:
            cur.execute(
                "UPDATE quota_reservations "
                "SET created_at = now() - interval '2 hours', "
                "    expires_at = now() - interval '1 hour' "
                "WHERE reservation_id = %s "
                "RETURNING expires_at",
                (reservation.reservation_id,),
            )
            lapsed_at = cur.fetchone()[0]

        # The caller's record now agrees with storage; only time has moved.
        lapsed = replace(reservation, expires_at=lapsed_at)

        with self.assertRaises(self.metering.ReservationExpiredError):
            self.service.commit_reservation(lapsed)

        self.assertEqual(
            self.service.get_reservation(self.tenant, reservation.reservation_id).status,
            "expired",
            "an expired reservation must not stay pending, or its hold is held forever",
        )
        self.assertEqual(
            self._used(), 0, "an expired hold must be returned to the balance"
        )

    def test_a_presented_record_that_disagrees_with_storage_is_refused(self):
        """
        The transition methods take the caller's record because four contract-required fields
        have no column. Accepting it unchecked would let a caller commit against a quantity or
        an expiry the database does not hold, so every stored field is compared first.
        """
        self._provision(quota_limit=100)
        reservation = self._reserve(quantity=5)

        inflated = replace(reservation, reserved_quantity=500)
        with self.assertRaises(self.metering.ReservationRecordMismatchError):
            self.service.commit_reservation(inflated)

        extended = replace(
            reservation, expires_at=reservation.expires_at + timedelta(days=365)
        )
        with self.assertRaises(self.metering.ReservationRecordMismatchError):
            self.service.commit_reservation(extended)

        self.assertEqual(
            self.service.get_reservation(self.tenant, reservation.reservation_id).status,
            "pending",
        )

    def test_a_reservation_is_invisible_to_another_tenant(self):
        self._provision(quota_limit=100)
        reservation = self._reserve(quantity=5)

        with self.assertRaises(self.metering.ReservationNotFoundError):
            self.service.get_reservation(self.other_tenant, reservation.reservation_id)

    def test_a_reservation_born_expired_is_refused_by_the_database(self):
        self._provision(quota_limit=100)

        with self.assertRaises(self.metering.ReservationExpiredError):
            self._reserve(
                quantity=5, expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
            )

        self.assertEqual(self._used(), 0, "a refused reservation must not leave a hold")

    def test_non_positive_reserved_quantity_is_refused(self):
        self._provision(quota_limit=100)

        with self.assertRaises(self.metering.InvalidQuantityError):
            self._reserve(quantity=0)
        self.assertEqual(self._used(), 0)

    def test_declared_window_must_match_the_balance_it_holds_against(self):
        """
        A daily reservation reporting month-long bounds would validate perfectly against
        `quota-reservation.schema.json` and over-report the tenant's allowance by roughly
        thirty times. The schema cannot express the relationship; this can.
        """
        self._provision(quota_limit=100)  # provisions a MONTHLY window

        with self.assertRaises(self.metering.AmbiguousQuotaWindowError):
            self._reserve(quantity=5, quota_window=self.metering.QuotaWindow.DAILY)

    def test_window_bounds_come_from_the_balance_row(self):
        balance = self._provision(quota_limit=100)
        reservation = self._reserve(quantity=5)

        self.assertEqual(reservation.window_starts_at, balance.window_start)
        self.assertEqual(reservation.window_ends_at, balance.window_end)

    # -- contract conformance -------------------------------------------------------------
    #
    # `contracts/schemas/quota-reservation.schema.json` was covered by
    # `tests/contracts/test_schema_instance_phase3.py`, which builds reservations in memory
    # against a `tnt_beta` tenant. That file is outside this work's lane and its
    # `QuotaReservationInstanceTests` cannot run against the database, so the schema would
    # otherwise lose instance coverage and `tools/check_contract_conformance.py` would report a
    # regression. Coverage is restored here, against reservations the database actually holds —
    # which is a stronger instance than the in-memory one it replaces, not a substitute for it.

    def test_persisted_reservation_validates_against_its_frozen_schema(self):
        import jsonschema

        schema = json.loads(
            (ROOT / "contracts" / "schemas" / "quota-reservation.schema.json").read_text(
                encoding="utf-8"
            )
        )
        checker = jsonschema.FormatChecker()

        self._provision(quota_limit=100)
        pending = self._reserve(quantity=5)
        jsonschema.validate(
            instance=pending.to_dict(), schema=schema, format_checker=checker
        )

        committed = self.service.commit_reservation(pending)
        jsonschema.validate(
            instance=committed.to_dict(), schema=schema, format_checker=checker
        )

        second = self._reserve(quantity=3, correlation_id="corr-res-release")
        released = self.service.release_reservation(second)
        jsonschema.validate(
            instance=released.to_dict(), schema=schema, format_checker=checker
        )

        for field in ("window_starts_at", "window_ends_at", "expires_at"):
            parsed = datetime.fromisoformat(committed.to_dict()[field])
            self.assertIsNotNone(
                parsed.tzinfo,
                msg=f"{field} serialized without a UTC offset; the instant is ambiguous",
            )

    def test_a_daily_reservation_validates_and_spans_one_day(self):
        """
        The daily path has its own balance row and its own bounds. A daily reservation
        carrying month-long bounds would validate against the schema and over-report the
        tenant's allowance by roughly thirty times, so the span is asserted as well as the
        document.
        """
        import jsonschema

        schema = json.loads(
            (ROOT / "contracts" / "schemas" / "quota-reservation.schema.json").read_text(
                encoding="utf-8"
            )
        )
        capability = "cap_daily_exports"
        self.service.provision_quota(
            self.tenant, capability, 50, self.metering.QuotaWindow.DAILY
        )

        reservation = self.service.create_quota_reservation(
            tenant_id=self.tenant,
            capability_id=capability,
            reserved_quantity=2,
            expires_at=self.expires_at,
            correlation_id="corr-daily-1",
            quota_window=self.metering.QuotaWindow.DAILY,
        )

        payload = reservation.to_dict()
        jsonschema.validate(
            instance=payload, schema=schema, format_checker=jsonschema.FormatChecker()
        )
        self.assertEqual(payload["quota_window"], "daily")
        self.assertEqual(
            reservation.window_ends_at - reservation.window_starts_at, timedelta(days=1)
        )

    def test_derived_idempotency_key_is_stable_for_identical_requests(self):
        """
        `minLength: 1` is satisfied by a random UUID, which would make the field meaningless
        while validating. The key must be a function of request content: identical requests
        share one, differing requests do not.

        `quota_reservations` has no column for it, so this asserts the key is honest, not that
        dedup exists — two identical calls still produce two reservations and two holds.
        """
        self._provision(quota_limit=100)
        first = self._reserve(quantity=5).to_dict()
        second = self._reserve(quantity=5).to_dict()
        different = self._reserve(quantity=9).to_dict()

        self.assertEqual(first["idempotency_key"], second["idempotency_key"])
        self.assertNotEqual(first["idempotency_key"], different["idempotency_key"])
        self.assertNotEqual(
            first["reservation_id"],
            second["reservation_id"],
            msg="reservation_id is per-call; if it were stable this test would prove nothing",
        )

    def test_caller_supplied_idempotency_key_is_not_overwritten(self):
        self._provision(quota_limit=100)
        payload = self._reserve(
            quantity=5, idempotency_key="idemp-caller-owned-1"
        ).to_dict()
        self.assertEqual(payload["idempotency_key"], "idemp-caller-owned-1")


if __name__ == "__main__":
    unittest.main()
