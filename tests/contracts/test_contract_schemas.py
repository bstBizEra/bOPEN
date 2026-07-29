import unittest
import json
from pathlib import Path

class TestContractSchemas(unittest.TestCase):
    """
    Automated contract test suite validating machine-readable JSON schemas in contracts/schemas/
    """

    def setUp(self):
        self.schemas_dir = Path(__file__).resolve().parents[2] / "contracts" / "schemas"

    def test_schema_files_exist_and_parse_valid_json(self):
        expected_schemas = [
            "tenant-context.json",
            "authorization-decision.json",
            "audit-event.json",
            "membership-transition.json"
        ]
        for filename in expected_schemas:
            filepath = self.schemas_dir / filename
            self.assertTrue(filepath.exists(), f"Missing schema file: {filename}")
            
            with open(filepath, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
                self.assertIn("$schema", schema_data, f"Missing $schema declaration in {filename}")
                self.assertEqual(schema_data["type"], "object", f"Schema root must be object in {filename}")

if __name__ == "__main__":
    unittest.main()
