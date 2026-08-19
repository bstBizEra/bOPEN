"""Subprocess tests for scripts/classify_authority_delta.py.

Invoked as CI invokes it — stdin numstat plus environment. Each test asserts
both the exit code and the verdict name, because the exit code alone cannot
distinguish `AGENT_BALLOT_REQUIRED` from `CONSTITUTIONAL_REQUIRED`.

Ported from the SecB Project Framework under BOPEN-WP-GOV-AUTONOMY-001;
unittest style so `unittest discover` can run it without pytest. Change-class
identifiers follow AGENTS.md section 30.4: AD0-AD5, tiers AT0-AT4.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "classify_authority_delta.py"
REAL_ENVELOPE = ROOT / "config" / "delegation_envelope.json"

EXIT_OK = 0
EXIT_ESCALATE = 2
EXIT_REJECTED = 3


def run(numstat: str, envelope: Path | None = None, diff_text: str | None = None):
    env = {k: v for k, v in os.environ.items() if k not in ("ENVELOPE", "DIFF_TEXT")}
    env["ENVELOPE"] = str(envelope or REAL_ENVELOPE)
    if diff_text is not None:
        env["DIFF_TEXT"] = diff_text
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=numstat,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        timeout=30,
    )


def verdict_of(result) -> str:
    text = result.stdout + result.stderr
    line = next(ln for ln in text.splitlines() if ln.startswith("VERDICT:"))
    return line.removeprefix("VERDICT:").strip().split("—")[0].strip()


class EnvelopeFixture(unittest.TestCase):
    """Base class providing a customised-envelope builder."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def custom_envelope(self, **overrides) -> Path:
        data = json.loads(REAL_ENVELOPE.read_text(encoding="utf-8"))
        for dotted, value in overrides.items():
            node = data
            *parents, leaf = dotted.split(".")
            for key in parents:
                node = node[key]
            node[leaf] = value
        path = Path(self._tmp.name) / "envelope.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path


class Ad0AutoApprovedTest(unittest.TestCase):
    def test_docs_only_auto_approved(self):
        result = run("12\t3\tdocs/work-packages/BOPEN-WP-GOV-FUTURE-999.md\n")
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertEqual(verdict_of(result), "AUTO_APPROVED")

    def test_mixed_docs_tests_code_auto_approved(self):
        numstat = (
            "20\t0\tdocs/evidence/phase-4/RECORD.md\n"
            "30\t5\ttests/unit/test_thing.py\n"
            "40\t1\tpackages/kernel/helper.py\n"
        )
        result = run(numstat)
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertIn("3 path(s)", result.stdout)

    def test_binary_file_counts_no_lines(self):
        result = run("-\t-\tdocs/diagram.png\n")
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)


class Ad4ConstitutionalTest(unittest.TestCase):
    def test_root_authority_surfaces_are_constitutional(self):
        for path in (
            "docs/00-governance/GL_ROOT_CONSTITUTION.md",
            "config/delegation_envelope.json",
            "scripts/classify_authority_delta.py",
            "scripts/check_dual_policy.py",
            ".github/workflows/governance-gates.yml",
            "AGENTS.md",
            "GOVERNANCE.md",
            "CODEOWNERS",
        ):
            with self.subTest(path=path):
                result = run(f"2\t1\t{path}\n")
                self.assertEqual(result.returncode, EXIT_ESCALATE)
                self.assertEqual(verdict_of(result), "CONSTITUTIONAL_REQUIRED")

    def test_ad4_wins_over_ad0_when_mixed(self):
        result = run("5\t0\tdocs/plan.md\n1\t1\tAGENTS.md\n")
        self.assertEqual(verdict_of(result), "CONSTITUTIONAL_REQUIRED")

    def test_path_outside_envelope_is_constitutional(self):
        result = run("1\t0\tops/terraform/main.tf\n")
        self.assertEqual(result.returncode, EXIT_ESCALATE)
        self.assertEqual(verdict_of(result), "CONSTITUTIONAL_REQUIRED")

    def test_absolute_ceiling_is_not_waivable(self):
        result = run("1500\t600\tdocs/enormous.md\n")  # 2100 > 2000
        self.assertEqual(verdict_of(result), "CONSTITUTIONAL_REQUIRED")
        self.assertIn("absolute ceiling", result.stderr)

    def test_editing_a_gate_script_is_constitutional_not_prohibited(self):
        # Additions plus deletions on a gate script is an edit -> AD4, not AD5:
        # all four gate scripts sit on the constitutional surface in bOPEN.
        result = run("10\t8\tscripts/check_budget.py\n")
        self.assertEqual(verdict_of(result), "CONSTITUTIONAL_REQUIRED")


