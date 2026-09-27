"""RED-first access-policy controls for Party ContactPoint corrective work.

These tests are maker-authored requirements, not an independent verdict.  They keep the
authorization question separate from RLS: a valid tenant context limits which rows exist, but it
does not itself grant any ContactPoint action.
"""

from __future__ import annotations

import ast
import sys
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "kernel-core" / "python"))

from kernel_core.evaluator import AuthorizationEvaluator
from kernel_core.types import (
    AuthorizationRequest,
    ContextPayload,
    DecisionResult,
)


# Handler -> (action, resource type).  Every externally reachable ContactPoint operation must make
# one independent decision.  A list or procedure-discovery call never grants a later mutation.
CONTACT_POINT_ACTION_MATRIX = {
    "create_contact_point": ("party.contact_point.create", "party"),
    "list_contact_points": ("party.contact_point.list", "party"),
    "read_contact_point": ("party.contact_point.read", "party_contact_point"),
    "update_contact_point": ("party.contact_point.update", "party_contact_point"),
    "retire_contact_point": ("party.contact_point.retire", "party_contact_point"),
    "verify_contact_point": ("party.contact_point.verify", "party_contact_point"),
    "set_primary_contact_point": ("party.contact_point.set_primary", "party_contact_point"),
    "resolve_recipient": ("party.contact_point.resolve", "party"),
}


class TestContactPointDefaultDenyMatrix(unittest.TestCase):
    """The existing decision interface must default-deny every ContactPoint action."""

    def setUp(self) -> None:
        self.tenant_id = str(uuid.uuid4())
        self.principal_id = str(uuid.uuid4())
        self.context = ContextPayload(
            context_id=str(uuid.uuid4()),
            principal_id=self.principal_id,
            tenant_id=self.tenant_id,
            active_membership_id=str(uuid.uuid4()),
            roles=[],
        )
        self.evaluator = AuthorizationEvaluator()

    def _decision(self, action: str, resource_type: str):
        return self.evaluator.evaluate(
            AuthorizationRequest(
                principal_id=self.principal_id,
                tenant_id=self.tenant_id,
                action=action,
                resource_type=resource_type,
                resource_id=str(uuid.uuid4()),
                context=self.context,
            ),
            active_membership_state="active",
        )

    def test_every_contact_point_action_is_denied_without_an_explicit_role_or_grant(self):
        for action, resource_type in CONTACT_POINT_ACTION_MATRIX.values():
            with self.subTest(action=action):
                decision = self._decision(action, resource_type)
                self.assertEqual(decision.decision, DecisionResult.DENY)
                self.assertEqual(decision.reason_code, "DEFAULT_DENY")

    def test_entitlement_or_tenant_context_cannot_substitute_for_permission(self):
        """An active context is present; no role/grant is.  Every action must still deny."""
        self.assertTrue(self.context.tenant_id)
        self.assertTrue(self.context.active_membership_id)
        for action, resource_type in CONTACT_POINT_ACTION_MATRIX.values():
            with self.subTest(action=action):
                self.assertEqual(
                    self._decision(action, resource_type).decision,
                    DecisionResult.DENY,
                )


class TestContactPointHttpAccessGateWiring(unittest.TestCase):
    """RED until every handler invokes the one central ContactPoint access gate."""

    @classmethod
    def setUpClass(cls) -> None:
        api_path = (
            ROOT
            / "services"
            / "platform-kernel"
            / "python"
            / "platform_kernel"
            / "api.py"
        )
        cls.tree = ast.parse(api_path.read_text(encoding="utf-8"))
        cls.functions = {
            node.name: node
            for node in cls.tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

    @staticmethod
    def _called_names(node: ast.AST) -> set[str]:
        names: set[str] = set()
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            if isinstance(child.func, ast.Name):
                names.add(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                names.add(child.func.attr)
        return names

    @staticmethod
    def _string_literals(node: ast.AST) -> set[str]:
        return {
            child.value
            for child in ast.walk(node)
            if isinstance(child, ast.Constant) and isinstance(child.value, str)
        }

    def test_every_http_handler_calls_the_central_access_gate(self):
        for handler_name in CONTACT_POINT_ACTION_MATRIX:
            with self.subTest(handler=handler_name):
                handler = self.functions[handler_name]
                self.assertIn(
                    "_require_contact_point_access",
                    self._called_names(handler),
                    f"{handler_name} trusts context/RLS without an explicit action decision",
                )

    def test_every_http_handler_binds_its_exact_action(self):
        for handler_name, (action, _resource_type) in CONTACT_POINT_ACTION_MATRIX.items():
            with self.subTest(handler=handler_name, action=action):
                self.assertIn(
                    action,
                    self._string_literals(self.functions[handler_name]),
                    f"{handler_name} does not bind the decision to {action}",
                )


if __name__ == "__main__":
    unittest.main()
