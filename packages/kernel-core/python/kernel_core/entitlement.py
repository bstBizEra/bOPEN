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
from typing import Dict, Any, Optional, List, Protocol
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
    """
    A rate limiting verdict, named to match contracts/schemas/rate-limit-decision.schema.json.

    Field names here are the schema's names, not convenient shorthands, because `to_dict()`
    is the wire form and the schema sets `additionalProperties: false`. Any field named
    differently from the schema is both a missing required property and a forbidden extra one.

    `current_rate` is the number of calls CONSUMED in the current window. It is not the
    headroom. The two are complements (`current_rate + remaining == limit_rate`), so
    serializing headroom under the name `current_rate` would validate cleanly against the
    frozen schema while reporting the inverse of the truth. The `remaining` property below
    exists to make that relationship explicit and derived, so the two can never drift apart.
    """

    decision_id: str
    tenant_id: str
    capability_id: str
    correlation_id: str
    allowed: bool
    limit_rate: int
    current_rate: int
    reset_in_seconds: int
    reason_code: str
    status_code: int
    evaluated_at: datetime

    @property
    def remaining(self) -> int:
        """Headroom left in the window. Derived from the consumed count, never stored."""
        return max(0, self.limit_rate - self.current_rate)

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "tenant_id": self.tenant_id,
            "capability_id": self.capability_id,
            "correlation_id": self.correlation_id,
            "allowed": self.allowed,
            "limit_rate": self.limit_rate,
            "current_rate": self.current_rate,
            "reset_in_seconds": self.reset_in_seconds,
            "reason_code": self.reason_code,
            "status_code": self.status_code,
            "evaluated_at": self.evaluated_at.isoformat()
        }


@dataclass(frozen=True)
class RateLimitPolicy:
    """A tenant's configured allowance for one capability."""

    max_per_window: int
    window_seconds: int


class FeatureToggleStore(Protocol):
    """Where rollout decisions live.

    A Protocol rather than a concrete class because `kernel_core` must not import
    `platform_kernel` — the dependency runs services -> packages and never back. Storage is
    injected so the decision logic here stays free of it.
    """

    def get_toggle(self, tenant_id: str, feature_key: str) -> Optional[bool]:
        """Return the tenant's decision for this feature, or None when none is recorded."""
        ...

    def set_toggle(self, tenant_id: str, feature_key: str, enabled: bool) -> None:
        ...


class RateLimitStore(Protocol):
    """Where rate limit policies and their windowed counters live."""

    def get_policy(self, tenant_id: str, capability_id: str) -> Optional[RateLimitPolicy]:
        ...

    def set_policy(
        self, tenant_id: str, capability_id: str, max_per_window: int, window_seconds: int = 60
    ) -> None:
        ...

    def try_consume(
        self, tenant_id: str, capability_id: str, policy: RateLimitPolicy, now: datetime
    ) -> "RateLimitOutcome":
        """Atomically consume one unit if the window has room.

        Atomicity belongs to the store, not to the caller. A read-then-write here would let two
        concurrent requests each observe the same count and both proceed, which is exactly the
        case a rate limit exists to stop.
        """
        ...


@dataclass(frozen=True)
class RateLimitOutcome:
    allowed: bool
    consumed: int
    window_ends_at: datetime


class FeatureRolloutEvaluator:
    """Decides whether a feature is rolled out to a tenant.

    Finding F-7. The previous implementation held a process-global `Dict[str, bool]`, accepted a
    `tenant_id` at the signature and never read it, so one tenant's rollout decision applied to
    every tenant and none of it survived a restart.

    **Absence of a toggle means enabled, and that is deliberate rather than the old bug
    preserved.** `EntitlementEvaluator` calls this with a `capability_id` as the feature key, so
    deny-by-default here would require a toggle row for every capability — which would turn a
    rollout flag into an entitlement. `AGENTS.md` §7 invariant 8 keeps those separate on purpose:
    entitlement decides whether a tenant is *allowed* a capability, rollout decides whether a
    capability is *being introduced gradually*. A capability nobody is staging is not withheld;
    it is simply not part of a rollout.

    The defect was never the default. It was that the decision was global and volatile.
    """

    def __init__(self, store: FeatureToggleStore):
        self._store = store

    def is_feature_enabled(self, feature_key: str, tenant_id: str) -> bool:
        decision = self._store.get_toggle(tenant_id, feature_key)
        return True if decision is None else decision


