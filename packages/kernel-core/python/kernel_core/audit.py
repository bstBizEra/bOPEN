"""
bOPEN Correlated Audit Dispatcher v1.0
Dispatches structured security audit events matching contracts/schemas/audit-event.json v1.0.0
"""

import re
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Protocol

# Phase 2 audit event catalog (BOPEN-IDP-001 15). Unknown event types are rejected.
PHASE2_EVENT_TYPES = frozenset({
    "invitation.issued",
    "invitation.accepted",
    "invitation.declined",
    "invitation.expired",
    "invitation.validation_failed",
    "membership.transitioned",
    "membership.transition_denied",
    "identity.connection_verified",
    "identity.authentication_succeeded",
    "identity.authentication_denied",
    "identity.linked",
    "identity.link_denied",
    "scim.user_provisioned",
    "scim.user_updated",
    "scim.user_deprovisioned",
    "scim.group_mapping_applied",
    "scim.event_denied",
    "context.issued",
    "context.switched",
    "context.switch_denied",
    "context.revoked",
    "delegation.created",
    "delegation.activated",
    "delegation.revoked",
    "delegation.expired",
})

# INV-P2-018: no raw credential, assertion, authorization code or token may be
# logged or evidenced. Metadata keys are allowlist-shaped by prohibition here.
PROHIBITED_METADATA_KEYS = frozenset({
    "password", "secret", "token", "access_token", "id_token", "refresh_token",
    "invitation_token", "raw_token", "bearer", "authorization", "assertion",
    "saml_assertion", "saml_response", "code", "authorization_code",
    "client_secret", "private_key", "api_key", "credential", "cookie",
})

_JWT_LIKE = re.compile(r"^ey[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.")
_SAML_LIKE = re.compile(r"<\s*(saml[0-9]*:)?(Assertion|Response)\b", re.IGNORECASE)


class AuditContractError(Exception):
    """Raised when an audit event violates the Phase 2 audit contract."""
    code = "AUDIT_REQUIRED"


def _reject_prohibited(metadata: Dict[str, Any]) -> None:
    for key, value in metadata.items():
        if key.lower() in PROHIBITED_METADATA_KEYS:
            raise AuditContractError(f"Prohibited audit metadata key: {key}")
        if isinstance(value, str) and (_JWT_LIKE.match(value) or _SAML_LIKE.search(value)):
            raise AuditContractError(f"Prohibited credential-like value in metadata key: {key}")


class LifecycleEventSink(Protocol):
    """Where lifecycle audit events are made durable.

    A Protocol because `kernel_core` imports `platform_kernel` zero times and must keep doing so.
    The PostgreSQL implementation lives in `platform_kernel.audit_repositories`.
    """

    def record(self, event: Dict[str, Any]) -> None:
        ...


class AuditDispatcher:
    """Emits audit events and hands them to a sink.

    The sink is required and has no default, which is a deliberate departure from how this class
    used to work. It previously appended to `self.logs` and nothing else, so every Phase 2 audit
    record — invitation, membership transition, SCIM, context switch, delegation — was lost on
    restart and differed per worker. An audit trail that does not survive the process it
    describes is not an audit trail, and a default sink would let that state return quietly.

    `self.logs` remains as an in-process view for callers that inspect what was emitted during a
    single operation. It is not storage and must not be read as such.
    """

    def __init__(self, sink: LifecycleEventSink):
        self.logs: List[Dict[str, Any]] = []
        self._sink = sink

    def dispatch(
        self,
        actor_id: str,
        tenant_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        status: str,
        correlation_id: str,
        reason_code: str = "MEMBERSHIP_ROLE_PERMITTED"
    ) -> Dict[str, Any]:
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "security.authorization.decision",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor_id": actor_id,
            "tenant_id": tenant_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "status": status,
            "reason_code": reason_code,
            "correlation_id": correlation_id
        }
        self.logs.append(event)
        return event

    def emit_authorization_audit(
        self,
        correlation_id: str,
        actor_id: str,
        tenant_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        decision: Any,
        reason_code: str
    ) -> Dict[str, Any]:
        status_str = "SUCCESS" if str(getattr(decision, "value", decision)).upper() == "ALLOW" else "DENIED"
        return self.dispatch(
            actor_id=actor_id,
            tenant_id=tenant_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status_str,
            correlation_id=correlation_id,
            reason_code=reason_code
        )

    def emit_lifecycle_event(
        self,
        event_type: str,
        correlation_id: str,
        actor_id: str,
        tenant_id: str,
        subject_type: str,
        subject_id: str,
        outcome: str,
        reason_code: str,
        metadata: Optional[Dict[str, Any]] = None,
        causation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Emit a bounded Phase 2 lifecycle audit event (BOPEN-IDP-001 15).

        Enforces INV-P2-017 (all security-relevant outcomes audited) and
        INV-P2-018 (no credential, assertion or token in evidence).
        """
        if event_type not in PHASE2_EVENT_TYPES:
            raise AuditContractError(f"Unknown Phase 2 audit event type: {event_type}")
        if outcome not in {"success", "deny", "failure"}:
            raise AuditContractError(f"Unsupported audit outcome: {outcome}")

        bounded = dict(metadata or {})
        _reject_prohibited(bounded)

        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "event_version": 1,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id,
            "causation_id": causation_id,
            "actor_principal_id": actor_id,
            "tenant_id": tenant_id,
            "subject_type": subject_type,
            "subject_id": subject_id,
            "outcome": outcome,
            "reason_code": reason_code,
            "metadata": bounded,
        }
        self.logs.append(event)
        self._sink.record(event)
        return event

    def events_of_type(self, event_type: str) -> List[Dict[str, Any]]:
        return [e for e in self.logs if e.get("event_type") == event_type]
