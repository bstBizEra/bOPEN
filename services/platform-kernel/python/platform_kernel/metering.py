"""
bOPEN Usage Metering & Outbox Service v1.0 (WP-P3-05 / BOPEN-ENT-001).

Manages high-throughput metered usage event ingestion, idempotency deduplication,
and transactional outbox record creation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
import uuid


class MeteredUnit(str, Enum):
    REQUESTS = "requests"
    BYTES = "bytes"
    SEATS = "seats"
    SECONDS = "seconds"


@dataclass(frozen=True)
class MeteredEvent:
    event_id: str
    tenant_id: str
    principal_id: str
    capability_id: str
    quantity: int
    unit: MeteredUnit
    timestamp: datetime
    correlation_id: str
    idempotency_key: str


class UsageMeterService:
    def __init__(self):
        self._events: Dict[str, MeteredEvent] = {}  # event_id -> event
        self._idempotency_index: Dict[str, MeteredEvent] = {}  # idempotency_key -> event
        self._outbox: List[MeteredEvent] = []

    def record_event(
        self,
        tenant_id: str,
        principal_id: str,
        capability_id: str,
        quantity: int,
        unit: MeteredUnit,
        correlation_id: str,
        idempotency_key: str
    ) -> MeteredEvent:
        # Idempotency replay check
        if idempotency_key in self._idempotency_index:
            return self._idempotency_index[idempotency_key]

        event = MeteredEvent(
            event_id=f"evt_mtr_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            principal_id=principal_id,
            capability_id=capability_id,
            quantity=quantity,
            unit=unit,
            timestamp=datetime.now(timezone.utc),
            correlation_id=correlation_id,
            idempotency_key=idempotency_key
        )
        self._events[event.event_id] = event
        self._idempotency_index[idempotency_key] = event
        self._outbox.append(event)
        return event

    def get_outbox_events(self) -> List[MeteredEvent]:

        return list(self._outbox)
