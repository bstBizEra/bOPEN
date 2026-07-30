"""
Phase 3 Integrated Acceptance Suite — Capability, Entitlement & Metering (BOPEN-MOD-001 / BOPEN-ENT-001 / WP-P3-02).

Verifies full Phase 3 flow:
    Module Registration -> Catalog Discovery -> Entitlement Evaluation
    -> Metered Usage -> Idempotency Replay Security -> Quota Reservations -> Outbox Dispatch

FIXTURES CHANGED 2026-07-30 (BOPEN-P35-001, findings F-3 and the F-2 residue)

`UsageMeterService` now persists to PostgreSQL instead of to Python dictionaries, so the
fixtures in this file had to change in three ways. None of them weakens a check:

1. Tenant identifiers were `tnt_beta`, `tnt_a` and `tnt_b`. Migration 003 constrains the
   `tenant_id` columns of the 002 family to UUID-shaped text and migration 004 tightens that
   to canonical lowercase, so those values are unstorable — and the isolation policy casts the
   session variable to `uuid`, so they cannot even open a session. They are now UUIDs,
   allocated per test so this suite is safe against a shared verification database.

2. A quota reservation now holds against a `usage_meter_balances` row, so one has to be
   provisioned before a reservation can be taken. Previously nothing was held, which is why
   nothing had to exist.

3. `expires_at` was passed the metered event's own timestamp — an instant already in the past
   by the time the reservation was created. `chk_reservation_expiry_future` refuses that row.
   The old code accepted it, which is the F-2 defect itself.

Two assertions also changed. Both are quoted and justified at their call sites, because
changing an assertion to make a suite pass is otherwise indistinguishable from deleting the
check.
"""

import json
import sys
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jsonschema

ROOT_FOR_PATH = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_FOR_PATH / "services" / "platform-kernel" / "python"))
sys.path.insert(0, str(ROOT_FOR_PATH / "packages" / "kernel-core" / "python"))

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

from tests.support.stores import FakeFeatureToggleStore, FakeRateLimitStore

ROOT = Path(__file__).resolve().parents[2]


