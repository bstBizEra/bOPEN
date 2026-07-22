"""GOV-P0-03 contract and negative tests for exact root control surfaces."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.validate_root_control_surfaces import (
    MANIFEST_PATH,
    PACKAGE_PATHS,
    ROOT,
    ROOT_SURFACES,
    SIGNED_ACTIVATION_AT,
    build_package_manifest,
    ACTIVATION_HEADING,
    read_git_blob,
    validate_append_only_bytes,
    validate_exact_root_names,
    validate_root_control_surfaces,
)


class RootControlSurfaceTests(unittest.TestCase):
    def make_fixture(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        for rel in PACKAGE_PATHS:
            source = ROOT / rel
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        manifest_path = root / MANIFEST_PATH
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(build_package_manifest(root), indent=2) + "\n", encoding="utf-8"
        )
        return temporary, root

    def test_repository_candidate_validates(self):
        self.assertEqual(validate_root_control_surfaces(), [])

        manifest = json.loads((ROOT / MANIFEST_PATH).read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "0.3")
        self.assertEqual(manifest["status"], "active")
        self.assertEqual(manifest["lifecycle"], "active")
        self.assertEqual(manifest["activation"]["activated_at"], SIGNED_ACTIVATION_AT)
        self.assertFalse(manifest["authority"]["pg_g0_passed"])
        self.assertFalse(manifest["authority"]["production_implementation_authorized"])

    def test_draft_schema_is_fail_closed(self):
        schema = json.loads(
            (ROOT / "contracts/governance/root-control-surface.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(schema["status"], "draft")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            set(schema["properties"]["document_id"]["enum"]), set(ROOT_SURFACES.values())
        )
        self.assertIn("activation", schema["required"])
        self.assertEqual(
            schema["properties"]["activation"]["properties"]["activated_at"]["const"],
            "2026-07-23T00:45:00+07:00",
        )
        for key in (
            "pg_g0_passed",
            "production_implementation_authorized",
            "merge_authorized",
            "release_authorized",
        ):
            self.assertFalse(schema["properties"]["authority"]["properties"][key]["const"])

    def test_missing_root_control_fails(self):
        temporary, root = self.make_fixture()
        with temporary:
            (root / "Roadmap.md").unlink()
            errors = validate_root_control_surfaces(root, check_git=False)
        self.assertTrue(any("ROOT CONTROL MISSING: Roadmap.md" in error for error in errors))

    def test_wrong_case_name_fails_closed(self):
        names = [name for name in ROOT_SURFACES if name != "Roadmap.md"] + ["roadmap.md"]
        self.assertTrue(validate_exact_root_names(names))

    def test_metadata_authority_mutation_fails(self):
        temporary, root = self.make_fixture()
        with temporary:
            path = root / "Roadmap.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "**PG-G0 passed:** false", "**PG-G0 passed:** true"
                ),
                encoding="utf-8",
            )
            errors = validate_root_control_surfaces(root, check_git=False)
        self.assertTrue(any("PG-G0 passed" in error for error in errors))

    def test_missing_crosslink_fails(self):
        temporary, root = self.make_fixture()
        with temporary:
            path = root / "Progress_Log.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace("[Backlog.md](Backlog.md)", "Backlog ledger"),
                encoding="utf-8",
            )
            errors = validate_root_control_surfaces(root, check_git=False)
        self.assertTrue(any("LINK MISSING Progress_Log.md: Backlog.md" in error for error in errors))

    def test_missing_unresolved_config_state_fails(self):
        temporary, root = self.make_fixture()
        with temporary:
            path = root / "Master_Standards.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "UNRESOLVED_EXTERNAL_DEPENDENCY", "AVAILABLE"
                ),
                encoding="utf-8",
            )
            errors = validate_root_control_surfaces(root, check_git=False)
        self.assertTrue(any("CONFIG STATE MISSING: Master_Standards.md" in error for error in errors))

    def test_mutable_backlog_checkbox_fails(self):
        temporary, root = self.make_fixture()
        with temporary:
            path = root / "Backlog.md"
            path.write_text(path.read_text(encoding="utf-8") + "\n- [ ] mutable task\n", encoding="utf-8")
            errors = validate_root_control_surfaces(root, check_git=False)
        self.assertTrue(any("MUTABLE CHECKBOX PROHIBITED: Backlog.md" in error for error in errors))

    def test_partial_activation_fails_closed(self):
        temporary, root = self.make_fixture()
        with temporary:
            for relative in tuple(ROOT_SURFACES)[1:]:
                path = root / relative
                prefix = path.read_text(encoding="utf-8").split(ACTIVATION_HEADING, 1)[0].rstrip()
                path.write_text(prefix + "\n", encoding="utf-8")
            errors = validate_root_control_surfaces(root, check_git=False)
        self.assertTrue(any("ACTIVATION MUST BE ATOMIC" in error for error in errors), errors)

    def test_unsigned_zero_activation_state_fails_closed(self):
        temporary, root = self.make_fixture()
        with temporary:
            for relative in ROOT_SURFACES:
                path = root / relative
                prefix = path.read_text(encoding="utf-8").split(ACTIVATION_HEADING, 1)[0].rstrip()
                path.write_text(prefix + "\n", encoding="utf-8")
            errors = validate_root_control_surfaces(root, check_git=False)
        self.assertTrue(any("ACTIVATION MUST BE ATOMIC" in error for error in errors), errors)

    def test_activation_requires_exact_signed_fields(self):
        temporary, root = self.make_fixture()
        with temporary:
            event = (
                f"\n{ACTIVATION_HEADING}\n\n"
                "**Activation status:** Active\n"
                "**Activation lifecycle:** Active\n"
                "**Activated by:** AGENT-INVENTED\n"
                "**Activated at:** not-a-time\n"
                "**Activation decision ref:** missing\n"
                "**Activation evidence ref:** missing\n"
                "**Activation substrate commit:** 0000000000000000000000000000000000000000\n"
            )
            for relative in ROOT_SURFACES:
                path = root / relative
                prefix = path.read_text(encoding="utf-8").split(ACTIVATION_HEADING, 1)[0].rstrip()
                path.write_text(prefix + event, encoding="utf-8")
            errors = validate_root_control_surfaces(root, check_git=False)
        self.assertTrue(any("ACTIVATION FIELD INVALID" in error for error in errors), errors)
        self.assertTrue(any("ACTIVATION SIGNING EVIDENCE MISSING" in error for error in errors), errors)

    def test_append_only_prefix_accepts_append(self):
        self.assertEqual(validate_append_only_bytes(b"old\n", b"old\nnew\n"), [])

    def test_append_only_prefix_rejects_rewrite_and_truncation(self):
        self.assertIn("ROOT CONTROL PREFIX REWRITTEN", validate_append_only_bytes(b"old\n", b"new\n"))
        self.assertIn("ROOT CONTROL TRUNCATED", validate_append_only_bytes(b"old\n", b"old"))

    def test_stale_package_manifest_fails(self):
        temporary, root = self.make_fixture()
        with temporary:
            path = root / "Recap_Today.md"
            path.write_text(path.read_text(encoding="utf-8") + "\nnew event\n", encoding="utf-8")
            errors = validate_root_control_surfaces(root, check_git=False)
        self.assertIn("ROOT CONTROL PACKAGE MANIFEST STALE", errors)

    def test_crlf_only_package_mutation_stales_manifest(self):
        temporary, root = self.make_fixture()
        with temporary:
            path = root / "Roadmap.md"
            path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
            errors = validate_root_control_surfaces(root, check_git=False)
        self.assertIn("ROOT CONTROL PACKAGE MANIFEST STALE", errors)

    def test_git_blob_reader_preserves_line_endings_and_rewrite_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "GOV-P0-03 Test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "gov-p0-03@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "config", "core.autocrlf", "false"], cwd=root, check=True)
            path = root / "control.md"
            path.write_bytes(b"line-one\r\n")
            subprocess.run(["git", "add", "control.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "crlf"], cwd=root, check=True)
            before_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True
            ).stdout.strip()
            path.write_bytes(b"line-one\n")
            subprocess.run(["git", "add", "control.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "lf"], cwd=root, check=True)
            after_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True
            ).stdout.strip()
            before = read_git_blob(root, f"{before_commit}:control.md")
            after = read_git_blob(root, f"{after_commit}:control.md")

        self.assertEqual(before, b"line-one\r\n")
        self.assertEqual(after, b"line-one\n")
        self.assertIn("ROOT CONTROL PREFIX REWRITTEN", validate_append_only_bytes(before, after))


if __name__ == "__main__":
    unittest.main()
