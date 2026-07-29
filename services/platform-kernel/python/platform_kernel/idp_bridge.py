"""
bOPEN Enterprise IdP & SCIM 2.0 Bridge v1.0

Milestone MILE-2.4 (Enterprise IdP & SCIM 2.0 Sync).

Governing artifacts:
  - BOPEN-IDP-001 sections 6.1-6.3, 7, 8, 9, 10, 11 (identity domain, trust
    boundaries, SAML/OIDC profiles, SCIM profile, identity linking)
  - BOPEN-P2-001 section 12 (bridge responsibilities, SSO and SCIM flows)
  - contracts/schemas/scim-event.json

TRUST BOUNDARY (BOPEN-IDP-001 section 7)
----------------------------------------
The broker (Ory Polis / BoxyHQ Jackson or a pinned conformant successor) terminates
and normalizes SAML and OIDC. This bridge validates broker authenticity, tenant
binding, replay control and event schema, then delegates every membership decision
to the kernel. It never treats inbound roles or groups as authorization.

PROVISIONAL DECISIONS (BOPEN-P2-001 section 21, awaiting ratification):
  D-P2-001  broker name/version -> not pinned here; adapter port only (ADR-P2-001)
  D-P2-009  SCIM deprovision target -> per-directory policy, default `suspended`
  D-P2-010  SCIM ordering -> provider sequence plus monotonic tombstone guard

This module holds no protocol secrets, no broker credentials and no raw assertions.
"""

from __future__ import annotations

import hmac
import secrets
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Tuple

from kernel_core.audit import AuditDispatcher
from kernel_core.membership import (
    ActorType,
    Clock,
    Conflict,
    Forbidden,
    IdentifierFactory,
    InMemoryInvitationRepository,
    InMemoryMembershipRepository,
    InvalidRequest,
    InvitationState,
    MembershipStateMachine,
    NotFoundOrNotAccessible,
    SystemClock,
    TransitionCommand,
    UuidIdentifierFactory,
)
from kernel_core.types import Membership, MembershipState

DEFAULT_TRANSACTION_LIFETIME = timedelta(minutes=10)


class ProtocolValidationFailed(Forbidden):
    code = "PROTOCOL_VALIDATION_FAILED"


class IdentityLinkDenied(Forbidden):
    code = "IDENTITY_LINK_DENIED"


class ScimOrderingConflict(Conflict):
    code = "SCIM_ORDERING_CONFLICT"


class DependencyUnavailable(Forbidden):
    code = "DEPENDENCY_UNAVAILABLE"


# --------------------------------------------------------------------------------------
# Domain records (BOPEN-IDP-001 6.1 - 6.3)
# --------------------------------------------------------------------------------------

class Protocol_(str, Enum):
    SAML = "saml"
    OIDC = "oidc"


class ConnectionStatus(str, Enum):
    DRAFT = "draft"
    VERIFIED = "verified"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class DirectoryStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class ExternalIdentityStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    UNLINKED = "unlinked"


class JitPolicy(str, Enum):
    DISABLED = "disabled"
    INVITATION_ONLY = "invitation_only"


@dataclass(frozen=True)
class IdentityProviderConnection:
    connection_id: str
    tenant_id: str
    protocol: Protocol_
    issuer: str
    broker_connection_ref: str
    status: ConnectionStatus = ConnectionStatus.DRAFT
    domain_hints: Tuple[str, ...] = ()
    jit_policy: JitPolicy = JitPolicy.INVITATION_ONLY
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    version: int = 1


@dataclass(frozen=True)
class SCIMDirectory:
    directory_id: str
    tenant_id: str
    broker_directory_ref: str
    status: DirectoryStatus = DirectoryStatus.DRAFT
    provisioning_mode: str = "users_and_groups"
    # D-P2-009 PROVISIONAL: never hard delete.
    deprovision_policy: str = MembershipState.SUSPENDED.value
    last_sync_at: Optional[datetime] = None
    version: int = 1


