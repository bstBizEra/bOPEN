"""Fail-closed tests for the governed GOV-P0-01 program-control registers."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tools.validate_program_controls import validate_program_controls


ROOT = Path(__file__).resolve().parents[2]
AS_OF = datetime(2026, 7, 21, 12, 0, 0, tzinfo=timezone.utc)


class ProgramControlValidationTests(unittest.TestCase):
    def make_root(self, temporary: str) -> Path:
        root = Path(temporary)
        for relative in (
            "contracts/governance",
            "docs/00-governance/registers",
            "docs/decisions",
            "docs/adr",
        ):
            shutil.copytree(ROOT / relative, root / relative)
        return root

    def load_register(self, root: Path, name: str) -> dict:
        return json.loads(
            (root / "docs/00-governance/registers" / name).read_text(encoding="utf-8")
        )

    def save_register(self, root: Path, name: str, value: dict) -> None:
        (root / "docs/00-governance/registers" / name).write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8"
        )

    def test_repository_approved_registers_validate_without_claiming_runtime_readiness(self):
        self.assertEqual(validate_program_controls(ROOT, AS_OF), [])
        schedule = self.load_register(ROOT, "SCHEDULE-REGISTER.json")
        for name in (
            "AGENT-REGISTER.json", "GOAL-REGISTER.json", "MODULE-REGISTER.json",
            "SKILL-REGISTER.json", "SCHEDULE-REGISTER.json", "AUTHORITY-MATRIX.json",
            "TECHNOLOGY-DECISION-ASSIGNMENTS.json",
        ):
            register = self.load_register(ROOT, name)
            self.assertEqual(register["status"], "approved")
            self.assertEqual(register["approved_by"], "HUMAN-OPERATOR-001")
            self.assertIn("SIGNING-PASS-2.md#append-only-batch-2-signing-record", register["approval_ref"])
        self.assertEqual(schedule["entries"][0]["status"], "COMPLETE")
        self.assertEqual(schedule["entries"][1]["status"], "ACTIVE")
        self.assertEqual(schedule["entries"][1]["work_item_refs"], ["SKEL-P0-01"])
        self.assertIn("SIGNING-PASS-5.md#signed-decision", schedule["entries"][1]["rebaseline_decision_ref"])
        self.assertTrue(all(item["status"] == "NOT_READY" for item in schedule["entries"][2:]))
        self.assertEqual(self.load_register(ROOT, "AGENT-REGISTER.json")["entries"], [])
        self.assertEqual(self.load_register(ROOT, "MODULE-REGISTER.json")["entries"], [])
        self.assertEqual(self.load_register(ROOT, "SKILL-REGISTER.json")["entries"], [])

    def test_active_pg_p0_fails_closed_without_signed_opening_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            register = self.load_register(root, "SCHEDULE-REGISTER.json")
            register["entries"][1]["evidence_refs"] = []
            self.save_register(root, "SCHEDULE-REGISTER.json", register)
            errors = validate_program_controls(root, AS_OF)
        self.assertTrue(any("ACTIVE PG-P0 SIGNING-PASS-5" in error for error in errors))

    def test_missing_and_unknown_fields_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            register = self.load_register(root, "GOAL-REGISTER.json")
            del register["entries"][0]["title"]
            register["entries"][0]["uncontrolled_claim"] = True
            self.save_register(root, "GOAL-REGISTER.json", register)
            errors = validate_program_controls(root, AS_OF)
        self.assertTrue(any("FIELD MISSING" in error and "title" in error for error in errors))
        self.assertTrue(any("UNKNOWN FIELD" in error and "uncontrolled_claim" in error for error in errors))

    def test_approved_register_without_approval_provenance_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            register = self.load_register(root, "AGENT-REGISTER.json")
            register.pop("approved_by")
            register.pop("approved_at")
            register.pop("approval_ref")
            self.save_register(root, "AGENT-REGISTER.json", register)
            errors = validate_program_controls(root, AS_OF)
        self.assertTrue(
            any("APPROVED REGISTER LACKS APPROVAL PROVENANCE" in error for error in errors)
        )

    def test_fully_provenanced_approved_register_set_is_schema_compatible(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            for name in (
                "AGENT-REGISTER.json",
                "GOAL-REGISTER.json",
                "MODULE-REGISTER.json",
                "SKILL-REGISTER.json",
                "SCHEDULE-REGISTER.json",
                "AUTHORITY-MATRIX.json",
                "TECHNOLOGY-DECISION-ASSIGNMENTS.json",
            ):
                register = self.load_register(root, name)
                register.update(
                    {
                        "version": "0.2.0" if name == "AUTHORITY-MATRIX.json" else "0.1.0",
                        "status": "approved",
                        "approved_by": "Independent Human Authority",
                        "approved_at": "2026-07-21T11:00:00Z",
                        "approval_ref": "DEC-GOV-P0-01-APPROVAL",
                    }
                )
                if name == "AUTHORITY-MATRIX.json":
                    for entry in register["entries"]:
                        entry["status"] = "approved"
                self.save_register(root, name, register)
            errors = validate_program_controls(root, AS_OF)
        self.assertEqual(errors, [])

    def test_ambiguous_bare_phase_identifier_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            register = self.load_register(root, "SCHEDULE-REGISTER.json")
            register["entries"][1]["phase_id"] = "P0"
            self.save_register(root, "SCHEDULE-REGISTER.json", register)
            errors = validate_program_controls(root, AS_OF)
        self.assertTrue(any("AMBIGUOUS PROGRAM PHASE IDENTIFIER" in error for error in errors))

    def test_active_agent_expiry_self_review_and_scope_overlap_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            register = self.load_register(root, "AGENT-REGISTER.json")
            common = {
                "harness": "Codex",
                "role_id": "QA & Evidence Agent",
                "status": "ACTIVE",
                "owner_authority": "Engineering Authority",
                "prohibited_authorities": ["self_approval"],
                "credential_mode": "SECRET_REFERENCE_ONLY",
                "registered_at": "2026-07-21T00:00:00Z",
                "review_due_at": "2026-08-01T00:00:00Z",
            }
            register["entries"] = [
                {
                    **common,
                    "agent_id": "AGT-MAKER",
                    "display_name": "Maker",
                    "allowed_scope_paths": ["docs/00-governance"],
                    "expires_at": "2026-07-20T00:00:00Z",
                    "maker_work_item_ids": ["GOV-P0-01"],
                    "checker_work_item_ids": ["GOV-P0-01"],
                },
                {
                    **common,
                    "agent_id": "AGT-CHECKER",
                    "display_name": "Checker",
                    "allowed_scope_paths": ["docs/00-governance/registers"],
                    "expires_at": "2026-08-01T00:00:00Z",
                    "maker_work_item_ids": [],
                    "checker_work_item_ids": ["GOV-P0-01"],
                },
            ]
            self.save_register(root, "AGENT-REGISTER.json", register)
            errors = validate_program_controls(root, AS_OF)
        self.assertTrue(any("SELF REVIEW PROHIBITED" in error for error in errors))
        self.assertTrue(any("EXPIRES_AT INVALID" in error for error in errors))
        self.assertTrue(any("SCOPE OVERLAP" in error for error in errors))

    def test_certified_module_without_prerequisites_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            register = self.load_register(root, "MODULE-REGISTER.json")
            register["entries"] = [{
                "module_id":"bopen.platform.example","name":"Example","module_class":"PLATFORM",
                "lifecycle_state":"ACTIVE","owner_authority":"Architecture Authority",
                "contract_ref":None,"dependency_ids":[],"capability_refs":[],"permission_refs":[],
                "entitlement_refs":[],"isolation_evidence_refs":[],"test_evidence_refs":[],
                "runbook_ref":None,"independent_acceptance_ref":None,
                "certification_state":"CERTIFIED","pilot_state":"NOT_REQUESTED","expires_at":None
            }]
            self.save_register(root, "MODULE-REGISTER.json", register)
            errors = validate_program_controls(root, AS_OF)
        self.assertTrue(any("MODULE CERTIFICATION PREREQUISITES MISSING" in error for error in errors))

    def test_schedule_cycle_and_missing_reference_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            register = self.load_register(root, "SCHEDULE-REGISTER.json")
            register["entries"][0]["depends_on"] = ["PG-C0"]
            register["entries"][2]["depends_on"] = ["PG-P0", "PG-MISSING"]
            self.save_register(root, "SCHEDULE-REGISTER.json", register)
            errors = validate_program_controls(root, AS_OF)
        self.assertTrue(any("SCHEDULE DEPENDENCY CYCLE DETECTED" in error for error in errors))
        self.assertTrue(any("SCHEDULE DEPENDENCY MISSING" in error for error in errors))

    def test_self_approval_and_unassigned_technology_review_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            authority = self.load_register(root, "AUTHORITY-MATRIX.json")
            authority["entries"][0]["self_approval_allowed"] = True
            self.save_register(root, "AUTHORITY-MATRIX.json", authority)
            technology = self.load_register(root, "TECHNOLOGY-DECISION-ASSIGNMENTS.json")
            technology["entries"][0]["status"] = "READY_FOR_REVIEW"
            technology["entries"][0]["checker_authorities"] = []
            technology["entries"][0]["due_at"] = None
            self.save_register(root, "TECHNOLOGY-DECISION-ASSIGNMENTS.json", technology)
            errors = validate_program_controls(root, AS_OF)
        self.assertTrue(any("AUTHORITY SELF APPROVAL PROHIBITED" in error for error in errors))
        self.assertTrue(any("TECHNOLOGY ASSIGNMENT REVIEW CONTROLS MISSING" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
