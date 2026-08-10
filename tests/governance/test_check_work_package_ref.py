"""Subprocess tests for scripts/check_work_package_ref.py (Authority Gate).

Invoked as CI invokes it — text through the WP_TEXT environment variable —
so a green test is evidence about the enforcement path, not about an
imported function. Ported from the SecB Project Framework under
BOPEN-WP-GOV-AUTONOMY-001; unittest style so `unittest discover` (the
Bootstrap Governance workflow) can run it without pytest.
"""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_work_package_ref.py"


def run_gate(text: str | None) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "WP_TEXT"}
    if text is not None:
        env["WP_TEXT"] = text
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


class AuthorityGateTest(unittest.TestCase):
    def test_canonical_reference_passes(self):
        result = run_gate("feat: add router\n\nCloses BOPEN-WP-GOV-AUTONOMY-001")
        self.assertEqual(result.returncode, 0)
        self.assertIn("BOPEN-WP-GOV-AUTONOMY-001", result.stdout)

    def test_legacy_id_shapes_pass(self):
        for legacy in ("BOPEN-P35-001", "WP-P35-07", "BOOT-P0-05"):
            with self.subTest(legacy=legacy):
                result = run_gate(f"work under {legacy}")
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_reference_fails(self):
        result = run_gate("chore: tidy the docs, no ticket cited")
        self.assertEqual(result.returncode, 2)
        self.assertIn("AUTHORITY GATE FAIL", result.stderr)

    def test_empty_input_fails_closed(self):
        result = run_gate("")
        self.assertEqual(result.returncode, 2)
        self.assertIn("fail", result.stderr.lower())

    def test_lowercase_reference_does_not_pass(self):
        result = run_gate("mentions bopen-wp-gov-autonomy-001 in lowercase")
        self.assertEqual(result.returncode, 2)

    def test_prefix_without_segment_does_not_pass(self):
        result = run_gate("BOPEN-WP- alone is not an ID")
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
