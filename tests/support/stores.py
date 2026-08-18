"""In-memory doubles for the rollout and rate limiting stores.

These live in the test tree on purpose, and it is worth saying why rather than treating it as
layout preference.

An in-memory store shipped inside `kernel_core` or `platform_kernel` would be reachable from
production. `platform_kernel.db` already refuses that pattern for persistence — "there is no
in-memory fallback by design: a fallback would let tenant isolation appear to work while no
policy is enforcing it" — and the same reasoning applies here exactly. Finding F-7 is that
shape: a `tenant_id` parameter accepted and never read, so a control looked tenant-scoped while
being global. A convenient default would reintroduce it.

So the doubles are here, importable only by tests, and the real implementations in
`platform_kernel.rollout_repositories` are the only ones a running kernel can reach.

Both doubles are tenant-keyed, which is not incidental. A double that ignored the tenant would
let a unit test pass against logic that ignores it too, and the test would then be evidence for
the defect rather than against it.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

from kernel_core.entitlement import RateLimitOutcome, RateLimitPolicy


class FakeFeatureToggleStore:
    """Tenant-keyed rollout decisions held in a dict."""

    def __init__(self) -> None:
        self._toggles: Dict[Tuple[str, str], bool] = {}

    def get_toggle(self, tenant_id: str, feature_key: str) -> Optional[bool]:
        return self._toggles.get((tenant_id, feature_key))

    def set_toggle(self, tenant_id: str, feature_key: str, enabled: bool) -> None:
        self._toggles[(tenant_id, feature_key)] = enabled


def _window_bounds(now: datetime, window_seconds: int) -> Tuple[datetime, datetime]:
    """Epoch-aligned windows, matching PostgresRateLimitStore.

    Aligned to the epoch rather than to first use so that the double and the real store agree on
    which window an instant belongs to. A double that windowed differently would let a test pass
    against behaviour the production store does not have.
    """
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    elapsed = int((now - epoch).total_seconds())
    start = epoch + timedelta(seconds=(elapsed // window_seconds) * window_seconds)
    return start, start + timedelta(seconds=window_seconds)


class FakeRateLimitStore:
    """Windowed counters held in a dict, keyed exactly as the table is."""

    def __init__(self) -> None:
        self._policies: Dict[Tuple[str, str], RateLimitPolicy] = {}
        self._counters: Dict[Tuple[str, str, datetime], int] = {}

    def get_policy(self, tenant_id: str, capability_id: str) -> Optional[RateLimitPolicy]:
        return self._policies.get((tenant_id, capability_id))

    def set_policy(
        self, tenant_id: str, capability_id: str, max_per_window: int, window_seconds: int = 60
    ) -> None:
        self._policies[(tenant_id, capability_id)] = RateLimitPolicy(
            max_per_window=max_per_window, window_seconds=window_seconds
        )

    def try_consume(
        self, tenant_id: str, capability_id: str, policy: RateLimitPolicy, now: datetime
    ) -> RateLimitOutcome:
        start, end = _window_bounds(now, policy.window_seconds)
        key = (tenant_id, capability_id, start)
        consumed = self._counters.get(key, 0)

        if consumed >= policy.max_per_window:
            return RateLimitOutcome(allowed=False, consumed=consumed, window_ends_at=end)

        # Not atomic, and it does not need to be: a double serving single-threaded unit tests
        # has no concurrency to lose to. The production store does this in one statement, and
        # that difference is the reason the concurrency property is asserted against PostgreSQL
        # and never here — a test proving atomicity against this class would prove nothing.
        self._counters[key] = consumed + 1
        return RateLimitOutcome(allowed=True, consumed=consumed + 1, window_ends_at=end)


class CollectingLifecycleSink:
    """A lifecycle sink that keeps events in a list.

    Implements `kernel_core.audit.LifecycleEventSink`. It exists so that a test which only checks
    the envelope's shape does not need a database, and it lives here rather than in the package
    for the reason at the top of this module: a default sink reachable from production would let
    `AuditDispatcher` go back to losing every Phase 2 audit record on restart, quietly.

    Passing this is a statement that the caller does not want durability. That is legitimate in a
    shape test and never legitimate in a running kernel, and requiring it to be named makes the
    difference visible at each construction site instead of hidden in a default argument.
    """

    def __init__(self) -> None:
        self.events: list = []

    def record(self, event: dict) -> None:
        self.events.append(event)


class FakeQuotaReservationStore:
    """A quota-reservation repository that holds rows in memory.

    Implements the one method `UsageMeterService.create_quota_reservation` calls —
    `create(...) -> (StoredReservation, StoredBalance)` — so that an instance of the real
    `QuotaReservation` can be produced and validated against its frozen schema without a database.

    It exists because `contracts/schemas/quota-reservation.schema.json` was covered only by
    database-gated integration tests. On 2026-08-17 the contract conformance gate reported a false
    regression when the database timed out: the gated tests skipped, their coverage vanished with
    them, and a schema that is in fact validated read as uncovered. Coverage that disappears with
    the environment is not a measurement.

    This fake deliberately does NOT bypass the service's own checks. The window it returns is a real
    monthly window, so `_assert_window_matches` still runs and still raises on a mismatch — a fake
    that returned a convenient window would let the test pass while proving nothing about the code
    under test.
    """

    def __init__(self, *, quota_limit: int = 1000, used_quantity: int = 0) -> None:
        from datetime import datetime, timezone

        self.quota_limit = quota_limit
        self.used_quantity = used_quantity
        self.created: list = []
        # A real calendar month, so the service's window assertion is exercised rather than dodged.
        self.window_start = datetime(2026, 8, 1, tzinfo=timezone.utc)
        self.window_end = datetime(2026, 9, 1, tzinfo=timezone.utc)

    def create(
        self,
        *,
        tenant_id: str,
        capability_id: str,
        reserved_quantity: int,
        expires_at,
        correlation_id: str,
    ):
        from datetime import datetime, timezone

        from platform_kernel.entitlement_repositories import StoredBalance, StoredReservation

        stored = StoredReservation(
            reservation_id="rsv_" + str(len(self.created) + 1).zfill(4),
            tenant_id=tenant_id,
            capability_id=capability_id,
            reserved_quantity=reserved_quantity,
            expires_at=expires_at,
            # The real repository INSERTs 'pending' (entitlement_repositories.py:608) and
            # commit_reservation refuses anything else. The first draft of this fake used
            # "held", and the schema's status enum rejected it — the fake was wrong and the
            # contract test caught it, which is the whole reason to validate an instance
            # rather than assert about a schema document.
            status="pending",
            correlation_id=correlation_id,
            created_at=datetime.now(timezone.utc),
        )
        balance = StoredBalance(
            balance_id="bal_0001",
            tenant_id=tenant_id,
            capability_id=capability_id,
            used_quantity=self.used_quantity + reserved_quantity,
            quota_limit=self.quota_limit,
            window_start=self.window_start,
            window_end=self.window_end,
        )
        self.created.append(stored)
        return stored, balance


class FakeUsageOutboxStore:
    """A usage-outbox repository that holds records in memory, with real idempotency.

    Implements the one method `UsageMeterService.record_event` calls —
    `record(...) -> (StoredOutboxRecord, created: bool)` — so a real `MeteredEvent` can be produced
    and validated against `contracts/schemas/usage-metered-event.schema.json` without a database.

    Written for the same reason as `FakeQuotaReservationStore`: that schema was covered only by
    database-gated integration tests, so its coverage vanished whenever the database did.

    Idempotency is implemented rather than stubbed. `record_event` inspects `created` and, when a key
    repeats, compares the stored fields against the new ones and raises on a conflict. A fake that
    always returned `created=True` would leave that branch untested while the test still passed.
    """

    def __init__(self) -> None:
        self.by_key: dict = {}
        self.sequence = 0

    def record(
        self,
        *,
        tenant_id: str,
        principal_id: str,
        capability_id: str,
        quantity: int,
        unit: str,
        correlation_id: str,
        idempotency_key: str,
    ):
        from datetime import datetime, timezone

        from platform_kernel.entitlement_repositories import StoredOutboxRecord

        existing = self.by_key.get((tenant_id, idempotency_key))
        if existing is not None:
            return existing, False

        self.sequence += 1
        suffix = str(self.sequence).zfill(4)
        stored = StoredOutboxRecord(
            outbox_id="obx_" + suffix,
            event_id="evt_" + suffix,
            tenant_id=tenant_id,
            principal_id=principal_id,
            capability_id=capability_id,
            quantity=quantity,
            unit=unit,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            created_at=datetime.now(timezone.utc),
            dispatched_at=None,
        )
        self.by_key[(tenant_id, idempotency_key)] = stored
        return stored, True
