"""
bOPEN Tenant Context Switching Service v1.0

Milestone MILE-2.3 (Tenant Context Switching Service).

Governing artifacts:
  - BOPEN-IDP-001 sections 12 (token standard) and 13 (context switching)
  - BOPEN-P2-001 section 11 (service algorithm, denial cases, SDK contract)
  - contracts/schemas/context-switch.json, contracts/schemas/tenant-context.json

PROVISIONAL DECISIONS (BOPEN-P2-001 section 21, awaiting ratification):
  D-P2-006  context token lifetime -> 5 minutes
  D-P2-007  JWT algorithm/key custody -> port only; no production key material here
  D-P2-008  context supersession -> latest context wins per session

SECURITY BOUNDARY
-----------------
`DeterministicTestSigner` exists solely so the Phase 2 acceptance suite can exercise
signature, algorithm and key-identifier negative paths offline. It is symmetric and
uses a clearly marked NON-PRODUCTION key. BOPEN-IDP-001 12.4 requires asymmetric
signing with key material managed outside source control; that binding is
ADR-P2-006 and is NOT resolved here.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Protocol, Tuple

from kernel_core.audit import AuditDispatcher
from kernel_core.membership import (
    Clock,
    Conflict,
    Forbidden,
    IdentifierFactory,
    InMemoryMembershipRepository,
    InvalidRequest,
    NotFoundOrNotAccessible,
    SystemClock,
    UuidIdentifierFactory,
)
from kernel_core.types import MembershipState
from kernel_core.delegation import DelegatedAccessService

# D-P2-006 PROVISIONAL
DEFAULT_CONTEXT_TOKEN_LIFETIME = timedelta(minutes=5)
MAX_CLOCK_SKEW = timedelta(seconds=60)

ALLOWED_ALGORITHMS = frozenset({"HS256"})   # test boundary only; see ADR-P2-006

# Claims that must never appear in a context token (BOPEN-IDP-001 12.3).
PROHIBITED_CLAIMS = frozenset({"email", "name", "given_name", "family_name", "groups", "assertion"})


class ContextDenied(Forbidden):
    code = "CONTEXT_DENIED"


class TokenValidationError(Forbidden):
    code = "CONTEXT_DENIED"


# --------------------------------------------------------------------------------------
# Ports
# --------------------------------------------------------------------------------------

class TokenSigner(Protocol):
    algorithm: str
    kid: str

    def sign(self, claims: Dict[str, Any]) -> str: ...


class RoleDeriver(Protocol):
    def derive(self, tenant_id: str, principal_id: str, membership_id: str) -> Tuple[Tuple[str, ...], Tuple[str, ...]]: ...


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64u_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class DeterministicTestSigner:
    """NON-PRODUCTION signer. See the module SECURITY BOUNDARY note."""

    NON_PRODUCTION_KEY = b"bopen-phase2-test-key-not-a-production-secret"

    def __init__(self, kid: str = "test-kid-1", algorithm: str = "HS256",
                 key: Optional[bytes] = None) -> None:
        self.kid = kid
        self.algorithm = algorithm
        self._key = key or self.NON_PRODUCTION_KEY

    def sign(self, claims: Dict[str, Any]) -> str:
        header = {"alg": self.algorithm, "kid": self.kid, "typ": "JWT"}
        segments = [
            _b64u(json.dumps(header, sort_keys=True, separators=(",", ":")).encode()),
            _b64u(json.dumps(claims, sort_keys=True, separators=(",", ":")).encode()),
        ]
        signing_input = ".".join(segments).encode()
        signature = hmac.new(self._key, signing_input, hashlib.sha256).digest()
        return ".".join(segments + [_b64u(signature)])


class DefaultRoleDeriver:
    """
    INV-P2-009: roles and scopes are derived from authoritative bOPEN state at
    issuance, never carried from a prior tenant and never taken from inbound claims.
    """

    def __init__(self, memberships: InMemoryMembershipRepository) -> None:
        self.memberships = memberships

    def derive(self, tenant_id: str, principal_id: str, membership_id: str):
        membership = self.memberships.get(membership_id)
        if membership is None or membership.tenant_id != tenant_id or membership.principal_id != principal_id:
            raise ContextDenied("Role derivation failed")
        if membership.state is not MembershipState.ACTIVE:
            raise ContextDenied("Role derivation failed")
        roles = (membership.role,)
        scopes = tuple(sorted({f"tenant:read", f"membership:read"}))
        return roles, scopes


# --------------------------------------------------------------------------------------
# Session and context state
# --------------------------------------------------------------------------------------

@dataclass
class AuthenticationSession:
    """Authentication session; not tenant-bound (BOPEN-IDP-001 12.1)."""
    session_id: str
    principal_id: str
    client_id: str
    established_at: datetime
    expires_at: datetime
    revoked: bool = False
    current_context_id: Optional[str] = None

    def is_valid_at(self, moment: datetime) -> bool:
        return not self.revoked and moment < self.expires_at


@dataclass(frozen=True)
class IssuedContext:
    context_id: str
    tenant_id: str
    membership_id: str
    principal_id: str
    session_id: str
    roles: Tuple[str, ...]
    scopes: Tuple[str, ...]
    issued_at: datetime
    expires_at: datetime
    access_token: str
    delegated_grant_id: Optional[str] = None

    def public_response(self) -> Dict[str, Any]:
        """Response body per contracts/schemas/context-switch.json."""
        return {
            "context_id": self.context_id,
            "tenant_id": self.tenant_id,
            "membership_id": self.membership_id,
            "access_token": self.access_token,
            "expires_at": self.expires_at.isoformat(),
            "delegated_grant_id": self.delegated_grant_id,
        }


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, AuthenticationSession] = {}
        self._contexts: Dict[str, IssuedContext] = {}
        self._superseded: set = set()

    def save_session(self, session: AuthenticationSession) -> AuthenticationSession:
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[AuthenticationSession]:
        return self._sessions.get(session_id)

    def save_context(self, context: IssuedContext) -> IssuedContext:
        self._contexts[context.context_id] = context
        return context

    def get_context(self, context_id: str) -> Optional[IssuedContext]:
        return self._contexts.get(context_id)

    def supersede(self, context_id: str) -> None:
        self._superseded.add(context_id)

    def is_superseded(self, context_id: str) -> bool:
        return context_id in self._superseded

    def revoke_for_membership(self, membership_id: str) -> List[str]:
        """Discharge a context-invalidation obligation (BOPEN-P2-001 10.6)."""
        affected = [c.context_id for c in self._contexts.values() if c.membership_id == membership_id]
        for context_id in affected:
            self._superseded.add(context_id)
        return affected

    def revoke_for_grant(self, grant_id: str) -> List[str]:
        affected = [c.context_id for c in self._contexts.values() if c.delegated_grant_id == grant_id]
        for context_id in affected:
            self._superseded.add(context_id)
        return affected


# --------------------------------------------------------------------------------------
# Token claim validation (BOPEN-IDP-001 12.2 - 12.4)
# --------------------------------------------------------------------------------------

MANDATORY_CLAIMS = ("iss", "aud", "sub", "tid", "mid", "roles", "scopes", "iat", "exp", "jti", "sid", "ctx")


class ContextTokenValidator:
    """
    Server-side validator. Signature, algorithm, issuer, audience, time and
    mandatory claims are all validated before context is resolved.

    Deliberately server-side only: BOPEN-P2-001 11.4 forbids SDKs from decoding
    tokens to make authorization decisions.
    """

    def __init__(
        self,
        issuer: str,
        audience: str,
        known_keys: Dict[str, bytes],
        clock: Optional[Clock] = None,
        skew: timedelta = MAX_CLOCK_SKEW,
    ) -> None:
        self.issuer = issuer
        self.audience = audience
        self.known_keys = known_keys
        self.clock = clock or SystemClock()
        self.skew = skew

    def validate(self, token: str) -> Dict[str, Any]:
        parts = token.split(".")
        if len(parts) != 3:
            raise TokenValidationError("Malformed token")

        try:
            header = json.loads(_b64u_decode(parts[0]))
            claims = json.loads(_b64u_decode(parts[1]))
        except Exception as exc:  # noqa: BLE001 - fail closed on any decode failure
            raise TokenValidationError("Malformed token") from exc

        algorithm = header.get("alg")
        if algorithm == "none" or algorithm not in ALLOWED_ALGORITHMS:
            raise TokenValidationError("Disallowed signing algorithm")

        kid = header.get("kid")
        key = self.known_keys.get(kid) if kid else None
        if key is None:
            raise TokenValidationError("Unknown signing key")

        expected = hmac.new(key, ".".join(parts[:2]).encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64u(expected), parts[2]):
            raise TokenValidationError("Signature verification failed")

        for claim in MANDATORY_CLAIMS:
            if claim not in claims:
                raise TokenValidationError(f"Missing mandatory claim: {claim}")
        for claim in PROHIBITED_CLAIMS:
            if claim in claims:
                raise TokenValidationError(f"Prohibited claim present: {claim}")

        if claims.get("iss") != self.issuer:
            raise TokenValidationError("Issuer mismatch")
        if claims.get("aud") != self.audience:
            raise TokenValidationError("Audience mismatch")

        now = self.clock.now()
        exp = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
        iat = datetime.fromtimestamp(claims["iat"], tz=timezone.utc)
        if now - self.skew >= exp:
            raise TokenValidationError("Token has expired")
        if iat - self.skew > now:
            raise TokenValidationError("Token issued in the future")
        if "nbf" in claims:
            nbf = datetime.fromtimestamp(claims["nbf"], tz=timezone.utc)
            if now + self.skew < nbf:
                raise TokenValidationError("Token is not yet valid")

        return claims


# --------------------------------------------------------------------------------------
# Context switching service
# --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class SwitchContextCommand:
    """Request per contracts/schemas/context-switch.json."""
    session_id: str
    tenant_id: str
    idempotency_key: str
    expected_context_id: Optional[str] = None
    header_tenant_id: Optional[str] = None
    client_id: Optional[str] = None


class ContextSwitchService:
    """
    Implements the BOPEN-P2-001 section 11.3 algorithm. Failure at any step returns
    no token (BOPEN-IDP-001 13.2).
    """

    def __init__(
        self,
        memberships: InMemoryMembershipRepository,
        sessions: InMemorySessionStore,
        signer: TokenSigner,
        audit: AuditDispatcher,
        issuer: str,
        audience: str,
        role_deriver: Optional[RoleDeriver] = None,
        delegation: Optional[DelegatedAccessService] = None,
        clock: Optional[Clock] = None,
        ids: Optional[IdentifierFactory] = None,
        token_lifetime: timedelta = DEFAULT_CONTEXT_TOKEN_LIFETIME,
    ) -> None:
        self.memberships = memberships
        self.sessions = sessions
        self.signer = signer
        self.audit = audit
        self.issuer = issuer
        self.audience = audience
        self.role_deriver = role_deriver or DefaultRoleDeriver(memberships)
        self.delegation = delegation
        self.clock = clock or SystemClock()
        self.ids = ids or UuidIdentifierFactory()
        self.token_lifetime = token_lifetime

    def _deny(self, command: SwitchContextCommand, reason_code: str, actor_id: str = "unknown") -> None:
        self.audit.emit_lifecycle_event(
            event_type="context.switch_denied",
            correlation_id=command.idempotency_key,
            actor_id=actor_id,
            tenant_id=command.tenant_id,
            subject_type="context",
            subject_id=command.expected_context_id or "none",
            outcome="deny",
            reason_code=reason_code,
            metadata={"requested_tenant": command.tenant_id},
        )

    def switch(self, command: SwitchContextCommand) -> IssuedContext:
        if not command.session_id or not command.tenant_id or not command.idempotency_key:
            raise InvalidRequest("Session, tenant and idempotency key are required")

        # Step 3: headers are untrusted selectors; a header/body mismatch denies.
        if command.header_tenant_id is not None and command.header_tenant_id != command.tenant_id:
            self._deny(command, "TENANT_SELECTOR_MISMATCH")
            raise ContextDenied("Context switch denied")

        # Steps 1, 4: validate the authentication session and client binding.
        session = self.sessions.get_session(command.session_id)
        now = self.clock.now()
        if session is None or not session.is_valid_at(now):
            self._deny(command, "SESSION_INVALID")
            raise ContextDenied("Context switch denied")
        if command.client_id is not None and command.client_id != session.client_id:
            self._deny(command, "CLIENT_BINDING_MISMATCH", session.principal_id)
            raise ContextDenied("Context switch denied")

        # Stale expected-context guard (D-P2-008).
        if command.expected_context_id is not None:
            if session.current_context_id != command.expected_context_id:
                self._deny(command, "STALE_CONTEXT", session.principal_id)
                raise Conflict("Expected context is stale")

        # Steps 5-7: resolve target membership, else an active delegated grant.
        membership = self.memberships.find_active(command.tenant_id, session.principal_id)
        grant = None
        if membership is None:
            if self.delegation is not None:
                grant = self.delegation.resolve_usable(session.principal_id, command.tenant_id)
            if grant is None:
                # Generic denial; never disclose whether the tenant exists.
                self._deny(command, "NO_ACTIVE_RELATIONSHIP", session.principal_id)
                raise ContextDenied("Context switch denied")

        # Step 8: derive roles and scopes fresh from target-tenant state (INV-P2-010).
        if membership is not None:
            roles, scopes = self.role_deriver.derive(
                command.tenant_id, session.principal_id, membership.id
            )
            membership_id = membership.id
        else:
            roles, scopes = grant.approved_roles, grant.approved_scopes
            membership_id = f"delegated:{grant.grant_id}"

        # Steps 9-10: new context identifier and short-lived tenant-bound token.
        context_id = self.ids.new_id("ctx")
        expires_at = now + self.token_lifetime
        claims: Dict[str, Any] = {
            "iss": self.issuer,
            "aud": self.audience,
            "sub": session.principal_id,
            "tid": command.tenant_id,
            "mid": membership_id,
            "roles": list(roles),
            "scopes": list(scopes),
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "jti": self.ids.new_id("jti"),
            "sid": session.session_id,
            "ctx": context_id,
        }
        if grant is not None:
            claims["dgr"] = grant.grant_id   # mandatory for delegated context

        token = self.signer.sign(claims)

        # Step 11: supersede the previous context.
        previous_context_id = session.current_context_id
        if previous_context_id:
            self.sessions.supersede(previous_context_id)

        issued = IssuedContext(
            context_id=context_id,
            tenant_id=command.tenant_id,
            membership_id=membership_id,
            principal_id=session.principal_id,
            session_id=session.session_id,
            roles=tuple(roles),
            scopes=tuple(scopes),
            issued_at=now,
            expires_at=expires_at,
            access_token=token,
            delegated_grant_id=grant.grant_id if grant else None,
        )
        self.sessions.save_context(issued)
        session.current_context_id = context_id
        self.sessions.save_session(session)

        # Step 12: emit context.switched with old/new references but no token.
        self.audit.emit_lifecycle_event(
            event_type="context.switched" if previous_context_id else "context.issued",
            correlation_id=command.idempotency_key,
            actor_id=session.principal_id,
            tenant_id=command.tenant_id,
            subject_type="context",
            subject_id=context_id,
            outcome="success",
            reason_code="CONTEXT_ISSUED",
            metadata={
                "previous_context_id": previous_context_id,
                "new_context_id": context_id,
                "membership_id": membership_id,
                "delegated_grant_id": grant.grant_id if grant else None,
            },
        )
        return issued

    def revoke_contexts_for_membership(self, membership_id: str, correlation_id: str, reason_code: str) -> List[str]:
        affected = self.sessions.revoke_for_membership(membership_id)
        for context_id in affected:
            self.audit.emit_lifecycle_event(
                event_type="context.revoked",
                correlation_id=correlation_id,
                actor_id="security_control",
                tenant_id="scoped",
                subject_type="context",
                subject_id=context_id,
                outcome="success",
                reason_code=reason_code,
                metadata={"membership_id": membership_id},
            )
        return affected

    def revoke_contexts_for_grant(self, grant_id: str, correlation_id: str, reason_code: str) -> List[str]:
        affected = self.sessions.revoke_for_grant(grant_id)
        for context_id in affected:
            self.audit.emit_lifecycle_event(
                event_type="context.revoked",
                correlation_id=correlation_id,
                actor_id="security_control",
                tenant_id="scoped",
                subject_type="context",
                subject_id=context_id,
                outcome="success",
                reason_code=reason_code,
                metadata={"grant_id": grant_id},
            )
        return affected
