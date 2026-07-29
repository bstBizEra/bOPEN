"""
Phase 3 Unit Acceptance Suite — Commercial Entitlement Evaluator (BOPEN-ENT-001 / WP-P3-02 & WP-P3-04).

Verifies entitlement plan evaluation, feature flags, capacity/metered quotas,
tenant overrides, and deterministic reason-code mapping to HTTP 403 vs 429 status codes.
"""

import unittest
from datetime import datetime, timezone
from kernel_core.types import ContextPayload

# Entitlement Evaluator imports
from kernel_core.entitlement import (
    EntitlementEvaluator,
    PlanTier,
    EntitlementDecision,
    DecisionOutcome,
    QuotaExceededError,
    NotEntitledError,
    UnsupportedCapabilityError,
)


class EntitlementEvaluatorUnitTests(unittest.TestCase):
    def setUp(self):
        self.evaluator = EntitlementEvaluator()
        self.context = ContextPayload(
            context_id="ctx_456",
            principal_id="usr_alice",
            tenant_id="tnt_alpha",
            active_membership_id="mem_alice_alpha",
            roles=["member"]
        )
        # Register standard plan tiers
        self.evaluator.register_plan(
            PlanTier(
                plan_id="plan_free",
                name="Free Tier",
                entitlements={
                    "cap_invoice_create": {"type": "boolean", "value": True},
                    "cap_invoice_export": {"type": "boolean", "value": False},
                    "cap_api_calls": {"type": "metered_allowance", "quota": 1000, "window": "monthly"}
                }
            )
        )
        self.evaluator.assign_tenant_plan("tnt_alpha", "plan_free")

    def test_entitled_capability_allows_execution(self):
        decision = self.evaluator.evaluate(self.context, "cap_invoice_create")
        self.assertEqual(decision.decision, DecisionOutcome.ALLOW)
        self.assertEqual(decision.reason_code, "ENTITLEMENT_ALLOWED")
        self.assertEqual(decision.http_status, 200)

    def test_unentitled_capability_denies_with_http_403(self):
        decision = self.evaluator.evaluate(self.context, "cap_invoice_export")
        self.assertEqual(decision.decision, DecisionOutcome.DENY)
        self.assertEqual(decision.reason_code, "DENY_NOT_ENTITLED")
        self.assertEqual(decision.http_status, 403)

    def test_unsupported_capability_denies_with_http_403(self):
        decision = self.evaluator.evaluate(self.context, "cap_unsupported_xyz")
        self.assertEqual(decision.decision, DecisionOutcome.DENY)
        self.assertEqual(decision.reason_code, "DENY_UNSUPPORTED_CAPABILITY")
        self.assertEqual(decision.http_status, 403)

    def test_quota_exceeded_denies_with_http_429(self):
        # Consume the 1000 quota
        self.evaluator.record_usage("tnt_alpha", "cap_api_calls", 1000)
        decision = self.evaluator.evaluate(self.context, "cap_api_calls", requested_quantity=1)
        self.assertEqual(decision.decision, DecisionOutcome.DENY)
        self.assertEqual(decision.reason_code, "DENY_QUOTA_EXCEEDED")
        self.assertEqual(decision.http_status, 429)

    def test_tenant_override_grants_capability(self):
        # Override tnt_alpha to have cap_invoice_export
        self.evaluator.add_tenant_override("tnt_alpha", "cap_invoice_export", {"type": "boolean", "value": True})
        decision = self.evaluator.evaluate(self.context, "cap_invoice_export")
        self.assertEqual(decision.decision, DecisionOutcome.ALLOW)
        self.assertEqual(decision.reason_code, "ENTITLEMENT_ALLOWED")
        self.assertEqual(decision.http_status, 200)


if __name__ == "__main__":
    unittest.main()
