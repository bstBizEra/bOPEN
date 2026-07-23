"""Negative fixtures for the SKEL-P0-01 skeleton validator.

Verifies the validator (a) passes on a minimal well-formed skeleton and
(b) fails closed on business-logic injection and on draft->active promotion.
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location("validate_skeleton", ROOT / "tools" / "validate_skeleton.py")
validate_skeleton = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validate_skeleton)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _make_valid_fixture(root: Path) -> None:
    for zone in ("apps", "services", "packages", "contracts", "sdk", "infrastructure", "tools", "tests"):
        _write(root / zone / "AGENTS.md", f"# AGENTS.md — {zone}\n")
    _write(root / "packages" / "kernel-contracts" / "src" / "index.d.ts",
           "export type Placeholder = never;\n")
    shell = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "bopen://schemas/platform/tenant/0.1.0-draft",
        "title": "Tenant Contract Shell (Draft)",
        "status": "draft",
        "x-bopen-control": {"artifactId": "X", "version": "0.1.0", "status": "draft", "owner": "Engineering Authority"},
        "x-bopen-stability": {"stableDependency": False},
        "x-bopen-traceability": {"normativeArtifact": "BOPEN-TENANT-001", "requirementIds": ["REQ-TEN-001"]},
        "type": "object",
    }
    _write(root / "contracts" / "platform" / "tenant.draft.schema.json", json.dumps(shell, indent=2) + "\n")
    for tier in ("unit", "contract", "integration", "tenant_isolation", "authorization"):
        _write(root / "tests" / tier / "test_guard.py", "# guard\n")
        _write(root / "tests" / tier / "negative-tests.manifest.json",
               json.dumps({"tier": tier, "status": "inactive", "requiredNegativeTests": []}) + "\n")


class SkeletonValidatorNegativeFixtures(unittest.TestCase):
    def test_valid_skeleton_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_valid_fixture(root)
            report = validate_skeleton.validate_skeleton(root)
            self.assertEqual(report.errors, [], f"expected clean skeleton, got: {report.errors}")

    def test_business_logic_injection_is_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_valid_fixture(root)
            _write(root / "packages" / "kernel-contracts" / "src" / "logic.ts",
                   "export function computeTax(x){ return x * 0.2 }\n")
            report = validate_skeleton.validate_skeleton(root)
            self.assertTrue(
                any("business-logic" in e or "type-only" in e for e in report.errors),
                f"business logic must be denied; errors: {report.errors}",
            )

    def test_draft_to_active_promotion_is_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_valid_fixture(root)
            shell_path = root / "contracts" / "platform" / "tenant.draft.schema.json"
            data = json.loads(shell_path.read_text(encoding="utf-8"))
            data["status"] = "active"
            data["x-bopen-control"]["status"] = "active"
            shell_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
            report = validate_skeleton.validate_skeleton(root)
            self.assertTrue(
                any("status must be draft" in e for e in report.errors),
                f"draft->active promotion must be denied; errors: {report.errors}",
            )


if __name__ == "__main__":
    unittest.main()