class Ad1Ad2BallotTest(EnvelopeFixture):
    def test_governance_implementation_requires_ballot(self):
        result = run("10\t2\tdocs/00-governance/SOME_POLICY.md\n")
        self.assertEqual(result.returncode, EXIT_ESCALATE)
        self.assertEqual(verdict_of(result), "AGENT_BALLOT_REQUIRED")
        self.assertIn("NOT_ACTIVE", result.stderr)

    def test_decision_and_adr_docs_are_governance_not_constitutional(self):
        for path in ("docs/decisions/DEC-SOMETHING.md", "docs/adr/ADR-SOMETHING.md"):
            with self.subTest(path=path):
                result = run(f"40\t0\t{path}\n")
                self.assertEqual(verdict_of(result), "AGENT_BALLOT_REQUIRED")

    def test_contracts_and_tools_are_governance_surfaces(self):
        for path in ("contracts/party/party.schema.json", "tools/run_tests.py"):
            with self.subTest(path=path):
                result = run(f"6\t2\t{path}\n")
                self.assertEqual(verdict_of(result), "AGENT_BALLOT_REQUIRED")

    def test_over_envelope_cap_but_under_ceiling_requires_ballot(self):
        result = run("400\t300\tdocs/large.md\n")  # 700 > 600, < 2000
        self.assertEqual(verdict_of(result), "AGENT_BALLOT_REQUIRED")
        self.assertIn("exceeds the envelope cap", result.stderr)

    def test_ballot_layer_active_changes_the_reason_not_the_verdict(self):
        envelope = self.custom_envelope(**{"ballot_layer.state": "ACTIVE"})
        result = run("10\t2\tdocs/00-governance/P.md\n", envelope=envelope)
        self.assertEqual(verdict_of(result), "AGENT_BALLOT_REQUIRED")
        self.assertNotIn("NOT_ACTIVE", result.stderr)


class Ad5RejectedTest(unittest.TestCase):
    def test_deleting_a_control_is_rejected(self):
        result = run("0\t80\tscripts/check_budget.py\n")
        self.assertEqual(result.returncode, EXIT_REJECTED)
        self.assertEqual(verdict_of(result), "REJECTED")

    def test_deleting_evidence_is_rejected(self):
        result = run("0\t40\tdocs/evidence/phase-3.5/location-maker.md\n")
        self.assertEqual(result.returncode, EXIT_REJECTED)

    def test_removing_a_ci_enforcement_step_is_rejected(self):
        result = run(
            "3\t4\tdocs/note.md\n",
            diff_text="-        run: python scripts/check_work_package_ref.py",
        )
        self.assertEqual(result.returncode, EXIT_REJECTED)
        self.assertIn("removes an enforcement step", result.stderr)

    def test_quoting_an_enforcement_step_on_an_added_line_is_not_a_removal(self):
        # Regression carried from SecB: an ADDED line quoting the marker — a
        # test fixture, or documentation of this rule — must not read as a
        # removal.
        added = (
            '+        diff_text="-        run: python scripts/check_work_package_ref.py",\n'
            "+# documents that removing `run: python scripts/check_budget.py` is prohibited\n"
        )
        result = run("3\t4\tdocs/note.md\n", diff_text=added)
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertEqual(verdict_of(result), "AUTO_APPROVED")

    def test_diff_file_header_is_not_read_as_a_removal(self):
        header = "--- a/.github/workflows/ci.yml\n+++ b/.github/workflows/ci.yml\n"
        result = run("3\t4\tdocs/note.md\n", diff_text=header)
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)


class FailClosedTest(EnvelopeFixture):
    def test_empty_diff_escalates(self):
        result = run("")
        self.assertEqual(result.returncode, EXIT_ESCALATE)
        self.assertIn("no diff parsed", result.stderr)

    def test_unparseable_numstat_escalates(self):
        result = run("garbage without tabs\n")
        self.assertEqual(result.returncode, EXIT_ESCALATE)

    def test_missing_envelope_escalates(self):
        result = run("1\t0\tdocs/a.md\n", envelope=Path(self._tmp.name) / "absent.json")
        self.assertEqual(result.returncode, EXIT_ESCALATE)
        self.assertIn("envelope unusable", result.stderr)

    def test_malformed_envelope_escalates(self):
        bad = Path(self._tmp.name) / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        result = run("1\t0\tdocs/a.md\n", envelope=bad)
        self.assertEqual(result.returncode, EXIT_ESCALATE)

    def test_envelope_missing_required_key_escalates(self):
        partial = Path(self._tmp.name) / "partial.json"
        partial.write_text(json.dumps({"scope": {}}), encoding="utf-8")
        result = run("1\t0\tdocs/a.md\n", envelope=partial)
        self.assertEqual(result.returncode, EXIT_ESCALATE)

    def test_expired_envelope_escalates(self):
        envelope = self.custom_envelope(expires_at="2020-01-01")
        result = run("1\t0\tdocs/a.md\n", envelope=envelope)
        self.assertEqual(result.returncode, EXIT_ESCALATE)
        self.assertIn("expired", result.stderr)


if __name__ == "__main__":
    unittest.main()
