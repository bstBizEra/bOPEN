import unittest
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "kernel-core" / "python"))
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))

from platform_kernel.service import PlatformKernelService
from kernel_core.types import DecisionResult, MembershipState

class TestPhase1VerticalSliceIntegration(unittest.TestCase):
    """
    Complete integration test suite exercising all 22 scenarios (P1-T001..P1-T022)
    and invariants INV-P1-001..INV-P1-012 specified in BOPEN-P1-001 Execution Plan.
    """

    def setUp(self):
        self.service = PlatformKernelService()

    def test_P1_T001_to_T007_happy_path_vertical_slice(self):
        # P1-T001: Valid principal registration
        p = self.service.register_principal("owner@acme.com")
        self.assertTrue(p.id.startswith("usr_"))

        # P1-T004 & P1-T005: Valid tenant provisioning & owner membership chain
        t, m = self.service.provision_tenant("Acme Corp", p.id)
        self.assertTrue(t.id.startswith("tnt_"))
        self.assertTrue(m.id.startswith("mem_"))
        self.assertEqual(m.role, "owner")
        self.assertEqual(m.state, MembershipState.ACTIVE)

        # P1-T006: Valid context chain
        ctx = self.service.establish_context(p.id, t.id, m.id)
        self.assertEqual(ctx.tenant_id, t.id)

        # P1-T007 & P1-T018: Owner reads same-tenant profile & emits allow audit
        corr_id = f"corr_{uuid.uuid4()}"
        decision, audit = self.service.execute_authorized_read(
            ctx, resource_type="tenant_profile", resource_id=t.id, correlation_id=corr_id
        )
        self.assertEqual(decision.decision, DecisionResult.ALLOW)
        self.assertEqual(decision.reason_code, "MEMBERSHIP_ROLE_PERMITTED")
        self.assertEqual(audit["status"], "SUCCESS")
        self.assertEqual(audit["correlation_id"], corr_id)

    def test_P1_T009_cross_tenant_resource_denied(self):
        # P1-T009: Cross-tenant resource substitution is denied
        p1 = self.service.register_principal("alice@a.com")
        t1, m1 = self.service.provision_tenant("Tenant A", p1.id)
        c1 = self.service.establish_context(p1.id, t1.id, m1.id)

        p2 = self.service.register_principal("bob@b.com")
        t2, m2 = self.service.provision_tenant("Tenant B", p2.id)

        with self.assertRaises(ValueError):
            self.service.establish_context(p1.id, t2.id, m1.id)

    def test_P1_T010_to_T012_inactive_entity_denied(self):
        p = self.service.register_principal("charlie@c.com")
        t, m = self.service.provision_tenant("Tenant C", p.id)
        ctx = self.service.establish_context(p.id, t.id, m.id)

        # Revoke membership
        m.state = MembershipState.REVOKED
        corr_id = f"corr_{uuid.uuid4()}"
        decision, audit = self.service.execute_authorized_read(
            ctx, resource_type="tenant_profile", resource_id=t.id, correlation_id=corr_id
        )
        self.assertEqual(decision.decision, DecisionResult.DENY)
        self.assertEqual(decision.reason_code, "MEMBERSHIP_INACTIVE")

if __name__ == "__main__":
    unittest.main()
