"""Subprocess tests for scripts/check_budget.py (Budget circuit breaker).

Ported from the SecB Project Framework under BOPEN-WP-GOV-AUTONOMY-001;
unittest style so `unittest discover` can run it without pytest.
"""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_budget.py"


def run_gate(numstat: str, budget_text: str | None) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "BUDGET_TEXT"}
    if budget_text is not None:
        env["BUDGET_TEXT"] = budget_text
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=numstat,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        timeout=30,
    )


class BudgetGateTest(unittest.TestCase):
    def test_within_budget_passes(self):
        result = run_gate(
            "10\t5\tdocs/a.md\n3\t0\ttests/governance/test_b.py\n",
            "Some PR body\nBUDGET: max_files=5 max_lines=50\n",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("BUDGET GATE PASS: 2/5 files, 18/50 changed lines", result.stdout)

    def test_missing_budget_fails_closed(self):
        result = run_gate("1\t1\tdocs/a.md\n", "a body with no budget line")
        self.assertEqual(result.returncode, 2)
        self.assertIn("no budget declared", result.stderr)

    def test_two_budget_lines_fail(self):
        body = "BUDGET: max_files=5 max_lines=50\nBUDGET: max_files=9 max_lines=900\n"
        result = run_gate("1\t1\tdocs/a.md\n", body)
        self.assertEqual(result.returncode, 2)
        self.assertIn("ambiguous", result.stderr)

    def test_exceeded_lines_fail(self):
        result = run_gate(
            "40\t20\tdocs/a.md\n", "BUDGET: max_files=5 max_lines=50\n"
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("exceeds the declared budget", result.stderr)

    def test_exceeded_files_fail(self):
        numstat = "".join(f"1\t0\tdocs/f{i}.md\n" for i in range(6))
        result = run_gate(numstat, "BUDGET: max_files=5 max_lines=50\n")
        self.assertEqual(result.returncode, 2)

    def test_binary_file_counts_as_file_with_zero_lines(self):
        result = run_gate(
            "-\t-\tdocs/diagram.png\n", "BUDGET: max_files=1 max_lines=0\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_malformed_numstat_fails_closed(self):
        result = run_gate("garbage row\n", "BUDGET: max_files=5 max_lines=50\n")
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
