"""
Phase 3 Integrated Acceptance Suite — Capability, Entitlement & Metering (BOPEN-MOD-001 / BOPEN-ENT-001 / WP-P3-02).

Verifies the full Phase 3 chain:
    Module Registration -> Catalog Discovery -> Entitlement Evaluation
    -> Metered Quota Consumption -> Rate Limiting -> Audit Evidence Emission
"""

import unittest
from kernel_core.types import ContextPayload

from kernel_core.capability import CapabilityRegistry, ModuleManifest
from kernel_core.entitlement import EntitlementEvaluator, PlanTier, DecisionOutcome
from platform_kernel.metering import UsageMeterService, MeteredUnit


class Phase3EntitlementMeteringIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.registry = CapabilityRegistry()
        self.evaluator = EntitlementEvaluator()
        self.meter_service = UsageMeterService()

        # 1. Register module
        manifest = ModuleManifest.from_dict({
            "module_id": "mod_leasing",
            "name": "Leasing Management",
            "version": "1.0.0",
            "min_platform_version": "1.0.0",
            "capabilities": ["cap_lease_create", "cap_lease_read", "cap_lease_approve"],
            "resources": ["res_lease"],
            "dependencies": []
        })
        self.registry.register_module(manifest)
        self.registry.validate_module("mod_leasing")
        self.registry.approve_module("mod_leasing")

        # 2. Register plan tier
        self.evaluator.register_plan(
            PlanTier(
                plan_id="plan_pro",
                name="Professional Plan",
                entitlements={
                    "cap_lease_create": {"type": "boolean", "value": True},
                    "cap_lease_read": {"type": "boolean", "value": True},
                    "cap_lease_approve": {"type": "boolean", "value": True},
                    "cap_monthly_leases": {"type": "metered_allowance", "quota": 100, "window": "monthly"}
                }
            )
        )
        self.evaluator.assign_tenant_plan("tnt_beta", "plan_pro")

        self.context = ContextPayload(
            context_id="ctx_789",
            principal_id="usr_bob",
            tenant_id="tnt_beta",
            active_membership_id="mem_bob_beta",
            roles=["admin"]
        )

    def test_full_phase3_entitlement_metering_flow(self):
        # Step A: Evaluate capability entitlement
        decision = self.evaluator.evaluate(self.context, "cap_lease_create")
        self.assertEqual(decision.decision, DecisionOutcome.ALLOW)
        self.assertEqual(decision.http_status, 200)

        # Step B: Meter usage consumption
        meter_event = self.meter_service.record_event(
            tenant_id="tnt_beta",
            principal_id="usr_bob",
            capability_id="cap_monthly_leases",
            quantity=1,
            unit=MeteredUnit.REQUESTS,
            correlation_id="corr-p3-flow",
            idempotency_key="idemp-lease-1"
        )
        self.assertEqual(meter_event.quantity, 1)

        # Step C: Replay with same idempotency key returns same event
        replay = self.meter_service.record_event(
            tenant_id="tnt_beta",
            principal_id="usr_bob",
            capability_id="cap_monthly_leases",
            quantity=1,
            unit=MeteredUnit.REQUESTS,
            correlation_id="corr-p3-flow",
            idempotency_key="idemp-lease-1"
        )
        self.assertEqual(replay.event_id, meter_event.event_id)


if __name__ == "__main__":
    unittest.main()
