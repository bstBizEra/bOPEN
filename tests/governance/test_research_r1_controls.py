"""Governance checks for the BOPEN-RES-001 R1 static trace."""

import copy
import json
import subprocess
import sys
import unittest
import uuid
from pathlib import Path

from tools.validate_research_r1 import (
    CONTRACT,
    PACKAGE_IDS,
    safe_source_path,
    validate_contract,
)


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
        gap = next(item for item in self.contract["evidence"] if item["id"] == "R1-E056")
        self.assertEqual(gap["evidence_kind"], "gap-anchor")
        self.assertIn("replay", gap["case_markers"])
        self.assertIn("concurrency", gap["case_markers"])

    def test_missing_required_case_fails_closed(self):
        mutated = copy.deepcopy(self.contract)
        for item in mutated["evidence"]:
            item["case_markers"].pop("concurrency", None)
        errors = validate_contract(mutated)
        self.assertTrue(
            any("RES-P0-07 concurrency missing layers: gap" in error for error in errors)
        )

    def test_missing_required_layer_fails_closed(self):
        mutated = copy.deepcopy(self.contract)
        mutated["evidence"] = [
            item
            for item in mutated["evidence"]
            if not ("RES-P0-06" in item["packages"] and item["layer"] == "integration")
        ]
        errors = validate_contract(mutated)
        self.assertTrue(
            any("RES-P0-06 team-update missing layers: integration" in error for error in errors)
        )

    def test_unknown_package_attribution_fails_closed(self):
        mutated = copy.deepcopy(self.contract)
        mutated["evidence"][0]["packages"].append("RES-P0-99")
        self.assertTrue(
            any("invalid package attribution" in error for error in validate_contract(mutated))
        )

    def test_runner_validates_paths_before_writing_and_executes_no_upstream_code(self):
        script = (SCRIPTS / "run-boxyhq-r1-trace.ps1").read_text(encoding="utf-8")
        self.assertLess(script.index("validate_research_r0.py"), script.index("New-Item"))
        self.assertIn("test-declaration-receipt.json", script)
        self.assertNotIn("node_modules", script)
        self.assertNotIn("playwright", script.lower())

    def test_rejected_repository_evidence_path_is_not_created(self):
        probe = ROOT / f".r1-invalid-{uuid.uuid4().hex}"
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools/validate_research_r1.py"),
                "--target",
                str(ROOT),
                "--evidence-root",
                str(probe),
                "--approved-root",
                r"C:\laragon\www\bopen-research",
                "--operator-id",
                "NEGATIVE",
                "--receipt",
                str(probe / "trace.json"),
                "--test-receipt",
                str(probe / "tests.json"),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(probe.exists())

    def test_source_path_escape_is_rejected(self):
        self.assertIsNone(safe_source_path(ROOT, "../outside.txt"))

    def test_team_case_attribution_uses_case_specific_paths(self):
        evidence = {item["id"]: item for item in self.contract["evidence"]}
        self.assertEqual(evidence["R1-E036"]["path"], "pages/api/teams/[slug]/index.ts")
        self.assertEqual(
            evidence["R1-E038"]["case_markers"]["team-create"],
            ["Create a new team"],
        )

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
