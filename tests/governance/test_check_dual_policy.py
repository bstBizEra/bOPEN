"""Subprocess tests for scripts/check_dual_policy.py.

Each test builds a throwaway git repository containing a base commit and a
head working tree, so the base-vs-head comparison is exercised against real
`git show` output rather than a stub.

Ported from the SecB Project Framework under BOPEN-WP-GOV-AUTONOMY-001;
unittest style so `unittest discover` can run it without pytest.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_dual_policy.py"
CLASSIFIER = ROOT / "scripts" / "classify_authority_delta.py"
ENVELOPE = ROOT / "config" / "delegation_envelope.json"

EXIT_OK = 0
EXIT_ESCALATE = 2
EXIT_REJECTED = 3


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, timeout=60, check=True
    )


def make_repo(tmp_path: Path, base_envelope: dict | None = None) -> Path:
    """A repo whose base commit carries the real classifier and envelope."""
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    (repo / "config").mkdir(parents=True)
    shutil.copy(CLASSIFIER, repo / "scripts" / "classify_authority_delta.py")
    shutil.copy(SCRIPT, repo / "scripts" / "check_dual_policy.py")
    envelope = base_envelope or json.loads(ENVELOPE.read_text(encoding="utf-8"))
    (repo / "config" / "delegation_envelope.json").write_text(
        json.dumps(envelope), encoding="utf-8"
    )
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "test@bst.local")
    git(repo, "config", "user.name", "test")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    return repo


def run_dual(repo: Path, numstat: str, base_ref: str = "main"):
    env = {k: v for k, v in os.environ.items() if k != "BASE_REF"}
    env["BASE_REF"] = base_ref
    return subprocess.run(
        [sys.executable, "scripts/check_dual_policy.py"],
        cwd=repo,
        input=numstat,
        capture_output=True,
        text=True,
        env=env,
        timeout=90,
    )


class DualPolicyTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_path = Path(self._tmp.name)

    def test_agreeing_pass_on_ad0_change(self):
        repo = make_repo(self.tmp_path)
        result = run_dual(repo, "5\t2\tdocs/note.md\n")
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertIn("DUAL POLICY: PASS", result.stdout)
        self.assertIn("base (main)", result.stdout)
        self.assertIn("head (this PR)", result.stdout)

    def test_agreeing_escalation_still_escalates(self):
        repo = make_repo(self.tmp_path)
        result = run_dual(repo, "2\t1\tAGENTS.md\n")
        self.assertEqual(result.returncode, EXIT_ESCALATE)
        self.assertIn("both policies agree that this escalates", result.stderr)

    def test_divergence_escalates_even_when_head_would_pass(self):
        """The core anti-self-approval property: a head policy that widens its
        own scope cannot use that widening to approve the widening."""
        repo = make_repo(self.tmp_path)
        # Head envelope adds ops/ to the auto-approved scope.
        envelope = json.loads((repo / "config" / "delegation_envelope.json").read_text())
        envelope["scope"]["auto_paths"].append("ops/")
        (repo / "config" / "delegation_envelope.json").write_text(json.dumps(envelope))

        result = run_dual(repo, "3\t0\tops/thing.tf\n")
        self.assertEqual(result.returncode, EXIT_ESCALATE)
        self.assertIn("base and head policies disagree", result.stderr)
        # Head alone would have said AUTO_APPROVED; base said CONSTITUTIONAL_REQUIRED.
        self.assertIn("AUTO_APPROVED", result.stdout)
        self.assertIn("CONSTITUTIONAL_REQUIRED", result.stdout)

    def test_rejected_under_either_policy_is_rejected(self):
        repo = make_repo(self.tmp_path)
        result = run_dual(repo, "0\t50\tscripts/check_budget.py\n")
        self.assertEqual(result.returncode, EXIT_REJECTED)
        self.assertIn("DUAL POLICY: REJECTED", result.stderr)

    def test_missing_base_ref_escalates(self):
        repo = make_repo(self.tmp_path)
        result = run_dual(repo, "5\t2\tdocs/note.md\n", base_ref="origin/nonexistent")
        self.assertEqual(result.returncode, EXIT_ESCALATE)
        self.assertIn("base logic not recoverable", result.stderr)

    def test_deleting_head_classifier_cannot_escape_comparison(self):
        repo = make_repo(self.tmp_path)
        (repo / "scripts" / "classify_authority_delta.py").unlink()
        result = run_dual(repo, "0\t200\tscripts/classify_authority_delta.py\n")
        self.assertEqual(result.returncode, EXIT_ESCALATE)
        self.assertIn("may not remove the logic that judges it", result.stderr)

    def test_head_envelope_expiry_diverges_and_escalates(self):
        repo = make_repo(self.tmp_path)
        envelope = json.loads((repo / "config" / "delegation_envelope.json").read_text())
        envelope["expires_at"] = "2020-01-01"
        (repo / "config" / "delegation_envelope.json").write_text(json.dumps(envelope))
        result = run_dual(repo, "5\t2\tdocs/note.md\n")
        self.assertEqual(result.returncode, EXIT_ESCALATE)


if __name__ == "__main__":
    unittest.main()
