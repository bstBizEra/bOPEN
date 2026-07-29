"""
bOPEN Usage Metering & Outbox Service v1.0 (WP-P3-05 / BOPEN-ENT-001).

Manages high-throughput metered usage event ingestion, tenant-isolated idempotency deduplication,
atomic quota reservations, and transactional outbox record creation.
Matches contracts/schemas/usage-metered-event.schema.json.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple
import uuid
from kernel_core.types import ContextPayload


class MeteredUnit(str, Enum):
    REQUESTS = "requests"
    BYTES = "bytes"
    SEATS = "seats"
    SECONDS = "seconds"


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
    reservation_id: str
    tenant_id: str
    capability_id: str
    reserved_quantity: int
    expires_at: datetime
    status: str
    correlation_id: str


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
        correlation_id: str
    ) -> QuotaReservation:
        if reserved_quantity <= 0:
            raise InvalidQuantityError(f"Reserved quantity must be a positive integer > 0, got {reserved_quantity}")
        res_id = f"res_{uuid.uuid4().hex[:12]}"
        reservation = QuotaReservation(
            reservation_id=res_id,
            tenant_id=tenant_id,
            capability_id=capability_id,
            reserved_quantity=reserved_quantity,
            expires_at=expires_at,
            status="pending",
            correlation_id=correlation_id
        )
        self._reservations[res_id] = reservation
        return reservation

    def commit_reservation(self, reservation_id: str) -> QuotaReservation:
        if reservation_id not in self._reservations:
            raise QuotaReservationError(f"Reservation {reservation_id} not found")
        old = self._reservations[reservation_id]
        committed = QuotaReservation(
            reservation_id=old.reservation_id,
            tenant_id=old.tenant_id,
            capability_id=old.capability_id,
            reserved_quantity=old.reserved_quantity,
            expires_at=old.expires_at,
            status="committed",
            correlation_id=old.correlation_id
        )
        self._reservations[reservation_id] = committed
        return committed

    def release_reservation(self, reservation_id: str) -> QuotaReservation:
        if reservation_id not in self._reservations:
            raise QuotaReservationError(f"Reservation {reservation_id} not found")
        old = self._reservations[reservation_id]
        released = QuotaReservation(
            reservation_id=old.reservation_id,
            tenant_id=old.tenant_id,
            capability_id=old.capability_id,
            reserved_quantity=old.reserved_quantity,
            expires_at=old.expires_at,
            status="released",
            correlation_id=old.correlation_id
        )
        self._reservations[reservation_id] = released
        return released

    def get_outbox_events(self) -> List[MeteredEvent]:
        return list(self._outbox)

    def dispatch_outbox(self) -> int:
        events = list(self._outbox)
        count = self._dispatcher.dispatch(events)
        self._outbox.clear()
        return count
