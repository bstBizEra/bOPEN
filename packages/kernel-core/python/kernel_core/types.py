"""
bOPEN Platform Kernel Core Types v1.0
Governed by Approved Specifications BOPEN-ARCH-001, BOPEN-TENANT-001, BOPEN-AUTHZ-001
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from datetime import datetime, timezone
import uuid

class PrincipalType(str, Enum):
    HUMAN = "human"
    SERVICE = "service"
    APPLICATION = "application"
    DEVICE = "device"
    AGENT = "agent"

class TenantStatus(str, Enum):
    DRAFT = "draft"
    PENDING_VERIFICATION = "pending_verification"
    APPROVED = "approved"
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    SUSPENDED = "suspended"

class MembershipState(str, Enum):
    """
    Closed Phase 2 membership state set (BOPEN-IDP-001 6.5, BOPEN-P2-001 10.2).

    Phase 1 values are preserved unchanged; EXPIRED, LEFT and REMOVED complete the
    approved seven-state set. `declined` is an Invitation state, not a Membership
    state, and is deliberately absent here.
    """
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"
    LEFT = "left"
    REMOVED = "removed"

class DecisionResult(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"

@dataclass
class Principal:
    id: str
    type: PrincipalType
    email: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class Tenant:
    id: str
    name: str
    status: TenantStatus = TenantStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class Membership:
    id: str
    tenant_id: str
    principal_id: str
    role: str
    state: MembershipState = MembershipState.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # Positive concurrency version supporting compare-and-swap transitions
    # (BOPEN-P2-001 10.5). Phase 1 callers keep the default.
    version: int = 1

@dataclass
class ContextPayload:
    context_id: str
    principal_id: str
    tenant_id: str
    active_membership_id: str
    roles: List[str]
    issued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class AuthorizationRequest:
    principal_id: str
    tenant_id: str
    action: str
    resource_type: str
    resource_id: str
    context: ContextPayload

@dataclass
class AuthorizationDecision:
    decision_id: str
    principal_id: str
    tenant_id: str
    action: str
    resource_type: str
    resource_id: str
    decision: DecisionResult
    reason_code: str
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
