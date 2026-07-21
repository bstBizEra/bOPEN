"""Adversarial tests for the draft QUAL-P0-00 common qualification envelope."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.validate_qualification_common import (
    DEFAULT_CATALOG,
    NON_AUTHORITY_FLAGS,
    ROOT,
    canonical_payload_sha256,
    build_package_manifest,
    exact_file_bytes,
    normalized_path,
    resolve_json_pointer,
    validate_catalog_graph,
    validate_checker_receipt,
    validate_common_package,
    validate_direct_parent_chain,
    validate_qualification_envelope,
)


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class QualificationCommonTests(unittest.TestCase):
    def test_repository_common_package_validates(self):
        self.assertEqual(validate_common_package(ROOT, DEFAULT_CATALOG), [])

    def test_normalized_paths_are_fail_closed(self):
        self.assertTrue(normalized_path("docs/evidence/run-001/result.json"))
        for value in ("", "/absolute", "C:/drive", "../escape", "a/../b", "a\\b", "a//b", "./a"):
            self.assertFalse(normalized_path(value), value)

    def test_catalog_digest_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = ROOT / "contracts/qualification/common"
            target = root / "contracts/qualification/common"
            shutil.copytree(source, target)
            with (target / "repository-binding.schema.json").open("a", encoding="utf-8") as stream:
                stream.write("\n")
            _, errors = validate_catalog_graph(root, Path("contracts/qualification/common/QUAL-P0-00-SCHEMA-CATALOG.json"))
        self.assertTrue(any("digest mismatch" in error for error in errors))

    def test_network_and_unresolved_refs_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = ROOT / "contracts/qualification/common"
            target = root / "contracts/qualification/common"
            shutil.copytree(source, target)
            schema_path = target / "repository-binding.schema.json"
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            schema["properties"]["branch_ref"] = {"$ref": "https://invalid.example/schema"}
            schema["properties"]["repository_ref"] = {
                "$ref": "bopen://schemas/qualification/common/not-cataloged/0.1.0-draft"
            }
            schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8", newline="\n")
            catalog_path = target / "QUAL-P0-00-SCHEMA-CATALOG.json"
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            for entry in catalog["entries"]:
                if entry["path"].endswith("repository-binding.schema.json"):
                    entry["sha256"] = sha256(schema_path)
            catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8", newline="\n")
            _, errors = validate_catalog_graph(root, Path("contracts/qualification/common/QUAL-P0-00-SCHEMA-CATALOG.json"))
        self.assertTrue(any("network schema ref prohibited" in error for error in errors))
        self.assertTrue(any("offline schema ref unresolved" in error for error in errors))

    def test_local_json_pointer_missing_target_and_cycles_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "contracts/qualification/common"
            shutil.copytree(ROOT / "contracts/qualification/common", target)
            schema_path = target / "repository-binding.schema.json"
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            schema["properties"]["branch_ref"] = {"$ref": "#/$defs/missing"}
            schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8", newline="\n")
            catalog_path = target / "QUAL-P0-00-SCHEMA-CATALOG.json"
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            for entry in catalog["entries"]:
                if entry["path"].endswith("repository-binding.schema.json"):
                    entry["sha256"] = sha256(schema_path)
            catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8", newline="\n")
            _, missing_errors = validate_catalog_graph(root, Path("contracts/qualification/common/QUAL-P0-00-SCHEMA-CATALOG.json"))

            schema["$defs"] = {
                "a": {"$ref": "#/$defs/b"},
                "b": {"$ref": "#/$defs/a"},
            }
            schema["properties"]["branch_ref"] = {"$ref": "#/$defs/a"}
            schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8", newline="\n")
            for entry in catalog["entries"]:
                if entry["path"].endswith("repository-binding.schema.json"):
                    entry["sha256"] = sha256(schema_path)
            catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8", newline="\n")
            _, cycle_errors = validate_catalog_graph(root, Path("contracts/qualification/common/QUAL-P0-00-SCHEMA-CATALOG.json"))

        self.assertTrue(any("JSON Pointer unresolved" in error for error in missing_errors))
        self.assertTrue(any("schema reference cycle" in error for error in cycle_errors))

    def test_json_pointer_escape_and_array_rules_are_exact(self):
        document = {"a/b": {"~key": ["zero", "one"]}}
        self.assertEqual(resolve_json_pointer(document, "/a~1b/~0key/1"), "one")
        self.assertIsNot(resolve_json_pointer(document, "/a~2b"), document)
        self.assertIsNot(resolve_json_pointer(document, "/a~1b/~0key/01"), document)

    def test_unknown_catalog_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "contracts/qualification/common"
            shutil.copytree(ROOT / "contracts/qualification/common", target)
            catalog_path = target / "QUAL-P0-00-SCHEMA-CATALOG.json"
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            catalog["authority"] = "invented"
            catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8", newline="\n")
            _, errors = validate_catalog_graph(root, Path("contracts/qualification/common/QUAL-P0-00-SCHEMA-CATALOG.json"))
        self.assertTrue(any("unknown field: authority" in error for error in errors))

    def test_package_manifest_hashes_exact_crlf_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            from tools.validate_qualification_common import PACKAGE_PATHS

            for relative in PACKAGE_PATHS:
                source = ROOT / relative
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            target = root / "docs/work-packages/QUAL-P0-00.md"
            target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))
            manifest = build_package_manifest(root)
            record = next(item for item in manifest["records"] if item["path"] == "docs/work-packages/QUAL-P0-00.md")
            raw = target.read_bytes()
            self.assertEqual(exact_file_bytes(target), raw)
            self.assertEqual(record["bytes"], len(raw))
            self.assertEqual(record["sha256"], hashlib.sha256(raw).hexdigest())

    def _make_repo(self, root: Path) -> tuple[str, str, dict, dict]:
        run_git(root, "init")
        run_git(root, "config", "user.name", "QUAL Test")
        run_git(root, "config", "user.email", "qual-test@bopen.invalid")
        write(root / "environment.json", '{"kind":"synthetic","network":"offline"}\n')
        write(root / "evidence/inventory.json", '{"entries":[]}\n')
        for name in ("requirement", "governance", "adr", "authority"):
            write(root / f"docs/{name}.md", f"# {name}\n")
        run_git(root, "add", ".")
        run_git(root, "commit", "-m", "subject A")
        commit = run_git(root, "rev-parse", "HEAD")
        tree = run_git(root, "rev-parse", "HEAD^{tree}")
        binding = {
            "repository_ref": "bstBizEra/bopen",
            "commit_sha": commit,
            "tree_sha": tree,
            "branch_ref": "refs/heads/master",
            "dirty": False,
        }
        environment = {
            "environment_id": f"sha256:{sha256(root / 'environment.json')}",
            "manifest_ref": "environment.json",
            "manifest_sha256": sha256(root / "environment.json"),
            "os_family": "OTHER",
            "os_version": "synthetic-1",
            "architecture": "test",
            "locale": "C",
            "timezone": "UTC",
            "network_mode": "OFFLINE",
            "runner_kind": "HOST",
            "runner_image_digest": None,
            "toolchain": [
                {"name": "python", "version": "test", "executable_sha256": "1" * 64}
            ],
            "captured_at": "2026-07-21T00:00:00Z",
        }
        return commit, tree, binding, environment

    def _binding(self, root: Path, path: str, artifact_id: str, source: dict) -> dict:
        data = (root / path).read_bytes()
        return {
            "artifact_id": artifact_id,
            "path": path,
            "sha256": hashlib.sha256(data).hexdigest(),
            "byte_length": len(data),
            "media_type": "application/json",
            "canonicalization": "RAW_BYTES",
            "source_repository_binding": copy.deepcopy(source),
        }

    def _controlled(self, root: Path, name: str) -> dict:
        path = root / f"docs/{name}.md"
        return {
            "artifact_id": name.upper(),
            "version": "0.1-draft",
            "status": "Draft",
            "artifact_ref": f"docs/{name}.md",
            "sha256": sha256(path),
        }

    def _envelope(self, root: Path, binding: dict, environment: dict) -> dict:
        actor = {
            "actor_kind": "AGENT",
            "identity_ref": "AGENT-MAKER",
            "role": "Maker",
            "registration_ref": "PG-REG-AGENT-001#AGENT-MAKER",
            "session_ref": "SESSION-MAKER",
        }
        return {
            "$schema": "bopen://schemas/qualification/common/qualification-envelope/0.1.0-draft",
            "envelope_id": "QUAL-P0-00-ENV-001",
            "version": "0.1.0-draft",
            "status": "draft",
            "work_package_id": "QUAL-P0-00",
            "qualification_run_id": "QUAL-P0-00-RUN-001",
            "subject_repository_binding": copy.deepcopy(binding),
            "environment_binding": copy.deepcopy(environment),
            "provenance": {
                "generated_by": actor,
                "checked_by": None,
                "tools": [{"tool_id": "qual-validator", "version": "0.1", "sha256": "2" * 64}],
                "source_refs": ["QUAL-P0-00"],
                "created_at": "2026-07-21T00:00:00Z",
            },
            "redaction": {
                "policy_id": "BOPEN-SECRET-POLICY",
                "credential_mode": "NONE",
                "redacted_fields": [],
                "secret_scan_result": "PASS",
                "production_credentials_present": False,
                "scanner_ref": "tools/check_secrets.py",
            },
            "evidence_root": "evidence",
            "artifact_inventory_ref": self._binding(root, "evidence/inventory.json", "INVENTORY-001", binding),
            "requirement_bindings": [self._controlled(root, "requirement")],
            "governing_artifact_bindings": [self._controlled(root, "governance")],
            "adr_bindings": [self._controlled(root, "adr")],
            "authority_binding": {
                "authorization_status": "PROPOSED",
                "authority_source_ref": "docs/authority.md",
                "authority_source_sha256": sha256(root / "docs/authority.md"),
                "accepted_by": None,
                "accepted_at": None,
                "expires_at": "2026-08-21T00:00:00+07:00",
                "authority_effective": False,
            },
            "execution_scope": {
                "branch_ref": "refs/heads/codex/QUAL-P0-00-common",
                "worktree_ref": "synthetic-worktree",
                "base_repository_binding": copy.deepcopy(binding),
                "allowed_paths": ["contracts/qualification/common"],
                "prohibited_paths": ["apps", "services"],
            },
            "exception_refs": [],
            "coverage_claims": [
                {
                    "requirement_id": "PG-O1-SC",
                    "coverage_level": "DIRECT",
                    "evidence_refs": ["evidence/inventory.json"],
                    "coverage_limit": "Technical qualification evidence only",
                }
            ],
            "gate_context": {
                "gate_id": "PG-G0",
                "prerequisites": [
                    {
                        "requirement_id": "PG-GATE-G0-TEMPLATES",
                        "status": "PENDING",
                        "evidence_refs": ["evidence/inventory.json"],
                    }
                ],
                "gate_effective": False,
            },
            "created_at": "2026-07-21T00:00:00Z",
            "non_authority_flags": {key: False for key in NON_AUTHORITY_FLAGS},
        }

    def test_valid_envelope_and_fail_closed_mutations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, _, binding, environment = self._make_repo(root)
            envelope = self._envelope(root, binding, environment)
            self.assertEqual(validate_qualification_envelope(envelope, root), [])

            changed = copy.deepcopy(envelope)
            changed["non_authority_flags"]["technology_stack_frozen"] = True
            self.assertTrue(any("must be false" in item for item in validate_qualification_envelope(changed, root)))

            changed = copy.deepcopy(envelope)
            changed["redaction"]["secret_scan_result"] = "NOT_RUN"
            self.assertIn("secret scan must pass", validate_qualification_envelope(changed, root))

            changed = copy.deepcopy(envelope)
            changed["coverage_claims"][0]["evidence_refs"] = []
            self.assertTrue(any("direct coverage lacks evidence" in item for item in validate_qualification_envelope(changed, root)))

            changed = copy.deepcopy(envelope)
            changed["subject_repository_binding"]["tree_sha"] = "0" * 40
            self.assertTrue(any("commit/tree mismatch" in item for item in validate_qualification_envelope(changed, root)))

            changed = copy.deepcopy(envelope)
            changed["provenance"]["generated_by"]["unreviewed_claim"] = True
            self.assertTrue(any("unknown field: unreviewed_claim" in item for item in validate_qualification_envelope(changed, root)))

    def _receipt(self, root: Path, a_binding: dict, b_binding: dict, environment: dict) -> dict:
        maker = {
            "actor_kind": "AGENT",
            "identity_ref": "AGENT-MAKER",
            "role": "Maker",
            "registration_ref": "PG-REG-AGENT-001#AGENT-MAKER",
            "session_ref": "SESSION-MAKER",
        }
        checker = {
            "actor_kind": "AGENT",
            "identity_ref": "AGENT-CHECKER",
            "role": "Checker",
            "registration_ref": "PG-REG-AGENT-001#AGENT-CHECKER",
            "session_ref": "SESSION-CHECKER",
        }
        receipt = {
            "$schema": "bopen://schemas/qualification/common/checker-receipt/0.1.0-draft",
            "checker_receipt_id": "QUAL-P0-00-RECEIPT-001",
            "version": "0.1.0-draft",
            "status": "draft",
            "work_package_id": "QUAL-P0-00",
            "qualification_run_id": "QUAL-P0-00-RUN-001",
            "reviewed_subject_binding": copy.deepcopy(a_binding),
            "reviewed_evidence_binding": copy.deepcopy(b_binding),
            "storage_parent_binding": copy.deepcopy(b_binding),
            "scorecard_binding": self._binding(root, "evidence/scorecard.json", "SCORECARD-001", b_binding),
            "inventory_binding": self._binding(root, "evidence/inventory.json", "INVENTORY-001", b_binding),
            "environment_binding": copy.deepcopy(environment),
            "maker": maker,
            "checker": checker,
            "independence_asserted": True,
            "checks": [
                {"check_id": "CHECK-001", "required": True, "result": "PASS", "evidence_refs": ["evidence/scorecard.json"], "reason_code": "PASS"}
            ],
            "findings": [],
            "coverage_verdicts": [
                {"requirement_id": "PG-O1-SC", "verdict": "PASS", "evidence_refs": ["evidence/scorecard.json"]}
            ],
            "specialist_domains": ["GOVERNANCE"],
            "scope_complete": False,
            "unresolved_high_or_critical_count": 0,
            "verdict": "ACCEPT_EXACT_SHA",
            "reason_codes": ["TECHNICAL_ACCEPTANCE_ONLY"],
            "reviewed_at": "2026-07-21T01:00:00Z",
            "receipt_payload_sha256": "0" * 64,
            "non_authority_flags": {key: False for key in NON_AUTHORITY_FLAGS},
        }
        receipt["receipt_payload_sha256"] = canonical_payload_sha256(receipt, "receipt_payload_sha256")
        return receipt

    def test_a_b_c_lineage_and_receipt_independence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a_commit, _, a_binding, environment = self._make_repo(root)
            write(root / "evidence/scorecard.json", '{"candidate":"synthetic"}\n')
            write(root / "evidence/inventory.json", '{"entries":["scorecard"]}\n')
            run_git(root, "add", "evidence")
            run_git(root, "commit", "-m", "evidence B")
            b_commit = run_git(root, "rev-parse", "HEAD")
            b_binding = {
                **a_binding,
                "commit_sha": b_commit,
                "tree_sha": run_git(root, "rev-parse", "HEAD^{tree}"),
            }
            receipt = self._receipt(root, a_binding, b_binding, environment)
            receipt_path = "evidence/checker-receipt.json"
            write(root / receipt_path, json.dumps(receipt, indent=2) + "\n")
            run_git(root, "add", receipt_path)
            run_git(root, "commit", "-m", "receipt C")
            c_commit = run_git(root, "rev-parse", "HEAD")
            self.assertEqual(validate_checker_receipt(receipt, root, c_commit, receipt_path), [])

            self.assertIn(
                "terminal receipt requires external storage commit and path",
                validate_checker_receipt(receipt, root),
            )

            changed = copy.deepcopy(receipt)
            changed["checker"] = copy.deepcopy(changed["maker"])
            changed["receipt_payload_sha256"] = canonical_payload_sha256(changed, "receipt_payload_sha256")
            self.assertTrue(any("independence" in item for item in validate_checker_receipt(changed, root)))

            changed = copy.deepcopy(receipt)
            changed["checks"][0]["result"] = "NOT_RUN"
            changed["receipt_payload_sha256"] = canonical_payload_sha256(changed, "receipt_payload_sha256")
            self.assertTrue(any("required check not evidenced" in item for item in validate_checker_receipt(changed, root)))

            changed = copy.deepcopy(receipt)
            changed["checks"][0]["override"] = "ALLOW"
            changed["receipt_payload_sha256"] = canonical_payload_sha256(changed, "receipt_payload_sha256")
            self.assertTrue(any("unknown field: override" in item for item in validate_checker_receipt(changed, root)))

    def test_receipt_rejects_non_direct_or_multi_file_storage_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, _, a_binding, environment = self._make_repo(root)
            write(root / "evidence/scorecard.json", "{}\n")
            write(root / "evidence/inventory.json", "{}\n")
            run_git(root, "add", "evidence")
            run_git(root, "commit", "-m", "evidence B")
            b_binding = {
                **a_binding,
                "commit_sha": run_git(root, "rev-parse", "HEAD"),
                "tree_sha": run_git(root, "rev-parse", "HEAD^{tree}"),
            }
            receipt = self._receipt(root, a_binding, b_binding, environment)
            path = "evidence/checker-receipt.json"
            write(root / path, json.dumps(receipt, indent=2) + "\n")
            write(root / "evidence/extra.txt", "scope violation\n")
            run_git(root, "add", "evidence")
            run_git(root, "commit", "-m", "invalid receipt C")
            errors = validate_checker_receipt(receipt, root, run_git(root, "rev-parse", "HEAD"), path)
        self.assertTrue(any("must add only" in item for item in errors))

    def test_a_b_c_chain_rejects_merge_evidence_and_merge_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a_commit, _, _, _ = self._make_repo(root)
            primary = run_git(root, "branch", "--show-current")
            run_git(root, "checkout", "-b", "side-b")
            write(root / "side-b.txt", "side\n")
            run_git(root, "add", "side-b.txt")
            run_git(root, "commit", "-m", "side B")
            run_git(root, "checkout", primary)
            write(root / "evidence-b.txt", "evidence\n")
            run_git(root, "add", "evidence-b.txt")
            run_git(root, "commit", "-m", "linear evidence")
            run_git(root, "merge", "--no-ff", "side-b", "-m", "merge evidence B")
            merge_b = run_git(root, "rev-parse", "HEAD")
            write(root / "receipt-c.txt", "receipt\n")
            run_git(root, "add", "receipt-c.txt")
            run_git(root, "commit", "-m", "receipt C")
            c_commit = run_git(root, "rev-parse", "HEAD")
            merge_b_errors = validate_direct_parent_chain(root, a_commit, merge_b, c_commit)

        self.assertTrue(any("evidence must have exactly one parent" in item for item in merge_b_errors))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a_commit, _, _, _ = self._make_repo(root)
            primary = run_git(root, "branch", "--show-current")
            write(root / "evidence-b.txt", "evidence\n")
            run_git(root, "add", "evidence-b.txt")
            run_git(root, "commit", "-m", "evidence B")
            b_commit = run_git(root, "rev-parse", "HEAD")
            run_git(root, "checkout", "-b", "side-c")
            write(root / "side-c.txt", "side\n")
            run_git(root, "add", "side-c.txt")
            run_git(root, "commit", "-m", "side C")
            run_git(root, "checkout", primary)
            write(root / "receipt-c.txt", "receipt\n")
            run_git(root, "add", "receipt-c.txt")
            run_git(root, "commit", "-m", "linear receipt")
            run_git(root, "merge", "--no-ff", "side-c", "-m", "merge receipt C")
            merge_c = run_git(root, "rev-parse", "HEAD")
            merge_c_errors = validate_direct_parent_chain(root, a_commit, b_commit, merge_c)

        self.assertTrue(any("receipt must have exactly one parent" in item for item in merge_c_errors))


if __name__ == "__main__":
    unittest.main()
