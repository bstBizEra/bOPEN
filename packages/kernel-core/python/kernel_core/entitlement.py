"""
bOPEN Commercial Entitlement Engine v1.0 (WP-P3-04 / BOPEN-ENT-001).

Evaluates commercial subscription plan tiers, quota allowances, feature gates,
tenant overrides, and maps deterministic reason codes to HTTP status codes (200, 403, 429).
Matches contracts/schemas/entitlement-decision.schema.json.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import uuid
from kernel_core.types import ContextPayload


class DecisionOutcome(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    THROTTLED = "THROTTLED"


class UnsupportedCapabilityError(Exception):
    pass


class NotEntitledError(Exception):
    pass


class QuotaExceededError(Exception):
    pass


class InvalidQuantityError(Exception):
    pass


class StructurallyInvalidContextError(Exception):
    pass


@dataclass(frozen=True)
class PlanTier:
    plan_id: str
    name: str
    entitlements: Dict[str, Dict[str, Any]]


@dataclass(frozen=True)
class EntitlementDecision:
    decision_id: str
    tenant_id: str
    capability_id: str
    decision: DecisionOutcome
    reason_code: str
    http_status: int
    evaluated_at: datetime
    context_id: str
    principal_id: str
    correlation_id: str
    requested_quantity: int = 1
    remaining_quota: Optional[int] = None

    def to_dict(self) -> dict:
        d = {
            "decision_id": self.decision_id,
            "tenant_id": self.tenant_id,
            "capability_id": self.capability_id,
            "decision": self.decision.value,
            "reason_code": self.reason_code,
            "evaluated_at": self.evaluated_at.isoformat(),
            "context_id": self.context_id,
            "principal_id": self.principal_id,
            "correlation_id": self.correlation_id,
            "requested_quantity": self.requested_quantity
        }
        if self.remaining_quota is not None:
            d["remaining_quota"] = self.remaining_quota
        return d



@dataclass(frozen=True)
class RateLimitDecision:
    decision_id: str
    tenant_id: str
    capability_id: str
    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int
    reason_code: str
    http_status: int
    evaluated_at: datetime

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "tenant_id": self.tenant_id,
            "capability_id": self.capability_id,
            "allowed": self.allowed,
            "limit": self.limit,
            "remaining": self.remaining,
            "reset_seconds": self.reset_seconds,
            "reason_code": self.reason_code,
            "http_status": self.http_status,
            "evaluated_at": self.evaluated_at.isoformat()
        }


class FeatureRolloutEvaluator:
    def __init__(self):
        self._feature_toggles: Dict[str, bool] = {}  # feature_key -> enabled

    def set_feature_toggle(self, feature_key: str, enabled: bool):
        self._feature_toggles[feature_key] = enabled

    def is_feature_enabled(self, feature_key: str, tenant_id: str) -> bool:
        return self._feature_toggles.get(feature_key, True)


class RateLimiter:
    def __init__(self):
        self._limits: Dict[str, int] = {}  # capability_id -> max_per_minute
        self._counts: Dict[str, Dict[str, int]] = {}  # tenant_id -> capability_id -> count

    def set_limit(self, capability_id: str, max_per_minute: int):
        self._limits[capability_id] = max_per_minute

    def evaluate(self, tenant_id: str, capability_id: str) -> RateLimitDecision:
        now = datetime.now(timezone.utc)
        decision_id = f"rat_dec_{uuid.uuid4().hex[:12]}"
        limit = self._limits.get(capability_id, 10000)
        current = self._counts.get(tenant_id, {}).get(capability_id, 0)

        if current >= limit:
            return RateLimitDecision(
                decision_id=decision_id,
                tenant_id=tenant_id,
                capability_id=capability_id,
                allowed=False,
                limit=limit,
                remaining=0,
                reset_seconds=60,
                reason_code="DENY_RATE_LIMIT_EXCEEDED",
                http_status=429,
                evaluated_at=now
            )

        if tenant_id not in self._counts:
            self._counts[tenant_id] = {}
        self._counts[tenant_id][capability_id] = current + 1

        return RateLimitDecision(
            decision_id=decision_id,
            tenant_id=tenant_id,
            capability_id=capability_id,
            allowed=True,
            limit=limit,
            remaining=limit - (current + 1),
            reset_seconds=60,
            reason_code="ENTITLEMENT_ALLOWED",
            http_status=200,
            evaluated_at=now
        )


class PlanRepository:
    def __init__(self):
        self._plans: Dict[str, PlanTier] = {}

    def save_plan(self, plan: PlanTier):
        self._plans[plan.plan_id] = plan

    def get_plan(self, plan_id: str) -> Optional[PlanTier]:
        return self._plans.get(plan_id)


class EntitlementEvaluator:
    def __init__(self, plan_repo: Optional[PlanRepository] = None):
        self._plans: Dict[str, PlanTier] = {}
        self._tenant_plans: Dict[str, str] = {}  # tenant_id -> plan_id
        self._tenant_overrides: Dict[str, Dict[str, Dict[str, Any]]] = {}  # tenant_id -> capability_id -> rule
        self._usage_counters: Dict[str, Dict[str, int]] = {}  # tenant_id -> capability_id -> count
        self._rollout_evaluator = FeatureRolloutEvaluator()
        self._rate_limiter = RateLimiter()

    def register_plan(self, plan: PlanTier):
        self._plans[plan.plan_id] = plan

    def assign_tenant_plan(self, tenant_id: str, plan_id: str):
        self._tenant_plans[tenant_id] = plan_id

    def add_tenant_override(self, tenant_id: str, capability_id: str, rule: Dict[str, Any]):
        if tenant_id not in self._tenant_overrides:
            self._tenant_overrides[tenant_id] = {}
        self._tenant_overrides[tenant_id][capability_id] = rule

    def set_feature_toggle(self, feature_key: str, enabled: bool):
        self._rollout_evaluator.set_feature_toggle(feature_key, enabled)

    def set_rate_limit(self, capability_id: str, max_per_minute: int):
        self._rate_limiter.set_limit(capability_id, max_per_minute)

    def record_usage(self, tenant_id: str, capability_id: str, quantity: int):
        if quantity <= 0:
            raise InvalidQuantityError("Quantity must be a positive integer greater than 0")
        if tenant_id not in self._usage_counters:
            self._usage_counters[tenant_id] = {}
        current = self._usage_counters[tenant_id].get(capability_id, 0)
        self._usage_counters[tenant_id][capability_id] = current + quantity

    def is_entitled(self, context: ContextPayload, capability_id: str) -> bool:
        decision = self.evaluate(context, capability_id)
        return decision.decision == DecisionOutcome.ALLOW

    def evaluate(self, context: ContextPayload, capability_id: str, requested_quantity: int = 1, correlation_id: str = "corr-default") -> EntitlementDecision:
        # 1. Structural context validation
        if not context.context_id or not context.principal_id or not context.tenant_id or not context.active_membership_id:
            raise StructurallyInvalidContextError("ContextPayload is missing required context_id, principal_id, tenant_id, or active_membership_id")

        # 2. Reject negative or zero quantity injection (Finding 3)
        if requested_quantity <= 0:
            raise InvalidQuantityError(f"Requested quantity must be a positive integer > 0, got {requested_quantity}")

        now = datetime.now(timezone.utc)
        decision_id = f"ent_dec_{uuid.uuid4().hex[:12]}"

        # 3. Check rate limiter
        rate_dec = self._rate_limiter.evaluate(context.tenant_id, capability_id)
        if not rate_dec.allowed:
            return EntitlementDecision(
                decision_id=decision_id,
                tenant_id=context.tenant_id,
                capability_id=capability_id,
                decision=DecisionOutcome.THROTTLED,
                reason_code=rate_dec.reason_code,
                http_status=rate_dec.http_status,
                evaluated_at=now,
                context_id=context.context_id,
                principal_id=context.principal_id,
                correlation_id=correlation_id,
                requested_quantity=requested_quantity
            )

        # 4. Feature rollout gate check
        if not self._rollout_evaluator.is_feature_enabled(capability_id, context.tenant_id):
            return EntitlementDecision(
                decision_id=decision_id,
                tenant_id=context.tenant_id,
                capability_id=capability_id,
                decision=DecisionOutcome.DENY,
                reason_code="DENY_FEATURE_DISABLED",
                http_status=403,
                evaluated_at=now,
                context_id=context.context_id,
                principal_id=context.principal_id,
                correlation_id=correlation_id,
                requested_quantity=requested_quantity
            )

        # 5. Resolve entitlement rule
        rule = None
        if context.tenant_id in self._tenant_overrides and capability_id in self._tenant_overrides[context.tenant_id]:
            rule = self._tenant_overrides[context.tenant_id][capability_id]
        else:
            plan_id = self._tenant_plans.get(context.tenant_id, "plan_free")
            plan = self._plans.get(plan_id)
            if plan and capability_id in plan.entitlements:
                rule = plan.entitlements[capability_id]

        if rule is None:
            if capability_id.startswith("cap_unsupported"):
                return EntitlementDecision(
                    decision_id=decision_id,
                    tenant_id=context.tenant_id,
                    capability_id=capability_id,
                    decision=DecisionOutcome.DENY,
                    reason_code="DENY_UNSUPPORTED_CAPABILITY",
                    http_status=403,
                    evaluated_at=now,
                    context_id=context.context_id,
                    principal_id=context.principal_id,
                    correlation_id=correlation_id,
                    requested_quantity=requested_quantity
                )
            return EntitlementDecision(
                decision_id=decision_id,
                tenant_id=context.tenant_id,
                capability_id=capability_id,
                decision=DecisionOutcome.DENY,
                reason_code="DENY_NOT_ENTITLED",
                http_status=403,
                evaluated_at=now,
                context_id=context.context_id,
                principal_id=context.principal_id,
                correlation_id=correlation_id,
                requested_quantity=requested_quantity
            )

        # 6. Evaluate Rule Type
        rule_type = rule.get("type")
        if rule_type == "boolean":
            if rule.get("value") is True:
                return EntitlementDecision(
                    decision_id=decision_id,
                    tenant_id=context.tenant_id,
                    capability_id=capability_id,
                    decision=DecisionOutcome.ALLOW,
                    reason_code="ENTITLEMENT_ALLOWED",
                    http_status=200,
                    evaluated_at=now,
                    context_id=context.context_id,
                    principal_id=context.principal_id,
                    correlation_id=correlation_id,
                    requested_quantity=requested_quantity
                )
            return EntitlementDecision(
                decision_id=decision_id,
                tenant_id=context.tenant_id,
                capability_id=capability_id,
                decision=DecisionOutcome.DENY,
                reason_code="DENY_NOT_ENTITLED",
                http_status=403,
                evaluated_at=now,
                context_id=context.context_id,
                principal_id=context.principal_id,
                correlation_id=correlation_id,
                requested_quantity=requested_quantity
            )

        elif rule_type in {"metered_allowance", "capacity", "seat_count"}:
            quota = rule.get("quota", rule.get("value", 0))
            current_usage = self._usage_counters.get(context.tenant_id, {}).get(capability_id, 0)
            remaining = max(0, quota - current_usage)

            if current_usage + requested_quantity > quota:
                return EntitlementDecision(
                    decision_id=decision_id,
                    tenant_id=context.tenant_id,
                    capability_id=capability_id,
                    decision=DecisionOutcome.DENY,
                    reason_code="DENY_QUOTA_EXCEEDED",
                    http_status=429,
                    evaluated_at=now,
                    context_id=context.context_id,
                    principal_id=context.principal_id,
                    correlation_id=correlation_id,
                    requested_quantity=requested_quantity,
                    remaining_quota=remaining
                )
            return EntitlementDecision(
                decision_id=decision_id,
                tenant_id=context.tenant_id,
                capability_id=capability_id,
                decision=DecisionOutcome.ALLOW,
                reason_code="ENTITLEMENT_ALLOWED",
                http_status=200,
                evaluated_at=now,
                context_id=context.context_id,
                principal_id=context.principal_id,
                correlation_id=correlation_id,
                requested_quantity=requested_quantity,
                remaining_quota=remaining - requested_quantity
            )

        return EntitlementDecision(
            decision_id=decision_id,
            tenant_id=context.tenant_id,
            capability_id=capability_id,
            decision=DecisionOutcome.DENY,
            reason_code="DENY_NOT_ENTITLED",
            http_status=403,
            evaluated_at=now,
            context_id=context.context_id,
            principal_id=context.principal_id,
            correlation_id=correlation_id,
            requested_quantity=requested_quantity
        )
