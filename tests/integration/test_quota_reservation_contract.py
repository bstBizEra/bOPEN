"""
quota-reservation.schema.json against the real UsageMeterService.

Work package: BOPEN-P35-001
Governing artifact: BOPEN-ENT-001
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed), R5 (fails loudly)

Moved here from tests/contracts/ on 2026-07-30, not repaired in place.

These assertions were written when QuotaReservation was produced entirely in memory, and the
file they lived in stated "no database is required; all Phase 3 producers in scope are
in-memory". That statement stopped being true the moment `create_quota_reservation` began
writing to `quota_reservations` and holding against `usage_meter_balances`.

Patching the fixtures and leaving the class in `tests/contracts/` would have made the contract
category quietly database-dependent — and a category whose meaning has drifted is exactly the
kind of thing that lets a suite report green while measuring something other than what its name
says. The assertions are unchanged; only where they live and what they are given has.

What remains genuinely DB-free about quota-reservation conformance — that `to_dict()` emits
every required property — is exercised here too, because the same call produces it.
"""

from __future__ import annotations

import os
import sys
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))
sys.path.insert(0, str(ROOT / "packages" / "kernel-core" / "python"))

SCHEMA_DIR = ROOT / "contracts" / "schemas"


def _unavailable_reason() -> str | None:
    for module in ("psycopg", "jsonschema"):
        try:
            __import__(module)
        except ImportError:
            return f"{module} is not installed. Run: python -m pip install -r requirements.txt"
    if not os.environ.get("BOPEN_DATABASE_URL", "").strip():
        return "BOPEN_DATABASE_URL is not set. Run: python tools/db_bootstrap.py --apply"
    return None


def load_schema(name: str) -> dict:
    import json
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def validate(instance, schema) -> None:
    import jsonschema
    jsonschema.validate(instance=instance, schema=schema)


def assert_rfc3339(testcase: unittest.TestCase, value: str, field: str) -> None:
    """
    Parse a serialized timestamp, since the installed `jsonschema` cannot.

    `rfc3339-validator` is not installed, so `FormatChecker()` has no `date-time` entry and
    silently accepts anything for `format: date-time`. Without this the schema's timestamp
    constraint is decorative.

    The offset assertion is the part that matters: a naive timestamp on a billing record is
    ambiguous by exactly the server's UTC offset, which is the difference between a quota window
    that closed and one that has not.
    """
    parsed = datetime.fromisoformat(value)
    testcase.assertIsNotNone(
        parsed.tzinfo,
        msg=f"{field} serialized without a UTC offset ({value!r}); the instant is ambiguous.",
    )


class TestQuotaReservationEvidenceAvailability(unittest.TestCase):
    """EBIV R5 — this conformance cannot be checked without a database, and says so."""

    def test_quota_reservation_evidence_can_be_produced(self):
        reason = _unavailable_reason()
        self.assertIsNone(
            reason,
            msg=(
                "quota-reservation conformance cannot be verified in this environment.\n\n"
                f"{reason}\n\n"
                "This failure is intentional under BOPEN-GOV-EBIV-001 R5."
            ),
        )


