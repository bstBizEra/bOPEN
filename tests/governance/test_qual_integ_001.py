"""Tests for the QUAL-INTEG-001 fail-closed integration validator."""

from __future__ import annotations

import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import validate_qual_integ_001 as validator  # noqa: E402


class QualIntegrationValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest, errors = validator.load_integration_manifest(ROOT)
        if errors or cls.manifest is None:
            raise AssertionError(errors)

    def canonical_patch_ids(self) -> dict:
        candidate = copy.deepcopy(self.manifest)
        for chain in candidate["source_chains"]:
            for mapping in chain["mappings"]:
                excluded = validator.scope_exclusions(mapping["scope"], candidate["shared_paths"])
                self.assertIsNotNone(excluded)
                for label in ("source", "replay"):
                    patch_id = validator.stable_patch_id(ROOT, mapping[label], excluded or ())
                    self.assertIsNotNone(patch_id)
                    mapping[f"{label}_patch_id"] = patch_id
        return candidate

    def test_positive_candidate_components(self) -> None:
        """The composed Git objects and package bytes satisfy the validator."""

        candidate = self.canonical_patch_ids()
        self.assertEqual(validator.validate_authority(candidate), [])
        self.assertEqual(validator.validate_mappings(candidate, ROOT), [])
        self.assertEqual(validator.validate_package_bytes(ROOT), [])
        self.assertEqual(validator.validate_res_replay_bytes(candidate, ROOT), [])
        self.assertEqual(validator.tracked_text_conflicts(ROOT), [])

    def test_full_candidate_path_invokes_index_and_semantic_gates(self) -> None:
        candidate = self.canonical_patch_ids()
        with (
            patch.object(validator, "load_integration_manifest", return_value=(candidate, [])),
            patch.object(validator, "validate_manifest_index", return_value=[]),
            patch.object(validator, "validate_semantic_union", return_value=[]),
        ):
            self.assertEqual(validator.validate_candidate(ROOT), [])

    def test_enabled_authority_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.manifest)
        candidate["authority"]["merge_authorized"] = True
        self.assertIn(
            "integration authority flag must remain false: merge_authorized",
            validator.validate_authority(candidate),
        )

    def test_missing_authority_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.manifest)
        del candidate["authority"]["release_authorized"]
        self.assertIn(
            "integration authority flag missing: release_authorized",
            validator.validate_authority(candidate),
        )

    def test_incorrect_declared_patch_id_is_rejected(self) -> None:
        candidate = self.canonical_patch_ids()
        mapping = candidate["source_chains"][0]["mappings"][0]
        mapping["source_patch_id"] = "0" * 40
        errors = validator.validate_mappings(candidate, ROOT)
        self.assertTrue(any("source patch-id mismatch" in error for error in errors))

    def test_package_byte_drift_is_rejected(self) -> None:
        path = validator.PACKAGE_BINDINGS[0][2]
        original = (ROOT / path).read_bytes()
        real_read_bytes = Path.read_bytes
        with patch.object(Path, "read_bytes", autospec=True) as read_bytes:
            read_bytes.side_effect = lambda value: (
                original + b"drift" if value == ROOT / path else real_read_bytes(value)
            )
            errors = validator.validate_package_bytes(ROOT)
        self.assertIn(f"GOV-P0-03 package byte drift: {path}", errors)

    def test_conflict_marker_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            marker = "<" * 7
            (root / "tracked.txt").write_text(f"{marker} ours\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
            self.assertEqual(
                validator.tracked_text_conflicts(root),
                ["unresolved conflict marker: tracked.txt"],
            )

    def test_semantic_token_absence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "control.txt"
            path.write_text("alpha\n", encoding="utf-8")
            self.assertEqual(
                validator.require_tokens(path, ("alpha", "beta"), "control"),
                ["control semantic union missing: beta"],
            )


if __name__ == "__main__":
    unittest.main()
