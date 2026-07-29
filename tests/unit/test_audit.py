import unittest
import uuid
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "kernel-core" / "python"))

from kernel_core.audit import AuditDispatcher
from kernel_core.types import DecisionResult

class TestAuditDispatcherUnit(unittest.TestCase):
    """
    Unit test suite asserting correlated security audit dispatch & schema envelope verification
    """

    def setUp(self):
        self.audit = AuditDispatcher()
        self.p_id = f"usr_{uuid.uuid4()}"
        self.t_id = f"tnt_{uuid.uuid4()}"
        self.correlation_id = f"corr_{uuid.uuid4()}"

    def test_emit_allow_audit_event(self):
        event = self.audit.emit_authorization_audit(
            correlation_id=self.correlation_id,
            actor_id=self.p_id,
            tenant_id=self.t_id,
            action="tenant_profile:read",
            resource_type="tenant_profile",
            resource_id=self.t_id,
            decision=DecisionResult.ALLOW,
            reason_code="MEMBERSHIP_ROLE_PERMITTED"
        )
        self.assertEqual(event["status"], "SUCCESS")
        self.assertEqual(event["correlation_id"], self.correlation_id)
        self.assertEqual(event["tenant_id"], self.t_id)

    def test_emit_deny_audit_event(self):
        event = self.audit.emit_authorization_audit(
            correlation_id=self.correlation_id,
            actor_id=self.p_id,
            tenant_id=self.t_id,
            action="tenant_profile:read",
            resource_type="tenant_profile",
            resource_id=self.t_id,
            decision=DecisionResult.DENY,
            reason_code="TENANT_CONTEXT_MISMATCH"
        )
        self.assertEqual(event["status"], "DENIED")
        self.assertEqual(event["reason_code"], "TENANT_CONTEXT_MISMATCH")

if __name__ == "__main__":
    unittest.main()