class RateLimiter:
    """Windowed, tenant-scoped rate limiting.

    Finding F-7, second half. The previous implementation keyed limits on capability alone, so a
    limit set for one tenant applied to all of them, and its counters carried no timestamp — the
    `reset_seconds=60` in the response was a number no code path acted on, so a tenant that hit
    its limit stayed throttled for the remaining life of the process.

    Windows are now identified by their start instant and the counter row is keyed on it, so a
    window boundary is a new row rather than a reset somebody has to schedule. Nothing runs for a
    limit to expire.
    """

    def __init__(self, store: RateLimitStore):
        self._store = store

    def evaluate(self, tenant_id: str, capability_id: str, correlation_id: str) -> RateLimitDecision:
        """
        Evaluate the window for one call.

        `correlation_id` is required rather than defaulted. The schema requires it with
        `minLength: 1`, and a default here would be a placeholder invented by the producer
        instead of the request identity carried by the caller.
        """
        now = datetime.now(timezone.utc)
        decision_id = f"rat_dec_{uuid.uuid4().hex[:12]}"

        policy = self._store.get_policy(tenant_id, capability_id)

        if policy is None:
            # No configured policy means this capability is not rate limited for this tenant.
            #
            # The previous code substituted a magic `10000`, which is worse than either honest
            # answer: it silently throttles at a number nobody chose and that appears in no
            # configuration. Rate limiting is a protective control, and the absence of one means
            # unprotected — not denied. Denying here would make the control's absence
            # indistinguishable from its enforcement.
            #
            # `limit_rate` must still satisfy the schema's `minimum: 1`, and `current_rate` must
            # remain the consumed count. Reporting a consumed count of 1 against a limit of 1
            # would read as "at the limit"; the honest shape for "not limited" is a window that
            # is not being counted, so the outcome is allowed and the numbers describe this one
            # call rather than an allowance.
            return RateLimitDecision(
                decision_id=decision_id,
                tenant_id=tenant_id,
                capability_id=capability_id,
                correlation_id=correlation_id,
                allowed=True,
                limit_rate=1,
                current_rate=0,
                reset_in_seconds=0,
                reason_code="ENTITLEMENT_ALLOWED",
                status_code=200,
                evaluated_at=now,
            )

        outcome = self._store.try_consume(tenant_id, capability_id, policy, now)
        reset_in = max(0, int((outcome.window_ends_at - now).total_seconds()))

        if not outcome.allowed:
            # Denied: nothing is consumed by this call, so the consumed count is unchanged.
            return RateLimitDecision(
                decision_id=decision_id,
                tenant_id=tenant_id,
                capability_id=capability_id,
                correlation_id=correlation_id,
                allowed=False,
                limit_rate=policy.max_per_window,
                current_rate=outcome.consumed,
                reset_in_seconds=reset_in,
                reason_code="DENY_RATE_LIMIT_EXCEEDED",
                status_code=429,
                evaluated_at=now,
            )

        # Allowed: this call consumes one unit, so the consumed count includes it. The store
        # returns the post-increment value rather than the caller computing it, because only the
        # store knows what the atomic update actually landed on.
        return RateLimitDecision(
            decision_id=decision_id,
            tenant_id=tenant_id,
            capability_id=capability_id,
            correlation_id=correlation_id,
            allowed=True,
            limit_rate=policy.max_per_window,
            current_rate=outcome.consumed,
            reset_in_seconds=reset_in,
            reason_code="ENTITLEMENT_ALLOWED",
            status_code=200,
            evaluated_at=now,
        )


