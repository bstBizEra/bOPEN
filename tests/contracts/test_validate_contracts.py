import tempfile
import unittest
from pathlib import Path

from tools.validate_contracts import validate_contracts


class ContractValidationTests(unittest.TestCase):
    def test_repository_contracts_validate(self):
        self.assertEqual(validate_contracts(), [])

    def test_draft_json_schema_requires_draft_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_dir = root / "docs" / "06-contracts" / "policies"
            contract_dir.mkdir(parents=True)
            (contract_dir / "example.schema.json").write_text(
                """{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "bopen://schemas/example/0.1.0-draft",
  "title": "Example",
  "type": "object"
}
""",
                encoding="utf-8",
            )

            errors = validate_contracts(root)

        self.assertIn(
            "DRAFT CONTRACT STATUS MISSING: docs\\06-contracts\\policies\\example.schema.json".replace(
                "\\", "/"
            ),
            [error.replace("\\", "/") for error in errors],
        )

    def test_draft_yaml_contract_requires_draft_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_dir = root / "docs" / "06-contracts" / "modules"
            contract_dir.mkdir(parents=True)
            (contract_dir / "example.yaml").write_text(
                "id: bopen.example\nversion: 0.1.0-draft\n",
                encoding="utf-8",
            )

            errors = validate_contracts(root)

        self.assertIn(
            "DRAFT YAML CONTRACT STATUS MISSING: docs\\06-contracts\\modules\\example.yaml".replace(
                "\\", "/"
            ),
            [error.replace("\\", "/") for error in errors],
        )


if __name__ == "__main__":
    unittest.main()
