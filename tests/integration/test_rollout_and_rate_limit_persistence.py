"""
Feature rollout and rate limiting against PostgreSQL — finding F-7.

Work package: BOPEN-P35-001
Tables: migration 005 — tenant_feature_toggles, rate_limit_policies, rate_limit_counters
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed), R4 (adversarial), R5 (fails loudly)

F-7 had two halves and both were the same mistake in different places: a control that accepted a
tenant identifier and did not use it.

`is_feature_enabled(feature_key, tenant_id)` took the tenant at the signature and read a
process-global dict, so one tenant's rollout decision applied to every tenant. `RateLimiter`
keyed limits on capability alone and its counters carried no timestamp, so `reset_seconds=60`
was a number in the response that nothing acted on and a tenant that reached its limit stayed
throttled for the life of the process.

The assertions that matter here are the ones the in-memory double cannot make: that the tenant
scoping is enforced by the database rather than by the code that happens to be reading, and that
the counter's increment is atomic. A double serving single-threaded tests has no concurrency to
lose, so proving atomicity against it would prove nothing.
"""

from __future__ import annotations

import os
import sys
import threading
import unittest
import uuid
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
        return "BOPEN_DATABASE_URL is not set. Run: python tools/db_bootstrap.py --apply"
    return None


class TestRolloutEvidenceAvailability(unittest.TestCase):
    """EBIV R5 — F-7 cannot be verified without a database, and this says so rather than skipping."""

    def test_rollout_evidence_can_be_produced(self):
        reason = _unavailable_reason()
        self.assertIsNone(
            reason,
            msg=(
                "Feature rollout and rate limiting cannot be verified in this environment, so "
                f"no admissible evidence exists for finding F-7.\n\n{reason}\n\n"
                "This failure is intentional under BOPEN-GOV-EBIV-001 R5."
            ),
        )


