"""
bOPEN Membership State Machine & Principal Invitation Engine v1.0

Milestones MILE-2.1 (Principal Invitation Engine) and MILE-2.2 (Membership State
Machine Engine).

Governing artifacts:
  - BOPEN-IDP-001 sections 6.4, 6.5 (invitation and membership domain model)
  - BOPEN-P2-001 sections 9, 10, 14 (commands, transition algorithm, error model)
  - contracts/schemas/membership-transition-matrix.json (pinned transition authority)
  - contracts/schemas/invitation.json

PROVISIONAL DECISIONS
---------------------
The BOPEN-P2-001 section 23 entry gate is not recorded and D-P2-001..D-P2-015 remain
OPEN. This module implements the plan's own section 21 recommended defaults so no
architecture is invented here. Each is marked PROVISIONAL and awaits Engineering
Authority ratification:

  D-P2-002  token digest scheme      -> versioned one-way digest via TokenHasher port
  D-P2-003  invitation lifetime      -> 7 days (DEFAULT_INVITATION_LIFETIME)
  D-P2-004  duplicate invitation     -> one active per (tenant, destination, purpose)
  D-P2-005  terminal-state semantics -> no implicit reactivation

See docs/evidence/phase-2/provisional-decisions.md.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple

from kernel_core.types import Membership, MembershipState
from kernel_core.audit import AuditDispatcher

# --------------------------------------------------------------------------------------
# Provisional defaults (BOPEN-P2-001 section 21)
# --------------------------------------------------------------------------------------

DEFAULT_INVITATION_LIFETIME = timedelta(days=7)          # D-P2-003 PROVISIONAL
MAX_INVITATION_LIFETIME = timedelta(days=30)             # bounded expiry guard
TOKEN_DIGEST_SCHEME = "sha256-v1"                        # D-P2-002 PROVISIONAL

_CONTRACT_PATH = (
    Path(__file__).resolve().parents[4] / "contracts" / "schemas" / "membership-transition-matrix.json"
)


# --------------------------------------------------------------------------------------
# Error model (BOPEN-P2-001 section 14.3)
# --------------------------------------------------------------------------------------

class KernelError(Exception):
    """Typed, stable domain error. Public message minimizes disclosure."""

    code = "INVALID_REQUEST"

    def __init__(self, message: str = "", detail: str = ""):
        super().__init__(message or self.code)
        self.detail = detail


class InvalidRequest(KernelError):
    code = "INVALID_REQUEST"


class Forbidden(KernelError):
    code = "FORBIDDEN"


class NotFoundOrNotAccessible(KernelError):
    code = "NOT_FOUND_OR_NOT_ACCESSIBLE"


class Conflict(KernelError):
    code = "CONFLICT"


class StaleVersion(KernelError):
    code = "STALE_VERSION"


class InvalidTransition(KernelError):
    code = "INVALID_TRANSITION"


class InvitationInvalid(KernelError):
    code = "INVITATION_INVALID"


class InvitationExpired(KernelError):
    code = "INVITATION_EXPIRED"


# --------------------------------------------------------------------------------------
# Enumerations
# --------------------------------------------------------------------------------------

class InvitationState(str, Enum):
    """Invitation state set (BOPEN-IDP-001 6.4). Distinct from MembershipState."""
    INVITED = "invited"
    ACTIVE = "active"
    DECLINED = "declined"
    EXPIRED = "expired"


class ActorType(str, Enum):
    """Actor types recognised by the pinned transition matrix."""
    TENANT_ADMIN = "tenant_admin"
    SECURITY_CONTROL = "security_control"
    SCIM_DIRECTORY = "scim_directory"
    INVITATION_SERVICE = "invitation_service"
    EXPIRY_SCHEDULER = "expiry_scheduler"
    PRINCIPAL = "principal"


# --------------------------------------------------------------------------------------
# Ports (BOPEN-IDP-001 section 5: injected clock; deterministic tests)
# --------------------------------------------------------------------------------------

class Clock(Protocol):
    def now(self) -> datetime: ...


class IdentifierFactory(Protocol):
    def new_id(self, prefix: str) -> str: ...


class TokenGenerator(Protocol):
    def generate(self) -> str: ...


class TokenHasher(Protocol):
    scheme: str

    def hash(self, raw_token: str) -> str: ...

    def verify(self, raw_token: str, digest: str) -> bool: ...


class TenantStateReader(Protocol):
    def is_active(self, tenant_id: str) -> bool: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class UuidIdentifierFactory:
    def new_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4()}"


class SecretsTokenGenerator:
    def generate(self) -> str:
        return secrets.token_urlsafe(32)


class Sha256TokenHasher:
    """
    PROVISIONAL (D-P2-002). Versioned one-way digest with constant-time comparison.

    BOPEN-P2-001 section 21 recommends a "versioned keyed or slow one-way digest".
    The scheme identifier is persisted with every invitation so the Engineering
    Authority can ratify a keyed or slow construction without rewriting the engine
    or re-hashing existing records.
    """

    scheme = TOKEN_DIGEST_SCHEME

    def hash(self, raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    def verify(self, raw_token: str, digest: str) -> bool:
        return hmac.compare_digest(self.hash(raw_token), digest)


# --------------------------------------------------------------------------------------
# Value objects
# --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Invitation:
    """Invitation record (BOPEN-IDP-001 6.4). The raw token is never held here."""
    invitation_id: str
    tenant_id: str
    email_normalized: str
    state: InvitationState
    token_digest: str
    token_digest_scheme: str
    invited_by_principal_id: str
    issued_at: datetime
    expires_at: datetime
    purpose: str = "membership"
    requested_roles: Tuple[str, ...] = ()
    requested_scopes: Tuple[str, ...] = ()
    principal_id: Optional[str] = None
    membership_id: Optional[str] = None
    accepted_at: Optional[datetime] = None
    declined_at: Optional[datetime] = None
    version: int = 1


@dataclass(frozen=True)
class ContextInvalidationObligation:
    """
    Recorded obligation to revoke or supersede active contexts (BOPEN-P2-001 10.6,
    14.2). Obligations are idempotent and retryable.
    """
    obligation_id: str
    tenant_id: str
    principal_id: str
    membership_id: str
    reason_code: str
    grant_action: str
    correlation_id: str
    recorded_at: datetime
    discharged: bool = False


@dataclass(frozen=True)
class TransitionReceipt:
    """Immutable membership transition receipt (BOPEN-P2-001 10.4 step 12)."""
    receipt_id: str
    membership_id: str
    tenant_id: str
    principal_id: str
    from_state: str
    to_state: str
    action: str
    actor_type: str
    actor_id: str
    reason_code: str
    resulting_version: int
    terminal: bool
    context_invalidation: bool
    grant_action: str
    effective_at: datetime
    correlation_id: str
    event_id: Optional[str] = None


@dataclass(frozen=True)
class TransitionCommand:
    """Command envelope for a membership transition (BOPEN-P2-001 10.4, 10.5)."""
    membership_id: str
    from_state: str
    to_state: str
    action: str
    actor_type: ActorType
    actor_id: str
    reason_code: str
    expected_version: int
    correlation_id: str
    idempotency_key: str
    invitation_id: Optional[str] = None
    reinstatement_preconditions_checked: bool = False


# --------------------------------------------------------------------------------------
# Deterministic in-memory adapters (Phase 2 test boundary)
# --------------------------------------------------------------------------------------

class InMemoryMembershipRepository:
    def __init__(self) -> None:
        self._items: Dict[str, Membership] = {}

    def save(self, membership: Membership) -> Membership:
        self._items[membership.id] = membership
        return membership

    def get(self, membership_id: str) -> Optional[Membership]:
        return self._items.get(membership_id)

    def find_for(self, tenant_id: str, principal_id: str) -> List[Membership]:
        return [
            m for m in self._items.values()
            if m.tenant_id == tenant_id and m.principal_id == principal_id
        ]

    def find_active(self, tenant_id: str, principal_id: str) -> Optional[Membership]:
        for m in self.find_for(tenant_id, principal_id):
            if m.state == MembershipState.ACTIVE:
                return m
        return None


class InMemoryInvitationRepository:
    def __init__(self) -> None:
        self._items: Dict[str, Invitation] = {}

    def save(self, invitation: Invitation) -> Invitation:
        self._items[invitation.invitation_id] = invitation
        return invitation

    def get(self, invitation_id: str) -> Optional[Invitation]:
        return self._items.get(invitation_id)

    def find_by_digest(self, digest: str) -> Optional[Invitation]:
        for inv in self._items.values():
            if hmac.compare_digest(inv.token_digest, digest):
                return inv
        return None

    def find_open(self, tenant_id: str, email_normalized: str, purpose: str) -> Optional[Invitation]:
        for inv in self._items.values():
            if (
                inv.tenant_id == tenant_id
                and inv.email_normalized == email_normalized
                and inv.purpose == purpose
                and inv.state == InvitationState.INVITED
            ):
                return inv
        return None

    def list_expirable(self, cutoff: datetime, limit: int) -> List[Invitation]:
        eligible = [
            inv for inv in self._items.values()
            if inv.state == InvitationState.INVITED and inv.expires_at <= cutoff
        ]
        eligible.sort(key=lambda i: (i.expires_at, i.invitation_id))
        return eligible[:limit]


class InMemoryIdempotencyStore:
    """
    Same key + equivalent payload returns the prior result; same key + different
    payload conflicts (BOPEN-P2-001 10.5).
    """

    def __init__(self) -> None:
        self._items: Dict[str, Tuple[str, Any]] = {}

    @staticmethod
    def fingerprint(payload: Dict[str, Any]) -> str:
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

    def resolve(self, key: str, payload: Dict[str, Any]) -> Optional[Any]:
        entry = self._items.get(key)
        if entry is None:
            return None
        stored_fingerprint, result = entry
        if stored_fingerprint != self.fingerprint(payload):
            raise Conflict("Idempotency key reused with a different payload")
        return result

    def remember(self, key: str, payload: Dict[str, Any], result: Any) -> None:
        self._items[key] = (self.fingerprint(payload), result)


class InMemoryObligationRecorder:
    def __init__(self) -> None:
        self.obligations: List[ContextInvalidationObligation] = []

    def record(self, obligation: ContextInvalidationObligation) -> ContextInvalidationObligation:
        for existing in self.obligations:
            if (
                existing.membership_id == obligation.membership_id
                and existing.correlation_id == obligation.correlation_id
                and existing.reason_code == obligation.reason_code
            ):
                return existing  # idempotent
        self.obligations.append(obligation)
        return obligation

    def open_for(self, membership_id: str) -> List[ContextInvalidationObligation]:
        return [o for o in self.obligations if o.membership_id == membership_id and not o.discharged]


class StaticTenantStateReader:
    def __init__(self, active_tenant_ids: Optional[set] = None) -> None:
        self._active = set(active_tenant_ids or ())

    def activate(self, tenant_id: str) -> None:
        self._active.add(tenant_id)

    def deactivate(self, tenant_id: str) -> None:
        self._active.discard(tenant_id)

    def is_active(self, tenant_id: str) -> bool:
        return tenant_id in self._active


# --------------------------------------------------------------------------------------
# MILE-2.2 — Membership transition contract and state machine
# --------------------------------------------------------------------------------------

class MembershipTransitionContract:
    """
    Loads and pins the canonical transition matrix.

    BOPEN-IDP-001 6.5: "The implementation must reject any transition absent from
    that file." Unknown states, actions, actor types, conditions or reason codes
    are rejected (BOPEN-P2-001 10.3).
    """

    def __init__(self, contract: Dict[str, Any]):
        self.raw = contract
        self.contract_version: str = contract["contract_version"]
        self.states: frozenset = frozenset(contract["states"])
        self.terminal_states: frozenset = frozenset(contract["terminal_states"])
        self.actor_types: frozenset = frozenset(contract["actor_types"])
        self.conditions: frozenset = frozenset(contract["conditions"])
        self._by_key: Dict[Tuple[str, str], Dict[str, Any]] = {}

        for definition in contract["transitions"]:
            self._validate_definition(definition)
            self._by_key[(definition["from"], definition["to"])] = definition

        self._validate_terminal_states()

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "MembershipTransitionContract":
        target = path or _CONTRACT_PATH
        return cls(json.loads(target.read_text(encoding="utf-8")))

    def _validate_definition(self, definition: Dict[str, Any]) -> None:
        if definition["from"] not in self.states or definition["to"] not in self.states:
            raise InvalidRequest("Transition references a state outside the closed set")
        unknown_actors = set(definition["allowed_actor_types"]) - self.actor_types
        if unknown_actors:
            raise InvalidRequest(f"Transition references unknown actor types: {sorted(unknown_actors)}")
        unknown_conditions = set(definition["required_conditions"]) - self.conditions
        if unknown_conditions:
            raise InvalidRequest(f"Transition references unknown conditions: {sorted(unknown_conditions)}")
        if not definition["reason_codes"]:
            raise InvalidRequest("Transition defines no reason codes")

    def _validate_terminal_states(self) -> None:
        """A terminal state must have no outbound transition (D-P2-005)."""
        for (from_state, _to_state) in self._by_key:
            if from_state in self.terminal_states:
                raise InvalidRequest(
                    f"Terminal state '{from_state}' must not define an outbound transition"
                )

    def resolve(self, from_state: str, to_state: str) -> Dict[str, Any]:
        definition = self._by_key.get((from_state, to_state))
        if definition is None:
            raise InvalidTransition(
                f"Transition {from_state} -> {to_state} is absent from the pinned contract "
                f"v{self.contract_version}"
            )
        return definition

    def allowed_pairs(self) -> List[Tuple[str, str]]:
        return sorted(self._by_key.keys())

    def absent_pairs(self) -> List[Tuple[str, str]]:
        return sorted(
            (a, b)
            for a in self.states
            for b in self.states
            if a != b and (a, b) not in self._by_key
        )


class MembershipStateMachine:
    """
    Single authoritative membership transition handler (BOPEN-P2-001 10.1).

    Implements the ordered algorithm in section 10.4. Every path either returns an
    immutable receipt or raises a typed error and emits a denial event; there is no
    indeterminate outcome.
    """

    def __init__(
        self,
        contract: MembershipTransitionContract,
        memberships: InMemoryMembershipRepository,
        tenants: TenantStateReader,
        audit: AuditDispatcher,
        obligations: InMemoryObligationRecorder,
        idempotency: InMemoryIdempotencyStore,
        clock: Optional[Clock] = None,
        ids: Optional[IdentifierFactory] = None,
    ) -> None:
        self.contract = contract
        self.memberships = memberships
        self.tenants = tenants
        self.audit = audit
        self.obligations = obligations
        self.idempotency = idempotency
        self.clock = clock or SystemClock()
        self.ids = ids or UuidIdentifierFactory()

    # -- internals ---------------------------------------------------------------

    @staticmethod
    def _command_payload(command: TransitionCommand) -> Dict[str, Any]:
        return {
            "membership_id": command.membership_id,
            "from_state": command.from_state,
            "to_state": command.to_state,
            "action": command.action,
            "actor_type": command.actor_type.value,
            "actor_id": command.actor_id,
            "reason_code": command.reason_code,
            "expected_version": command.expected_version,
        }

    def _deny(
        self,
        command: TransitionCommand,
        membership: Optional[Membership],
        error: KernelError,
    ) -> None:
        self.audit.emit_lifecycle_event(
            event_type="membership.transition_denied",
            correlation_id=command.correlation_id,
            actor_id=command.actor_id,
            tenant_id=membership.tenant_id if membership else "unknown",
            subject_type="membership",
            subject_id=command.membership_id,
            outcome="deny",
            reason_code=error.code,
            metadata={
                "requested_from": command.from_state,
                "requested_to": command.to_state,
                "action": command.action,
                "actor_type": command.actor_type.value,
                "contract_version": self.contract.contract_version,
            },
        )

    def _evaluate_conditions(
        self,
        definition: Dict[str, Any],
        command: TransitionCommand,
        membership: Membership,
    ) -> None:
        for condition in definition["required_conditions"]:
            if condition == "tenant_active":
                if not self.tenants.is_active(membership.tenant_id):
                    raise Forbidden("Condition not satisfied", detail="tenant_active")
            elif condition == "membership_version_match":
                if membership.version != command.expected_version:
                    raise StaleVersion(
                        "Membership version mismatch",
                        detail=f"expected={command.expected_version} actual={membership.version}",
                    )
            elif condition == "invitation_valid":
                if command.actor_type is not ActorType.INVITATION_SERVICE:
                    if command.actor_type is not ActorType.SCIM_DIRECTORY:
                        raise Forbidden("Condition not satisfied", detail="invitation_valid")
                elif not command.invitation_id:
                    raise Forbidden("Condition not satisfied", detail="invitation_valid")
            elif condition == "reinstatement_preconditions_checked":
                if not command.reinstatement_preconditions_checked:
                    raise Forbidden(
                        "Condition not satisfied", detail="reinstatement_preconditions_checked"
                    )
            else:  # pragma: no cover - contract loader rejects unknown conditions
                raise InvalidRequest(f"Unevaluable condition: {condition}")

    # -- public API --------------------------------------------------------------

    def transition(self, command: TransitionCommand) -> TransitionReceipt:
        # 1. Validate command and correlation.
        if not command.correlation_id or not command.idempotency_key:
            raise InvalidRequest("Correlation ID and idempotency key are required")
        if command.from_state not in self.contract.states or command.to_state not in self.contract.states:
            error = InvalidTransition("State outside the closed Phase 2 set")
            self._deny(command, None, error)
            raise error

        payload = self._command_payload(command)
        prior = self.idempotency.resolve(command.idempotency_key, payload)
        if prior is not None:
            return prior  # equivalent replay returns the prior receipt

        # 2-3. Resolve membership and compare expected version.
        membership = self.memberships.get(command.membership_id)
        if membership is None:
            error = NotFoundOrNotAccessible("Membership not found or not accessible")
            self._deny(command, None, error)
            raise error

        try:
            # 4. Confirm current state equals command from_state.
            if membership.state.value != command.from_state:
                raise Conflict(
                    "Current membership state does not match command",
                    detail=f"actual={membership.state.value}",
                )

            # 5. Resolve the exact transition from the pinned contract.
            definition = self.contract.resolve(command.from_state, command.to_state)

            # 6. Authorize the transition action.
            if command.action != definition["action"]:
                raise InvalidTransition("Action does not match the pinned transition definition")
            if command.actor_type.value not in definition["allowed_actor_types"]:
                raise Forbidden("Actor type is not permitted for this transition")

            # 7. Evaluate required conditions and terminal-state constraints.
            if command.from_state in self.contract.terminal_states:
                raise InvalidTransition("Terminal states do not reactivate implicitly")
            self._evaluate_conditions(definition, command, membership)

            # 8. Derive transition reason and effective time.
            if command.reason_code not in definition["reason_codes"]:
                raise InvalidRequest("Reason code is not permitted for this transition")
            effective_at = self.clock.now()

        except KernelError as error:
            self._deny(command, membership, error)
            raise

        # 9. Persist new state and increment version atomically.
        updated = replace(
            membership,
            state=MembershipState(command.to_state),
            version=membership.version + 1,
        )
        self.memberships.save(updated)

        # 10. Trigger required session/context invalidation obligations.
        if definition["context_invalidation"]:
            self.obligations.record(
                ContextInvalidationObligation(
                    obligation_id=self.ids.new_id("obl"),
                    tenant_id=updated.tenant_id,
                    principal_id=updated.principal_id,
                    membership_id=updated.id,
                    reason_code=command.reason_code,
                    grant_action=definition["grant_action"],
                    correlation_id=command.correlation_id,
                    recorded_at=effective_at,
                )
            )

        # 11. Emit the success audit event.
        event = self.audit.emit_lifecycle_event(
            event_type=definition["event_type"],
            correlation_id=command.correlation_id,
            actor_id=command.actor_id,
            tenant_id=updated.tenant_id,
            subject_type="membership",
            subject_id=updated.id,
            outcome="success",
            reason_code=command.reason_code,
            metadata={
                "from_state": command.from_state,
                "to_state": command.to_state,
                "action": command.action,
                "actor_type": command.actor_type.value,
                "resulting_version": updated.version,
                "contract_version": self.contract.contract_version,
            },
        )

        # 12. Return the immutable transition receipt.
        receipt = TransitionReceipt(
            receipt_id=self.ids.new_id("rcp"),
            membership_id=updated.id,
            tenant_id=updated.tenant_id,
            principal_id=updated.principal_id,
            from_state=command.from_state,
            to_state=command.to_state,
            action=command.action,
            actor_type=command.actor_type.value,
            actor_id=command.actor_id,
            reason_code=command.reason_code,
            resulting_version=updated.version,
            terminal=definition["terminal"],
            context_invalidation=definition["context_invalidation"],
            grant_action=definition["grant_action"],
            effective_at=effective_at,
            correlation_id=command.correlation_id,
            event_id=event["event_id"],
        )
        self.idempotency.remember(command.idempotency_key, payload, receipt)
        return receipt


# --------------------------------------------------------------------------------------
# MILE-2.1 — Principal invitation engine
# --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class IssuedInvitation:
    """
    Issue result. `raw_token` is returned exactly once and is never persisted
    (INV-P2-002). Callers must hand it to the approved delivery boundary and drop it.
    """
    invitation: Invitation
    raw_token: str


@dataclass(frozen=True)
class InvitationSummary:
    """Non-disclosing validation summary (BOPEN-P2-001 9.2)."""
    invitation_id: str
    tenant_id: str
    state: str
    expires_at: datetime
    requested_roles: Tuple[str, ...]


@dataclass(frozen=True)
class AcceptanceResult:
    invitation: Invitation
    membership: Membership
    receipt: TransitionReceipt


class InvitationEngine:
    """
    Issue, validate, accept, decline and expire tenant invitations
    (BOPEN-P2-001 section 9).

    Acceptance is single-use and atomic with membership activation (INV-P2-003):
    the invitation version compare-and-swap is performed before any membership
    mutation, so exactly one concurrent acceptance can win.
    """

    def __init__(
        self,
        invitations: InMemoryInvitationRepository,
        memberships: InMemoryMembershipRepository,
        state_machine: MembershipStateMachine,
        audit: AuditDispatcher,
        idempotency: InMemoryIdempotencyStore,
        clock: Optional[Clock] = None,
        ids: Optional[IdentifierFactory] = None,
        tokens: Optional[TokenGenerator] = None,
        hasher: Optional[TokenHasher] = None,
    ) -> None:
        self.invitations = invitations
        self.memberships = memberships
        self.state_machine = state_machine
        self.audit = audit
        self.idempotency = idempotency
        self.clock = clock or SystemClock()
        self.ids = ids or UuidIdentifierFactory()
        self.tokens = tokens or SecretsTokenGenerator()
        self.hasher = hasher or Sha256TokenHasher()

    # -- helpers -----------------------------------------------------------------

    @staticmethod
    def normalize_email(email: str) -> str:
        if not email or "@" not in email:
            raise InvalidRequest("A valid destination address is required")
        return email.strip().lower()

    def _emit(
        self,
        event_type: str,
        correlation_id: str,
        actor_id: str,
        tenant_id: str,
        subject_id: str,
        outcome: str,
        reason_code: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.audit.emit_lifecycle_event(
            event_type=event_type,
            correlation_id=correlation_id,
            actor_id=actor_id,
            tenant_id=tenant_id,
            subject_type="invitation",
            subject_id=subject_id,
            outcome=outcome,
            reason_code=reason_code,
            metadata=metadata or {},
        )

    def _resolve_or_deny(self, raw_token: str, correlation_id: str) -> Invitation:
        """
        Resolve by constant-time digest comparison. An unresolvable token yields a
        generic denial with no account or tenant enumeration (BOPEN-P2-001 9.5).
        """
        if not raw_token:
            raise InvitationInvalid("Invitation is not valid")
        invitation = self.invitations.find_by_digest(self.hasher.hash(raw_token))
        if invitation is None:
            self._emit(
                "invitation.validation_failed", correlation_id, "anonymous", "unknown",
                "unknown", "deny", "INVITATION_INVALID",
            )
            raise InvitationInvalid("Invitation is not valid")
        return invitation

    # -- commands ----------------------------------------------------------------

    def issue(
        self,
        tenant_id: str,
        email: str,
        invited_by_principal_id: str,
        correlation_id: str,
        idempotency_key: str,
        requested_roles: Tuple[str, ...] = ("member",),
        requested_scopes: Tuple[str, ...] = (),
        purpose: str = "membership",
        lifetime: Optional[timedelta] = None,
    ) -> IssuedInvitation:
        """BOPEN-P2-001 9.3. Returns the raw token exactly once."""
        if not tenant_id or not invited_by_principal_id:
            raise InvalidRequest("Tenant and inviter are required")
        if not requested_roles:
            raise InvalidRequest("At least one bootstrap role is required")

        email_normalized = self.normalize_email(email)
        effective_lifetime = lifetime or DEFAULT_INVITATION_LIFETIME
        if effective_lifetime <= timedelta(0) or effective_lifetime > MAX_INVITATION_LIFETIME:
            raise InvalidRequest("Invitation lifetime is outside approved bounds")

        payload = {
            "tenant_id": tenant_id,
            "email_normalized": email_normalized,
            "purpose": purpose,
            "roles": sorted(requested_roles),
            "scopes": sorted(requested_scopes),
        }
        prior = self.idempotency.resolve(idempotency_key, payload)
        if prior is not None:
            return prior

        # D-P2-004 PROVISIONAL: one open invitation per tenant + destination + purpose.
        if self.invitations.find_open(tenant_id, email_normalized, purpose) is not None:
            raise Conflict("An open invitation already exists for this destination")

        now = self.clock.now()
        raw_token = self.tokens.generate()
        invitation = Invitation(
            invitation_id=self.ids.new_id("inv"),
            tenant_id=tenant_id,
            email_normalized=email_normalized,
            state=InvitationState.INVITED,
            token_digest=self.hasher.hash(raw_token),   # only the digest is persisted
            token_digest_scheme=self.hasher.scheme,
            invited_by_principal_id=invited_by_principal_id,
            issued_at=now,
            expires_at=now + effective_lifetime,
            purpose=purpose,
            requested_roles=tuple(requested_roles),
            requested_scopes=tuple(requested_scopes),
        )
        self.invitations.save(invitation)

        self._emit(
            "invitation.issued", correlation_id, invited_by_principal_id, tenant_id,
            invitation.invitation_id, "success", "INVITATION_ISSUED",
            {"purpose": purpose, "expires_at": invitation.expires_at.isoformat(),
             "digest_scheme": invitation.token_digest_scheme},
        )

        result = IssuedInvitation(invitation=invitation, raw_token=raw_token)
        self.idempotency.remember(idempotency_key, payload, result)
        return result

    def validate(self, raw_token: str, tenant_id: str, correlation_id: str) -> InvitationSummary:
        """BOPEN-P2-001 9.2. Returns a summary or a typed denial without enumeration."""
        invitation = self._resolve_or_deny(raw_token, correlation_id)

        # Tenant mismatch denies without disclosing the real tenant (P2-T007).
        if invitation.tenant_id != tenant_id:
            self._emit(
                "invitation.validation_failed", correlation_id, "anonymous", tenant_id,
                invitation.invitation_id, "deny", "INVITATION_INVALID",
            )
            raise InvitationInvalid("Invitation is not valid")

        if invitation.state is not InvitationState.INVITED:
            self._emit(
                "invitation.validation_failed", correlation_id, "anonymous", tenant_id,
                invitation.invitation_id, "deny", "INVITATION_INVALID",
                {"observed_state": invitation.state.value},
            )
            raise InvitationInvalid("Invitation is not valid")

        if self.clock.now() >= invitation.expires_at:
            self._emit(
                "invitation.validation_failed", correlation_id, "anonymous", tenant_id,
                invitation.invitation_id, "deny", "INVITATION_EXPIRED",
            )
            raise InvitationExpired("Invitation has expired")

        return InvitationSummary(
            invitation_id=invitation.invitation_id,
            tenant_id=invitation.tenant_id,
            state=invitation.state.value,
            expires_at=invitation.expires_at,
            requested_roles=invitation.requested_roles,
        )

    def accept(
        self,
        raw_token: str,
        tenant_id: str,
        principal_id: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> AcceptanceResult:
        """
        BOPEN-P2-001 9.4. Atomic: invitation consumption and membership activation
        commit together, or neither commits.
        """
        if not principal_id:
            raise InvalidRequest("An authenticated principal is required")

        payload = {"tenant_id": tenant_id, "principal_id": principal_id}
        prior = self.idempotency.resolve(idempotency_key, payload)
        if prior is not None:
            return prior

        summary = self.validate(raw_token, tenant_id, correlation_id)
        invitation = self.invitations.get(summary.invitation_id)
        assert invitation is not None  # resolved by validate()

        # Compare-and-swap the invitation version first: exactly one concurrent
        # acceptance can pass this guard (INV-P2-003, P2-T004).
        observed_version = invitation.version
        current = self.invitations.get(invitation.invitation_id)
        if current is None or current.version != observed_version:
            raise Conflict("Invitation was concurrently modified")
        if current.state is not InvitationState.INVITED:
            raise InvitationInvalid("Invitation is not valid")

        now = self.clock.now()
        consumed = replace(
            current,
            state=InvitationState.ACTIVE,
            principal_id=principal_id,
            accepted_at=now,
            version=current.version + 1,
        )
        self.invitations.save(consumed)

        try:
            membership = self.memberships.find_active(tenant_id, principal_id)
            if membership is not None:
                raise Conflict("An active membership already exists for this principal and tenant")

            membership = Membership(
                id=self.ids.new_id("mem"),
                tenant_id=tenant_id,
                principal_id=principal_id,
                role=invitation.requested_roles[0] if invitation.requested_roles else "member",
                state=MembershipState.INVITED,
                version=1,
            )
            self.memberships.save(membership)

            receipt = self.state_machine.transition(
                TransitionCommand(
                    membership_id=membership.id,
                    from_state=MembershipState.INVITED.value,
                    to_state=MembershipState.ACTIVE.value,
                    action="membership.activate",
                    actor_type=ActorType.INVITATION_SERVICE,
                    actor_id=invitation.invitation_id,
                    reason_code="INVITATION_ACCEPTED",
                    expected_version=membership.version,
                    correlation_id=correlation_id,
                    idempotency_key=f"{idempotency_key}:activate",
                    invitation_id=invitation.invitation_id,
                )
            )
        except Exception:
            self.invitations.save(current)  # roll the invitation back; nothing commits
            raise

        finalized = replace(consumed, membership_id=membership.id)
        self.invitations.save(finalized)

        self._emit(
            "invitation.accepted", correlation_id, principal_id, tenant_id,
            finalized.invitation_id, "success", "INVITATION_ACCEPTED",
            {"membership_id": membership.id},
        )

        result = AcceptanceResult(
            invitation=finalized,
            membership=self.memberships.get(membership.id),
            receipt=receipt,
        )
        self.idempotency.remember(idempotency_key, payload, result)
        return result

    def decline(self, raw_token: str, tenant_id: str, correlation_id: str) -> Invitation:
        """BOPEN-P2-001 9.2. Declining is terminal for the invitation."""
        summary = self.validate(raw_token, tenant_id, correlation_id)
        invitation = self.invitations.get(summary.invitation_id)
        assert invitation is not None

        declined = replace(
            invitation,
            state=InvitationState.DECLINED,
            declined_at=self.clock.now(),
            version=invitation.version + 1,
        )
        self.invitations.save(declined)
        self._emit(
            "invitation.declined", correlation_id, "anonymous", tenant_id,
            declined.invitation_id, "success", "INVITATION_DECLINED",
        )
        return declined

    def expire_due(self, correlation_id: str, limit: int = 100) -> List[Invitation]:
        """BOPEN-P2-001 9.2. Idempotent bounded batch expiry driven by injected time."""
        if limit <= 0:
            raise InvalidRequest("Batch limit must be positive")
        now = self.clock.now()
        expired: List[Invitation] = []
        for invitation in self.invitations.list_expirable(now, limit):
            record = replace(
                invitation,
                state=InvitationState.EXPIRED,
                version=invitation.version + 1,
            )
            self.invitations.save(record)
            self._emit(
                "invitation.expired", correlation_id, "expiry_scheduler", record.tenant_id,
                record.invitation_id, "success", "INVITATION_EXPIRED",
            )
            expired.append(record)
        return expired
