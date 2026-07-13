"""Governance checks for BOPEN-RES-001 Research Sprint R0 controls."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.validate_research_r0 import validate_paths, validate_provenance


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
        self.assertIn(
            '"check-format" "npx.cmd" @("--yes", "npm@$NpmVersion", "run", "check-format") 1',
            script,
        )

    def test_path_validator_rejects_worktree_and_root_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            approved = base / "approved"
            repository = base / "repository"
            approved.mkdir()
            repository.mkdir()
            self.assertEqual(
                validate_paths(
                    approved / "run/upstream",
                    approved / "run/evidence",
                    approved,
                    repository,
                ),
                [],
            )
            escaped = validate_paths(base / "outside", approved / "evidence", approved, repository)
            self.assertTrue(any("escapes" in error for error in escaped))
            entered = validate_paths(repository / "upstream", approved / "evidence", approved, repository)
            self.assertTrue(any("worktree" in error for error in entered))

    def test_provenance_validator_rejects_every_identity_mutation(self):
        pin = json.loads((ROOT / "research/sources/boxyhq-upstream-pin.json").read_text())
        record = {
            "source_id": pin["source_id"],
            "repository": pin["repository_url"],
            "pinned_commit": pin["commit"],
            "actual_commit": pin["commit"],
            "license_sha256": pin["license_sha256"],
            "lockfile": pin["lockfile"],
            "lock_sha256": pin["lock_sha256"],
            "credential_prompting": "disabled",
        }
        self.assertEqual(validate_provenance(record, pin), [])
        for key in record:
            mutated = dict(record)
            mutated[key] = "wrong"
            with self.subTest(key=key):
                self.assertTrue(validate_provenance(mutated, pin))

    def test_baseline_runner_enforces_boundary_pin_and_pinned_npm(self):
        script = (RESEARCH / "scripts/run-boxyhq-baseline.ps1").read_text()
        for marker in (
            "validate_research_r0.py",
            "verify-upstream-pin.ps1",
            "NPM_CONFIG_USERCONFIG",
            "registry.npmjs.org",
            "node_modules/prisma/build/index.js",
        ):
            self.assertIn(marker, script)
        self.assertNotIn('"check-lint" "npm.cmd"', script)

    def test_external_secret_scan_writes_normalized_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "evidence.txt").write_text("synthetic evidence", encoding="utf-8")
            receipt = root / "secret-scan-receipt.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools/check_secrets.py"),
                    "--root",
                    str(root),
                    "--receipt",
                    str(receipt),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)
            data = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "PASS")
            self.assertEqual(data["finding_count"], 0)

    def test_evidence_finalizer_is_tracked_and_verifies_file_set(self):
        script = (RESEARCH / "scripts/finalize-research-evidence.ps1").read_text()
        self.assertIn("secret-scan-receipt.json", script)
        self.assertIn("evidence-manifest.json", script)
        self.assertIn("Compare-Object", script)

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
