"""Governance checks for BOPEN-RES-001 Research Sprint R0 controls."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "docs/resources/open-source-research/BOPEN-RES-001"


class ResearchR0ControlTests(unittest.TestCase):
    def test_pin_contract_contains_expected_integrity_fields(self):
        pin = json.loads((ROOT / "research/sources/boxyhq-upstream-pin.json").read_text())
        self.assertEqual(pin["source_id"], "SRC-BOX-001")
        self.assertEqual(pin["commit"], "abc9b686823cbfb4973c79bc36fea37a3244be6c")
        self.assertRegex(pin["license_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(pin["lock_sha256"], r"^[0-9a-f]{64}$")
        self.assertFalse(pin["archived_observed"])

    def test_clone_harness_fails_closed_on_identity_and_integrity(self):
        script = (RESEARCH / "scripts/bootstrap-boxyhq-study.ps1").read_text()
        for marker in (
            "GIT_TERMINAL_PROMPT",
            "credential.helper=",
            "repository_url",
            "license_sha256",
            "lock_sha256",
            "Physical upstream clones must remain outside",
        ):
            self.assertIn(marker, script)

    def test_baseline_runner_records_declared_exit_matrix(self):
        script = (RESEARCH / "scripts/run-boxyhq-baseline.ps1").read_text()
        self.assertIn('[string]$NpmVersion = "10.9.2"', script)
        for command in (
            '"npm-ci"',
            '"prisma-generate"',
            '"check-format"',
            '"check-lint"',
            '"check-types"',
            '"unit-tests"',
            '"build-ci"',
        ):
            self.assertIn(command, script)
        self.assertIn('"check-format" "npm.cmd" @("run", "check-format") 1', script)

    def test_decision_keeps_upstream_source_outside_worktree(self):
        decision = (ROOT / "docs/decisions/DEC-0009.md").read_text()
        self.assertIn("**Status:** Approved", decision)
        self.assertIn("external ephemeral workspace", decision)
        self.assertIn("does not authorize production implementation", decision)

    def test_r0_receipt_keeps_later_gates_closed(self):
        receipt = (ROOT / "docs/evidence/EVD-RES-002-r0-control-establishment.md").read_text()
        self.assertIn("G0: PASS WITH CONDITIONS", receipt)
        self.assertIn("G1: PASS WITH CONDITIONS", receipt)
        self.assertIn("G2: PASS WITH CONDITIONS", receipt)
        self.assertIn("G3-G7 remain open", receipt)


if __name__ == "__main__":
    unittest.main()
