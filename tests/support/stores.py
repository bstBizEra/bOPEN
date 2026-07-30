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