@dataclass(frozen=True)
class ExternalIdentity:
    """
    Uniqueness is enforced on canonical (connection_id, issuer, subject).
    Email address alone must never establish identity equivalence (INV-P2-012).
    """
    external_identity_id: str
    principal_id: str
    tenant_id: str
    connection_id: str
    protocol: Protocol_
    issuer: str
    subject: str
    email_snapshot: Optional[str] = None
    status: ExternalIdentityStatus = ExternalIdentityStatus.ACTIVE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    version: int = 1

    @property
    def canonical_key(self) -> Tuple[str, str, str]:
        return (self.connection_id, self.issuer, self.subject)


@dataclass(frozen=True)
class GroupRoleMapping:
    """
    directory_id + group_external_id -> mapping_policy_version -> approved role.
    Unmapped groups have no authorization effect (BOPEN-IDP-001 10.4).
    """
    directory_id: str
    group_external_id: str
    mapping_policy_version: str
    target_role: str


@dataclass(frozen=True)
class SsoTransaction:
    """Bounded single-use SSO transaction state (BOPEN-P2-001 12.4)."""
    transaction_id: str
    connection_id: str
    tenant_id: str
    state: str
    nonce: str
    pkce_challenge: Optional[str]
    created_at: datetime
    expires_at: datetime
    consumed: bool = False


@dataclass(frozen=True)
class NormalizedAuthResult:
    """
    Normalized broker output. Raw assertions and authorization codes are never
    represented here and never persisted (INV-P2-018).
    """
    connection_id: str
    protocol: Protocol_
    issuer: str
    subject: str
    state: str
    assertion_id: str
    nonce: Optional[str] = None
    email_snapshot: Optional[str] = None
    display_name: Optional[str] = None
    groups: Tuple[str, ...] = ()
    broker_signature_valid: bool = True


@dataclass(frozen=True)
class ScimEvent:
    """Normalized SCIM event per contracts/schemas/scim-event.json."""
    event_id: str
    event_type: str
    directory_id: str
    tenant_id: str
    resource_type: str
    resource_id: str
    observed_at: datetime
    external_id: Optional[str] = None
    user_name: Optional[str] = None
    email_normalized: Optional[str] = None
    display_name: Optional[str] = None
    active: Optional[bool] = None
    groups: Tuple[str, ...] = ()
    sequence: Optional[int] = None


# --------------------------------------------------------------------------------------
# Ports and deterministic adapters
# --------------------------------------------------------------------------------------

class BrokerPort(Protocol):
    """Adapter boundary for the pinned SSO/SCIM broker (ADR-P2-001)."""

    def is_available(self) -> bool: ...

    def authenticate_source(self, credential_ref: str) -> bool: ...


class StaticBrokerPort:
    """Deterministic test adapter. Holds a reference, never a secret."""

    def __init__(self, trusted_refs: Optional[set] = None, available: bool = True) -> None:
        self._trusted = set(trusted_refs or {"broker-ref-1"})
        self._available = available

    def set_available(self, available: bool) -> None:
        self._available = available

    def is_available(self) -> bool:
        return self._available

    def authenticate_source(self, credential_ref: str) -> bool:
        return credential_ref in self._trusted


class InMemoryIdentityStore:
    def __init__(self) -> None:
        self.connections: Dict[str, IdentityProviderConnection] = {}
        self.directories: Dict[str, SCIMDirectory] = {}
        self.identities: Dict[str, ExternalIdentity] = {}
        self.mappings: List[GroupRoleMapping] = []
        self.transactions: Dict[str, SsoTransaction] = {}
        # Replay controls (BOPEN-IDP-001 16).
        self.seen_assertion_ids: set = set()
        self.seen_event_ids: set = set()
        # Ordering guard state: (directory_id, resource_id) -> last sequence.
        self.last_sequence: Dict[Tuple[str, str], int] = {}
        # Deprovision tombstones prevent stale reactivation (INV-P2-014).
        self.deprovision_tombstones: Dict[Tuple[str, str], int] = {}
        # Directory resource -> principal mapping for idempotent replay.
        self.resource_principal: Dict[Tuple[str, str], str] = {}
        # (directory_id, external_id) -> resource_id, to reject conflicting reuse.
        self.external_id_binding: Dict[Tuple[str, str], str] = {}

    def find_identity(self, connection_id: str, issuer: str, subject: str) -> Optional[ExternalIdentity]:
        for identity in self.identities.values():
            if identity.canonical_key == (connection_id, issuer, subject):
                return identity
        return None

    def resolve_mapping(self, directory_id: str, group_external_id: str) -> Optional[GroupRoleMapping]:
        for mapping in self.mappings:
            if mapping.directory_id == directory_id and mapping.group_external_id == group_external_id:
                return mapping
        return None