@unittest.skipIf(
    _unavailable_reason() is not None,
    "database unavailable — reported as a failure by TestQuotaReservationEvidenceAvailability",
)
class QuotaReservationInstanceTests(unittest.TestCase):
    """contracts/schemas/quota-reservation.schema.json against the real UsageMeterService."""

    def setUp(self):
        from platform_kernel.metering import QuotaWindow, UsageMeterService

        self.QuotaWindow = QuotaWindow
        self.schema = load_schema("quota-reservation.schema.json")
        self.service = UsageMeterService()
        self.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        # A fresh tenant per test. The identifier must be a canonical lowercase UUID: migration
        # 003 constrains the column to that shape and migration 004's policy casts the session
        # variable to uuid, so a value like "tnt_beta" cannot even open a session.
        self.tenant_id = str(uuid.uuid4())

        # A reservation now holds against a balance, so one has to exist. Provisioning it here
        # rather than letting the service create it on demand is deliberate: quota_limit comes
        # from a tenant's plan tier, and a metered call arriving is not a reason to grant quota.
        #
        # The two windows go on DIFFERENT capabilities, and that is forced rather than tidy.
        # `usage_meter_balances` has no `quota_window` column — migration 002 gives it only
        # window_start and window_end — so a monthly and a daily balance for one capability are
        # two rows that both cover the present instant and are indistinguishable to a lookup.
        # The repository raises AmbiguousQuotaWindowError rather than picking one, which is the
        # right refusal: a schema that cannot express which allowance is in force should not
        # have the question answered for it by whichever row sorts first.
        self.service.provision_quota(
            tenant_id=self.tenant_id,
            capability_id="cap_monthly_leases",
            quota_limit=10_000,
            quota_window=QuotaWindow.MONTHLY,
        )
        self.service.provision_quota(
            tenant_id=self.tenant_id,
            capability_id="cap_daily_exports",
            quota_limit=10_000,
            quota_window=QuotaWindow.DAILY,
        )

    def _reserve(self, **kwargs):
        params = dict(
            tenant_id=self.tenant_id,
            capability_id="cap_monthly_leases",
            reserved_quantity=5,
            expires_at=self.expires_at,
            correlation_id="corr-res-1",
        )
        params.update(kwargs)
        return self.service.create_quota_reservation(**params)

    def test_pending_reservation_validates(self):
        """
        Before this work `QuotaReservation` had no `to_dict()` at all, so nothing could
        validate it and four required properties were simply absent from the type. This is
        the assertion whose absence let that ship.
        """
        validate(self._reserve().to_dict(), self.schema)

    def test_committed_and_released_reservations_validate(self):
        """
        Status transitions rebuild the record. A transition that drops a property produces an
        instance that fails `required` — so each reachable status is validated, not just the
        one the constructor returns.
        """
        reservation = self._reserve()

        committed = self.service.commit_reservation(reservation)
        self.assertEqual(committed.status, "committed")
        validate(committed.to_dict(), self.schema)

        second = self._reserve()
        released = self.service.release_reservation(second)
        self.assertEqual(released.status, "released")
        validate(released.to_dict(), self.schema)

    def test_transition_preserves_every_field_but_status(self):
        """
        A transition must change the status and nothing else. Enumerating fields by hand is
        how a rebuild silently drops one, and `required` only catches it if the field vanishes
        entirely — not if it is rebuilt with a different value.
        """
        reservation = self._reserve()
        before = reservation.to_dict()
        after = self.service.commit_reservation(reservation).to_dict()

        self.assertEqual(after["status"], "committed")
        del before["status"], after["status"]
        self.assertEqual(before, after, "commit altered a field other than status")

    def test_window_bounds_bracket_the_reservation(self):
        """
        `window_starts_at` and `window_ends_at` are `format: date-time` strings, so the schema
        accepts any two valid timestamps in any order — including a window that ends before it
        starts, or one that does not contain the reservation. Ordering and containment are
        checked here because the contract cannot express them.
        """
        payload = self._reserve(quota_window=self.QuotaWindow.MONTHLY).to_dict()

        starts = datetime.fromisoformat(payload["window_starts_at"])
        ends = datetime.fromisoformat(payload["window_ends_at"])
        now = datetime.now(timezone.utc)

        self.assertLess(starts, ends, "a billing window must end after it starts")
        self.assertLessEqual(starts, now, "the reservation falls before its own window")
        self.assertGreater(ends, now, "the reservation falls after its own window")
        self.assertEqual(payload["quota_window"], "monthly")
        validate(payload, self.schema)

    def test_daily_window_is_a_single_day(self):
        """
        `quota_window` is an enum of daily and monthly, but the schema cannot check that the
        declared window matches the bounds. A daily reservation carrying month-long bounds
        would validate and then over-report a tenant's allowance by roughly thirty times.
        """
        payload = self._reserve(
            capability_id="cap_daily_exports", quota_window=self.QuotaWindow.DAILY
        ).to_dict()

        starts = datetime.fromisoformat(payload["window_starts_at"])
        ends = datetime.fromisoformat(payload["window_ends_at"])

        self.assertEqual(payload["quota_window"], "daily")
        self.assertEqual(ends - starts, timedelta(days=1))
        validate(payload, self.schema)

    def test_derived_idempotency_key_is_stable_for_identical_requests(self):
        """
        `minLength: 1` is satisfied by a random UUID, which would make the field meaningless
        while validating. An idempotency key must be a function of request content: identical
        requests share one, differing requests do not.

        Note the reservation path does not yet dedup on this key — see the docstring on
        `create_quota_reservation`. This asserts the key is honest, not that dedup exists.
        """
        first = self._reserve().to_dict()
        second = self._reserve().to_dict()
        different = self._reserve(reserved_quantity=9).to_dict()

        self.assertEqual(first["idempotency_key"], second["idempotency_key"])
        self.assertNotEqual(first["idempotency_key"], different["idempotency_key"])
        self.assertNotEqual(
            first["reservation_id"],
            second["reservation_id"],
            msg="reservation_id is per-call; if it were stable this test would prove nothing",
        )

    def test_caller_supplied_idempotency_key_is_not_overwritten(self):
        """A caller that owns a real request key must see that key on the record."""
        payload = self._reserve(idempotency_key="idemp-caller-owned-1").to_dict()
        self.assertEqual(payload["idempotency_key"], "idemp-caller-owned-1")
        validate(payload, self.schema)

    def test_timestamps_carry_an_offset(self):
        """See `assert_rfc3339` — the installed jsonschema cannot enforce `format: date-time`."""
        payload = self._reserve().to_dict()
        for field in ("window_starts_at", "window_ends_at", "expires_at"):
            assert_rfc3339(self, payload[field], field)


if __name__ == "__main__":
    unittest.main()
