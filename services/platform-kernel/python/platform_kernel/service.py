"""
bOPEN Platform Kernel Service — Phase 1 Vertical Slice Service v1.0
Implements the minimum relationship chain specified in FIRST-VERTICAL-SLICE-SPEC.md:
Register Human Principal -> Provision Tenant -> Create Owner Membership -> Establish Context -> Authorize Read -> Emit Audit Event
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Tuple

from kernel_core.types import (
    Principal, PrincipalType, Tenant, TenantStatus,
    Membership, MembershipState, ContextPayload,
    AuthorizationRequest, AuthorizationDecision, DecisionResult
)
from kernel_core.evaluator import AuthorizationEvaluator
from kernel_core.audit import AuditDispatcher

class PlatformKernelService:
    def __init__(self):
        self.principals: Dict[str, Principal] = {}
        self.tenants: Dict[str, Tenant] = {}
        self.memberships: Dict[str, Membership] = {}
        self.evaluator = AuthorizationEvaluator()
        self.audit_dispatcher = AuditDispatcher()

    def register_principal(self, email: str, principal_type: PrincipalType = PrincipalType.HUMAN) -> Principal:
        principal_id = f"usr_{uuid.uuid4()}"
        principal = Principal(id=principal_id, type=principal_type, email=email)
        self.principals[principal_id] = principal
        return principal

    def provision_tenant(self, tenant_name: str, owner_principal_id: str) -> Tuple[Tenant, Membership]:
        if owner_principal_id not in self.principals:
            raise ValueError(f"Principal {owner_principal_id} does not exist.")

        tenant_id = f"tnt_{uuid.uuid4()}"
        tenant = Tenant(id=tenant_id, name=tenant_name, status=TenantStatus.ACTIVE)
        self.tenants[tenant_id] = tenant

        membership_id = f"mem_{uuid.uuid4()}"
        membership = Membership(
            id=membership_id,
            tenant_id=tenant_id,
            principal_id=owner_principal_id,
            role="owner",
            state=MembershipState.ACTIVE
        )
        self.memberships[membership_id] = membership

        return tenant, membership

    def establish_context(self, principal_id: str, tenant_id: str, membership_id: str) -> ContextPayload:
        membership = self.memberships.get(membership_id)
        if not membership or membership.tenant_id != tenant_id or membership.principal_id != principal_id:
            raise ValueError("Invalid membership for context establishment.")

        return ContextPayload(
            context_id=f"ctx_{uuid.uuid4()}",
            principal_id=principal_id,
            tenant_id=tenant_id,
            active_membership_id=membership_id,
            roles=[membership.role]
        )

    def execute_authorized_read(self, context: ContextPayload, resource_type: str, resource_id: str, correlation_id: str) -> Tuple[AuthorizationDecision, Dict[str, Any]]:
        membership = self.memberships.get(context.active_membership_id)
        membership_state = membership.state.value if membership else "none"

        authz_req = AuthorizationRequest(
            principal_id=context.principal_id,
            tenant_id=context.tenant_id,
            action=f"{resource_type}:read",
            resource_type=resource_type,
            resource_id=resource_id,
            context=context
        )

        decision = self.evaluator.evaluate(authz_req, active_membership_state=membership_state)
        status_str = "SUCCESS" if decision.decision == DecisionResult.ALLOW else "DENIED"

        audit_event = self.audit_dispatcher.dispatch(
            actor_id=context.principal_id,
            tenant_id=context.tenant_id,
            action=f"{resource_type}:read",
            resource_type=resource_type,
            resource_id=resource_id,
            status=status_str,
            correlation_id=correlation_id
        )

        return decision, audit_event