# --------------------------------------------------------------------------------------
# The bridge
# --------------------------------------------------------------------------------------

class IdpBridge:
    """
    Normalization, tenant binding, mapping and replay guard. Owns no permission
    grants: every membership change is executed through the kernel state machine.
    """

    def __init__(
        self,
        store: InMemoryIdentityStore,
        memberships: InMemoryMembershipRepository,
        invitations: InMemoryInvitationRepository,
        state_machine: MembershipStateMachine,
        audit: AuditDispatcher,
        broker: Optional[BrokerPort] = None,
        clock: Optional[Clock] = None,
        ids: Optional[IdentifierFactory] = None,
    ) -> None:
        self.store = store
        self.memberships = memberships
        self.invitations = invitations
        self.state_machine = state_machine
        self.audit = audit
        self.broker = broker or StaticBrokerPort()
        self.clock = clock or SystemClock()
        self.ids = ids or UuidIdentifierFactory()

    # -- helpers -----------------------------------------------------------------

    def _emit(
        self, event_type: str, correlation_id: str, actor_id: str, tenant_id: str,
        subject_type: str, subject_id: str, outcome: str, reason_code: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.audit.emit_lifecycle_event(
            event_type=event_type,
            correlation_id=correlation_id,
            actor_id=actor_id,
            tenant_id=tenant_id,
            subject_type=subject_type,
            subject_id=subject_id,
            outcome=outcome,
            reason_code=reason_code,
            metadata=metadata or {},
        )

    def _require_active_connection(self, connection_id: str) -> IdentityProviderConnection:
        connection = self.store.connections.get(connection_id)
        if connection is None:
            raise NotFoundOrNotAccessible("Connection not found or not accessible")
        if connection.status is not ConnectionStatus.ACTIVE:
            raise ProtocolValidationFailed("Connection is not active")
        return connection

    def _require_active_directory(self, directory_id: str, tenant_id: str) -> SCIMDirectory:
        directory = self.store.directories.get(directory_id)
        if directory is None:
            raise NotFoundOrNotAccessible("Directory not found or not accessible")
        if directory.status is not DirectoryStatus.ACTIVE:
            raise ProtocolValidationFailed("Directory is not active")
        # Directory/tenant mismatch denies (P2-T052); tenant is never inferred.
        if directory.tenant_id != tenant_id:
            raise ProtocolValidationFailed("Directory and tenant do not correspond")
        return directory

    # -- connection lifecycle ----------------------------------------------------

    def verify_connection(self, connection_id: str, approved_by: str, correlation_id: str) -> IdentityProviderConnection:
        connection = self.store.connections.get(connection_id)
        if connection is None:
            raise NotFoundOrNotAccessible("Connection not found or not accessible")
        if connection.created_by is not None and connection.created_by == approved_by:
            raise Forbidden("Connection approval requires a distinct accountable identity")

        now = self.clock.now()
        verified = replace(
            connection,
            status=ConnectionStatus.ACTIVE,
            approved_by=approved_by,
            verified_at=now,
            version=connection.version + 1,
        )
        self.store.connections[connection_id] = verified
        self._emit(
            "identity.connection_verified", correlation_id, approved_by, verified.tenant_id,
            "connection", connection_id, "success", "CONNECTION_VERIFIED",
            {"protocol": verified.protocol.value, "issuer": verified.issuer},
        )
        return verified

    # -- SSO (BOPEN-P2-001 12.4) -------------------------------------------------

    def begin_sso(self, connection_id: str, correlation_id: str) -> SsoTransaction:
        connection = self._require_active_connection(connection_id)
        if not self.broker.is_available():
            raise DependencyUnavailable("Broker is unavailable")

        now = self.clock.now()
        transaction = SsoTransaction(
            transaction_id=self.ids.new_id("sso"),
            connection_id=connection_id,
            tenant_id=connection.tenant_id,
            state=secrets.token_urlsafe(24),
            nonce=secrets.token_urlsafe(24),
            pkce_challenge=secrets.token_urlsafe(24) if connection.protocol is Protocol_.OIDC else None,
            created_at=now,
            expires_at=now + DEFAULT_TRANSACTION_LIFETIME,
        )
        self.store.transactions[transaction.state] = transaction
        return transaction

    def complete_sso(self, result: NormalizedAuthResult, correlation_id: str) -> ExternalIdentity:
        """
        Callback handling. Every failure is a typed denial and never a local allow
        (BOPEN-IDP-001 18).
        """
        connection = self.store.connections.get(result.connection_id)
        tenant_id = connection.tenant_id if connection else "unknown"

        def deny(reason: str) -> None:
            self._emit(
                "identity.authentication_denied", correlation_id, "anonymous", tenant_id,
                "external_identity", result.subject or "unknown", "deny", reason,
                {"protocol": result.protocol.value, "connection_id": result.connection_id},
            )

        if not result.broker_signature_valid:
            deny("BROKER_SIGNATURE_INVALID")
            raise ProtocolValidationFailed("Protocol validation failed")

        if connection is None or connection.status is not ConnectionStatus.ACTIVE:
            deny("CONNECTION_NOT_ACTIVE")
            raise ProtocolValidationFailed("Protocol validation failed")

        # Issuer must match the connection exactly (tenant confusion control).
        if result.issuer != connection.issuer:
            deny("ISSUER_MISMATCH")
            raise ProtocolValidationFailed("Protocol validation failed")

        # Single-use transaction state and nonce.
        transaction = self.store.transactions.get(result.state)
        if transaction is None or transaction.consumed:
            deny("STATE_INVALID_OR_REPLAYED")
            raise ProtocolValidationFailed("Protocol validation failed")
        if transaction.connection_id != result.connection_id:
            deny("STATE_CONNECTION_MISMATCH")
            raise ProtocolValidationFailed("Protocol validation failed")
        if self.clock.now() >= transaction.expires_at:
            deny("STATE_EXPIRED")
            raise ProtocolValidationFailed("Protocol validation failed")
        if connection.protocol is Protocol_.OIDC and result.nonce != transaction.nonce:
            deny("NONCE_MISMATCH")
            raise ProtocolValidationFailed("Protocol validation failed")

        # Assertion/response replay guard.
        if result.assertion_id in self.store.seen_assertion_ids:
            deny("ASSERTION_REPLAYED")
            raise ProtocolValidationFailed("Protocol validation failed")

        if not result.subject:
            deny("SUBJECT_MISSING")
            raise ProtocolValidationFailed("Protocol validation failed")

        self.store.transactions[result.state] = replace(transaction, consumed=True)
        self.store.seen_assertion_ids.add(result.assertion_id)

        identity = self.store.find_identity(connection.connection_id, result.issuer, result.subject)
        if identity is None:
            # No automatic linking. An unknown subject requires an explicit link
            # under BOPEN-IDP-001 section 11 (INV-P2-012, P2-T045).
            deny("IDENTITY_NOT_LINKED")
            raise IdentityLinkDenied("Identity link denied")

        # Enterprise authentication requires an active bOPEN relationship.
        membership = self.memberships.find_active(connection.tenant_id, identity.principal_id)
        if membership is None:
            deny("NO_ACTIVE_MEMBERSHIP")
            raise ProtocolValidationFailed("Protocol validation failed")

        self._emit(
            "identity.authentication_succeeded", correlation_id, identity.principal_id,
            connection.tenant_id, "external_identity", identity.external_identity_id,
            "success", "AUTHENTICATION_SUCCEEDED",
            {"protocol": connection.protocol.value, "connection_id": connection.connection_id},
        )
        return identity

    # -- identity linking (BOPEN-IDP-001 section 11) -----------------------------

    def link_identity(
        self,
        connection_id: str,
        issuer: str,
        subject: str,
        principal_id: str,
        correlation_id: str,
        link_challenge_accepted: bool = False,
        invitation_token_digest: Optional[str] = None,
        email_snapshot: Optional[str] = None,
    ) -> ExternalIdentity:
        """
        Linking is permitted only via an accepted link challenge by an authenticated
        active Principal, or a valid invitation bound to the same tenant. Email
        equality alone can never link (INV-P2-012).
        """
        connection = self._require_active_connection(connection_id)

        def deny(reason: str) -> None:
            self._emit(
                "identity.link_denied", correlation_id, principal_id, connection.tenant_id,
                "external_identity", subject, "deny", reason,
                {"connection_id": connection_id},
            )

        if issuer != connection.issuer:
            deny("ISSUER_MISMATCH")
            raise IdentityLinkDenied("Identity link denied")

        # Never overwrite or reassign an existing (connection, issuer, subject).
        existing = self.store.find_identity(connection_id, issuer, subject)
        if existing is not None:
            if existing.principal_id != principal_id:
                deny("SUBJECT_ALREADY_BOUND")
                raise IdentityLinkDenied("Identity link denied")
            return existing

        authorized = False
        basis = ""
        if link_challenge_accepted:
            authorized, basis = True, "LINK_CHALLENGE_ACCEPTED"
        elif invitation_token_digest is not None:
            # Basis 2: a valid invitation bound to the same tenant.
            invitation = self.invitations.find_by_digest(invitation_token_digest)
            if (
                invitation is not None
                and invitation.tenant_id == connection.tenant_id
                and invitation.state in {InvitationState.INVITED, InvitationState.ACTIVE}
            ):
                authorized, basis = True, "INVITATION_VERIFIED"

        if not authorized:
            deny("NO_APPROVED_LINKING_BASIS")
            raise IdentityLinkDenied("Identity link denied")

        now = self.clock.now()
        identity = ExternalIdentity(
            external_identity_id=self.ids.new_id("eid"),
            principal_id=principal_id,
            tenant_id=connection.tenant_id,
            connection_id=connection_id,
            protocol=connection.protocol,
            issuer=issuer,
            subject=subject,
            email_snapshot=email_snapshot,
            created_at=now,
            updated_at=now,
        )
        self.store.identities[identity.external_identity_id] = identity
        self._emit(
            "identity.linked", correlation_id, principal_id, connection.tenant_id,
            "external_identity", identity.external_identity_id, "success", basis,
            {"connection_id": connection_id},
        )
        return identity

    # -- SCIM (BOPEN-P2-001 12.5) ------------------------------------------------

    def _guard_ordering(self, event: ScimEvent, deprovision: bool = False) -> None:
        """
        D-P2-010 PROVISIONAL. Provider sequence plus monotonic tombstone guard.
        A stale update can never reactivate a later deprovisioned relationship
        (INV-P2-014, P2-T049).
        """
        key = (event.directory_id, event.resource_id)
        sequence = event.sequence

        if sequence is not None:
            last = self.store.last_sequence.get(key)
            if last is not None and sequence < last:
                raise ScimOrderingConflict("Out-of-order SCIM event rejected")
            tombstone = self.store.deprovision_tombstones.get(key)
            if tombstone is not None and not deprovision and sequence <= tombstone:
                raise ScimOrderingConflict("Stale event cannot reactivate a deprovisioned relationship")
            self.store.last_sequence[key] = max(sequence, self.store.last_sequence.get(key, sequence))

    def handle_scim_event(self, event: ScimEvent, correlation_id: str, credential_ref: str = "broker-ref-1") -> Dict[str, Any]:
        """Entry point for normalized SCIM directory events."""
        if not self.broker.authenticate_source(credential_ref):
            self._emit(
                "scim.event_denied", correlation_id, "scim_directory", event.tenant_id,
                "scim_event", event.event_id, "deny", "SOURCE_AUTHENTICATION_FAILED",
            )
            raise ProtocolValidationFailed("Protocol validation failed")

        try:
            directory = self._require_active_directory(event.directory_id, event.tenant_id)
        except (NotFoundOrNotAccessible, ProtocolValidationFailed):
            self._emit(
                "scim.event_denied", correlation_id, "scim_directory", event.tenant_id,
                "scim_event", event.event_id, "deny", "DIRECTORY_TENANT_MISMATCH",
            )
            raise

        # Replay: an already-processed event id returns the prior logical outcome.
        if event.event_id in self.store.seen_event_ids:
            return {"status": "replayed", "event_id": event.event_id}

        try:
            if event.event_type == "user.created":
                outcome = self._scim_user_created(event, directory, correlation_id)
            elif event.event_type == "user.updated":
                outcome = self._scim_user_updated(event, directory, correlation_id)
            elif event.event_type == "user.deprovisioned":
                outcome = self._scim_user_deprovisioned(event, directory, correlation_id)
            elif event.event_type == "group.changed":
                outcome = self._scim_group_changed(event, directory, correlation_id)
            else:
                raise InvalidRequest("Unsupported SCIM event type")
        except Exception:
            self._emit(
                "scim.event_denied", correlation_id, "scim_directory", event.tenant_id,
                "scim_event", event.event_id, "deny", "SCIM_EVENT_REJECTED",
                {"event_type": event.event_type},
            )
            raise

        self.store.seen_event_ids.add(event.event_id)
        self.store.directories[directory.directory_id] = replace(
            directory, last_sync_at=self.clock.now()
        )
        return outcome

    def _scim_user_created(self, event: ScimEvent, directory: SCIMDirectory, correlation_id: str) -> Dict[str, Any]:
        self._guard_ordering(event)
        key = (event.directory_id, event.resource_id)

        # Idempotent replay: an equivalent create returns the existing mapping
        # without creating a duplicate Principal or Membership (INV-P2-013).
        principal_id = self.store.resource_principal.get(key)
        if principal_id is not None:
            existing = self.memberships.find_active(event.tenant_id, principal_id)
            return {
                "status": "existing",
                "principal_id": principal_id,
                "membership_id": existing.id if existing else None,
            }

        # Conflicting reuse of externalId within a directory is rejected and audited
        # (BOPEN-IDP-001 10.3).
        if event.external_id is not None:
            external_key = (event.directory_id, event.external_id)
            bound_resource = self.store.external_id_binding.get(external_key)
            if bound_resource is not None and bound_resource != event.resource_id:
                raise Conflict("externalId is already bound within this directory")

        principal_id = self.ids.new_id("usr")
        self.store.resource_principal[key] = principal_id
        if event.external_id is not None:
            self.store.external_id_binding[(event.directory_id, event.external_id)] = event.resource_id

        membership = Membership(
            id=self.ids.new_id("mem"),
            tenant_id=event.tenant_id,
            principal_id=principal_id,
            role="member",
            state=MembershipState.INVITED,
            version=1,
        )
        self.memberships.save(membership)

        # Initial active state is applied through the state machine, never directly.
        receipt = self.state_machine.transition(
            TransitionCommand(
                membership_id=membership.id,
                from_state=MembershipState.INVITED.value,
                to_state=MembershipState.ACTIVE.value,
                action="membership.activate",
                actor_type=ActorType.SCIM_DIRECTORY,
                actor_id=directory.directory_id,
                reason_code="SCIM_PROVISION",
                expected_version=membership.version,
                correlation_id=correlation_id,
                idempotency_key=f"scim:{event.event_id}:activate",
            )
        )

        self._emit(
            "scim.user_provisioned", correlation_id, directory.directory_id, event.tenant_id,
            "membership", membership.id, "success", "SCIM_PROVISION",
            {"directory_id": directory.directory_id, "resource_id": event.resource_id,
             "principal_id": principal_id},
        )
        return {"status": "created", "principal_id": principal_id,
                "membership_id": membership.id, "receipt": receipt}

    def _scim_user_updated(self, event: ScimEvent, directory: SCIMDirectory, correlation_id: str) -> Dict[str, Any]:
        self._guard_ordering(event)
        key = (event.directory_id, event.resource_id)
        principal_id = self.store.resource_principal.get(key)
        if principal_id is None:
            raise NotFoundOrNotAccessible("Directory resource is not mapped")

        transitions: List[Any] = []
        # `active` is a provisioning signal mapped through membership policy.
        if event.active is False:
            transitions.append(self._deprovision_membership(event, directory, principal_id, correlation_id))
        elif event.active is True:
            membership = self.memberships.find_active(event.tenant_id, principal_id)
            if membership is None:
                suspended = next(
                    (m for m in self.memberships.find_for(event.tenant_id, principal_id)
                     if m.state is MembershipState.SUSPENDED),
                    None,
                )
                if suspended is not None:
                    transitions.append(
                        self.state_machine.transition(
                            TransitionCommand(
                                membership_id=suspended.id,
                                from_state=MembershipState.SUSPENDED.value,
                                to_state=MembershipState.ACTIVE.value,
                                action="membership.reinstate",
                                actor_type=ActorType.TENANT_ADMIN,
                                actor_id=directory.directory_id,
                                reason_code="ADMIN_REINSTATEMENT",
                                expected_version=suspended.version,
                                correlation_id=correlation_id,
                                idempotency_key=f"scim:{event.event_id}:reinstate",
                                reinstatement_preconditions_checked=True,
                            )
                        )
                    )

        self._emit(
            "scim.user_updated", correlation_id, directory.directory_id, event.tenant_id,
            "membership", principal_id, "success", "SCIM_UPDATE",
            {"directory_id": directory.directory_id, "resource_id": event.resource_id,
             "transitions": len(transitions)},
        )
        return {"status": "updated", "principal_id": principal_id, "transitions": transitions}

    def _deprovision_membership(self, event: ScimEvent, directory: SCIMDirectory,
                                principal_id: str, correlation_id: str):
        membership = self.memberships.find_active(event.tenant_id, principal_id)
        if membership is None:
            return None
        target = directory.deprovision_policy   # D-P2-009 PROVISIONAL; never hard delete
        action = "membership.suspend" if target == MembershipState.SUSPENDED.value else "membership.revoke"
        return self.state_machine.transition(
            TransitionCommand(
                membership_id=membership.id,
                from_state=membership.state.value,
                to_state=target,
                action=action,
                actor_type=ActorType.SCIM_DIRECTORY,
                actor_id=directory.directory_id,
                reason_code="SCIM_DEPROVISION",
                expected_version=membership.version,
                correlation_id=correlation_id,
                idempotency_key=f"scim:{event.event_id}:deprovision",
            )
        )

    def _scim_user_deprovisioned(self, event: ScimEvent, directory: SCIMDirectory, correlation_id: str) -> Dict[str, Any]:
        self._guard_ordering(event, deprovision=True)
        key = (event.directory_id, event.resource_id)
        principal_id = self.store.resource_principal.get(key)
        if principal_id is None:
            raise NotFoundOrNotAccessible("Directory resource is not mapped")

        receipt = self._deprovision_membership(event, directory, principal_id, correlation_id)

        # Tombstone: later stale updates cannot reactivate (INV-P2-014).
        if event.sequence is not None:
            self.store.deprovision_tombstones[key] = event.sequence

        self._emit(
            "scim.user_deprovisioned", correlation_id, directory.directory_id, event.tenant_id,
            "membership", principal_id, "success", "SCIM_DEPROVISION",
            {"directory_id": directory.directory_id, "resource_id": event.resource_id,
             "target_state": directory.deprovision_policy},
        )
        return {"status": "deprovisioned", "principal_id": principal_id, "receipt": receipt}

    def _scim_group_changed(self, event: ScimEvent, directory: SCIMDirectory, correlation_id: str) -> Dict[str, Any]:
        self._guard_ordering(event)
        applied: List[str] = []
        ignored: List[str] = []
        for group_external_id in event.groups:
            mapping = self.store.resolve_mapping(directory.directory_id, group_external_id)
            if mapping is None:
                ignored.append(group_external_id)   # unmapped groups have no effect
                continue
            applied.append(mapping.target_role)

        if applied:
            self._emit(
                "scim.group_mapping_applied", correlation_id, directory.directory_id,
                event.tenant_id, "group", event.resource_id, "success", "GROUP_MAPPING_APPLIED",
                {"directory_id": directory.directory_id, "applied_roles": applied,
                 "ignored_group_count": len(ignored)},
            )
        return {"status": "group_processed", "applied_roles": applied, "ignored_groups": ignored}
