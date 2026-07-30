"""
PostgreSQL stores for feature rollout and rate limiting.

Work package: BOPEN-P35-001 — finding F-7
Governing artifacts: BOPEN-ENT-001; AGENTS.md §8
Tables: migration 005 — `tenant_feature_toggles`, `rate_limit_policies`, `rate_limit_counters`

These implement the `FeatureToggleStore` and `RateLimitStore` protocols declared in
`kernel_core.entitlement`. The protocols live there and the implementations live here because
`packages/kernel-core` imports `platform_kernel` zero times and must keep doing so — the
dependency runs services -> packages and never back. Giving the evaluator a database would
invert that and make the pure-domain package depend on psycopg.

Every statement runs inside `db.tenant_session`, so the row-level security policy does the
scoping. As in `repositories.py`, no method writes `WHERE tenant_id = ...` by hand.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from kernel_core.entitlement import RateLimitOutcome, RateLimitPolicy

from platform_kernel import db


class PostgresFeatureToggleStore:
    """Tenant-scoped feature rollout decisions.

    Finding F-7 in its storage form. The previous map was process-global, so a decision written
    for one tenant applied to all of them and none of it survived a restart. Here the tenant is
    part of the primary key and the row-level security policy makes it structurally impossible
    for one tenant to read or write another's.
    """

    def get_toggle(self, tenant_id: str, feature_key: str) -> Optional[bool]:
        """Return the tenant's decision, or None when none is recorded.

        None and False are different answers and the caller treats them differently: None means
        no rollout decision exists, False means the feature is deliberately withheld. Collapsing
        them would make "not being staged" indistinguishable from "staged and off".
        """
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT enabled FROM tenant_feature_toggles WHERE feature_key = %s",
                (feature_key,),
            )
            row = cur.fetchone()
        return None if row is None else bool(row[0])

    def set_toggle(
        self, tenant_id: str, feature_key: str, enabled: bool, updated_by: Optional[str] = None
    ) -> None:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "INSERT INTO tenant_feature_toggles (tenant_id, feature_key, enabled, updated_by) "
                "VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (tenant_id, feature_key) DO UPDATE "
                "SET enabled = EXCLUDED.enabled, "
                "    updated_at = CURRENT_TIMESTAMP, "
                "    updated_by = EXCLUDED.updated_by",
                (tenant_id, feature_key, enabled, updated_by),
            )

    def list_toggles(self, tenant_id: str) -> dict:
        with db.tenant_session(tenant_id) as cur:
            cur.execute("SELECT feature_key, enabled FROM tenant_feature_toggles ORDER BY feature_key")
            return {row[0]: bool(row[1]) for row in cur.fetchall()}


def window_bounds(now: datetime, window_seconds: int) -> tuple[datetime, datetime]:
    """Snap an instant to its fixed window.

    Windows are aligned to the epoch rather than to first use, so two workers computing the
    window for the same instant always agree. A window that started when a particular process
    first saw a request would give each worker its own allowance, which is the multi-worker
    version of the defect F-7 records.
    """
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    elapsed = int((now - epoch).total_seconds())
    start_offset = (elapsed // window_seconds) * window_seconds
    start = epoch + timedelta(seconds=start_offset)
    return start, start + timedelta(seconds=window_seconds)


class PostgresRateLimitStore:
    """Windowed rate limiting whose counter lives in the database.

    The window start is part of the counter's primary key, so crossing a boundary creates a new
    row and the previous one simply stops being selected. Nothing has to run for a limit to
    expire — there is no reset to schedule and no job to fail.
    """

    def get_policy(self, tenant_id: str, capability_id: str) -> Optional[RateLimitPolicy]:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT max_per_window, window_seconds FROM rate_limit_policies "
                "WHERE capability_id = %s",
                (capability_id,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return RateLimitPolicy(max_per_window=int(row[0]), window_seconds=int(row[1]))

    def set_policy(
        self, tenant_id: str, capability_id: str, max_per_window: int, window_seconds: int = 60
    ) -> None:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "INSERT INTO rate_limit_policies "
                "(tenant_id, capability_id, max_per_window, window_seconds) "
                "VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (tenant_id, capability_id) DO UPDATE "
                "SET max_per_window = EXCLUDED.max_per_window, "
                "    window_seconds = EXCLUDED.window_seconds, "
                "    updated_at = CURRENT_TIMESTAMP",
                (tenant_id, capability_id, max_per_window, window_seconds),
            )

    def try_consume(
        self, tenant_id: str, capability_id: str, policy: RateLimitPolicy, now: datetime
    ) -> RateLimitOutcome:
        """Consume one unit if the window has room, atomically.

        The whole decision is one statement. `INSERT ... ON CONFLICT DO UPDATE` with a `WHERE`
        on the update is what makes it atomic: PostgreSQL takes a row lock on the conflicting
        row, evaluates the predicate, and either increments or does nothing — with no window in
        which another transaction can observe the pre-increment value and also proceed.

        A read-then-write in Python would not do this. Two concurrent requests would each read
        the same count, each find room, and each write count+1 — admitting two calls where the
        policy allows one. That is precisely the case a rate limit exists to prevent, so
        implementing it non-atomically produces a control that works only when it is not needed.

        `RETURNING` gives back the value the update actually landed on rather than one computed
        by the caller. When the predicate fails there is no returned row, and the current count
        is read separately so the refusal can report the true consumed figure.
        """
        start, end = window_bounds(now, policy.window_seconds)

        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "INSERT INTO rate_limit_counters "
                "  (tenant_id, capability_id, window_start, window_end, consumed) "
                "VALUES (%s, %s, %s, %s, 1) "
                "ON CONFLICT (tenant_id, capability_id, window_start) DO UPDATE "
                "  SET consumed = rate_limit_counters.consumed + 1 "
                "  WHERE rate_limit_counters.consumed < %s "
                "RETURNING consumed",
                (tenant_id, capability_id, start, end, policy.max_per_window),
            )
            row = cur.fetchone()

            if row is not None:
                return RateLimitOutcome(
                    allowed=True, consumed=int(row[0]), window_ends_at=end
                )

            # The predicate refused the increment, so the window is full. Read the standing
            # count so the denial reports what was actually consumed rather than restating the
            # limit — those are the same number here, but they are the same only by coincidence
            # and a caller should not have to know that.
            cur.execute(
                "SELECT consumed FROM rate_limit_counters "
                "WHERE capability_id = %s AND window_start = %s",
                (capability_id, start),
            )
            standing = cur.fetchone()

        return RateLimitOutcome(
            allowed=False,
            consumed=int(standing[0]) if standing else policy.max_per_window,
            window_ends_at=end,
        )