class Phase3EntitlementMeteringIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.registry = ModuleRegistry()
        self.resolver = CapabilityResolver(self.registry)
        # Doubles rather than the PostgreSQL stores, deliberately. This suite exercises the
        # metering and entitlement flow; rollout storage is a different concern with its own
        # integration tests. The Postgres stores also require a real row in `tenants`, and these
        # fixtures intentionally do not create one — migration 002's tables carry no foreign key
        # to it, and that gap is something these tests exercise rather than paper over.
        self.evaluator = EntitlementEvaluator(
            feature_toggle_store=FakeFeatureToggleStore(),
            rate_limit_store=FakeRateLimitStore(),
        )
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
        # FIXTURE CHANGE: tenant identifiers are canonical lowercase UUIDs, allocated per
        # test. See the module docstring, item 1. Fresh identifiers each run mean this suite
        # never collides with, and never has to clean up after, other work sharing the
        # verification database.
        self.tenant_beta = str(uuid.uuid4())
        self.evaluator.assign_tenant_plan(self.tenant_beta, "plan_pro")

        self.context = ContextPayload(
            context_id="ctx_789",
            principal_id="usr_bob",
            tenant_id=self.tenant_beta,
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
            tenant_id=self.tenant_beta,
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
            tenant_id=self.tenant_beta,
            principal_id="usr_bob",
            context_id="ctx_789",
            capability_id="cap_monthly_leases",
            quantity=1,
            unit=MeteredUnit.REQUESTS,
            correlation_id="corr-p3-flow",
            idempotency_key="idemp-lease-1"
        )
        self.assertEqual(replay.event_id, meter_event.event_id)

    def test_cross_tenant_idempotency_key_reuse_is_isolated_not_refused(self):
        """
        ASSERTION CHANGED 2026-07-30. The previous form was:

            with self.assertRaises(CrossTenantIdempotencyViolationError):
                self.meter_service.record_event(tenant_id="tnt_b", ...,
                                                idempotency_key="idemp-shared-1")

        That assertion encoded the defect it appeared to guard against. The guard it pinned was
        a process-global dictionary, `_global_idempotency_keys`, mapping an idempotency key to
        the tenant that first used it. Three things were wrong with it:

        * It made one tenant's write fail because of another tenant's data. Tenant B could
          discover which keys tenant A had used by observing which of its own writes were
          refused.
        * The refusal message interpolated the owning tenant's identifier —
          "Key '...' is owned by tenant 'tnt_a'" — so the probe did not even have to be
          inferential. It named the other tenant outright.
        * It was not a security boundary at all. It lived in one process's memory, so a second
          worker enforced nothing, and it vanished on restart.

        The isolation model does not need it. `usage_outbox` is unique on
        `(tenant_id, idempotency_key)`, and the row-level security policy means tenant B cannot
        observe tenant A's row under any query. Two tenants holding the same key is a
        non-event, and it must be, because the alternative is the coupling above.

        So the check is inverted rather than removed: the reuse now succeeds, produces two
        independent events, and neither tenant can see the other's. That is a strictly stronger
        assertion than the original — it fails if the constraint is ever widened to the key
        alone, and it fails if the isolation policy stops working, whereas the original passed
        in both of those cases.
        """
        tenant_a = str(uuid.uuid4())
        tenant_b = str(uuid.uuid4())
        shared_key = f"idemp-shared-{uuid.uuid4()}"

        evt_a = self.meter_service.record_event(
            tenant_id=tenant_a,
            principal_id="usr_a",
            context_id="ctx_a",
            capability_id="cap_monthly_leases",
            quantity=10,
            unit=MeteredUnit.REQUESTS,
            correlation_id="corr-a",
            idempotency_key=shared_key
        )

        evt_b = self.meter_service.record_event(
            tenant_id=tenant_b,
            principal_id="usr_b",
            context_id="ctx_b",
            capability_id="cap_monthly_leases",
            quantity=10,
            unit=MeteredUnit.REQUESTS,
            correlation_id="corr-b",
            idempotency_key=shared_key
        )

        self.assertNotEqual(evt_a.event_id, evt_b.event_id)
        self.assertEqual(
            [r.event_id for r in self.meter_service.get_outbox_events(tenant_a)],
            [evt_a.event_id],
            "tenant A can see a row that is not its own",
        )
        self.assertEqual(
            [r.event_id for r in self.meter_service.get_outbox_events(tenant_b)],
            [evt_b.event_id],
            "tenant B can see a row that is not its own",
        )

    def test_same_tenant_replay_with_a_conflicting_payload_is_refused(self):
        """
        The half of the old guard that was a real check, kept and now enforced against the
        database rather than a dictionary. `IdempotencyPayloadConflictError` subclasses
        `CrossTenantIdempotencyViolationError`, so callers catching the old name still catch it.
        """
        key = f"idemp-conflict-{uuid.uuid4()}"
        self.meter_service.record_event(
            tenant_id=self.tenant_beta,
            principal_id="usr_bob",
            context_id="ctx_789",
            capability_id="cap_monthly_leases",
            quantity=1,
            unit=MeteredUnit.REQUESTS,
            correlation_id="corr-conflict",
            idempotency_key=key
        )

        with self.assertRaises(CrossTenantIdempotencyViolationError):
            self.meter_service.record_event(
                tenant_id=self.tenant_beta,
                principal_id="usr_bob",
                context_id="ctx_789",
                capability_id="cap_monthly_leases",
                quantity=99,
                unit=MeteredUnit.REQUESTS,
                correlation_id="corr-conflict",
                idempotency_key=key
            )

    def test_quota_reservation_commit_and_outbox_dispatch(self):
        # Finding 6 quota reservation & outbox test
        meter_event = self.meter_service.record_event(
            tenant_id=self.tenant_beta,
            principal_id="usr_bob",
            context_id="ctx_789",
            capability_id="cap_monthly_leases",
            quantity=5,
            unit=MeteredUnit.REQUESTS,
            correlation_id="corr-res-1",
            idempotency_key="idemp-res-1"
        )

        # FIXTURE ADDED: a reservation now holds against a balance row, so the allowance the
        # plan tier declares has to exist in `usage_meter_balances` before it can be reserved
        # from. 100 is the `cap_monthly_leases` quota registered on plan_pro in setUp.
        self.meter_service.provision_quota(
            tenant_id=self.tenant_beta,
            capability_id="cap_monthly_leases",
            quota_limit=100,
        )

        # FIXTURE CHANGE: this was `expires_at=now.timestamp`, where `now` was the metered
        # event recorded immediately above — an instant already in the past. That is the F-2
        # defect stated as a fixture: the service accepted an already-expired reservation and
        # committed it. `chk_reservation_expiry_future` now refuses the row outright.
        res = self.meter_service.create_quota_reservation(
            tenant_id=self.tenant_beta,
            capability_id="cap_monthly_leases",
            reserved_quantity=5,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            correlation_id="corr-res-1"
        )
        self.assertEqual(res.status, "pending")

        # FIXTURE CHANGE: `commit_reservation` takes the record rather than its identifier.
        # `quota_reservations` has no column for `quota_window`, `window_starts_at`,
        # `window_ends_at` or `idempotency_key`, so an identifier alone cannot rebuild a
        # contract-valid result. Every field the table does store is verified against the
        # stored row inside the transition's transaction.
        committed = self.meter_service.commit_reservation(res)
        self.assertEqual(committed.status, "committed")

        # Outbox dispatch
        count = self.meter_service.dispatch_outbox(self.tenant_beta)
        self.assertGreaterEqual(count, 1)

        # ASSERTION CHANGED 2026-07-30. The previous form was:
        #
        #     self.assertEqual(len(self.meter_service.get_outbox_events()), 0)
        #
        # It asserted that dispatching empties the outbox, which is what the implementation
        # did — `self._outbox.clear()` — and is the opposite of what an outbox is for. Once
        # cleared, "was this event delivered?" and "did this event ever exist?" have the same
        # answer, so redelivery cannot be investigated and a consumer that never received the
        # message leaves no trace. That assertion encoded finding F-3.
        #
        # A transactional outbox marks and keeps. The row survives with `dispatched_at` set,
        # and it is the *pending* set that empties. Both halves are asserted, because
        # asserting only that the row survives would pass against an implementation that never
        # dispatched anything.
        retained = self.meter_service.get_outbox_events(self.tenant_beta)
        self.assertEqual(len(retained), 1, "dispatch must not delete the record it sent")
        self.assertEqual(retained[0].event_id, meter_event.event_id)
        self.assertIsNotNone(retained[0].dispatched_at)
        self.assertEqual(
            len(self.meter_service.get_pending_outbox_events(self.tenant_beta)), 0
        )


if __name__ == "__main__":
    unittest.main()
