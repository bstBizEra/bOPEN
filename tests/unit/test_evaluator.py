import unittest
import uuid
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "kernel-core" / "python"))

from kernel_core.types import (
    ContextPayload, AuthorizationRequest, DecisionResult
)
from kernel_core.evaluator import AuthorizationEvaluator

class TestAuthorizationEvaluatorUnit(unittest.TestCase):
    """
    Unit test suite asserting 100% of evaluator reason codes & deny-by-default rules
    (P1-T007 through P1-T017)
    """

    def setUp(self):
        self.evaluator = AuthorizationEvaluator()
        self.p_id = f"usr_{uuid.uuid4()}"
        self.t_id = f"tnt_{uuid.uuid4()}"
        self.m_id = f"mem_{uuid.uuid4()}"

        self.context = ContextPayload(
            context_id=f"ctx_{uuid.uuid4()}",
            principal_id=self.p_id,
            tenant_id=self.t_id,
            active_membership_id=self.m_id,
            roles=["owner"]
        )

    def test_allow_explicit_owner_read(self):
        req = AuthorizationRequest(
            principal_id=self.p_id,
            tenant_id=self.t_id,
            action="tenant_profile:read",
            resource_type="tenant_profile",
            resource_id=self.t_id,
            context=self.context
        )
        decision = self.evaluator.evaluate(req, active_membership_state="active")
        self.assertEqual(decision.decision, DecisionResult.ALLOW)
        self.assertEqual(decision.reason_code, "MEMBERSHIP_ROLE_PERMITTED")

    def test_deny_tenant_mismatch(self):
        other_t_id = f"tnt_{uuid.uuid4()}"
        req = AuthorizationRequest(
            principal_id=self.p_id,
            tenant_id=other_t_id,
            action="tenant_profile:read",
            resource_type="tenant_profile",
            resource_id=other_t_id,
            context=self.context
        )
        decision = self.evaluator.evaluate(req, active_membership_state="active")
        self.assertEqual(decision.decision, DecisionResult.DENY)
        self.assertEqual(decision.reason_code, "TENANT_CONTEXT_MISMATCH")

    def test_deny_membership_inactive(self):
        req = AuthorizationRequest(
            principal_id=self.p_id,
            tenant_id=self.t_id,
            action="tenant_profile:read",
            resource_type="tenant_profile",
            resource_id=self.t_id,
            context=self.context
        )
        decision = self.evaluator.evaluate(req, active_membership_state="revoked")
        self.assertEqual(decision.decision, DecisionResult.DENY)
        self.assertEqual(decision.reason_code, "MEMBERSHIP_INACTIVE")

    def test_deny_no_matching_role(self):
        no_role_context = ContextPayload(
            context_id=f"ctx_{uuid.uuid4()}",
            principal_id=self.p_id,
            tenant_id=self.t_id,
            active_membership_id=self.m_id,
            roles=["guest"]
        )
        req = AuthorizationRequest(
            principal_id=self.p_id,
            tenant_id=self.t_id,
            action="tenant_profile:read",
            resource_type="tenant_profile",
            resource_id=self.t_id,
            context=no_role_context
        )
        decision = self.evaluator.evaluate(req, active_membership_state="active")
        self.assertEqual(decision.decision, DecisionResult.DENY)
        self.assertEqual(decision.reason_code, "DEFAULT_DENY")

if __name__ == "__main__":
    unittest.main()
