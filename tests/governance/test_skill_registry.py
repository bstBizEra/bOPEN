"""Contract tests for repo-local cross-harness skill discovery."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "validate_skill_registry.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_skill_registry", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SkillRegistryTests(unittest.TestCase):
    def test_registry_matches_installed_skill_tree(self) -> None:
        validator = load_validator()
        self.assertEqual([], validator.validate())

    def test_all_entries_are_inactive_candidates(self) -> None:
        registry = json.loads((ROOT / "docs/registers/skill-registry.json").read_text(encoding="utf-8"))
        self.assertEqual(34, len(registry["skills"]))
        self.assertTrue(all(item["state"] == "candidate" for item in registry["skills"]))
        self.assertTrue(all(item["activation"] == "inactive" for item in registry["skills"]))
        self.assertTrue(all(item["invocation"] != "eligible" for item in registry["skills"]))

    def test_transactional_and_gate_skills_are_explicit_only(self) -> None:
        registry = json.loads((ROOT / "docs/registers/skill-registry.json").read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in registry["skills"]}
        for skill_id in load_validator().EXPLICIT_ONLY:
            self.assertEqual("explicit_only", by_id[skill_id]["invocation"])

    def test_fabricated_package_validation_is_rejected(self) -> None:
        validator = load_validator()
        registry = json.loads((ROOT / "docs/registers/skill-registry.json").read_text(encoding="utf-8"))
        registry["skills"][0]["package_validation"] = "fabricated-pass"
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "registry.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            with mock.patch.object(validator, "REGISTRY_PATH", path):
                self.assertTrue(any("package_validation invalid" in item for item in validator.validate()))

    def test_activation_without_independent_decision_is_rejected(self) -> None:
        validator = load_validator()
        registry = json.loads((ROOT / "docs/registers/skill-registry.json").read_text(encoding="utf-8"))
        entry = registry["skills"][0]
        entry.update({"state": "approved", "activation": "active", "invocation": "eligible",
                      "source_revision": "a" * 40, "activation_decision": None})
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "registry.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            with mock.patch.object(validator, "REGISTRY_PATH", path):
                self.assertTrue(any("activation decision" in item for item in validator.validate()))

    def test_well_shaped_but_unverifiable_activation_is_rejected(self) -> None:
        validator = load_validator()
        registry = json.loads((ROOT / "docs/registers/skill-registry.json").read_text(encoding="utf-8"))
        entry = registry["skills"][0]
        entry.update({"state": "approved", "activation": "active", "invocation": "eligible",
                      "source_revision": "a" * 40,
                      "activation_decision": {"id": "MISSING-DECISION", "status": "approved",
                                              "maker": "maker", "checker": "checker",
                                              "decision_sha256": "b" * 64}})
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "registry.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            with mock.patch.object(validator, "REGISTRY_PATH", path):
                errors = validator.validate()
        self.assertTrue(any("cannot activate or promote" in item for item in errors))

    def test_inactive_workflow_resolution_fails_closed(self) -> None:
        errors = load_validator().resolve_workflow("start-governed-work")
        self.assertTrue(any("not active and approved" in item for item in errors))

    def test_cross_harness_adapters_are_present(self) -> None:
        self.assertEqual([], load_validator().adapter_errors())


if __name__ == "__main__":
    unittest.main()
