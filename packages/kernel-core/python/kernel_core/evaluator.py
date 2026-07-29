"""
bOPEN Authorization Decision Evaluator v1.0
Enforces Deny-by-Default ReBAC/ABAC Policy Evaluation (BOPEN-AUTHZ-001)
"""

import uuid
from datetime import datetime, timezone
from kernel_core.types import AuthorizationRequest, AuthorizationDecision, DecisionResult

class AuthorizationEvaluator:
    """
    Deny-by-Default decision engine evaluating requests against active tenant context and membership.
    """

    def evaluate(self, request: AuthorizationRequest, active_membership_state: str) -> AuthorizationDecision:
        # 1. Deny if context tenant does not match requested tenant
        if request.context.tenant_id != request.tenant_id:
            return AuthorizationDecision(
                decision_id=str(uuid.uuid4()),
                principal_id=request.principal_id,
                tenant_id=request.tenant_id,
                action=request.action,
                resource_type=request.resource_type,
                resource_id=request.resource_id,
                decision=DecisionResult.DENY,
                reason_code="TENANT_CONTEXT_MISMATCH"
            )

        # 2. Deny if principal membership is not active
        if active_membership_state != "active":
            return AuthorizationDecision(
                decision_id=str(uuid.uuid4()),
                principal_id=request.principal_id,
                tenant_id=request.tenant_id,
                action=request.action,
                resource_type=request.resource_type,
                resource_id=request.resource_id,
                decision=DecisionResult.DENY,
                reason_code="MEMBERSHIP_INACTIVE"
            )

        # 3. Allow if active owner/member role matches policy
        if "owner" in request.context.roles or "member" in request.context.roles:
            return AuthorizationDecision(
                decision_id=str(uuid.uuid4()),
                principal_id=request.principal_id,
                tenant_id=request.tenant_id,
                action=request.action,
                resource_type=request.resource_type,
                resource_id=request.resource_id,
                decision=DecisionResult.ALLOW,
                reason_code="MEMBERSHIP_ROLE_PERMITTED"
            )

        # Default Deny
        return AuthorizationDecision(
            decision_id=str(uuid.uuid4()),
            principal_id=request.principal_id,
            tenant_id=request.tenant_id,
            action=request.action,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            decision=DecisionResult.DENY,
            reason_code="DEFAULT_DENY"
        )
