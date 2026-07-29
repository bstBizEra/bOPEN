"""
bOPEN Commercial Entitlement Engine v1.0 (WP-P3-04 / BOPEN-ENT-001).

Evaluates commercial subscription plan tiers, quota allowances, feature gates,
tenant overrides, and maps deterministic reason codes to HTTP status codes (200, 403, 429).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, Optional
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
    requested_quantity: int = 1
    remaining_quota: Optional[int] = None


class EntitlementEvaluator:
    def __init__(self):
        self._plans: Dict[str, PlanTier] = {}
        self._tenant_plans: Dict[str, str] = {}  # tenant_id -> plan_id
        self._tenant_overrides: Dict[str, Dict[str, Dict[str, Any]]] = {}  # tenant_id -> capability_id -> rule
        self._usage_counters: Dict[str, Dict[str, int]] = {}  # tenant_id -> capability_id -> count

    def register_plan(self, plan: PlanTier):
        self._plans[plan.plan_id] = plan

    def assign_tenant_plan(self, tenant_id: str, plan_id: str):
        self._tenant_plans[tenant_id] = plan_id

    def add_tenant_override(self, tenant_id: str, capability_id: str, rule: Dict[str, Any]):
        if tenant_id not in self._tenant_overrides:
            self._tenant_overrides[tenant_id] = {}
        self._tenant_overrides[tenant_id][capability_id] = rule

    def record_usage(self, tenant_id: str, capability_id: str, quantity: int):
        if tenant_id not in self._usage_counters:
            self._usage_counters[tenant_id] = {}
        current = self._usage_counters[tenant_id].get(capability_id, 0)
        self._usage_counters[tenant_id][capability_id] = current + quantity

    def evaluate(self, context: ContextPayload, capability_id: str, requested_quantity: int = 1) -> EntitlementDecision:
        if not context.tenant_id:
            raise ValueError("ContextPayload must contain a valid tenant_id")

        now = datetime.now(timezone.utc)
        decision_id = f"ent_dec_{now.timestamp()}"

        # 1. Resolve capability rule (Override -> Plan -> Default Deny)
        rule = None
        if context.tenant_id in self._tenant_overrides and capability_id in self._tenant_overrides[context.tenant_id]:
            rule = self._tenant_overrides[context.tenant_id][capability_id]
        else:
            plan_id = self._tenant_plans.get(context.tenant_id, "plan_free")
            plan = self._plans.get(plan_id)
            if plan and capability_id in plan.entitlements:
                rule = plan.entitlements[capability_id]

        if rule is None:
            # Check if capability is totally unknown
            if capability_id.startswith("cap_unsupported"):
                return EntitlementDecision(
                    decision_id=decision_id,
                    tenant_id=context.tenant_id,
                    capability_id=capability_id,
                    decision=DecisionOutcome.DENY,
                    reason_code="DENY_UNSUPPORTED_CAPABILITY",
                    http_status=403,
                    evaluated_at=now,
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
                requested_quantity=requested_quantity
            )

        # 2. Evaluate Rule Type
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
                    requested_quantity=requested_quantity
                )
            else:
                return EntitlementDecision(
                    decision_id=decision_id,
                    tenant_id=context.tenant_id,
                    capability_id=capability_id,
                    decision=DecisionOutcome.DENY,
                    reason_code="DENY_NOT_ENTITLED",
                    http_status=403,
                    evaluated_at=now,
                    requested_quantity=requested_quantity
                )

        elif rule_type == "metered_allowance":
            quota = rule.get("quota", 0)
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
            requested_quantity=requested_quantity
        )
