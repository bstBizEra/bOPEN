from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_package import (  # noqa: E402
    Report,
    validate_checksums,
    validate_supply_chain,
    validator_for,
)


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
        with tempfile.TemporaryDirectory(prefix="bopen-artifact-test-", dir=ROOT.parents[1]) as tmp:
            output_dir = Path(tmp)
            output = output_dir / "adr.md"
            result = subprocess.run(
                [sys.executable, "scripts/new_artifact.py", "--type", "adr", "--id", "ADR-TEST-001", "--title", "Test Decision", "--output-dir", str(output_dir), "--output", output.name],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("ADR-TEST-001", output.read_text(encoding="utf-8"))

            repeat = subprocess.run(
                [sys.executable, "scripts/new_artifact.py", "--type", "adr", "--id", "ADR-TEST-002", "--title", "Replacement", "--output-dir", str(output_dir), "--output", output.name],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(repeat.returncode, 0)
            self.assertIn("Refusing to overwrite", repeat.stderr)

    def test_artifact_generation_rejects_output_escape(self) -> None:
        with tempfile.TemporaryDirectory(prefix="bopen-artifact-test-", dir=ROOT.parents[1]) as tmp:
            result = subprocess.run(
                [sys.executable, "scripts/new_artifact.py", "--type", "adr", "--id", "ADR-TEST-003", "--title", "Escape", "--output-dir", tmp, "--output", "../escape.md"],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("escapes --output-dir", result.stderr)

    def test_candidate_release_packaging_is_blocked(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/package_release.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("disabled until independently approved", result.stderr)

    def test_checksum_validation_rejects_unlisted_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="bopen-checksum-test-", dir=ROOT.parents[1]) as tmp:
            test_root = Path(tmp)
            tracked = test_root / "tracked.txt"
            tracked.write_text("tracked\n", encoding="utf-8")
            digest = hashlib.sha256(tracked.read_bytes()).hexdigest()
            (test_root / "SHA256SUMS").write_text(f"{digest}  tracked.txt\n", encoding="utf-8")
            (test_root / "unlisted.txt").write_text("unlisted\n", encoding="utf-8")

            report = Report()
            validate_checksums(report, test_root)

            self.assertIn("Unlisted package file: unlisted.txt", report.errors)

    def test_output_contract_uses_recommendation_only_dispositions(self) -> None:
        example = json.loads((ROOT / "evals/example-output.json").read_text(encoding="utf-8"))
        validator = validator_for(ROOT / "schemas/output.schema.json")
        self.assertFalse(list(validator.iter_errors(example)))

        example["disposition"] = "APPROVE"
        self.assertTrue(list(validator.iter_errors(example)))

    def test_supply_chain_validation_rejects_version_and_inventory_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix="bopen-supply-chain-test-", dir=ROOT.parents[1]) as tmp:
            test_root = Path(tmp) / "bopen-architecture"
            shutil.copytree(
                ROOT,
                test_root,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "evals/results"),
            )
            manifest_path = test_root / "supply-chain/release-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["version"] = "0.0.0"
            manifest["files"][0]["sha256"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            report = Report()
            validate_supply_chain(report, test_root)

            self.assertTrue(any("Release manifest version mismatch" in item for item in report.errors))
            self.assertTrue(any("Release manifest checksum mismatch" in item for item in report.errors))


if __name__ == "__main__":
    unittest.main()
