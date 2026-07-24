"""Negative fixtures for the SKEL-P0-01 skeleton validator (sole-maker authored).

Each fixture builds a minimal skeleton in a temporary directory and asserts the
validator passes on a clean skeleton and fails closed on: business logic in a kernel
zone (Python AST and TypeScript runtime), draft->active contract promotion, and an
implementation hidden in a nested tier subdirectory. It also asserts __pycache__ does
not cause a false positive.
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
        _write(root / zone / "AGENTS.md", f"# AGENTS.md - {zone}\n")
    _write(root / "packages" / "kernel-contracts" / "src" / "index.d.ts", "export type Placeholder = never;\n")
    _write(root / "services" / "__init__.py", "")  # an empty __init__ in a kernel zone must be allowed
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


def _errors(root: Path) -> list[str]:
    return validate_skeleton.validate_skeleton(root).errors


class SkeletonValidatorNegativeFixtures(unittest.TestCase):
    def test_valid_skeleton_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_valid_fixture(root)
            self.assertEqual(_errors(root), [], "expected a clean skeleton to pass")

    def test_python_function_body_in_kernel_zone_is_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_valid_fixture(root)
            _write(root / "packages" / "kernel-contracts" / "src" / "logic.py",
                   "def compute_tax(x):\n    return x * 0.2\n")
            self.assertTrue(any("business-logic" in e or "type-only" in e for e in _errors(root)))

    def test_typescript_runtime_export_is_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_valid_fixture(root)
            _write(root / "services" / "svc.ts", "export function handle(x: number) { return x + 1 }\n")
            self.assertTrue(any("business-logic" in e for e in _errors(root)))

    def test_one_line_arrow_without_parens_is_denied(self):
        """Regression for the reported bypass: a paren-less one-line arrow
        (export const inc = n => n + 1) must be denied. A content heuristic missed it;
        a non-.d.ts script file in a kernel zone is now runtime regardless of content."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_valid_fixture(root)
            _write(root / "services" / "svc.ts", "export const inc = n => n + 1\n")
            self.assertTrue(
                any("business-logic" in e and "svc.ts" in e for e in _errors(root)),
                "a paren-less one-line arrow must be denied",
            )

    def test_non_dts_typescript_is_denied_even_if_type_like(self):
        """Fail-closed: type declarations belong in .d.ts; a plain .ts in a kernel zone
        is treated as runtime so no runtime content can hide behind a type-looking file."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_valid_fixture(root)
            _write(root / "packages" / "kernel-contracts" / "src" / "extra.ts", "export type Extra = string\n")
            self.assertTrue(any("type-only" in e or "business-logic" in e for e in _errors(root)))

    def test_type_only_dts_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_valid_fixture(root)
            _write(root / "sdk" / "types.d.ts", "export interface Foo { id: string }\n")
            self.assertEqual(_errors(root), [])

    def test_draft_to_active_promotion_is_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_valid_fixture(root)
            shell_path = root / "contracts" / "platform" / "tenant.draft.schema.json"
            data = json.loads(shell_path.read_text(encoding="utf-8"))
            data["status"] = "active"
            data["x-bopen-control"]["status"] = "active"
            shell_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
            self.assertTrue(any("status must be draft" in e for e in _errors(root)))

    def test_nested_implementation_file_in_tier_is_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_valid_fixture(root)
            _write(root / "tests" / "authorization" / "policies" / "test_policy.py",
                   "def test_policy():\n    assert True\n")
            self.assertTrue(
                any("authorization" in e and "fail-closed" in e for e in _errors(root)),
                "a nested implementation must be denied fail-closed",
            )

    def test_pycache_in_tier_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_valid_fixture(root)
            _write(root / "tests" / "unit" / "__pycache__" / "test_guard.cpython-313.pyc", "bytecode\n")
            self.assertFalse(any("unit" in e and "fail-closed" in e for e in _errors(root)))


if __name__ == "__main__":
    unittest.main()
