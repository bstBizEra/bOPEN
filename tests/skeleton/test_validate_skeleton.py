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

    def test_nested_implementation_file_in_tier_is_denied(self):
        """Fail-closed guard must catch an implementation hidden in a tier SUBDIRECTORY,
        not only top-level files (I04: the non-recursive iterdir scan was a bypass)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_valid_fixture(root)
            # implementation nested one level deep, manifest deliberately left 'inactive'
            _write(root / "tests" / "authorization" / "policies" / "test_policy.py",
                   "def test_policy():\n    assert True\n")
            report = validate_skeleton.validate_skeleton(root)
            self.assertTrue(
                any("authorization" in e and "fail-closed" in e for e in report.errors),
                f"nested implementation must be denied fail-closed; errors: {report.errors}",
            )

    def test_pycache_in_tier_is_ignored(self):
        """A __pycache__ artifact must NOT trip the fail-closed guard (avoids false positives)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_valid_fixture(root)
            _write(root / "tests" / "unit" / "__pycache__" / "test_guard.cpython-313.pyc", "bytecode\n")
            report = validate_skeleton.validate_skeleton(root)
            self.assertFalse(
                any("unit" in e and "fail-closed" in e for e in report.errors),
                f"__pycache__ must be ignored; errors: {report.errors}",
            )

    def test_python_function_body_in_kernel_zone_is_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_valid_fixture(root)
            injected = root / "services" / "billing" / "logic.py"
            _write(injected, "def compute_tax(value):\n    return value * 0.2\n")
            report = validate_skeleton.validate_skeleton(root)
            relative = injected.relative_to(root).as_posix()
            self.assertTrue(
                any(relative in error for error in report.errors),
                f"Python business logic must be denied; errors: {report.errors}",
            )

    def test_empty_and_metadata_only_init_files_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_valid_fixture(root)
            _write(root / "apps" / "empty_package" / "__init__.py", "")
            _write(
                root / "services" / "metadata_package" / "__init__.py",
                '"""Preparation-only package."""\nfrom __future__ import annotations\n',
            )
            report = validate_skeleton.validate_skeleton(root)
            self.assertEqual(
                report.errors,
                [],
                f"empty or metadata-only __init__.py must be allowed; errors: {report.errors}",
            )

    def test_d_ts_type_only_file_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_valid_fixture(root)
            _write(
                root / "sdk" / "types" / "index.d.ts",
                "export interface Placeholder { readonly id: string }\n",
            )
            report = validate_skeleton.validate_skeleton(root)
            self.assertEqual(
                report.errors,
                [],
                f".d.ts type-only source must be allowed; errors: {report.errors}",
            )

    def test_typescript_runtime_export_is_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_valid_fixture(root)
            injected = root / "packages" / "kernel-contracts" / "src" / "logic.ts"
            _write(injected, "export function computeTax(x){ return x * 0.2 }\n")
            report = validate_skeleton.validate_skeleton(root)
            relative = injected.relative_to(root).as_posix()
            self.assertTrue(
                any(relative in error for error in report.errors),
                f"TypeScript runtime export must be denied; errors: {report.errors}",
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
