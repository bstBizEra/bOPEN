from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "audit_git_provenance.py"
PACKAGE = ROOT / "scripts" / "package_evidence.py"
SCHEMA = ROOT / "assets" / "audit-manifest.schema.json"


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, encoding="utf-8", capture_output=True, check=False)


class ScriptTests(unittest.TestCase):
    def make_repo(self, root: Path) -> tuple[Path, str]:
        repo = root / "repo"
        repo.mkdir()
        self.assertEqual(run("git", "init", "-q", str(repo)).returncode, 0)
        self.assertEqual(run("git", "config", "user.name", "Fixture", cwd=repo).returncode, 0)
        self.assertEqual(run("git", "config", "user.email", "fixture@example.invalid", cwd=repo).returncode, 0)
        (repo / "README.md").write_text("fixture\n", encoding="utf-8", newline="\n")
        self.assertEqual(run("git", "add", "README.md", cwd=repo).returncode, 0)
        self.assertEqual(run("git", "commit", "-q", "-m", "fixture", cwd=repo).returncode, 0)
        oid = run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
        return repo, oid

    def test_local_audit_and_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, oid = self.make_repo(root)
            output = root / "audit"
            result = run(
                sys.executable,
                str(AUDIT),
                "--repo",
                str(repo),
                "--output",
                str(output),
                "--target-ref",
                "HEAD",
                "--profile",
                "local-integrity",
                "--expected-commit",
                oid,
                "--observed-at",
                "2026-07-28T00:00:00Z",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
            self.assertEqual(audit["baseline"]["observed_ref_oid"], oid)
            self.assertEqual(audit["overall_verdict"], "PASS_WITH_GAPS")
            packaged = run(
                sys.executable,
                str(PACKAGE),
                "--audit-dir",
                str(output),
                "--schema",
                str(SCHEMA),
            )
            self.assertEqual(packaged.returncode, 0, packaged.stderr)
            manifest = json.loads((output / "audit-manifest.json").read_text(encoding="utf-8"))
            self.assertRegex(manifest["checksum_root_sha256"], r"^[0-9a-f]{64}$")

    def test_expected_commit_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, _ = self.make_repo(root)
            output = root / "audit"
            result = run(
                sys.executable,
                str(AUDIT),
                "--repo",
                str(repo),
                "--output",
                str(output),
                "--target-ref",
                "HEAD",
                "--expected-commit",
                "0" * 40,
            )
            self.assertEqual(result.returncode, 2, result.stderr)
            findings = json.loads((output / "findings.json").read_text(encoding="utf-8"))
            self.assertEqual(findings[0]["verdict"], "FAIL")


if __name__ == "__main__":
    unittest.main()
