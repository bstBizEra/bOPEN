"""
Phase 3 Unit Acceptance Suite — Commercial Entitlement Evaluator (BOPEN-ENT-001 / WP-P3-02 & WP-P3-04).

Verifies entitlement plan evaluation, feature rollout flags, rate limiting, quota caps,
negative quantity rejection, schema contract compliance, and reason-code HTTP mapping.
"""

import unittest
import json
from pathlib import Path
import jsonschema
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
    InvalidQuantityError,
    StructurallyInvalidContextError,
)

# Test doubles. They live in the test tree because a fallback store reachable from production
# would reintroduce finding F-7 as a convenience — see tests/support/stores.py.
from tests.support.stores import FakeFeatureToggleStore, FakeRateLimitStore

ROOT = Path(__file__).resolve().parents[2]


class EntitlementEvaluatorUnitTests(unittest.TestCase):
    def setUp(self):
        # F-7: the stores are required and have no default. An in-memory double is legitimate
        # here because these are unit tests of decision logic; what is refused is a fallback
        # reachable from production. See tests/support/stores.py.
        # One tenant per test class. The doubles are tenant-keyed, so a test that forgot to
        # pass it would fail rather than silently exercise the global behaviour F-7 records.
        self.tenant_id = "tnt_alpha"
        self.toggles = FakeFeatureToggleStore()
        self.rate_limits = FakeRateLimitStore()
        self.evaluator = EntitlementEvaluator(
            feature_toggle_store=self.toggles, rate_limit_store=self.rate_limits
        )
        self.context = ContextPayload(
            context_id="ctx_456",
            principal_id="usr_alice",
            tenant_id="tnt_alpha",
            active_membership_id="mem_alice_alpha",
            roles=["member"]
        )
        # Load schema for contract compliance verification (Finding 4)
        schema_path = ROOT / "contracts/schemas/entitlement-decision.schema.json"
        self.decision_schema = json.loads(schema_path.read_text(encoding="utf-8"))

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

    def test_entitled_capability_allows_execution_and_matches_schema(self):
        decision = self.evaluator.evaluate(self.context, "cap_invoice_create", correlation_id="corr-schema-1")
        self.assertEqual(decision.decision, DecisionOutcome.ALLOW)
        self.assertEqual(decision.reason_code, "ENTITLEMENT_ALLOWED")
        self.assertEqual(decision.http_status, 200)

        # Validate generated decision against frozen JSON Schema (Finding 4)
        jsonschema.validate(instance=decision.to_dict(), schema=self.decision_schema)

    def test_unentitled_capability_denies_with_http_403(self):
        decision = self.evaluator.evaluate(self.context, "cap_invoice_export")
        self.assertEqual(decision.decision, DecisionOutcome.DENY)
        self.assertEqual(decision.reason_code, "DENY_NOT_ENTITLED")
        self.assertEqual(decision.http_status, 403)
        jsonschema.validate(instance=decision.to_dict(), schema=self.decision_schema)

    def test_unsupported_capability_denies_with_http_403(self):
        decision = self.evaluator.evaluate(self.context, "cap_unsupported_xyz")
        self.assertEqual(decision.decision, DecisionOutcome.DENY)
        self.assertEqual(decision.reason_code, "DENY_UNSUPPORTED_CAPABILITY")
        self.assertEqual(decision.http_status, 403)

    def test_negative_or_zero_quantity_injection_rejected(self):
        # Finding 3 negative quantity probe
        with self.assertRaises(InvalidQuantityError):
            self.evaluator.evaluate(self.context, "cap_api_calls", requested_quantity=0)

        with self.assertRaises(InvalidQuantityError):
            self.evaluator.evaluate(self.context, "cap_api_calls", requested_quantity=-50)

        with self.assertRaises(InvalidQuantityError):
            self.evaluator.record_usage("tnt_alpha", "cap_api_calls", -100)

    def test_quota_exceeded_denies_with_http_429(self):
        self.evaluator.record_usage("tnt_alpha", "cap_api_calls", 1000)
        decision = self.evaluator.evaluate(self.context, "cap_api_calls", requested_quantity=1)
        self.assertEqual(decision.decision, DecisionOutcome.DENY)
        self.assertEqual(decision.reason_code, "DENY_QUOTA_EXCEEDED")
        self.assertEqual(decision.http_status, 429)
        jsonschema.validate(instance=decision.to_dict(), schema=self.decision_schema)

    def test_disabled_feature_rollout_toggle_denies_execution(self):
        # Finding 6 & 7 feature rollout test
        self.evaluator.set_feature_toggle(self.tenant_id, "cap_invoice_create", False)
        decision = self.evaluator.evaluate(self.context, "cap_invoice_create")
        self.assertEqual(decision.decision, DecisionOutcome.DENY)
        self.assertEqual(decision.reason_code, "DENY_FEATURE_DISABLED")
        self.assertEqual(decision.http_status, 403)

    def test_rate_limit_burst_threshold_exceeded(self):
        # Finding 6 & 7 rate limit test
        self.evaluator.set_rate_limit(self.tenant_id, "cap_invoice_create", 2)
        dec1 = self.evaluator.evaluate(self.context, "cap_invoice_create")
        dec2 = self.evaluator.evaluate(self.context, "cap_invoice_create")
        dec3 = self.evaluator.evaluate(self.context, "cap_invoice_create")

        self.assertEqual(dec1.decision, DecisionOutcome.ALLOW)
        self.assertEqual(dec2.decision, DecisionOutcome.ALLOW)
        self.assertEqual(dec3.decision, DecisionOutcome.THROTTLED)
        self.assertEqual(dec3.reason_code, "DENY_RATE_LIMIT_EXCEEDED")
        self.assertEqual(dec3.http_status, 429)

    def test_structurally_invalid_context_rejected(self):
        invalid_ctx = ContextPayload(context_id="", principal_id="", tenant_id="", active_membership_id="", roles=[])
        with self.assertRaises(StructurallyInvalidContextError):
            self.evaluator.evaluate(invalid_ctx, "cap_invoice_create")


if __name__ == "__main__":
    unittest.main()
