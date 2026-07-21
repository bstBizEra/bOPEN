"""Tests for the QUAL-INTEG-001 fail-closed integration validator."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import validate_qual_integ_001 as validator  # noqa: E402
import generate_document_manifest as manifest_generator  # noqa: E402


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


class ManifestWriteAndHistoryTests(unittest.TestCase):
    """Adversarial coverage for immutable manifest write and history controls."""

    @staticmethod
    def init_repository(root: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(
            ["git", "config", "user.name", "QUAL-INTEG-001 Tests"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "qual-integ-001@bst.invalid"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "core.autocrlf", "false"], cwd=root, check=True
        )

    @staticmethod
    def index_entry(
        identifier: str,
        sequence: int,
        previous_digest: str | None,
        path: str,
        payload: bytes,
    ) -> dict:
        return {
            "id": identifier,
            "sequence": sequence,
            "previous_entry_sha256": previous_digest,
            "mode": "current_exact_file",
            "path": path,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }

    @staticmethod
    def canonical_index_line(entry: dict) -> bytes:
        return (
            json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            + "\n"
        ).encode("utf-8")

    def make_index_history(self, root: Path) -> tuple[Path, bytes, bytes, bytes]:
        first_payload = b'{"manifest":"first"}\n'
        second_payload = b'{"manifest":"second"}\n'
        third_payload = b'{"manifest":"third"}\n'
        manifests = root / "docs" / "manifests"
        manifests.mkdir(parents=True)
        (manifests / "first.json").write_bytes(first_payload)
        (manifests / "second.json").write_bytes(second_payload)
        (manifests / "third.json").write_bytes(third_payload)

        first = self.index_entry(
            "FIRST", 1, None, "docs/manifests/first.json", first_payload
        )
        first_canonical = json.dumps(
            first, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        second = self.index_entry(
            "SECOND",
            2,
            hashlib.sha256(first_canonical).hexdigest(),
            "docs/manifests/second.json",
            second_payload,
        )
        second_canonical = json.dumps(
            second, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        third = self.index_entry(
            "THIRD",
            3,
            hashlib.sha256(second_canonical).hexdigest(),
            "docs/manifests/third.json",
            third_payload,
        )
        first_line = self.canonical_index_line(first)
        second_line = self.canonical_index_line(second)
        third_line = self.canonical_index_line(third)
        index = manifests / "MANIFEST-INDEX.jsonl"
        index.write_bytes(first_line + second_line)
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "[QUAL-INTEG-001] Seed manifest index"],
            cwd=root,
            check=True,
        )
        return index, first_line, second_line, third_line

    def run_generator(self, root: Path, *arguments: str) -> tuple[int, str]:
        stdout = io.StringIO()
        with (
            patch.object(manifest_generator, "ROOT", root),
            patch.object(sys, "argv", ["generate_document_manifest.py", *arguments]),
            redirect_stdout(stdout),
        ):
            result = manifest_generator.main()
        return result, stdout.getvalue()

    def test_generator_refuses_canonical_manifest_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            canonical = root / "docs" / "DOCUMENT-MANIFEST.json"
            canonical.parent.mkdir(parents=True)
            original = b'{"historical":"canonical"}\n'
            canonical.write_bytes(original)

            result, output = self.run_generator(
                root,
                "--aggregate",
                "--output",
                "docs/DOCUMENT-MANIFEST.json",
            )

            self.assertNotEqual(result, 0, output)
            self.assertIn("MANIFEST WRITE TARGET IS PROTECTED", output)
            self.assertEqual(canonical.read_bytes(), original)

    def test_generator_refuses_existing_indexed_historical_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repository(root)
            index, _, _, _ = self.make_index_history(root)
            historical = root / "docs" / "manifests" / "first.json"
            original = historical.read_bytes()

            result, output = self.run_generator(
                root,
                "--aggregate",
                "--output",
                "docs/manifests/first.json",
                "--index",
                str(index.relative_to(root)),
            )

            self.assertNotEqual(result, 0, output)
            self.assertIn("MANIFEST WRITE TARGET IS ALREADY INDEXED", output)
            self.assertEqual(historical.read_bytes(), original)

    def test_generator_requires_aggregate_for_new_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repository(root)
            output_path = root / "docs" / "manifests" / "NEW-SNAPSHOT-MANIFEST.json"

            result, output = self.run_generator(
                root, "--output", "docs/manifests/NEW-SNAPSHOT-MANIFEST.json"
            )

            self.assertNotEqual(result, 0, output)
            self.assertIn("writes require explicit --aggregate", output)
            self.assertFalse(output_path.exists())

    def test_generator_refuses_overwrite_of_existing_new_snapshot_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repository(root)
            output_path = root / "docs" / "manifests" / "EXISTING-SNAPSHOT-MANIFEST.json"
            output_path.parent.mkdir(parents=True)
            original = b'{"unindexed":"existing"}\n'
            output_path.write_bytes(original)

            result, output = self.run_generator(
                root,
                "--aggregate",
                "--output",
                "docs/manifests/EXISTING-SNAPSHOT-MANIFEST.json",
            )

            self.assertNotEqual(result, 0, output)
            self.assertIn("MANIFEST WRITE TARGET MUST NOT ALREADY EXIST", output)
            self.assertEqual(output_path.read_bytes(), original)

    def assert_history_rejected(self, candidate: bytes) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repository(root)
            index, _, _, _ = self.make_index_history(root)
            index.write_bytes(candidate)
            errors = manifest_generator.validate_manifest_index_history(index, root=root)
            self.assertTrue(errors, "adversarial manifest-index history was accepted")

    def test_manifest_index_history_accepts_exact_raw_byte_append(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repository(root)
            index, first_line, second_line, third_line = self.make_index_history(root)
            index.write_bytes(first_line + second_line + third_line)

            self.assertEqual(
                manifest_generator.validate_manifest_index_history(index, root=root), []
            )

    def test_manifest_index_history_rejects_truncation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repository(root)
            index, first_line, _, _ = self.make_index_history(root)
            index.write_bytes(first_line)
            self.assertTrue(
                manifest_generator.validate_manifest_index_history(index, root=root)
            )

    def test_manifest_index_history_rejects_prior_line_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repository(root)
            index, first_line, second_line, third_line = self.make_index_history(root)
            mutated = first_line.replace(b'"FIRST"', b'"ALTER"')
            index.write_bytes(mutated + second_line + third_line)
            self.assertTrue(
                manifest_generator.validate_manifest_index_history(index, root=root)
            )

    def test_manifest_index_history_rejects_reordered_prior_lines(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repository(root)
            index, first_line, second_line, third_line = self.make_index_history(root)
            index.write_bytes(second_line + first_line + third_line)
            self.assertTrue(
                manifest_generator.validate_manifest_index_history(index, root=root)
            )

    def test_manifest_index_history_rejects_crlf_append(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repository(root)
            index, first_line, second_line, third_line = self.make_index_history(root)
            index.write_bytes(first_line + second_line + third_line.replace(b"\n", b"\r\n"))
            self.assertTrue(
                manifest_generator.validate_manifest_index_history(index, root=root)
            )

    def test_manifest_index_history_rejects_malformed_appended_line(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repository(root)
            index, first_line, second_line, _ = self.make_index_history(root)
            index.write_bytes(first_line + second_line + b"not-json\n")
            self.assertTrue(
                manifest_generator.validate_manifest_index_history(index, root=root)
            )


if __name__ == "__main__":
    unittest.main()
