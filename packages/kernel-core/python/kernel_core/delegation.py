"""
bOPEN Delegated Cross-Tenant Access v1.0

Milestone MILE-2.5 (Delegated Cross-Tenant Access).

Governing artifacts:
  - BOPEN-IDP-001 section 14 (grant fields and controls)
  - BOPEN-P2-001 section 13 (commands, grant flow, partner/support controls)
  - contracts/schemas/delegated-grant.json

PROVISIONAL DECISIONS (BOPEN-P2-001 section 21, awaiting ratification):
  D-P2-012  support grant maximum -> 8 hours
  D-P2-013  partner grant maximum -> bounded default of 90 days pending contract policy
  D-P2-014  revocation propagation -> immediate new-issuance deny

Invariants enforced here: INV-P2-015 (tenant-specific, scope-bounded, time-bounded)
and INV-P2-016 (revoked or expired delegation cannot issue a context token).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

from kernel_core.audit import AuditDispatcher
from kernel_core.membership import (
    Clock,
    Conflict,
    Forbidden,
    IdentifierFactory,
    InvalidRequest,
    NotFoundOrNotAccessible,
    SystemClock,
    UuidIdentifierFactory,
)

# D-P2-012 / D-P2-013 PROVISIONAL
MAX_SUPPORT_GRANT_DURATION = timedelta(hours=8)
MAX_PARTNER_GRANT_DURATION = timedelta(days=90)

WILDCARDS = frozenset({"*", "**", "all", "any"})


class DelegationDenied(Forbidden):
    code = "DELEGATION_DENIED"


class GrantType(str, Enum):
    PARTNER = "partner"
    SUPPORT = "support"


class GrantState(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass(frozen=True)
class DelegatedGrant:
    grant_id: str
    grant_type: GrantType
    source_principal_id: str
    target_tenant_id: str
    approved_roles: Tuple[str, ...]
    approved_scopes: Tuple[str, ...]
    reason_code: str
    created_by: str
    starts_at: datetime
    expires_at: datetime
    state: GrantState = GrantState.PENDING
    case_reference: Optional[str] = None
    approved_by: Optional[str] = None
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    version: int = 1

    def is_usable_at(self, moment: datetime) -> bool:
        return (
            self.state is GrantState.ACTIVE
            and self.starts_at <= moment < self.expires_at
        )


class InMemoryGrantRepository:
    def __init__(self) -> None:
        self._items: Dict[str, DelegatedGrant] = {}

    def save(self, grant: DelegatedGrant) -> DelegatedGrant:
        self._items[grant.grant_id] = grant
        return grant

    def get(self, grant_id: str) -> Optional[DelegatedGrant]:
        return self._items.get(grant_id)

    def find_usable(
        self, principal_id: str, tenant_id: str, moment: datetime
    ) -> Optional[DelegatedGrant]:
        for grant in self._items.values():
            if (
                grant.source_principal_id == principal_id
                and grant.target_tenant_id == tenant_id
                and grant.is_usable_at(moment)
            ):
                return grant
        return None

    def list_expirable(self, cutoff: datetime) -> List[DelegatedGrant]:
        return sorted(
            (
                g for g in self._items.values()
                if g.state in {GrantState.PENDING, GrantState.ACTIVE} and g.expires_at <= cutoff
            ),
            key=lambda g: (g.expires_at, g.grant_id),
        )


class DelegatedAccessService:
    """
    Time-bounded partner and support access with no standing cross-tenant privilege
    (BOPEN-IDP-001 14.2).
    """

    def __init__(
        self,
        grants: InMemoryGrantRepository,
        audit: AuditDispatcher,
        clock: Optional[Clock] = None,
        ids: Optional[IdentifierFactory] = None,
        require_separation_of_duties: bool = True,
    ) -> None:
        self.grants = grants
        self.audit = audit
        self.clock = clock or SystemClock()
        self.ids = ids or UuidIdentifierFactory()
        self.require_separation_of_duties = require_separation_of_duties

    # -- helpers -----------------------------------------------------------------

    @staticmethod
    def _reject_wildcards(target_tenant_id: str, roles: Tuple[str, ...], scopes: Tuple[str, ...]) -> None:
        """INV-P2-015: no wildcard tenant and no wildcard scope (P2-T061)."""
        if target_tenant_id.strip().lower() in WILDCARDS or "*" in target_tenant_id:
            raise DelegationDenied("Wildcard target tenant is prohibited")
        for value in tuple(roles) + tuple(scopes):
            if value.strip().lower() in WILDCARDS or "*" in value:
                raise DelegationDenied("Wildcard role or scope is prohibited")

    def _max_duration(self, grant_type: GrantType) -> timedelta:
        return (
            MAX_SUPPORT_GRANT_DURATION
            if grant_type is GrantType.SUPPORT
            else MAX_PARTNER_GRANT_DURATION
        )

    def _emit(
        self, event_type: str, grant: DelegatedGrant, actor_id: str,
        correlation_id: str, outcome: str, reason_code: str,
    ) -> None:
        self.audit.emit_lifecycle_event(
            event_type=event_type,
            correlation_id=correlation_id,
            actor_id=actor_id,
            tenant_id=grant.target_tenant_id,
            subject_type="delegated_grant",
            subject_id=grant.grant_id,
            outcome=outcome,
            reason_code=reason_code,
            metadata={
                "grant_id": grant.grant_id,          # P2-T065: grant reference present
                "grant_type": grant.grant_type.value,
                "expires_at": grant.expires_at.isoformat(),
                "state": grant.state.value,
            },
        )

    # -- commands ----------------------------------------------------------------

    def create(
        self,
        grant_type: GrantType,
        source_principal_id: str,
        target_tenant_id: str,
        approved_roles: Tuple[str, ...],
        approved_scopes: Tuple[str, ...],
        reason_code: str,
        created_by: str,
        correlation_id: str,
        duration: Optional[timedelta] = None,
        case_reference: Optional[str] = None,
    ) -> DelegatedGrant:
        """BOPEN-P2-001 13.3 steps 1-3."""
        if not source_principal_id or not target_tenant_id:
            raise InvalidRequest("Recipient principal and target tenant are required")
        if not approved_roles or not approved_scopes:
            raise InvalidRequest("Least-privilege roles and scopes are required")
        if not reason_code:
            raise InvalidRequest("An approved business or security reason is required")

        self._reject_wildcards(target_tenant_id, approved_roles, approved_scopes)

        # Support grants require case/ticket correlation (BOPEN-IDP-001 14.2).
        if grant_type is GrantType.SUPPORT and not case_reference:
            raise DelegationDenied("Support grants require an active case reference")

        limit = self._max_duration(grant_type)
        effective = duration or limit
        if effective <= timedelta(0) or effective > limit:
            raise DelegationDenied("Grant duration exceeds the approved maximum")

        now = self.clock.now()
        grant = DelegatedGrant(
            grant_id=self.ids.new_id("dgr"),
            grant_type=grant_type,
            source_principal_id=source_principal_id,
            target_tenant_id=target_tenant_id,
            approved_roles=tuple(approved_roles),
            approved_scopes=tuple(approved_scopes),
            reason_code=reason_code,
            created_by=created_by,
            starts_at=now,
            expires_at=now + effective,
            state=GrantState.PENDING,
            case_reference=case_reference,
        )
        self.grants.save(grant)
        self._emit("delegation.created", grant, created_by, correlation_id, "success", reason_code)
        return grant

    def approve(self, grant_id: str, approver_id: str, correlation_id: str) -> DelegatedGrant:
        """
        BOPEN-P2-001 13.3 step 4. The maker cannot self-approve where separation of
        duties applies (P2-T062).
        """
        grant = self.grants.get(grant_id)
        if grant is None:
            raise NotFoundOrNotAccessible("Grant not found or not accessible")
        if grant.state is not GrantState.PENDING:
            raise Conflict("Only a pending grant can be approved")
        if self.require_separation_of_duties and approver_id == grant.created_by:
            self._emit("delegation.created", grant, approver_id, correlation_id, "deny", "SELF_APPROVAL_PROHIBITED")
            raise DelegationDenied("Self-approval is prohibited for this grant")

        approved = replace(grant, approved_by=approver_id, version=grant.version + 1)
        self.grants.save(approved)
        return approved

    def activate(self, grant_id: str, actor_id: str, correlation_id: str) -> DelegatedGrant:
        """BOPEN-P2-001 13.3 step 5. Activation only after all conditions are met."""
        grant = self.grants.get(grant_id)
        if grant is None:
            raise NotFoundOrNotAccessible("Grant not found or not accessible")
        if grant.state is not GrantState.PENDING:
            raise Conflict("Only a pending grant can be activated")
        if grant.approved_by is None:
            raise DelegationDenied("Grant has not been approved")
        if self.clock.now() >= grant.expires_at:
            raise DelegationDenied("Grant has already expired")

        active = replace(grant, state=GrantState.ACTIVE, version=grant.version + 1)
        self.grants.save(active)
        self._emit("delegation.activated", active, actor_id, correlation_id, "success", active.reason_code)
        return active

    def revoke(self, grant_id: str, revoked_by: str, correlation_id: str) -> DelegatedGrant:
        """
        BOPEN-P2-001 13.3 steps 8-9. Revocation denies all future issuance
        immediately (D-P2-014) and invalidates active delegated contexts.
        """
        grant = self.grants.get(grant_id)
        if grant is None:
            raise NotFoundOrNotAccessible("Grant not found or not accessible")
        if grant.state in {GrantState.REVOKED, GrantState.EXPIRED}:
            return grant  # idempotent

        now = self.clock.now()
        revoked = replace(
            grant,
            state=GrantState.REVOKED,
            revoked_at=now,
            revoked_by=revoked_by,
            version=grant.version + 1,
        )
        self.grants.save(revoked)
        self._emit("delegation.revoked", revoked, revoked_by, correlation_id, "success", "GRANT_REVOKED")
        return revoked

    def expire_due(self, correlation_id: str) -> List[DelegatedGrant]:
        """Automatic expiry; no manual cleanup required. Expiry never auto-renews."""
        now = self.clock.now()
        expired: List[DelegatedGrant] = []
        for grant in self.grants.list_expirable(now):
            record = replace(grant, state=GrantState.EXPIRED, version=grant.version + 1)
            self.grants.save(record)
            self._emit("delegation.expired", record, "expiry_scheduler", correlation_id, "success", "GRANT_EXPIRED")
            expired.append(record)
        return expired

    def resolve_usable(self, principal_id: str, tenant_id: str) -> Optional[DelegatedGrant]:
        """
        Resolve an active, unexpired grant for delegated context issuance
        (INV-P2-016). Returns None rather than raising so the caller can apply a
        generic non-disclosing denial.
        """
        return self.grants.find_usable(principal_id, tenant_id, self.clock.now())
