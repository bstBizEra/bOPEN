from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PackageValidationTests(unittest.TestCase):
    def test_package_validator_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/validate_package.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_artifact_generation(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "adr.md"
            result = subprocess.run(
                [sys.executable, "scripts/new_artifact.py", "--type", "adr", "--id", "ADR-TEST-001", "--title", "Test Decision", "--output", str(output)],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("ADR-TEST-001", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
