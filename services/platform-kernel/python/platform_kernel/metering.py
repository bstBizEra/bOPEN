"""
bOPEN Usage Metering & Outbox Service v1.0 (WP-P3-05 / BOPEN-ENT-001).

Manages high-throughput metered usage event ingestion, tenant-isolated idempotency deduplication,
atomic quota reservations, and transactional outbox record creation.
Matches contracts/schemas/usage-metered-event.schema.json.
"""

from __future__ import annotations
import hashlib
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple
import uuid
from kernel_core.types import ContextPayload


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

    Callers that own a real request-level key should pass it explicitly. See the module
    note on `create_quota_reservation` — the reservation path currently has no dedup index
    keyed on this value, unlike `record_event`.
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


class CrossTenantIdempotencyViolationError(Exception):
    """Raised when an idempotency key is reused across different tenants or mismatched payloads."""
    pass


class InvalidQuantityError(Exception):
    """Raised when quantity <= 0."""
    pass


class QuotaReservationError(Exception):
    """Raised when quota reservation fails or expires."""
    pass


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
    `to_dict()` must emit exactly those eleven. Before this change the type had no
    `to_dict()` at all, which is why the divergence was invisible: a contract test that
    never serializes an instance cannot detect that the instance is unserializable.
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
    def __init__(self):
        self._dispatched: List[MeteredEvent] = []

    def dispatch(self, events: List[MeteredEvent]) -> int:
        count = len(events)
        self._dispatched.extend(events)
        return count

    def get_dispatched(self) -> List[MeteredEvent]:
        return list(self._dispatched)


class UsageMeterService:
    def __init__(self):
        self._events: Dict[str, MeteredEvent] = {}  # event_id -> event
        self._idempotency_index: Dict[Tuple[str, str], MeteredEvent] = {}  # (tenant_id, idempotency_key) -> event
        self._global_idempotency_keys: Dict[str, str] = {}  # idempotency_key -> tenant_id
        self._outbox: List[MeteredEvent] = []
        self._reservations: Dict[str, QuotaReservation] = {}
        self._dispatcher = OutboxDispatcher()

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
        # Reject negative/zero quantity (Finding 3)
        if quantity <= 0:
            raise InvalidQuantityError(f"Quantity must be a positive integer > 0, got {quantity}")

        # Cross-tenant idempotency key reuse check (Finding 1)
        if idempotency_key in self._global_idempotency_keys:
            existing_tenant = self._global_idempotency_keys[idempotency_key]
            if existing_tenant != tenant_id:
                raise CrossTenantIdempotencyViolationError(
                    f"Cross-tenant idempotency violation: Key '{idempotency_key}' is owned by tenant '{existing_tenant}'"
                )

        key = (tenant_id, idempotency_key)

        # Idempotency replay check with payload fingerprint verification (Finding 1)
        if key in self._idempotency_index:
            existing = self._idempotency_index[key]
            if (existing.principal_id != principal_id or
                existing.capability_id != capability_id or
                existing.quantity != quantity or
                existing.unit != unit):
                raise CrossTenantIdempotencyViolationError(
                    f"Idempotency key '{idempotency_key}' reused with conflicting payload"
                )
            return existing


        event = MeteredEvent(
            event_id=f"evt_mtr_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            principal_id=principal_id,
            context_id=context_id,
            capability_id=capability_id,
            quantity=quantity,
            unit=unit,
            timestamp=datetime.now(timezone.utc),
            correlation_id=correlation_id,
            idempotency_key=idempotency_key
        )
        self._events[event.event_id] = event
        self._idempotency_index[key] = event
        self._global_idempotency_keys[idempotency_key] = tenant_id
        self._outbox.append(event)
        return event


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
        Place a pending hold on quota.

        `quota_window` defaults to monthly to match the `window` declared by the metered
        allowance plan tiers this service reserves against; pass it explicitly for daily
        capabilities. Window bounds are computed from the creation instant rather than
        accepted as input, so they always describe the window the reservation is in.

        `idempotency_key` is content-derived when absent. Note this service does not yet
        index reservations by that key, so two identical calls produce two reservations
        with the same key and different `reservation_id`s. That is a real gap in the
        reservation path, not something the key derivation papers over.
        """
        if reserved_quantity <= 0:
            raise InvalidQuantityError(f"Reserved quantity must be a positive integer > 0, got {reserved_quantity}")
        res_id = f"res_{uuid.uuid4().hex[:12]}"
        window_starts_at, window_ends_at = _window_bounds(quota_window, datetime.now(timezone.utc))
        reservation = QuotaReservation(
            reservation_id=res_id,
            tenant_id=tenant_id,
            capability_id=capability_id,
            reserved_quantity=reserved_quantity,
            quota_window=quota_window,
            window_starts_at=window_starts_at,
            window_ends_at=window_ends_at,
            expires_at=expires_at,
            status="pending",
            correlation_id=correlation_id,
            idempotency_key=idempotency_key or _derive_idempotency_key(
                tenant_id, capability_id, reserved_quantity,
                quota_window, window_starts_at, correlation_id
            )
        )
        self._reservations[res_id] = reservation
        return reservation

    def commit_reservation(self, reservation_id: str) -> QuotaReservation:
        if reservation_id not in self._reservations:
            raise QuotaReservationError(f"Reservation {reservation_id} not found")
        # `replace` copies every field by construction. Enumerating fields by hand is how a
        # transition silently drops a property that was added to the dataclass later.
        committed = replace(self._reservations[reservation_id], status="committed")
        self._reservations[reservation_id] = committed
        return committed

    def release_reservation(self, reservation_id: str) -> QuotaReservation:
        if reservation_id not in self._reservations:
            raise QuotaReservationError(f"Reservation {reservation_id} not found")
        released = replace(self._reservations[reservation_id], status="released")
        self._reservations[reservation_id] = released
        return released

    def get_outbox_events(self) -> List[MeteredEvent]:
        return list(self._outbox)

    def dispatch_outbox(self) -> int:
        events = list(self._outbox)
        count = self._dispatcher.dispatch(events)
        self._outbox.clear()
        return count
