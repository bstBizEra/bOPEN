"""Adversarial tests for the draft TECH-P0-01 technology qualification contracts."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.validate_qualification_common import NON_AUTHORITY_FLAGS, sha256_file
from tools.validate_technology_qualification import (
    COMMON_CATALOG,
    COMMON_CATALOG_SHA256,
    PACKAGE_PATHS,
    PROGRAM_GOAL,
    ROOT,
    build_package_manifest,
    program_goal_ids,
    validate_case_result,
    validate_command_evidence,
    validate_inventory,
    validate_package,
    validate_scorecard,
)


def false_flags() -> dict[str, bool]:
    return {name: False for name in NON_AUTHORITY_FLAGS}


def digest_binding(path: str = "artifacts/qualification/example.txt") -> dict:
    return {
        "artifact_id": "TECH-ART-001",
        "path": path,
        "sha256": "0" * 64,
        "byte_length": 0,
        "media_type": "text/plain",
        "canonicalization": "RAW_BYTES",
        "source_repository_binding": None,
    }


class TechnologyQualificationTests(unittest.TestCase):
    def make_cases(self) -> list[dict]:
        categories = [
            "TENANT_RLS_NEGATIVE",
            "TENANT_POOL_NEGATIVE",
            "TENANT_CONTEXT_NEGATIVE",
            "OBSERVABILITY",
            "OUTBOX",
            "RECOVERY",
            "SUPPLY_CHAIN",
        ]
        cases = []
        for index, category in enumerate(categories, 1):
            cases.append(
                {
                    "$schema": "bopen://schemas/qualification/technology/case-result/0.1.0-draft",
                    "case_id": f"TECH-CASE-{index:03d}",
                    "version": "0.1.0-draft",
                    "status": "draft",
                    "work_package_id": "TECH-P0-01",
                    "qualification_run_id": "TECH-RUN-001",
                    "candidate_id": "TECH-CAND-001",
                    "category": category,
                    "mandatory": True,
                    "result": "PASS",
                    "requirement_ids": ["PG-GOAL-OBJ"],
                    "command_evidence_refs": [f"artifacts/qualification/case-{index}/command.json"],
                    "artifact_refs": [digest_binding(f"artifacts/qualification/case-{index}/result.txt")],
                    "negative_case": category.startswith("TENANT_"),
                    "limitation": "Synthetic proposal evidence only; no production conclusion.",
                    "non_authority_flags": false_flags(),
                }
            )
        return cases

    def make_scorecard(self, cases: list[dict]) -> dict:
        case_ids = [case["case_id"] for case in cases]
        coverage = [
            {
                "requirement_id": requirement_id,
                "coverage_level": "PARTIAL",
                "case_ids": [],
                "coverage_limit": "Contract mapping only; no qualification or gate conclusion.",
            }
            for requirement_id in sorted(program_goal_ids())
        ]
        return {
            "$schema": "bopen://schemas/qualification/technology/candidate-scorecard/0.1.0-draft",
            "scorecard_id": "TECH-SCORE-001",
            "version": "0.1.0-draft",
            "status": "draft",
            "work_package_id": "TECH-P0-01",
            "qualification_run_id": "TECH-RUN-001",
            "candidate_id": "TECH-CAND-001",
            "candidate_name": "Synthetic Candidate",
            "vendor_disposition": "UNDECIDED",
            "common_catalog_binding": {
                **digest_binding(COMMON_CATALOG.as_posix()),
                "sha256": COMMON_CATALOG_SHA256,
                "byte_length": (ROOT / COMMON_CATALOG).stat().st_size,
                "media_type": "application/json",
            },
            "program_goal_catalog_binding": {
                **digest_binding(PROGRAM_GOAL.as_posix()),
                "sha256": sha256_file(ROOT / PROGRAM_GOAL),
                "byte_length": (ROOT / PROGRAM_GOAL).stat().st_size,
                "media_type": "application/json",
            },
            "mandatory_criteria": [
                {
                    "criterion_id": "MAND-CORE",
                    "case_ids": case_ids,
                    "requirement_ids": ["PG-GOAL-OBJ"],
                    "result": "PASS",
                    "failure_reason": None,
                }
            ],
            "weighted_criteria": [
                {
                    "criterion_id": "WEIGHT-FIT",
                    "weight": 100,
                    "score": 80,
                    "case_ids": case_ids,
                    "limitation": "Synthetic comparison only.",
                }
            ],
            "program_goal_coverage": coverage,
            "weighted_score": 80,
            "recommendation": "PROPOSAL_ONLY",
            "limitations": ["No stack approval, freeze, vendor selection, release or runtime authority."],
            "non_authority_flags": false_flags(),
        }

    def materialize_evidence(self, root: Path, cases: list[dict]) -> dict:
        for relative in (COMMON_CATALOG, PROGRAM_GOAL):
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)
        records = []

        def create_artifact(path: str, payload: bytes, artifact_id: str) -> dict:
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            binding = digest_binding(path)
            binding["artifact_id"] = artifact_id
            binding["sha256"] = hashlib.sha256(payload).hexdigest()
            binding["byte_length"] = len(payload)
            records.append(binding)
            return binding

        for index, case in enumerate(cases, 1):
            case["artifact_refs"] = [
                create_artifact(
                    f"artifacts/qualification/case-{index}/result.txt",
                    f"case-{index}-result\n".encode(),
                    f"TECH-CASE-{index:03d}-RESULT",
                )
            ]
            command_artifacts = {
                "stdout_artifact": create_artifact(
                    f"artifacts/qualification/case-{index}/stdout.txt",
                    b"synthetic stdout\n",
                    f"TECH-CASE-{index:03d}-STDOUT",
                ),
                "stderr_artifact": create_artifact(
                    f"artifacts/qualification/case-{index}/stderr.txt",
                    b"",
                    f"TECH-CASE-{index:03d}-STDERR",
                ),
                "environment_manifest": create_artifact(
                    f"artifacts/qualification/case-{index}/environment.json",
                    b"{\"synthetic\":true}\n",
                    f"TECH-CASE-{index:03d}-ENV",
                ),
            }
            command = {
                "$schema": "bopen://schemas/qualification/technology/command-evidence/0.1.0-draft",
                "command_evidence_id": f"TECH-CMD-{index:03d}",
                "version": "0.1.0-draft",
                "status": "draft",
                "work_package_id": "TECH-P0-01",
                "qualification_run_id": case["qualification_run_id"],
                "candidate_id": case["candidate_id"],
                "case_id": case["case_id"],
                "argv": ["python", "-m", "unittest"],
                "working_directory": "worktrees/qualification",
                "started_at": "2026-07-22T00:00:00+07:00",
                "completed_at": "2026-07-22T00:01:00+07:00",
                "exit_code": 0,
                **command_artifacts,
                "secret_scan_passed": True,
                "synthetic_data_only": True,
                "deterministic_replay": True,
                "non_authority_flags": false_flags(),
            }
            command_path = root / case["command_evidence_refs"][0]
            command_path.parent.mkdir(parents=True, exist_ok=True)
            command_path.write_text(json.dumps(command, indent=2) + "\n", encoding="utf-8")

        return {
            "$schema": "bopen://schemas/qualification/technology/artifact-digest-inventory/0.1.0-draft",
            "inventory_id": "TECH-INV-001",
            "version": "0.1.0-draft",
            "status": "draft",
            "work_package_id": "TECH-P0-01",
            "qualification_run_id": "TECH-RUN-001",
            "generated_at": "2026-07-22T00:00:00+07:00",
            "raw_bytes": True,
            "records": records,
            "non_authority_flags": false_flags(),
        }

    def test_catalog_and_program_goal_are_pinned_offline(self):
        self.assertEqual(validate_package(), [])
        self.assertEqual(len(program_goal_ids()), 242)
        self.assertEqual(sha256_file(ROOT / COMMON_CATALOG), COMMON_CATALOG_SHA256)

    def test_complete_proposal_scorecard_passes_semantics(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases = self.make_cases()
            inventory = self.materialize_evidence(Path(tmp), cases)
            self.assertEqual(validate_scorecard(self.make_scorecard(cases), cases, Path(tmp), inventory), [])

    def test_mandatory_failure_stops_before_weighted_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = self.make_cases()
            cases[0]["result"] = "FAIL"
            inventory = self.materialize_evidence(root, cases)
            scorecard = self.make_scorecard(cases)
            scorecard["mandatory_criteria"][0]["result"] = "FAIL"
            errors = validate_scorecard(scorecard, cases, root, inventory)
            self.assertIn("mandatory failure must stop before weighted score", errors)
            self.assertIn("mandatory failure must leave weighted criterion scores null", errors)
            self.assertIn("mandatory failure requires NOT_QUALIFIED", errors)

            scorecard["weighted_score"] = None
            scorecard["weighted_criteria"][0]["score"] = None
            scorecard["recommendation"] = "NOT_QUALIFIED"
            self.assertEqual(validate_scorecard(scorecard, cases, root, inventory), [])

            lying = self.make_scorecard(cases)
            lying["mandatory_criteria"][0]["result"] = "PASS"
            self.assertIn(
                "mandatory criterion result mismatch: MAND-CORE",
                validate_scorecard(lying, cases, root, inventory),
            )

    def test_program_goal_coverage_is_complete_unique_and_limited(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = self.make_cases()
            inventory = self.materialize_evidence(root, cases)
            scorecard = self.make_scorecard(cases)
            scorecard["program_goal_coverage"].pop()
            self.assertIn(
                "Program Goal coverage must include every catalog item exactly once",
                validate_scorecard(scorecard, cases, root, inventory),
            )
            scorecard = self.make_scorecard(cases)
            scorecard["program_goal_coverage"][0]["coverage_limit"] = ""
            self.assertIn(
                "every Program Goal coverage item requires an explicit limit",
                validate_scorecard(scorecard, cases, root, inventory),
            )

    def test_tenant_negative_declarations_fail_closed(self):
        for field in ("negative_case", "mandatory"):
            case = self.make_cases()[0]
            case[field] = False
            self.assertTrue(
                any("must be declared mandatory negative case" in error for error in validate_case_result(case))
            )

    def test_operational_and_supply_chain_cases_require_evidence(self):
        for case in self.make_cases()[3:]:
            case["command_evidence_refs"] = []
            case["artifact_refs"] = []
            errors = validate_case_result(case)
            self.assertTrue(any("requires command and artifact evidence" in error for error in errors))

    def test_command_evidence_requires_safe_replay_declarations(self):
        command = {
            "$schema": "bopen://schemas/qualification/technology/command-evidence/0.1.0-draft",
            "command_evidence_id": "TECH-CMD-001",
            "version": "0.1.0-draft",
            "status": "draft",
            "work_package_id": "TECH-P0-01",
            "qualification_run_id": "TECH-RUN-001",
            "candidate_id": "TECH-CAND-001",
            "case_id": "TECH-CASE-001",
            "argv": ["python", "-m", "unittest"],
            "working_directory": "worktrees/qualification",
            "started_at": "2026-07-22T00:00:00+07:00",
            "completed_at": "2026-07-22T00:01:00+07:00",
            "exit_code": 0,
            "stdout_artifact": digest_binding(),
            "stderr_artifact": digest_binding(),
            "environment_manifest": digest_binding(),
            "secret_scan_passed": True,
            "synthetic_data_only": True,
            "deterministic_replay": True,
            "non_authority_flags": false_flags(),
        }
        self.assertEqual(validate_command_evidence(command), [])
        command["secret_scan_passed"] = False
        command["deterministic_replay"] = False
        errors = validate_command_evidence(command)
        self.assertIn("command evidence secret_scan_passed must be true", errors)
        self.assertIn("command evidence deterministic_replay must be true", errors)

    def test_vendor_and_authority_claims_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = self.make_cases()
            inventory = self.materialize_evidence(root, cases)
            scorecard = self.make_scorecard(cases)
            scorecard["vendor_disposition"] = "SELECTED"
            scorecard["non_authority_flags"]["technology_stack_frozen"] = True
            errors = validate_scorecard(scorecard, cases, root, inventory)
            self.assertIn("scorecard cannot select a vendor", errors)
            self.assertIn("scorecard flags technology_stack_frozen must be false", errors)

    def test_command_refs_reject_traversal_and_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = self.make_cases()
            inventory = self.materialize_evidence(root, cases)
            scorecard = self.make_scorecard(cases)
            cases[0]["command_evidence_refs"] = ["../outside.json"]
            errors = validate_scorecard(scorecard, cases, root, inventory)
            self.assertTrue(any("command evidence ref 0 invalid" in error for error in errors))
            self.assertTrue(any("command evidence missing or invalid" in error for error in errors))

            cases = self.make_cases()
            inventory = self.materialize_evidence(root, cases)
            (root / cases[0]["command_evidence_refs"][0]).unlink()
            self.assertTrue(
                any(
                    "command evidence missing or invalid" in error
                    for error in validate_scorecard(self.make_scorecard(cases), cases, root, inventory)
                )
            )

    def test_command_binding_and_artifact_inventory_reconciliation(self):
        for field, value in (
            ("qualification_run_id", "TECH-RUN-999"),
            ("candidate_id", "TECH-CAND-999"),
            ("case_id", "TECH-CASE-999"),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                cases = self.make_cases()
                inventory = self.materialize_evidence(root, cases)
                command_path = root / cases[0]["command_evidence_refs"][0]
                command = json.loads(command_path.read_text(encoding="utf-8"))
                command[field] = value
                command_path.write_text(json.dumps(command) + "\n", encoding="utf-8")
                errors = validate_scorecard(self.make_scorecard(cases), cases, root, inventory)
                self.assertTrue(any("command evidence binding mismatch" in error for error in errors))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = self.make_cases()
            inventory = self.materialize_evidence(root, cases)
            cases[0]["artifact_refs"][0] = {}
            errors = validate_scorecard(self.make_scorecard(cases), cases, root, inventory)
            self.assertTrue(any("malformed" in error or "missing field" in error for error in errors))

            cases = self.make_cases()
            inventory = self.materialize_evidence(root, cases)
            inventory["records"].pop(0)
            errors = validate_scorecard(self.make_scorecard(cases), cases, root, inventory)
            self.assertTrue(any("not reconciled with inventory" in error for error in errors))

    def test_direct_coverage_requires_relevant_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = self.make_cases()
            inventory = self.materialize_evidence(root, cases)
            scorecard = self.make_scorecard(cases)
            direct = next(
                item for item in scorecard["program_goal_coverage"]
                if item["requirement_id"] != "PG-GOAL-OBJ"
            )
            direct["coverage_level"] = "DIRECT"
            direct["case_ids"] = [cases[0]["case_id"]]
            self.assertIn(
                f"DIRECT coverage lacks a relevant case: {direct['requirement_id']}",
                validate_scorecard(scorecard, cases, root, inventory),
            )

    def test_inventory_verifies_exact_raw_bytes_and_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "artifacts/qualification/result.txt"
            artifact.parent.mkdir(parents=True)
            artifact.write_bytes(b"line-one\r\nline-two\r\n")
            raw = artifact.read_bytes()
            record = digest_binding("artifacts/qualification/result.txt")
            record["sha256"] = hashlib.sha256(raw).hexdigest()
            record["byte_length"] = len(raw)
            inventory = {
                "$schema": "bopen://schemas/qualification/technology/artifact-digest-inventory/0.1.0-draft",
                "inventory_id": "TECH-INV-001",
                "version": "0.1.0-draft",
                "status": "draft",
                "work_package_id": "TECH-P0-01",
                "qualification_run_id": "TECH-RUN-001",
                "generated_at": "2026-07-22T00:00:00+07:00",
                "raw_bytes": True,
                "records": [record],
                "non_authority_flags": false_flags(),
            }
            self.assertEqual(validate_inventory(inventory, root), [])
            inventory["records"][0]["byte_length"] -= 1
            self.assertIn("inventory record 0 byte length mismatch", validate_inventory(inventory, root))
            inventory["records"][0]["path"] = "../outside.txt"
            self.assertIn("inventory record 0 path missing or invalid", validate_inventory(inventory, root))

    def test_package_manifest_hashes_unmodified_file_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in PACKAGE_PATHS:
                source = ROOT / relative
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            target = root / "docs/work-packages/TECH-P0-01.md"
            target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))
            raw = target.read_bytes()
            record = next(
                item for item in build_package_manifest(root)["records"]
                if item["path"] == "docs/work-packages/TECH-P0-01.md"
            )
            self.assertEqual(record["bytes"], len(raw))
            self.assertEqual(record["sha256"], hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    unittest.main()