class PlanRepository:
    def __init__(self):
        self._plans: Dict[str, PlanTier] = {}

    def save_plan(self, plan: PlanTier):
        self._plans[plan.plan_id] = plan

    def get_plan(self, plan_id: str) -> Optional[PlanTier]:
        return self._plans.get(plan_id)


class EntitlementEvaluator:
    def __init__(
        self,
        plan_repo: Optional[PlanRepository] = None,
        *,
        feature_toggle_store: FeatureToggleStore,
        rate_limit_store: RateLimitStore,
    ):
        """
        The two stores are required and keyword-only, deliberately.

        There is no default in-memory implementation to fall back to. `platform_kernel.db`
        already records why for persistence, and the reasoning transfers exactly: a fallback
        would let tenant-scoped rollout appear to work while nothing tenant-scoped was
        happening. That is the shape of finding F-7 — a `tenant_id` parameter accepted and
        never read — and a default would reintroduce it as a convenience.

        Keyword-only because a positional store would be easy to pass in the wrong order, and
        the two have no type overlap to catch it.
        """
        self._plans: Dict[str, PlanTier] = {}
        self._tenant_plans: Dict[str, str] = {}  # tenant_id -> plan_id
        self._tenant_overrides: Dict[str, Dict[str, Dict[str, Any]]] = {}  # tenant_id -> capability_id -> rule
        self._usage_counters: Dict[str, Dict[str, int]] = {}  # tenant_id -> capability_id -> count
        self._rollout_evaluator = FeatureRolloutEvaluator(feature_toggle_store)
        self._rate_limiter = RateLimiter(rate_limit_store)
        self._feature_toggle_store = feature_toggle_store
        self._rate_limit_store = rate_limit_store

    def register_plan(self, plan: PlanTier):
        self._plans[plan.plan_id] = plan

    def assign_tenant_plan(self, tenant_id: str, plan_id: str):
        self._tenant_plans[tenant_id] = plan_id

    def add_tenant_override(self, tenant_id: str, capability_id: str, rule: Dict[str, Any]):
        if tenant_id not in self._tenant_overrides:
            self._tenant_overrides[tenant_id] = {}
        self._tenant_overrides[tenant_id][capability_id] = rule

    def set_feature_toggle(self, tenant_id: str, feature_key: str, enabled: bool):
        """
        SIGNATURE CHANGED 2026-07-30 — `tenant_id` added as the first parameter.

        The previous form took no tenant and wrote to a process-global map, so one tenant's
        rollout decision silently applied to every tenant. That is finding F-7. A caller that
        has not been updated now fails at the call rather than quietly configuring the wrong
        thing, which is the point of changing the arity rather than defaulting it.
        """
        self._feature_toggle_store.set_toggle(tenant_id, feature_key, enabled)

    def set_rate_limit(
        self, tenant_id: str, capability_id: str, max_per_window: int, window_seconds: int = 60
    ):
        """
        SIGNATURE CHANGED 2026-07-30 — `tenant_id` added, and the window made explicit.

        The previous form keyed limits on capability alone, so a limit configured for one tenant
        throttled all of them. `window_seconds` was previously the hardcoded `60` that appeared
        in every response and that no code path acted on.
        """
        self._rate_limit_store.set_policy(
            tenant_id, capability_id, max_per_window, window_seconds
        )

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
        rate_dec = self._rate_limiter.evaluate(context.tenant_id, capability_id, correlation_id)
        if not rate_dec.allowed:
            return EntitlementDecision(
                decision_id=decision_id,
                tenant_id=context.tenant_id,
                capability_id=capability_id,
                decision=DecisionOutcome.THROTTLED,
                reason_code=rate_dec.reason_code,
                http_status=rate_dec.status_code,
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
