"""Governance checks for the BOPEN-RES-001 R1 static trace."""

import copy
import json
import unittest
from pathlib import Path

from tools.validate_research_r1 import CONTRACT, PACKAGE_IDS, validate_contract


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "docs/resources/open-source-research/BOPEN-RES-001/scripts"


class ResearchR1ControlTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_trace_contract_covers_authorized_r1_packages(self):
        self.assertEqual(validate_contract(self.contract), [])
        self.assertEqual(
            {item["id"] for item in self.contract["work_packages"]}, PACKAGE_IDS
        )

    def test_trace_contract_keeps_runtime_gate_open(self):
        runtime = self.contract["runtime_evidence"]
        self.assertEqual(runtime["gate"], "G3")
        self.assertEqual(runtime["status"], "open")
        self.assertFalse(runtime["executed"])
        gap = next(item for item in self.contract["evidence"] if item["id"] == "R1-E024")
        self.assertEqual(gap["evidence_kind"], "gap-anchor")
        self.assertIn("replay", gap["cases"])
        self.assertIn("concurrency", gap["cases"])

    def test_missing_required_case_fails_closed(self):
        mutated = copy.deepcopy(self.contract)
        for item in mutated["evidence"]:
            item["cases"] = [case for case in item["cases"] if case != "concurrency"]
        errors = validate_contract(mutated)
        self.assertTrue(any("RES-P0-07 missing cases: concurrency" in error for error in errors))

    def test_missing_required_layer_fails_closed(self):
        mutated = copy.deepcopy(self.contract)
        mutated["evidence"] = [
            item
            for item in mutated["evidence"]
            if not ("RES-P0-06" in item["packages"] and item["layer"] == "integration")
        ]
        errors = validate_contract(mutated)
        self.assertTrue(any("RES-P0-06 missing layers: integration" in error for error in errors))

    def test_runner_clears_ambient_secrets_and_only_lists_tests(self):
        script = (SCRIPTS / "run-boxyhq-r1-trace.ps1").read_text(encoding="utf-8")
        self.assertIn("Remove-Item \"Env:$Name\"", script)
        self.assertIn("$Playwright test --list", script)
        self.assertIn("runner_sha256", script)
        self.assertIn("runtime_executed = $false", script)
        self.assertNotIn("$Playwright test -x", script)

    def test_r1_evidence_keeps_g3_and_invitation_acceptance_open(self):
        evidence = (ROOT / "docs/evidence/EVD-RES-003-r1-lifecycle-trace.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("RES-P0-04 | Complete at E2", evidence)
        self.assertIn("RES-P0-07 | Trace complete; acceptance not satisfied", evidence)
        self.assertIn("**G3 remains OPEN.**", evidence)
        self.assertNotIn("G3: PASS", evidence)


if __name__ == "__main__":
    unittest.main()
