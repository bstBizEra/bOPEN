"""
bOPEN Usage Metering & Outbox Service v1.0 (WP-P3-05 / BOPEN-ENT-001).

Work package: BOPEN-P35-001
Governing findings: F-3 (transactional outbox), F-2 residue (quota holds and expiry)
Contracts: contracts/schemas/usage-metered-event.schema.json
           contracts/schemas/quota-reservation.schema.json

WHAT CHANGED AND WHY
--------------------
`UsageMeterService` previously held all of its state in five Python dictionaries and lists:
`_events`, `_idempotency_index`, `_global_idempotency_keys`, `_outbox` and `_reservations`.
Migration 002 had created the five tables those structures shadow, migration 003 had added
their integrity constraints and migration 004 had corrected their isolation policies — and no
production code path read or wrote any of them.

The consequences were not cosmetic:

* the outbox lost every event when the process restarted, and `dispatch_outbox` called
  `self._outbox.clear()`, which is the opposite of what an outbox does;
* the idempotency guard was a dictionary in one process, so two workers deduplicated nothing;
* the cross-tenant guard was a *global* dictionary keyed on the idempotency key alone. It
  coupled one tenant's behaviour to another's data, and its error message interpolated the
  owning tenant's identifier — disclosing to the caller both that another tenant exists and
  which one it is;
* a reservation held nothing. Nothing was decremented, nothing could be exceeded, and the
  quota guarantee the type is named after was not made anywhere.

All five are now rows in PostgreSQL, reached through `platform_kernel.entitlement_repositories`
and therefore through `db.tenant_session`, so isolation is the row-level security policy's
property and not this module's. There is no in-memory mode and no fallback, for the reason
recorded in `db.py`: a fallback lets tenant isolation appear to work while no policy is
enforcing it.

TWO THINGS THIS MODULE CANNOT DO, STATED RATHER THAN HIDDEN
-----------------------------------------------------------
1. `usage_outbox` has no `context_id` column, but `usage-metered-event.schema.json` requires
   `context_id`. A replayed event therefore carries the `context_id` of the call that replayed
   it, because the original was never stored. Every other field on a replay comes from the
   stored row. See `record_event`.

2. `quota_reservations` has no `quota_window`, `window_starts_at`, `window_ends_at` or
   `idempotency_key` column, but `quota-reservation.schema.json` requires all four. A
   reservation identifier alone therefore cannot rebuild a contract-valid record, which is why
   `commit_reservation` and `release_reservation` take the caller's `QuotaReservation` rather
   than an identifier string. Every field the table *does* store is verified against the stored
   row before the transition, so presenting a record does not mean the caller's numbers are
   trusted.

Closing either gap needs a migration, and migrations are append-only after merge
(AGENTS.md section 14). Both are raised as decisions rather than worked around.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Optional, Sequence, Tuple

from platform_kernel.entitlement_repositories import (
    AmbiguousQuotaWindowError,
    BalanceRowMissingError,
    CrossTenantIdempotencyViolationError,
    EntitlementRepositoryError,
    IdempotencyPayloadConflictError,
    InvalidQuantityError,
    MeterBalanceRepository,
    OutboxRecordMissingError,
    QuotaBalanceNotProvisionedError,
    QuotaExceededError,
    QuotaReservationError,
    QuotaReservationRepository,
    ReservationExpiredError,
    ReservationNotFoundError,
    ReservationNotPendingError,
    ReservationRecordMismatchError,
    StoredBalance,
    StoredOutboxRecord,
    StoredReservation,
    UsageOutboxRepository,
)

# The error names above are defined in the repository module because that is where they are
# raised, and re-exported here because `from platform_kernel.metering import
# QuotaReservationError` is the established import path. Re-exporting is not decoration: it
# keeps one exception hierarchy rather than two that must be kept in agreement.
__all__ = [
    "MeteredUnit",
    "QuotaWindow",
    "MeteredEvent",
    "QuotaReservation",
    "OutboxDispatcher",
    "UsageMeterService",
    "current_window_bounds",
    "AmbiguousQuotaWindowError",
    "BalanceRowMissingError",
    "CrossTenantIdempotencyViolationError",
    "EntitlementRepositoryError",
    "IdempotencyPayloadConflictError",
    "InvalidQuantityError",
    "OutboxRecordMissingError",
    "QuotaBalanceNotProvisionedError",
    "QuotaExceededError",
    "QuotaReservationError",
    "ReservationExpiredError",
    "ReservationNotFoundError",
    "ReservationNotPendingError",
    "ReservationRecordMismatchError",
    "StoredBalance",
    "StoredOutboxRecord",
    "StoredReservation",
]


class MeteredUnit(str, Enum):
    REQUESTS = "requests"
    BYTES = "bytes"
    SEATS = "seats"
    SECONDS = "seconds"


class QuotaWindow(str, Enum):
    """Billing window a reservation belongs to. Mirrors the `quota_window` enum in
    contracts/schemas/quota-reservation.schema.json."""
    DAILY = "daily"
    MONTHLY = "monthly"


def _window_bounds(window: QuotaWindow, at: datetime) -> Tuple[datetime, datetime]:
    """
    Compute the half-open [start, end) bounds of the billing window containing `at`.

    These are calculated from the calendar rather than stored as caller input, so the
    reservation's declared window is the window it actually falls in. Bounds are UTC
    because billing windows must not shift with the server's local timezone.
    """
    at = at.astimezone(timezone.utc)
    if window is QuotaWindow.DAILY:
        start = at.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, start + timedelta(days=1)

    start = at.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        return start, start.replace(year=start.year + 1, month=1)
    return start, start.replace(month=start.month + 1)


def current_window_bounds(
    window: QuotaWindow, at: Optional[datetime] = None
) -> Tuple[datetime, datetime]:
    """Public form of `_window_bounds`, used when provisioning a balance row.

    Provisioning has to name a window before any usage exists, so the bounds are computed from
    the calendar here. Once a balance row exists it, not this function, is the authority: a
    reservation reports the window of the row it actually held against. Those two can only
    disagree if a balance was provisioned with bounds that do not match its declared window,
    and `UsageMeterService.create_quota_reservation` refuses that case rather than reporting a
    window the tenant is not being billed on.
    """
    return _window_bounds(window, at or datetime.now(timezone.utc))


def _derive_idempotency_key(
    tenant_id: str,
    capability_id: str,
    reserved_quantity: int,
    quota_window: QuotaWindow,
    window_starts_at: datetime,
    correlation_id: str
) -> str:
    """
    Derive a content-addressed idempotency key when the caller supplies none.

    This is a deterministic fingerprint of the reservation's identifying content, so the
    same request in the same window yields the same key. It is NOT a random token: a
    random value under the name `idempotency_key` would satisfy the schema while making
    the field meaningless.

    Callers that own a real request-level key should pass it explicitly. Note that
    `quota_reservations` has no column for either form, so the key exists only on the record
    the caller holds — see the module docstring.
    """
    fingerprint = "|".join([
        tenant_id,
        capability_id,
        str(reserved_quantity),
        quota_window.value,
        window_starts_at.isoformat(),
        correlation_id,
    ])
    return f"qres_{hashlib.sha256(fingerprint.encode('utf-8')).hexdigest()[:32]}"


@dataclass(frozen=True)
class MeteredEvent:
    event_id: str
    tenant_id: str
    principal_id: str
    context_id: str
    capability_id: str
    quantity: int
    unit: MeteredUnit
    timestamp: datetime
    correlation_id: str
    idempotency_key: str

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "tenant_id": self.tenant_id,
            "principal_id": self.principal_id,
            "context_id": self.context_id,
            "capability_id": self.capability_id,
            "quantity": self.quantity,
            "unit": self.unit.value,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "idempotency_key": self.idempotency_key
        }


@dataclass(frozen=True)
class QuotaReservation:
    """
    An atomic hold on quota, named to match contracts/schemas/quota-reservation.schema.json.

    The schema sets `additionalProperties: false` and requires eleven properties, so
    `to_dict()` must emit exactly those eleven. Four of them —`quota_window`,
    `window_starts_at`, `window_ends_at` and `idempotency_key` — have no column in
    `quota_reservations`, so an instance of this type carries more than the database holds.
    That asymmetry is why the transition methods take an instance rather than an identifier.
    """

    reservation_id: str
    tenant_id: str
    capability_id: str
    reserved_quantity: int
    quota_window: QuotaWindow
    window_starts_at: datetime
    window_ends_at: datetime
    expires_at: datetime
    status: str
    correlation_id: str
    idempotency_key: str

    def to_dict(self) -> dict:
        return {
            "reservation_id": self.reservation_id,
            "tenant_id": self.tenant_id,
            "capability_id": self.capability_id,
            "reserved_quantity": self.reserved_quantity,
            "quota_window": self.quota_window.value,
            "window_starts_at": self.window_starts_at.isoformat(),
            "window_ends_at": self.window_ends_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status,
            "correlation_id": self.correlation_id,
            "idempotency_key": self.idempotency_key
        }


class OutboxDispatcher:
    """The sink an outbox drains into.

    It receives stored rows rather than `MeteredEvent`s because a stored row is what the
    database holds; a `MeteredEvent` would have to invent the `context_id` the table has no
    column for. A dispatcher that reports success on a record it partly invented is not
    evidence that the record was delivered.
    """

    def __init__(self):
        self._dispatched: List[StoredOutboxRecord] = []

    def dispatch(self, records: Sequence[StoredOutboxRecord]) -> int:
        count = len(records)
        self._dispatched.extend(records)
        return count

    def get_dispatched(self) -> List[StoredOutboxRecord]:
        return list(self._dispatched)


class UsageMeterService:
    """Metered usage ingestion, transactional outbox, and quota reservations on PostgreSQL.

    The service holds no state. Every method opens a tenant-scoped transaction through the
    repositories, so two processes running this service deduplicate against the same unique
    index rather than against two dictionaries that have never met.
    """

    def __init__(
        self,
        *,
        outbox: Optional[UsageOutboxRepository] = None,
        reservations: Optional[QuotaReservationRepository] = None,
        balances: Optional[MeterBalanceRepository] = None,
        dispatcher: Optional[OutboxDispatcher] = None,
    ):
        self._outbox = outbox or UsageOutboxRepository()
        self._reservations = reservations or QuotaReservationRepository()
        self._balances = balances or MeterBalanceRepository()
        self._dispatcher = dispatcher or OutboxDispatcher()

    # -- metered events -------------------------------------------------------------------

    def record_event(
        self,
        tenant_id: str,
        principal_id: str,
        context_id: str,
        capability_id: str,
        quantity: int,
        unit: MeteredUnit,
        correlation_id: str,
        idempotency_key: str
    ) -> MeteredEvent:
        """Append a metered usage event to the transactional outbox.

        The write is one statement — `INSERT ... ON CONFLICT (tenant_id, idempotency_key) DO
        NOTHING` — followed by a re-SELECT when it conflicted, so a replay returns the row that
        was stored rather than a new event carrying the same key. The guard is the unique
        constraint, which means it holds across processes and across restarts; the dictionary
        it replaces held only within one process's lifetime.

        A second tenant using the same idempotency key is not an error and is not observable.
        The constraint is on `(tenant_id, idempotency_key)`, so that tenant gets its own row,
        and the isolation policy means neither tenant can see that the other holds the key.
        The previous global registry raised instead, and named the owning tenant while doing
        it.

        A replay whose payload differs from the stored one is still refused, because returning
        the stored event would silently discard the caller's differing numbers.

        `context_id` is returned as passed. `usage_outbox` has no column for it, so on a replay
        this is the only field that comes from the call rather than from the stored row.
        """
        if quantity <= 0:
            raise InvalidQuantityError(
                f"Quantity must be a positive integer > 0, got {quantity}"
            )

        stored, created = self._outbox.record(
            tenant_id=tenant_id,
            principal_id=principal_id,
            capability_id=capability_id,
            quantity=quantity,
            unit=unit.value,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
        )

        if not created:
            conflicts = []
            if stored.principal_id != principal_id:
                conflicts.append(
                    f"principal_id stored={stored.principal_id!r} replayed={principal_id!r}"
                )
            if stored.capability_id != capability_id:
                conflicts.append(
                    f"capability_id stored={stored.capability_id!r} "
                    f"replayed={capability_id!r}"
                )
            if stored.quantity != quantity:
                conflicts.append(
                    f"quantity stored={stored.quantity} replayed={quantity}"
                )
            if stored.unit != unit.value:
                conflicts.append(f"unit stored={stored.unit!r} replayed={unit.value!r}")
            if conflicts:
                raise IdempotencyPayloadConflictError(
                    f"idempotency key {idempotency_key!r} was already used by this tenant "
                    f"with a different payload: " + "; ".join(conflicts)
                )

        return self._to_event(stored, context_id)

    @staticmethod
    def _to_event(stored: StoredOutboxRecord, context_id: str) -> MeteredEvent:
        return MeteredEvent(
            event_id=stored.event_id,
            tenant_id=stored.tenant_id,
            principal_id=stored.principal_id,
            context_id=context_id,
            capability_id=stored.capability_id,
            quantity=stored.quantity,
            unit=MeteredUnit(stored.unit),
            timestamp=stored.created_at,
            correlation_id=stored.correlation_id,
            idempotency_key=stored.idempotency_key,
        )

    # -- outbox ---------------------------------------------------------------------------

    def get_outbox_events(self, tenant_id: str) -> Sequence[StoredOutboxRecord]:
        """Every outbox row this tenant owns, dispatched or not.

        Returns stored rows rather than `MeteredEvent`s: the table has no `context_id`, so a
        `MeteredEvent` could only be produced by inventing one.

        The length of this list is not a measure of outstanding work. Dispatch marks and keeps,
        so the list only grows. Use `get_pending_outbox_events` for what has not been sent.
        """
        return self._outbox.list_all(tenant_id)

    def get_pending_outbox_events(self, tenant_id: str) -> Sequence[StoredOutboxRecord]:
        """The rows with `dispatched_at IS NULL` — what a dispatcher run would pick up."""
        return self._outbox.list_pending(tenant_id)

    def dispatch_outbox(self, tenant_id: str) -> int:
        """Dispatch every undispatched row and stamp `dispatched_at` on it. Returns the count.

        Nothing is deleted. The previous implementation called `self._outbox.clear()`, which
        destroyed the record of what had been sent: after it ran, "was this event delivered?"
        and "did this event ever exist?" had the same answer.

        The sink runs inside the same transaction as the stamping, so a sink that raises leaves
        the rows pending and the next run retries them.
        """
        records = self._outbox.mark_dispatched(
            tenant_id, sink=lambda rows: self._dispatcher.dispatch(rows)
        )
        return len(records)

    # -- quota ----------------------------------------------------------------------------

    def provision_quota(
        self,
        tenant_id: str,
        capability_id: str,
        quota_limit: int,
        quota_window: QuotaWindow = QuotaWindow.MONTHLY,
        at: Optional[datetime] = None,
    ) -> StoredBalance:
        """Ensure a `usage_meter_balances` row exists for the window containing `at`.

        A balance row is what a reservation holds against, so an allowance that has never been
        provisioned cannot be reserved from — `create_quota_reservation` refuses rather than
        creating a hold against nothing. `quota_limit` comes from the tenant's plan, which is
        the entitlement layer's concern; this method only writes what it is told.
        """
        window_start, window_end = current_window_bounds(quota_window, at)
        return self._balances.provision(
            tenant_id=tenant_id,
            capability_id=capability_id,
            quota_limit=quota_limit,
            window_start=window_start,
            window_end=window_end,
        )

    def get_quota_balance(
        self,
        tenant_id: str,
        capability_id: str,
        quota_window: QuotaWindow = QuotaWindow.MONTHLY,
        at: Optional[datetime] = None,
    ) -> Optional[StoredBalance]:
        window_start, _ = current_window_bounds(quota_window, at)
        return self._balances.get(tenant_id, capability_id, window_start)

    def create_quota_reservation(
        self,
        tenant_id: str,
        capability_id: str,
        reserved_quantity: int,
        expires_at: datetime,
        correlation_id: str,
        quota_window: QuotaWindow = QuotaWindow.MONTHLY,
        idempotency_key: Optional[str] = None
    ) -> QuotaReservation:
        """
        Place a hold on quota: one transaction, one increment of `used_quantity`, one row.

        The hold is what makes this a reservation. Before this change the method wrote a
        dataclass into a dictionary and decremented nothing, so no sequence of reservations
        could ever exceed a quota and the guarantee the type is named for was made nowhere.
        Now `chk_balance_within_quota` refuses the increment, in the database, for any writer.

        The window is read from the balance row the hold lands on rather than computed here.
        A computed window is a second opinion about which allowance is in force, and at a
        boundary the two disagree; the row that exists is the allowance that exists. The
        caller's declared `quota_window` is then checked against that row's actual length, so a
        daily reservation cannot report month-long bounds — which would over-report the
        tenant's allowance by roughly thirty times while validating perfectly against the
        schema.

        `idempotency_key` is content-derived when absent. `quota_reservations` has no column
        for it, so it is not a dedup key here in the way it is for `record_event`: two
        identical calls produce two reservations and two holds. That gap is real and is
        recorded in the module docstring rather than implied away.
        """
        if reserved_quantity <= 0:
            raise InvalidQuantityError(
                f"Reserved quantity must be a positive integer > 0, got {reserved_quantity}"
            )

        stored, balance = self._reservations.create(
            tenant_id=tenant_id,
            capability_id=capability_id,
            reserved_quantity=reserved_quantity,
            expires_at=expires_at,
            correlation_id=correlation_id,
        )

        window_starts_at = balance.window_start
        window_ends_at = balance.window_end
        self._assert_window_matches(quota_window, window_starts_at, window_ends_at)

        return QuotaReservation(
            reservation_id=stored.reservation_id,
            tenant_id=stored.tenant_id,
            capability_id=stored.capability_id,
            reserved_quantity=stored.reserved_quantity,
            quota_window=quota_window,
            window_starts_at=window_starts_at,
            window_ends_at=window_ends_at,
            expires_at=stored.expires_at,
            status=stored.status,
            correlation_id=stored.correlation_id,
            idempotency_key=idempotency_key or _derive_idempotency_key(
                tenant_id, capability_id, reserved_quantity,
                quota_window, window_starts_at, correlation_id
            )
        )

    @staticmethod
    def _assert_window_matches(
        quota_window: QuotaWindow, window_start: datetime, window_end: datetime
    ) -> None:
        length = window_end - window_start
        if quota_window is QuotaWindow.DAILY and length != timedelta(days=1):
            raise AmbiguousQuotaWindowError(
                f"reservation declares a daily window but the balance row it holds against "
                f"spans {length}; reporting the declared window would misstate the allowance"
            )
        if quota_window is QuotaWindow.MONTHLY and not (
            timedelta(days=28) <= length <= timedelta(days=31)
        ):
            raise AmbiguousQuotaWindowError(
                f"reservation declares a monthly window but the balance row it holds against "
                f"spans {length}; reporting the declared window would misstate the allowance"
            )

    def commit_reservation(self, reservation: QuotaReservation) -> QuotaReservation:
        """Turn a pending hold into consumption, refusing one that has since expired.

        Takes the record rather than an identifier because `quota_reservations` stores neither
        the window bounds nor the idempotency key, so an identifier alone cannot rebuild a
        contract-valid result. The presented record is not trusted: every field the table does
        store is compared against the stored row inside the same transaction as the transition,
        so a caller cannot commit against a larger quantity or a later expiry than the database
        holds.

        The expiry comparison is the F-2 residue this closes. `chk_reservation_expiry_future`
        compares `expires_at` to `created_at`, both fixed at insert, so it can reject a
        reservation that was born expired and nothing else. A reservation that lapsed between
        creation and commit is refused here, marked `expired`, and its hold returned to the
        balance.

        `replace` copies every field by construction. Enumerating fields by hand is how a
        transition silently drops a property that was added to the dataclass later.
        """
        stored = self._reservations.commit(
            reservation.tenant_id,
            reservation.reservation_id,
            window_start=reservation.window_starts_at,
            expect_capability_id=reservation.capability_id,
            expect_reserved_quantity=reservation.reserved_quantity,
            expect_correlation_id=reservation.correlation_id,
            expect_expires_at=reservation.expires_at,
        )
        return replace(reservation, status=stored.status)

    def release_reservation(self, reservation: QuotaReservation) -> QuotaReservation:
        """Return a pending hold to the balance.

        Only a `pending` reservation may be released, which is what stops a second release
        from decrementing `used_quantity` twice and handing the tenant free allowance.
        """
        stored = self._reservations.release(
            reservation.tenant_id,
            reservation.reservation_id,
            window_start=reservation.window_starts_at,
            expect_capability_id=reservation.capability_id,
            expect_reserved_quantity=reservation.reserved_quantity,
            expect_correlation_id=reservation.correlation_id,
            expect_expires_at=reservation.expires_at,
        )
        return replace(reservation, status=stored.status)

    def get_reservation(self, tenant_id: str, reservation_id: str) -> StoredReservation:
        """The stored row, which is eight of the eleven contract fields. See the module note."""
        return self._reservations.get(tenant_id, reservation_id)
