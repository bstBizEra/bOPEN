"""Contract evidence for the DEV-P0-01 multi-tenant readiness boundary."""

import copy
import json
import unittest
from pathlib import Path

from tools.validate_contracts import (
    validate_contracts,
    validate_multitenant_readiness_fixture,
    validate_schema_instance,
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
        cls.instances = cls.fixture["instances"]

    def resolve(self, scenario_id, ref_name, group_name):
        ref = self.scenarios[scenario_id]["instance_refs"][ref_name]
        return None if ref is None else self.instances[group_name][ref]

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
            for scenario_id, scenario in self.scenarios.items()
            if isinstance(self.resolve(scenario_id, "active_context", "active_contexts"), dict)
            and self.resolve(scenario_id, "active_context", "active_contexts")["tenant_id"]
            != self.resolve(scenario_id, "resource_ownership", "resource_ownership")["tenant_id"]
            and scenario["authorization_decision"]["decision"] == "DENY"
        }
        self.assertEqual(layers, {"api", "database"})

    def test_catalog_instances_conform_to_their_contracts(self):
        schema_by_group = {
            "memberships": "membership.schema.json",
            "active_contexts": "active-context.schema.json",
            "resource_ownership": "tenant-ownership.schema.json",
        }
        for group_name, schema_name in schema_by_group.items():
            schema = json.loads((CONTRACT_ROOT / "tenancy" / schema_name).read_text(encoding="utf-8"))
            for instance_id, instance in self.instances[group_name].items():
                with self.subTest(group=group_name, instance=instance_id):
                    self.assertEqual(validate_schema_instance(instance, schema, instance_id), [])

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

    def test_validator_rejects_present_membership_in_missing_membership_scenario(self):
        fixture = copy.deepcopy(self.fixture)
        fixture["scenarios"][1]["instance_refs"]["membership"] = "membership-alpha-owner"
        errors = validate_multitenant_readiness_fixture(
            fixture, Path("multitenant-dev-readiness.acceptance.json")
        )
        self.assertTrue(any("MISSING MEMBERSHIP SCENARIO" in error for error in errors))

    def test_validator_rejects_active_membership_in_suspended_scenario(self):
        fixture = copy.deepcopy(self.fixture)
        fixture["scenarios"][2]["instance_refs"]["membership"] = "membership-alpha-owner"
        errors = validate_multitenant_readiness_fixture(
            fixture, Path("multitenant-dev-readiness.acceptance.json")
        )
        self.assertTrue(any("SUSPENDED MEMBERSHIP SCENARIO" in error for error in errors))

    def test_validator_rejects_non_forged_context_in_forgery_scenario(self):
        fixture = copy.deepcopy(self.fixture)
        fixture["scenarios"][3]["context"]["tenant_id"] = "tenant-alpha"
        errors = validate_multitenant_readiness_fixture(
            fixture, Path("multitenant-dev-readiness.acceptance.json")
        )
        self.assertTrue(any("FORGED CONTEXT SCENARIO" in error for error in errors))

    def test_validator_rejects_matching_membership_in_mismatch_scenario(self):
        fixture = copy.deepcopy(self.fixture)
        fixture["scenarios"][4]["instance_refs"]["active_context"] = "context-alpha-owner"
        errors = validate_multitenant_readiness_fixture(
            fixture, Path("multitenant-dev-readiness.acceptance.json")
        )
        self.assertTrue(any("MEMBERSHIP TENANT MISMATCH SCENARIO" in error for error in errors))

    def test_validator_rejects_wrong_cross_tenant_reason_codes(self):
        for index in (5, 6):
            fixture = copy.deepcopy(self.fixture)
            fixture["scenarios"][index]["authorization_decision"]["reason_code"] = "WRONG_REASON"
            errors = validate_multitenant_readiness_fixture(
                fixture, Path("multitenant-dev-readiness.acceptance.json")
            )
            self.assertTrue(any("DENIAL REASON INVALID" in error for error in errors))

    def test_validator_rejects_inconsistent_positive_composition(self):
        mutations = (
            ("memberships", "membership-alpha-owner", "principal_id", "principal-other", "PRINCIPAL"),
            ("memberships", "membership-alpha-owner", "tenant_id", "tenant-other", "CONTEXT TENANT"),
            ("active_contexts", "context-alpha-owner", "status", "expired", "MUST BE ACTIVE"),
        )
        for group, instance_id, key, value, expected in mutations:
            fixture = copy.deepcopy(self.fixture)
            fixture["instances"][group][instance_id][key] = value
            errors = validate_multitenant_readiness_fixture(
                fixture, Path("multitenant-dev-readiness.acceptance.json")
            )
            with self.subTest(group=group, key=key):
                self.assertTrue(any(expected in error for error in errors))

    def test_validator_rejects_contradictory_positive_claims(self):
        fixture = copy.deepcopy(self.fixture)
        fixture["scenarios"][0]["context"]["tenant_id"] = "tenant-contradiction"
        fixture["scenarios"][0]["resource"]["resource_id"] = "resource-contradiction"
        errors = validate_multitenant_readiness_fixture(
            fixture, Path("multitenant-dev-readiness.acceptance.json")
        )
        self.assertTrue(any("CONTEXT CLAIMS MUST MATCH" in error for error in errors))
        self.assertTrue(any("RESOURCE CLAIMS MUST MATCH" in error for error in errors))

    def test_validator_rejects_invalid_active_context_time_window(self):
        fixture = copy.deepcopy(self.fixture)
        fixture["instances"]["active_contexts"]["context-alpha-owner"]["expires_at"] = (
            "2026-07-13T03:00:00+07:00"
        )
        errors = validate_multitenant_readiness_fixture(
            fixture, Path("multitenant-dev-readiness.acceptance.json")
        )
        self.assertTrue(any("TIME WINDOW INVALID" in error for error in errors))

    def test_validator_requires_timezone_aware_rfc3339_datetime(self):
        membership_schema = json.loads(
            (CONTRACT_ROOT / "tenancy/membership.schema.json").read_text(encoding="utf-8")
        )
        membership = copy.deepcopy(self.instances["memberships"]["membership-alpha-owner"])
        for invalid_value in ("2026-07-13", "2026-07-13T03:10:00", "not-a-date"):
            candidate = copy.deepcopy(membership)
            candidate["created_at"] = invalid_value
            errors = validate_schema_instance(candidate, membership_schema, "membership")
            with self.subTest(value=invalid_value):
                self.assertTrue(any("DATE-TIME INVALID" in error for error in errors))

    def test_validator_handles_non_string_context_dates_as_errors(self):
        for invalid_value in (123, None):
            fixture = copy.deepcopy(self.fixture)
            fixture["instances"]["active_contexts"]["context-alpha-owner"]["issued_at"] = invalid_value
            errors = validate_multitenant_readiness_fixture(
                fixture, Path("multitenant-dev-readiness.acceptance.json")
            )
            with self.subTest(value=invalid_value):
                self.assertTrue(any("TYPE INVALID" in error for error in errors))
                self.assertTrue(any("TIME WINDOW INVALID" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
