"""
Phase 3 Integrated Acceptance Suite — Capability, Entitlement & Metering (BOPEN-MOD-001 / BOPEN-ENT-001 / WP-P3-02).

Verifies full Phase 3 flow:
    Module Registration -> Catalog Discovery -> Entitlement Evaluation
    -> Metered Usage -> Idempotency Replay Security -> Quota Reservations -> Outbox Dispatch
"""

import unittest
import json
from pathlib import Path
import jsonschema
from kernel_core.types import ContextPayload

from kernel_core.capability import ModuleRegistry, CapabilityResolver, ModuleManifest
from kernel_core.entitlement import EntitlementEvaluator, PlanTier, DecisionOutcome
from platform_kernel.metering import (
    UsageMeterService,
    MeteredUnit,
    CrossTenantIdempotencyViolationError,
    InvalidQuantityError,
    QuotaReservationError,
)

ROOT = Path(__file__).resolve().parents[2]


class Phase3EntitlementMeteringIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.registry = ModuleRegistry()
        self.resolver = CapabilityResolver(self.registry)
        self.evaluator = EntitlementEvaluator()
        self.meter_service = UsageMeterService()

        # Load schema for contract compliance verification (Finding 4)
        schema_path = ROOT / "contracts/schemas/usage-metered-event.schema.json"
        self.event_schema = json.loads(schema_path.read_text(encoding="utf-8"))

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
        self.registry.publish_module("mod_leasing")

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
        # Step A: Resolve capability
        mod_id = self.resolver.resolve_capability("cap_lease_create")
        self.assertEqual(mod_id, "mod_leasing")

        # Step B: Evaluate capability entitlement
        decision = self.evaluator.evaluate(self.context, "cap_lease_create")
        self.assertEqual(decision.decision, DecisionOutcome.ALLOW)
        self.assertEqual(decision.http_status, 200)

        # Step C: Meter usage consumption
        meter_event = self.meter_service.record_event(
            tenant_id="tnt_beta",
            principal_id="usr_bob",
            context_id="ctx_789",
            capability_id="cap_monthly_leases",
            quantity=1,
            unit=MeteredUnit.REQUESTS,
            correlation_id="corr-p3-flow",
            idempotency_key="idemp-lease-1"
        )
        self.assertEqual(meter_event.quantity, 1)

        # Validate event against frozen JSON Schema (Finding 4)
        jsonschema.validate(instance=meter_event.to_dict(), schema=self.event_schema)

        # Step D: Same tenant replay with same key returns same event
        replay = self.meter_service.record_event(
            tenant_id="tnt_beta",
            principal_id="usr_bob",
            context_id="ctx_789",
            capability_id="cap_monthly_leases",
            quantity=1,
            unit=MeteredUnit.REQUESTS,
            correlation_id="corr-p3-flow",
            idempotency_key="idemp-lease-1"
        )
        self.assertEqual(replay.event_id, meter_event.event_id)

    def test_cross_tenant_idempotency_replay_attack_prevented(self):
        # Finding 1 cross-tenant event disclosure probe
        # Tenant A records event with key 'idemp-shared-1'
        evt_a = self.meter_service.record_event(
            tenant_id="tnt_a",
            principal_id="usr_a",
            context_id="ctx_a",
            capability_id="cap_monthly_leases",
            quantity=10,
            unit=MeteredUnit.REQUESTS,
            correlation_id="corr-a",
            idempotency_key="idemp-shared-1"
        )

        # Tenant B attempts to reuse Tenant A's idempotency key 'idemp-shared-1' with different payload
        with self.assertRaises(CrossTenantIdempotencyViolationError):
            self.meter_service.record_event(
                tenant_id="tnt_b",
                principal_id="usr_b",
                context_id="ctx_b",
                capability_id="cap_monthly_leases",
                quantity=10,
                unit=MeteredUnit.REQUESTS,
                correlation_id="corr-b",
                idempotency_key="idemp-shared-1"
            )

    def test_quota_reservation_commit_and_outbox_dispatch(self):
        # Finding 6 quota reservation & outbox test
        now = meter_event = self.meter_service.record_event(
            tenant_id="tnt_beta",
            principal_id="usr_bob",
            context_id="ctx_789",
            capability_id="cap_monthly_leases",
            quantity=5,
            unit=MeteredUnit.REQUESTS,
            correlation_id="corr-res-1",
            idempotency_key="idemp-res-1"
        )
        res = self.meter_service.create_quota_reservation(
            tenant_id="tnt_beta",
            capability_id="cap_monthly_leases",
            reserved_quantity=5,
            expires_at=now.timestamp,
            correlation_id="corr-res-1"
        )
        self.assertEqual(res.status, "pending")

        committed = self.meter_service.commit_reservation(res.reservation_id)
        self.assertEqual(committed.status, "committed")

        # Outbox dispatch
        count = self.meter_service.dispatch_outbox()
        self.assertGreaterEqual(count, 1)
        self.assertEqual(len(self.meter_service.get_outbox_events()), 0)


if __name__ == "__main__":
    unittest.main()
