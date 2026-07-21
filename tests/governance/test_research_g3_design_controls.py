"""Negative and deterministic tests for the non-executing G3 design controls."""
from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("g3_validator", ROOT / "tools/validate_research_g3_design.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ResearchG3DesignControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = VALIDATOR.load_contract(VALIDATOR.DEFAULT_CONTRACT)
        cls.schema = VALIDATOR.load_contract(VALIDATOR.DEFAULT_SCHEMA)

    def assert_invalid(self, changed: dict) -> None:
        self.assertTrue(VALIDATOR.validate_all(changed, self.schema))

    def test_canonical_design_passes_and_remains_non_executing(self) -> None:
        self.assertEqual([], VALIDATOR.validate_all(self.contract, self.schema))
        self.assertFalse(self.contract["gate_state"]["runtime_executed"])
        self.assertFalse(self.contract["gate_state"]["g3_pass"])
        self.assertFalse(self.contract["authority"]["production_authority"])

    def test_runtime_authority_claim_fails_closed(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["authority"]["runtime_execution_authorized"] = True
        self.assert_invalid(changed)

    def test_missing_case_fails_closed(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["case_families"][0]["stable_case_ids"].pop()
        changed["case_families"][0]["secure_oracles"].pop()
        self.assert_invalid(changed)

    def test_oracle_observation_merge_fails_closed(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["case_families"][0]["observed_upstream"]["executed"] = True
        changed["case_families"][0]["observed_upstream"]["decision"] = "ALLOW"
        self.assert_invalid(changed)

    def test_external_network_or_real_data_fails_closed(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["safety"]["external_network_prohibited"] = False
        changed["safety"]["synthetic_data_only"] = False
        self.assert_invalid(changed)

    def test_mutable_substitute_fails_closed(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["substitutes"][0]["immutable_runtime_required"] = False
        self.assert_invalid(changed)

    def test_self_acceptance_fails_closed(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["independent_reproduction"]["self_acceptance_prohibited"] = False
        self.assert_invalid(changed)

    def test_required_property_removal_fails_closed(self) -> None:
        changed = copy.deepcopy(self.contract)
        del changed["status"]
        self.assert_invalid(changed)

    def test_reason_decision_conflict_fails_closed(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["case_families"][0]["secure_oracles"][0]["decision"] = "DENY"
        self.assert_invalid(changed)

    def test_database_and_reproduction_weakening_fails_closed(self) -> None:
        for section, key in (("database_design", "fresh_database_per_run"), ("database_design", "synthetic_seed_only"), ("independent_reproduction", "same_source_and_build")):
            changed = copy.deepcopy(self.contract)
            changed[section][key] = False
            self.assert_invalid(changed)

    def test_evidence_hash_requirement_weakening_fails_closed(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["evidence_artifacts"][0]["sha256_required"] = False
        self.assert_invalid(changed)

    def test_r1_hash_and_reference_tampering_fail_closed(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["source_binding"]["r1_contract_sha256"] = "0" * 64
        self.assert_invalid(changed)
        changed = copy.deepcopy(self.contract)
        changed["research_references"][0]["path"] = "docs/does-not-exist.md"
        self.assert_invalid(changed)

    def test_e4_demoted_to_e3_fails_closed(self) -> None:
        changed = copy.deepcopy(self.contract)
        for family in changed["case_families"]:
            family["evidence_target"] = "E3"
        self.assert_invalid(changed)

    def test_schema_metadata_tampering_fails_closed(self) -> None:
        changed_schema = copy.deepcopy(self.schema)
        changed_schema["properties"]["contract_id"]["const"] = "BOGUS"
        self.assertTrue(VALIDATOR.validate_schema(changed_schema))

    def test_report_integrity_rejects_hand_edit(self) -> None:
        original = VALIDATOR.DEFAULT_REPORT
        with tempfile.TemporaryDirectory() as temp:
            VALIDATOR.DEFAULT_REPORT = Path(temp) / "report.md"
            try:
                VALIDATOR.DEFAULT_REPORT.write_text(VALIDATOR.render_report(self.contract), encoding="utf-8")
                self.assertEqual([], VALIDATOR.validate_report_integrity(self.contract))
                VALIDATOR.DEFAULT_REPORT.write_text("runtime=true\nG3=PASS\n", encoding="utf-8")
                self.assertTrue(VALIDATOR.validate_report_integrity(self.contract))
            finally:
                VALIDATOR.DEFAULT_REPORT = original

    def test_inventory_integrity_rejects_stale_file(self) -> None:
        original = VALIDATOR.ARTIFACT_INVENTORY
        with tempfile.TemporaryDirectory() as temp:
            VALIDATOR.ARTIFACT_INVENTORY = Path(temp) / "inventory.json"
            try:
                VALIDATOR.ARTIFACT_INVENTORY.write_text(json.dumps({"generated_on": "stale", "files": []}), encoding="utf-8")
                self.assertTrue(VALIDATOR.validate_inventory_integrity(self.contract))
            finally:
                VALIDATOR.ARTIFACT_INVENTORY = original


if __name__ == "__main__":
    unittest.main()
