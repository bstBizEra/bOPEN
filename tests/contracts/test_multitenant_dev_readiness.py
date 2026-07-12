"""Contract evidence for the DEV-P0-01 multi-tenant readiness boundary."""

import copy
import json
import unittest
from pathlib import Path

from tools.validate_contracts import (
    validate_contracts,
    validate_multitenant_readiness_fixture,
    validate_tenancy_schema,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "docs/06-contracts"
FIXTURE = CONTRACT_ROOT / "acceptance/multitenant-dev-readiness.acceptance.json"


class MultiTenantDevReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.scenarios = {scenario["id"]: scenario for scenario in cls.fixture["scenarios"]}

    def test_repository_contracts_validate(self):
        self.assertEqual(validate_contracts(), [])

    def test_membership_is_not_role_permission_or_entitlement(self):
        membership = json.loads(
            (CONTRACT_ROOT / "tenancy/membership.schema.json").read_text(encoding="utf-8")
        )
        properties = set(membership["properties"])
        self.assertTrue({"membership_id", "principal_id", "tenant_id", "state"}.issubset(properties))
        self.assertTrue(
            properties.isdisjoint(
                {"role", "role_id", "permission", "permissions", "entitlement", "entitlements"}
            )
        )

    def test_active_context_accepts_only_trusted_validation_sources(self):
        context = json.loads(
            (CONTRACT_ROOT / "tenancy/active-context.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            set(context["properties"]["validation_source"]["enum"]),
            {"server_session", "trusted_service"},
        )

    def test_all_negative_scenarios_deny_by_default(self):
        for scenario_id, scenario in self.scenarios.items():
            if scenario_id == "MTD-001":
                continue
            with self.subTest(scenario=scenario_id):
                self.assertEqual(scenario["authorization_decision"]["decision"], "DENY")

    def test_cross_tenant_denial_exists_at_api_and_database_layers(self):
        layers = {
            scenario["enforcement_layer"]
            for scenario in self.scenarios.values()
            if scenario["context"]["tenant_id"] != scenario["resource"]["tenant_id"]
            and scenario["authorization_decision"]["decision"] == "DENY"
        }
        self.assertEqual(layers, {"api", "database"})

    def test_every_decision_is_correlated_with_its_audit_event(self):
        for scenario_id, scenario in self.scenarios.items():
            with self.subTest(scenario=scenario_id):
                decision = scenario["authorization_decision"]
                audit = scenario["audit_event"]
                self.assertEqual(audit["correlation_id"], decision["correlation_id"])
                self.assertEqual(audit["result"], decision["decision"])
                self.assertEqual(audit["reason_code"], decision["reason_code"])
                self.assertEqual(audit["policy_version"], decision["policy_version"])

    def test_validator_rejects_role_embedded_in_membership(self):
        membership = json.loads(
            (CONTRACT_ROOT / "tenancy/membership.schema.json").read_text(encoding="utf-8")
        )
        membership["properties"]["role_id"] = {"type": "string"}
        errors = validate_tenancy_schema(
            membership, Path("membership.schema.json"), "membership.schema.json"
        )
        self.assertTrue(any("MUST NOT EMBED" in error for error in errors))

    def test_validator_rejects_client_validated_active_context(self):
        context = json.loads(
            (CONTRACT_ROOT / "tenancy/active-context.schema.json").read_text(encoding="utf-8")
        )
        context["properties"]["validation_source"]["enum"].append("client_input")
        errors = validate_tenancy_schema(
            context, Path("active-context.schema.json"), "active-context.schema.json"
        )
        self.assertTrue(any("MUST BE SERVER VALIDATED" in error for error in errors))

    def test_validator_rejects_missing_database_denial(self):
        fixture = copy.deepcopy(self.fixture)
        fixture["scenarios"][-1]["authorization_decision"]["decision"] = "ALLOW"
        errors = validate_multitenant_readiness_fixture(
            fixture, Path("multitenant-dev-readiness.acceptance.json")
        )
        self.assertTrue(any("API AND DATABASE" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