@unittest.skipIf(
    _unavailable_reason() is not None,
    "database unavailable — reported as a failure by TestRolloutEvidenceAvailability",
)
class RolloutAndRateLimitPersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from kernel_core.entitlement import FeatureRolloutEvaluator, RateLimiter
        from platform_kernel import db
        from platform_kernel.rollout_repositories import (
            PostgresFeatureToggleStore,
            PostgresRateLimitStore,
        )

        cls.db = db
        cls.FeatureRolloutEvaluator = FeatureRolloutEvaluator
        cls.RateLimiter = RateLimiter
        cls.toggles = PostgresFeatureToggleStore()
        cls.limits = PostgresRateLimitStore()

    def setUp(self):
        # Real tenant rows: migration 005 gives every one of these tables a foreign key to
        # tenants(id), unlike migration 002's, so a fabricated identifier is refused at write.
        self.tenant_a = str(uuid.uuid4())
        self.tenant_b = str(uuid.uuid4())
        with self.db.system_session() as cur:
            for tenant_id, name in ((self.tenant_a, "A"), (self.tenant_b, "B")):
                cur.execute(
                    "INSERT INTO tenants (id, name, status) VALUES (%s, %s, 'active')",
                    (tenant_id, name),
                )

    # -- feature rollout ----------------------------------------------------------

    def test_a_toggle_set_for_one_tenant_does_not_apply_to_another(self):
        """The defect F-7 names, stated as an assertion.

        The previous evaluator would have returned False for BOTH tenants here, because the map
        was keyed on the feature alone. This is the assertion whose absence let that ship.
        """
        self.toggles.set_toggle(self.tenant_a, "cap_invoice_create", False)

        evaluator = self.FeatureRolloutEvaluator(self.toggles)

        self.assertFalse(
            evaluator.is_feature_enabled("cap_invoice_create", self.tenant_a),
            "tenant A disabled the feature and still sees it enabled",
        )
        self.assertTrue(
            evaluator.is_feature_enabled("cap_invoice_create", self.tenant_b),
            "tenant B is affected by a rollout decision it did not make",
        )

    def test_absence_of_a_toggle_means_enabled(self):
        """Documented behaviour, asserted so it cannot drift silently.

        Absence means the capability is not part of a staged rollout, which is not the same as
        being withheld. Withholding is entitlement's job — AGENTS.md §7 invariant 8 keeps the two
        separate, and deny-by-default here would collapse them by requiring a toggle row for
        every capability.
        """
        evaluator = self.FeatureRolloutEvaluator(self.toggles)
        self.assertTrue(evaluator.is_feature_enabled("cap_never_configured", self.tenant_a))
        self.assertIsNone(self.toggles.get_toggle(self.tenant_a, "cap_never_configured"))

    def test_a_tenant_cannot_read_another_tenants_toggles(self):
        """Enforced by the row-level security policy, not by the query.

        `list_toggles` has no tenant predicate in its SQL. If this assertion fails the policy is
        not in force, and no amount of care in the repository would compensate.
        """
        self.toggles.set_toggle(self.tenant_a, "cap_alpha_only", True)
        self.toggles.set_toggle(self.tenant_b, "cap_beta_only", True)

        self.assertEqual(set(self.toggles.list_toggles(self.tenant_a)), {"cap_alpha_only"})
        self.assertEqual(set(self.toggles.list_toggles(self.tenant_b)), {"cap_beta_only"})

    def test_a_toggle_survives_a_new_store_instance(self):
        """The previous map died with the process. This is the durability half of F-7."""
        self.toggles.set_toggle(self.tenant_a, "cap_durable", False)

        from platform_kernel.rollout_repositories import PostgresFeatureToggleStore

        self.assertIs(PostgresFeatureToggleStore().get_toggle(self.tenant_a, "cap_durable"), False)

    # -- rate limiting ------------------------------------------------------------

    def test_a_limit_set_for_one_tenant_does_not_throttle_another(self):
        self.limits.set_policy(self.tenant_a, "cap_reports", max_per_window=1)
        limiter = self.RateLimiter(self.limits)

        first = limiter.evaluate(self.tenant_a, "cap_reports", "corr-1")
        second = limiter.evaluate(self.tenant_a, "cap_reports", "corr-2")
        other = limiter.evaluate(self.tenant_b, "cap_reports", "corr-3")

        self.assertTrue(first.allowed)
        self.assertFalse(second.allowed, "tenant A was allowed past its own limit")
        self.assertTrue(other.allowed, "tenant B was throttled by tenant A's limit")

    def test_no_policy_means_not_rate_limited_rather_than_denied(self):
        """The previous code substituted a magic 10000 that appeared in no configuration.

        Rate limiting is a protective control; its absence means unprotected, not denied.
        Denying would make the control's absence indistinguishable from its enforcement.
        """
        limiter = self.RateLimiter(self.limits)
        for index in range(5):
            decision = limiter.evaluate(self.tenant_a, "cap_unconfigured", f"corr-{index}")
            self.assertTrue(decision.allowed)
            self.assertEqual(decision.status_code, 200)

    def test_the_counter_expires_with_its_window(self):
        """The half of F-7 that made a throttle permanent.

        `try_consume` takes `now` as a parameter, so the next window is reached by passing an
        instant inside it rather than by sleeping. That keeps the test deterministic and it
        tests the real mechanism: windows are epoch-aligned and keyed by their start, so
        crossing a boundary is a different row rather than a reset somebody has to schedule.
        """
        from kernel_core.entitlement import RateLimitPolicy

        policy = RateLimitPolicy(max_per_window=1, window_seconds=60)
        now = datetime.now(timezone.utc)

        first = self.limits.try_consume(self.tenant_a, "cap_windowed", policy, now)
        second = self.limits.try_consume(self.tenant_a, "cap_windowed", policy, now)
        self.assertTrue(first.allowed)
        self.assertFalse(second.allowed, "the window admitted more than its allowance")

        later = self.limits.try_consume(
            self.tenant_a, "cap_windowed", policy, now + timedelta(seconds=120)
        )
        self.assertTrue(later.allowed, "the counter did not expire with its window")
        self.assertEqual(later.consumed, 1, "the new window did not start from zero")

    def test_reset_in_seconds_reports_the_real_remaining_window(self):
        """Previously a hardcoded 60 that no code path acted on."""
        self.limits.set_policy(self.tenant_a, "cap_reset", max_per_window=5, window_seconds=60)
        decision = self.RateLimiter(self.limits).evaluate(self.tenant_a, "cap_reset", "corr-r")

        self.assertGreater(decision.reset_in_seconds, 0)
        self.assertLessEqual(decision.reset_in_seconds, 60)

    def test_concurrent_consumption_cannot_exceed_the_allowance(self):
        """The property the in-memory double cannot demonstrate.

        Ten threads race for an allowance of three. A read-then-write implementation lets
        several threads observe the same count, each find room, and each write count+1 — so more
        calls are admitted than the policy permits, and the control works only when it is not
        needed.

        The store does the whole decision in one INSERT ... ON CONFLICT DO UPDATE with a WHERE
        on the update, so PostgreSQL takes a row lock and evaluates the predicate under it. This
        asserts the outcome of that, which is the only way to tell the two implementations
        apart.
        """
        from kernel_core.entitlement import RateLimitPolicy
        from platform_kernel.rollout_repositories import PostgresRateLimitStore

        policy = RateLimitPolicy(max_per_window=3, window_seconds=300)
        now = datetime.now(timezone.utc)
        results: list[bool] = []
        lock = threading.Lock()

        def consume() -> None:
            # A store per thread: each opens its own connection, which is what makes this a
            # race in the database rather than in one Python object.
            outcome = PostgresRateLimitStore().try_consume(
                self.tenant_a, "cap_race", policy, now
            )
            with lock:
                results.append(outcome.allowed)

        threads = [threading.Thread(target=consume) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(
            sum(results),
            3,
            f"the allowance of 3 admitted {sum(results)} concurrent calls",
        )
        self.assertEqual(len(results), 10, "a thread failed without recording an outcome")


if __name__ == "__main__":
    unittest.main()
