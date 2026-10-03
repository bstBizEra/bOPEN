import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ValidatePackageTests(unittest.TestCase):
    def test_validator_passes(self):
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/validate_package.py")], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["errors"], [])


if __name__ == "__main__":
    unittest.main()
