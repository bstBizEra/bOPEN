import json
import unittest
from pathlib import Path


class TestContractSchemas(unittest.TestCase):
    """Validate the repository's machine-readable JSON schema contracts."""

    PHASE3_SCHEMAS = {
        "module-manifest.schema.json",
        "capability-registration.schema.json",
        "entitlement-decision.schema.json",
        "usage-metered-event.schema.json",
        "quota-reservation.schema.json",
        "rate-limit-decision.schema.json",
        "entitlement-reason-codes.json",
    }

    def setUp(self):
        self.schemas_dir = Path(__file__).resolve().parents[2] / "contracts" / "schemas"

    def load_schema(self, filename):
        filepath = self.schemas_dir / filename
        self.assertTrue(filepath.exists(), f"Missing schema file: {filename}")
        with filepath.open("r", encoding="utf-8") as schema_file:
            return json.load(schema_file)

    def test_schema_files_exist_and_parse_valid_json(self):
        expected_schemas = {
            "tenant-context.json",
            "authorization-decision.json",
            "audit-event.json",
            "membership-transition.json",
            *self.PHASE3_SCHEMAS,
        }
        for filename in expected_schemas:
            schema_data = self.load_schema(filename)
            self.assertIn("$schema", schema_data, f"Missing $schema declaration in {filename}")
            self.assertIn("type", schema_data, f"Missing root type in {filename}")

    def test_phase3_schema_identifiers_are_unique_and_versioned(self):
        schema_ids = set()
        for filename in self.PHASE3_SCHEMAS:
            schema = self.load_schema(filename)
            self.assertEqual(schema.get("version"), "1.0.0")
            schema_id = schema.get("$id")
            self.assertTrue(schema_id, f"Missing $id in {filename}")
            self.assertNotIn(schema_id, schema_ids, f"Duplicate $id: {schema_id}")
            schema_ids.add(schema_id)

    def test_module_dependencies_are_version_constrained(self):
        schema = self.load_schema("module-manifest.schema.json")
        dependencies = schema["properties"]["dependencies"]
        self.assertTrue(dependencies["uniqueItems"])
        self.assertEqual(
            dependencies["items"]["required"],
            ["module_id", "version_constraint"],
        )

    def test_global_capability_lifecycle_includes_available(self):
        schema = self.load_schema("capability-registration.schema.json")
        states = schema["properties"]["status"]["enum"]
        self.assertIn("available", states)

    def test_unlimited_quota_is_forbidden_and_reason_codes_are_closed(self):
        decision = self.load_schema("entitlement-decision.schema.json")
        reason_codes = self.load_schema("entitlement-reason-codes.json")
        self.assertNotIn("unlimited", decision["properties"]["quota_window"]["enum"])
        self.assertEqual(
            set(decision["properties"]["reason_code"]["enum"]),
            set(reason_codes["enum"]),
        )
        self.assertEqual(
            set(reason_codes["enum"]),
            set(reason_codes["x-bopen-http-status-map"]),
        )

    def test_usage_and_reservation_contracts_require_idempotency(self):
        usage = self.load_schema("usage-metered-event.schema.json")
        reservation = self.load_schema("quota-reservation.schema.json")
        self.assertIn("idempotency_key", usage["required"])
        self.assertIn("idempotency_key", reservation["required"])
        self.assertIn("context_id", usage["required"])

    def test_rate_limit_decision_is_capability_and_evidence_bound(self):
        schema = self.load_schema("rate-limit-decision.schema.json")
        required = set(schema["required"])
        self.assertTrue(
            {"capability_id", "correlation_id", "reason_code"}.issubset(required)
        )
        self.assertEqual(schema["properties"]["status_code"]["enum"], [200, 429])


if __name__ == "__main__":
    unittest.main()
