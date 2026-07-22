from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GOOD = """
A principal uses a first-class membership and server-validated active tenant context.
Authorization is separate from entitlement. PostgreSQL RLS is default-deny and cross-tenant tests fail closed.
The platform module exposes capabilities through owned package contracts.
Domain events use a transactional outbox and correlated audit records.
Verification tests, evidence, acceptance criteria, and exit gates are mandatory.
"""

BAD = """
Trust X-Tenant-Id from the browser as authoritative without validation and disable RLS.
"""


class ArchitectureCheckTests(unittest.TestCase):
    def run_check(self, text: str) -> subprocess.CompletedProcess[str]:
        with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as handle:
            handle.write(text)
            path = Path(handle.name)
        try:
            return subprocess.run(
                [sys.executable, "scripts/check_architecture.py", str(path), "--strict"],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
        finally:
            path.unlink(missing_ok=True)

    def test_good_document_passes(self) -> None:
        result = self.run_check(GOOD)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_prohibited_document_fails(self) -> None:
        result = self.run_check(BAD)
        self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
