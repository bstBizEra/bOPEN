"""
bOPEN Correlated Audit Dispatcher v1.0
Dispatches structured security audit events matching contracts/schemas/audit-event.json v1.0.0
"""

import math
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

# Whether an event belongs to a tenant is a statement the *producer* makes, not something a
# consumer should reconstruct by inspecting the identifier.
#
#   tenant   the event belongs to a resolved tenant, and tenant_id identifies it
#   unknown  no tenant could be resolved — an authentication failure, an absent membership
#   scoped   deliberately not tenant-specific — a revocation sweep across contexts
#
# `lifecycle_events` has modelled this correctly since migration 005: `chk_lifecycle_scope`
# constrains the column to these three values and `chk_lifecycle_tenant_agreement` requires the
# identifier and the scope to agree. The envelope did not carry the field, so the sink had to
# rebuild it by matching `tenant_id` against a list of magic strings — and on the context-switch
# denial path that identifier comes straight from the request body. Security review on
# 2026-07-30 found the consequence and it reproduces: a caller who names their tenant with the
# literal string `unknown` moves their own denial into the bucket the tenant cannot read.
#
#     same denial, tenant_id = <the real tenant>   -> visible in the tenant's audit trail
#     same denial, tenant_id = "unknown"           -> written with a NULL tenant, unreadable
#
# Carrying the scope explicitly is what removes the magic word: `unknown` becomes one
# unresolvable string among infinitely many, and which bucket an event lands in is decided by
# the producer parsing the value, never by the caller choosing it.
TENANT_SCOPES = frozenset({"tenant", "unknown", "scoped"})

_JWT_LIKE = re.compile(r"^ey[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.")
_SAML_LIKE = re.compile(r"<\s*(saml[0-9]*:)?(Assertion|Response)\b", re.IGNORECASE)


class AuditContractError(Exception):
    """Raised when an audit event violates the Phase 2 audit contract."""
    code = "AUDIT_REQUIRED"


# Metadata nests no deeper than this. Every shape produced by the kernel today is one
# level (scalars, and arrays of scalars), so the bound is not a constraint on real callers;
# it exists so that a self-referential structure terminates as a contract error rather than
# as a RecursionError, which would not be an AuditContractError and would surface as a 500.
_MAX_METADATA_DEPTH = 4


def _reject_prohibited(metadata: Dict[str, Any]) -> None:
    """Refuse metadata that is credential-bearing, unstorable, or unbounded.

    INV-P2-018 says no raw credential, assertion, authorization code or token may be logged
    or evidenced. This is the enforcement point: the last thing between a producer's mistake
    and a durable row.

    It previously walked `metadata.items()` once and applied `isinstance(value, str)`, so it
    saw only the top level. Security review on 2026-07-30 reproduced the consequence, and
    measurement widened it — ten of twelve probe shapes were accepted, including:

        {'token': jwt}                 -> refused      (the only shape it was written for)
        {'d': {'token': jwt}}          -> ACCEPTED     credential persisted
        {'d': [jwt]}                   -> ACCEPTED     credential persisted
        {'d': [{'password': '...'}]}   -> ACCEPTED     credential persisted
        {'d': {1: jwt}}                -> ACCEPTED     and json.dumps coerced the key to '1'
        {'d': b'...'} / {'d': object()}-> ACCEPTED     sink raises TypeError, event lost
        {'d': float('nan')}            -> ACCEPTED     json.dumps emits bare NaN, which is
                                                       not JSON; PostgreSQL refuses the
                                                       insert (measured), event lost

    The root cause is one decision, not three bugs: the check enumerated what is forbidden
    and let everything else through. A deny-list over an open value space is incomplete by
    construction, and every future container type reopens it.

    So the check now bounds what is *permitted*. Metadata is stored as `jsonb`, and the JSON
    value space is exactly object / array / string / number / bool / null — a closed set.
    Anything outside it cannot be stored faithfully anyway: a tuple reads back as a list, an
    int key reads back as a string, bytes and arbitrary objects do not serialise at all. The
    walk therefore recurses through objects and arrays applying the key prohibition and the
    credential-shape scan at every depth, and refuses any other type outright.

    That closes the enumeration in the direction that matters: a shape nobody anticipated is
    now refused rather than accepted. Errors name the path (`metadata.d[0].token`) so the
    producer can find it.

    Two limits worth stating plainly. The key list and the value patterns remain heuristics —
    a credential in a key named `note`, with no JWT or SAML shape, still passes, and no
    check at this layer can find it; not putting credentials in audit metadata remains the
    producer's obligation and this is a net beneath it, not a substitute. And refusal is
    total: a violating event is not written at all, so INV-P2-018 is enforced at the cost of
    INV-P2-017 for that event. That trade is deliberate — a lost audit row is recoverable
    from the operation that failed with it, a leaked credential in an append-only table is
    not — but it means a producer bug takes down the operation, which is the correct
    pressure to put on a producer bug.
    """
    _walk_metadata(metadata, "metadata", 0)


