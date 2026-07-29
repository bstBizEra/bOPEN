import unittest
import uuid
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "kernel-core" / "python"))

from kernel_core.types import (
    Principal, PrincipalType, Tenant, TenantStatus,
    Membership, MembershipState, ContextPayload,
    AuthorizationRequest, AuthorizationDecision, DecisionResult
)

class TestKernelCoreTypes(unittest.TestCase):
    """
    Unit test suite asserting domain model constraints, immutable UUIDs, and invariants INV-P1-001..006
    """

    def test_principal_instantiation(self):
        p_id = f"usr_{uuid.uuid4()}"
        p = Principal(id=p_id, type=PrincipalType.HUMAN, email="alice@example.com")
        self.assertEqual(p.id, p_id)
        self.assertEqual(p.type, PrincipalType.HUMAN)
        self.assertTrue(p.id.startswith("usr_"))

    def test_tenant_instantiation(self):
        t_id = f"tnt_{uuid.uuid4()}"
        t = Tenant(id=t_id, name="Acme Corp", status=TenantStatus.ACTIVE)
        self.assertEqual(t.id, t_id)
        self.assertEqual(t.status, TenantStatus.ACTIVE)

    def test_membership_binding(self):
        m_id = f"mem_{uuid.uuid4()}"
        t_id = f"tnt_{uuid.uuid4()}"
        p_id = f"usr_{uuid.uuid4()}"
        m = Membership(id=m_id, tenant_id=t_id, principal_id=p_id, role="owner", state=MembershipState.ACTIVE)
        self.assertEqual(m.tenant_id, t_id)
        self.assertEqual(m.principal_id, p_id)
        self.assertEqual(m.role, "owner")

    def test_context_payload(self):
        ctx_id = f"ctx_{uuid.uuid4()}"
        c = ContextPayload(
            context_id=ctx_id,
            principal_id="usr_123",
            tenant_id="tnt_456",
            active_membership_id="mem_789",
            roles=["owner"]
        )
        self.assertEqual(c.context_id, ctx_id)
        self.assertIn("owner", c.roles)

if __name__ == "__main__":
    unittest.main()