def _walk_metadata(value: Any, path: str, depth: int) -> None:
    if depth > _MAX_METADATA_DEPTH:
        raise AuditContractError(
            f"Audit metadata nests deeper than {_MAX_METADATA_DEPTH} levels at {path}. "
            f"Flatten it, or check for a self-referential structure."
        )

    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise AuditContractError(
                    f"Audit metadata key at {path} is {type(key).__name__}, not str: {key!r}. "
                    f"json.dumps would coerce it to a string, so the stored key would differ "
                    f"from the one written — and a non-string key cannot be matched against "
                    f"the prohibited-key list."
                )
            if key.lower() in PROHIBITED_METADATA_KEYS:
                raise AuditContractError(f"Prohibited audit metadata key: {path}.{key}")
            _walk_metadata(item, f"{path}.{key}", depth + 1)
        return

    if isinstance(value, list):
        for index, item in enumerate(value):
            _walk_metadata(item, f"{path}[{index}]", depth + 1)
        return

    if isinstance(value, str):
        if _JWT_LIKE.match(value) or _SAML_LIKE.search(value):
            raise AuditContractError(f"Prohibited credential-like value at {path}")
        return

    # bool before int: bool is a subclass of int, and both are storable, so the order only
    # matters for readability here — but it matters for the float branch below.
    if value is None or isinstance(value, (bool, int)):
        return

    if isinstance(value, float):
        if not math.isfinite(value):
            raise AuditContractError(
                f"Audit metadata value at {path} is {value!r}, which json.dumps emits as a "
                f"bare NaN/Infinity token. That is not valid JSON and PostgreSQL refuses the "
                f"insert, so the event would be lost rather than recorded."
            )
        return

    raise AuditContractError(
        f"Unsupported audit metadata type at {path}: {type(value).__name__}. Metadata is "
        f"stored as jsonb, so values must be object, array, string, number, bool or null. "
        f"Convert it at the call site, where its meaning is known."
    )


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
        tenant_scope: str = "tenant",
    ) -> Dict[str, Any]:
        """
        Emit a bounded Phase 2 lifecycle audit event (BOPEN-IDP-001 15).

        Enforces INV-P2-017 (all security-relevant outcomes audited) and
        INV-P2-018 (no credential, assertion or token in evidence).

        `tenant_scope` defaults to `tenant`, so a producer that says nothing is asserting the
        event belongs to a resolved tenant, and the sink will refuse to store it if `tenant_id`
        is not a tenant identifier. That default is the safe one: the failure it produces is a
        loud persistence error naming the producer, whereas defaulting to `unknown` would file
        the event where nobody is looking. See `TENANT_SCOPES`.

        A producer that cannot resolve a tenant passes the scope explicitly. It does not need
        to pass a matching `tenant_id`: the envelope value is derived from the scope below, so
        the two cannot disagree, and whatever the caller actually supplied belongs in
        `metadata` where it is evidence rather than routing.
        """
        if event_type not in PHASE2_EVENT_TYPES:
            raise AuditContractError(f"Unknown Phase 2 audit event type: {event_type}")
        if outcome not in {"success", "deny", "failure"}:
            raise AuditContractError(f"Unsupported audit outcome: {outcome}")
        if tenant_scope not in TENANT_SCOPES:
            raise AuditContractError(
                f"Unsupported tenant scope: {tenant_scope!r}. Expected one of "
                f"{sorted(TENANT_SCOPES)}."
            )
        if tenant_scope == "tenant" and not str(tenant_id or "").strip():
            raise AuditContractError(
                "an event declaring tenant scope must carry a tenant identifier; pass "
                "tenant_scope='unknown' if no tenant could be resolved"
            )

        # Derived, never passed through. A producer with no tenant has nothing meaningful to put
        # here, and letting it supply one is exactly how a request-controlled string reached the
        # routing decision.
        if tenant_scope != "tenant":
            tenant_id = tenant_scope

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
            "tenant_scope": tenant_scope,
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
