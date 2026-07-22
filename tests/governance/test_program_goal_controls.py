import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.report_program_g0 import (
    CATALOG_PATH,
    CERTIFICATION_CONDITION_IDS,
    EXPECTED_FAMILY_COUNTS,
    EXPECTED_TYPE_COUNTS,
    REGISTER_IDS,
    build_report,
    certified_module_enablement_rate,
    check_report,
    format_report,
    is_module_certified,
    validate_catalog,
)
from tools.validate_program_controls import validate_program_controls


ROOT = Path(__file__).resolve().parents[2]


class ProgramGoalControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / CATALOG_PATH).read_text(encoding="utf-8"))
        cls.items = {item["id"]: item for item in cls.catalog["items"]}

    def test_catalog_is_source_complete_and_non_authorizing(self):
        self.assertEqual(validate_catalog(self.catalog), [])
        self.assertEqual(len(self.catalog["items"]), 242)
        self.assertEqual(len(self.items), 242)
        self.assertEqual(self.catalog["status"], "draft")
        self.assertFalse(self.catalog["implementation_authority"])
        self.assertFalse(self.catalog["gate_promotion_authority"])
        self.assertFalse(self.catalog["release_authority"])
        self.assertEqual(
            self.catalog["source"]["sha256"],
            "e9ef66ba78ebc656dd613b835fabd568bff50ac2932ab07278b91526ac2125c0",
        )

    def test_committed_readiness_report_matches_deterministic_output(self):
        expected = format_report(build_report(ROOT))
        report_path = ROOT / "artifacts/validation/program-g0-readiness.md"
        self.assertEqual(check_report(report_path, expected), [])

    def test_missing_or_stale_readiness_report_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            report_path = Path(temporary) / "program-g0-readiness.md"
            missing_errors = check_report(report_path, "expected\n")
            self.assertTrue(any("missing" in item for item in missing_errors))
            report_path.write_text("stale\n", encoding="utf-8")
            stale_errors = check_report(report_path, "expected\n")
            self.assertTrue(any("stale" in item for item in stale_errors))

    def test_required_type_and_id_families_are_complete(self):
        type_counts = {}
        for item in self.catalog["items"]:
            type_counts[item["type"]] = type_counts.get(item["type"], 0) + 1
        self.assertEqual(type_counts, EXPECTED_TYPE_COUNTS)
        for prefix, expected in EXPECTED_FAMILY_COUNTS.items():
            with self.subTest(prefix=prefix):
                self.assertEqual(
                    sum(item_id.startswith(prefix) for item_id in self.items),
                    expected,
                )

    def test_exact_program_targets_are_preserved(self):
        self.assertEqual(
            self.items["PG-NS-FORMULA"]["target"],
            "(certified_pilot_modules / submitted_pilot_modules) * 100",
        )
        self.assertEqual(
            self.items["PG-NS-TARGET-P2"]["target"],
            "At least 1 certified platform module",
        )
        self.assertEqual(
            self.items["PG-NS-TARGET-P3"]["target"],
            "At least 3 certified shared foundation modules",
        )
        self.assertEqual(
            self.items["PG-NS-TARGET-P4"]["target"],
            "At least 1 complete product composition and 5 certified modules",
        )
        self.assertEqual(
            self.items["PG-NS-TARGET-POST-P4"]["target"],
            "≥90% of eligible modules reach pilot without platform-kernel modification",
        )
        self.assertEqual(
            self.items["PG-O4-IND-04"]["target"],
            {"P2": "≥90%", "Post-P4": "≥98%"},
        )
        self.assertEqual(
            self.items["PG-O4-IND-05"]["target"],
            {"P2": "≤10 business days", "Post-P4": "≤5 business days"},
        )
        self.assertEqual(
            self.items["PG-O6-IND-03"]["target"],
            {"P0/P1": "≥99%", "Pilot": "≥99.5%"},
        )
        self.assertEqual(self.items["PG-O6-SLO-P95-LATENCY"]["target"], "≤500 ms")
        self.assertEqual(self.items["PG-O6-SLO-RPO"]["target"], "≤24 hours")
        self.assertEqual(self.items["PG-O6-SLO-RTO"]["target"], "≤8 hours")

    def test_lifecycle_ids_are_unambiguous_and_outcome_scoped(self):
        module_ids = {
            item["id"]
            for item in self.catalog["items"]
            if item["type"] == "module_lifecycle_stage"
        }
        learning_ids = {
            item["id"]
            for item in self.catalog["items"]
            if item["type"] == "learning_lifecycle_stage"
        }
        self.assertEqual(len(module_ids), 9)
        self.assertEqual(len(learning_ids), 8)
        self.assertTrue(all(item_id.startswith("PG-O4-LC-") for item_id in module_ids))
        self.assertTrue(all(item_id.startswith("PG-O8-LC-") for item_id in learning_ids))
        self.assertTrue(module_ids.isdisjoint(learning_ids))

    def test_catalog_never_defaults_an_item_to_passed(self):
        forbidden = {"pass", "passed", "approved", "certified"}
        for item in self.catalog["items"]:
            with self.subTest(item=item["id"]):
                self.assertNotIn(item["disposition"].casefold(), forbidden)
                self.assertIn(
                    item["coverage_classification"],
                    {
                        "evidenced",
                        "draft_only",
                        "placeholder",
                        "missing",
                        "future_evidence",
                    },
                )

    def test_repository_controls_are_not_overstated_as_program_evidence(self):
        formerly_overbroad = {
            "PG-O1-IND-06",
            "PG-O1-IND-07",
            "PG-O7-IND-07",
            "PG-O7-IND-10",
            "PG-GATE-P0-REPOSITORY-CI",
        }
        self.assertFalse(
            any(
                item["coverage_classification"] == "evidenced"
                for item in self.catalog["items"]
            )
        )
        for item_id in formerly_overbroad:
            with self.subTest(item=item_id):
                self.assertEqual(
                    self.items[item_id]["coverage_classification"], "draft_only"
                )
                self.assertTrue(self.items[item_id]["evidence_refs"])

    def test_module_certification_requires_all_exact_eight_conditions(self):
        all_true = {condition: True for condition in CERTIFICATION_CONDITION_IDS}
        self.assertTrue(is_module_certified(all_true))
        for condition in CERTIFICATION_CONDITION_IDS:
            with self.subTest(condition=condition):
                missing = dict(all_true)
                missing.pop(condition)
                self.assertFalse(is_module_certified(missing))
                failed = dict(all_true)
                failed[condition] = False
                self.assertFalse(is_module_certified(failed))
        extra = dict(all_true)
        extra["PG-NS-CERT-UNCONTROLLED"] = True
        self.assertFalse(is_module_certified(extra))

    def test_certified_module_rate_rejects_invalid_denominators_and_counts(self):
        self.assertEqual(certified_module_enablement_rate(9, 10), 90.0)
        for certified, submitted in ((0, 0), (1, 0), (1, -1), (-1, 1), (2, 1)):
            with self.subTest(certified=certified, submitted=submitted):
                with self.assertRaises(ValueError):
                    certified_module_enablement_rate(certified, submitted)
        for certified, submitted in ((True, 1), (1, False), (1.5, 2), (1, 2.0)):
            with self.subTest(certified=certified, submitted=submitted):
                with self.assertRaises(ValueError):
                    certified_module_enablement_rate(certified, submitted)

    def test_current_repository_is_not_ready_and_never_authorizes_production(self):
        report = build_report()
        self.assertEqual(report["program_g0_status"], "NOT_READY")
        self.assertFalse(report["ready_for_authority_review"])
        self.assertFalse(report["production_implementation_authorized"])
        self.assertGreater(len(report["blockers"]), 0)
        rendered = format_report(report)
        self.assertIn("cannot approve Program G0", rendered)
        self.assertIn("authorize production", rendered)

    def test_missing_or_malformed_registers_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_catalog(root)
            register_root = root / "docs/00-governance/registers"
            register_root.mkdir(parents=True)
            (register_root / "GOAL-REGISTER.json").write_text("{", encoding="utf-8")
            report = build_report(root)
        self.assertEqual(report["program_g0_status"], "NOT_READY")
        self.assertFalse(report["ready_for_authority_review"])
        self.assertFalse(report["production_implementation_authorized"])
        self.assertTrue(any("goal register invalid" in item for item in report["blockers"]))
        self.assertTrue(any("agent register missing" in item for item in report["blockers"]))

    def test_fully_populated_controls_only_become_ready_for_authority_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_ready_control_set(root)
            self.assertEqual(validate_program_controls(root), [])
            report = build_report(root)
        self.assertEqual(report["program_g0_status"], "READY_FOR_AUTHORITY_REVIEW")
        self.assertTrue(report["ready_for_authority_review"])
        self.assertFalse(report["production_implementation_authorized"])
        self.assertEqual(report["blockers"], [])

    def test_schema_invalid_ready_set_cannot_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_ready_control_set(root)
            goal_path = root / "docs/00-governance/registers/GOAL-REGISTER.json"
            goal = json.loads(goal_path.read_text(encoding="utf-8"))
            goal["version"] = "0.1.0-draft"
            goal_path.write_text(json.dumps(goal), encoding="utf-8")
            structural_errors = validate_program_controls(root)
            report = build_report(root)
        self.assertTrue(
            any("APPROVED REGISTER USES DRAFT VERSION" in error for error in structural_errors)
        )
        self.assertEqual(report["program_g0_status"], "NOT_READY")
        self.assertFalse(report["ready_for_authority_review"])
        self.assertTrue(report["program_control_errors"])
        self.assertFalse(report["production_implementation_authorized"])

    def test_maker_and_checker_must_differ(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_ready_control_set(root, maker="same-agent", checker="same-agent")
            report = build_report(root)
        self.assertEqual(report["program_g0_status"], "NOT_READY")
        self.assertTrue(
            any("maker and checker must differ" in item for item in report["blockers"])
        )
        self.assertFalse(report["production_implementation_authorized"])

    def write_catalog(self, root: Path):
        path = root / CATALOG_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.catalog), encoding="utf-8")

    @staticmethod
    def approved_register(name, owner):
        schema_files = {
            "goal": "goal-register.schema.json",
            "agent": "agent-register.schema.json",
            "module": "module-register.schema.json",
            "skill": "skill-register.schema.json",
            "schedule": "schedule-register.schema.json",
            "authority": "authority-matrix.schema.json",
            "technology": "technology-decision-assignment.schema.json",
        }
        schema = json.loads(
            (ROOT / "contracts/governance" / schema_files[name]).read_text(
                encoding="utf-8"
            )
        )
        return {
            "$schema": schema["$id"],
            "register_id": REGISTER_IDS[name],
            "version": "0.1.0",
            "status": "approved",
            "owner_authority": owner,
            "updated_at": "2026-07-21T12:00:00+07:00",
            "approved_by": "human-authority",
            "approved_at": "2026-07-21T12:00:00+07:00",
            "approval_ref": "EVD-GOV-001",
        }

    def write_ready_control_set(self, root: Path, maker="maker-agent", checker="checker-agent"):
        self.write_catalog(root)
        schema_root = root / "contracts/governance"
        schema_root.mkdir(parents=True, exist_ok=True)
        for schema_path in (ROOT / "contracts/governance").glob("*.schema.json"):
            shutil.copy2(schema_path, schema_root / schema_path.name)
        register_root = root / "docs/00-governance/registers"
        register_root.mkdir(parents=True)

        goal = self.approved_register("goal", "Product Authority")
        goal["entries"] = [
            {
                "goal_id": "BOPEN-GOAL-001",
                "version": "0.2",
                "title": "bOPEN Program Goal and Measurable Outcomes",
                "status": "Approved",
                "owner_authority": "Product Authority",
                "artifact_ref": "docs/01-product/BOPEN-GOAL-001-DRAFT.md",
                "phase_ids": [
                    "PG-G0",
                    "PG-P0",
                    "PG-P1",
                    "PG-P2",
                    "PG-P3",
                    "PG-P4",
                    "PG-C0",
                ],
                "metric_ids": ["CERTIFIED_MODULE_ENABLEMENT_RATE"],
                "approval_ref": "DEC-0010",
                "approved_at": "2026-07-21T12:00:00+07:00",
                "review_due_at": "2027-07-21T12:00:00+07:00",
                "implementation_authority": False,
            }
        ]
        agent = self.approved_register("agent", "Engineering Authority")
        agent["entries"] = [
            {
                "agent_id": "AGT-CODEX-MAKER",
                "display_name": "Codex Maker",
                "harness": "Codex",
                "role_id": "Requirements Agent",
                "status": "ACTIVE",
                "owner_authority": "Engineering Authority",
                "allowed_scope_paths": ["contracts/governance"],
                "prohibited_authorities": ["self_approval", "release"],
                "credential_mode": "NONE",
                "registered_at": "2026-07-21T12:00:00+07:00",
                "review_due_at": "2027-07-21T12:00:00+07:00",
                "expires_at": "2027-07-28T12:00:00+07:00",
                "maker_work_item_ids": ["GOV-P0-01"],
                "checker_work_item_ids": [],
            }
        ]
        module = self.approved_register("module", "Architecture Authority")
        module["entries"] = []
        skill = self.approved_register("skill", "Engineering Authority")
        skill["entries"] = []
        schedule = self.approved_register("schedule", "Product Authority")
        phase_owners = {
            "PG-G0": "Product Authority",
            "PG-P0": "Architecture Authority",
            "PG-P1": "Architecture Authority",
            "PG-P2": "Architecture Authority",
            "PG-P3": "Product Authority",
            "PG-P4": "Product Authority",
            "PG-C0": "Engineering Authority",
        }
        phase_order = list(phase_owners)
        schedule["entries"] = []
        for index, phase_id in enumerate(phase_order):
            is_g0 = phase_id == "PG-G0"
            schedule["entries"].append(
                {
                    "schedule_id": phase_id,
                    "phase_id": phase_id,
                    "title": phase_id,
                    "status": "READY_FOR_AUTHORITY_REVIEW" if is_g0 else "NOT_READY",
                    "depends_on": [] if index == 0 else [phase_order[index - 1]],
                    "owner_authority": phase_owners[phase_id],
                    "work_item_refs": ["GOV-P0-01"] if is_g0 else [],
                    "planned_start": "2026-07-21T12:00:00+07:00" if is_g0 else None,
                    "planned_end": "2026-07-28T12:00:00+07:00" if is_g0 else None,
                    "rebaseline_decision_ref": None,
                    "evidence_refs": ["EVD-GOV-001"] if is_g0 else [],
                }
            )
        authority = json.loads(
            (ROOT / "docs/00-governance/registers/AUTHORITY-MATRIX.json").read_text(
                encoding="utf-8"
            )
        )
        authority.update(
            {
                "version": "0.2.0",
                "status": "approved",
                "approved_by": "human-authority",
                "approved_at": "2026-07-21T12:00:00+07:00",
                "approval_ref": "EVD-GOV-001",
            }
        )
        for entry in authority["entries"]:
            entry["status"] = "approved"
        technology = self.approved_register("technology", "Architecture Authority")
        technology["entries"] = [
            {
                "assignment_id": f"TECH-{index:03d}",
                "decision_id": decision_id,
                "subject": decision_id,
                "status": "PENDING_OWNER_ASSIGNED",
                "owner_authority": "Architecture Authority",
                "checker_authorities": [],
                "required_before_phase": "PG-P0",
                "due_at": None,
                "evidence_refs": ["docs/decisions/DECISION-REGISTER.md"],
                "blockers": ["checker and due date not assigned"],
            }
            for index, decision_id in enumerate(("DEC-0004", "DEC-0005"), start=1)
        ]
        file_names = {
            "goal": "GOAL-REGISTER.json",
            "agent": "AGENT-REGISTER.json",
            "module": "MODULE-REGISTER.json",
            "skill": "SKILL-REGISTER.json",
            "schedule": "SCHEDULE-REGISTER.json",
            "authority": "AUTHORITY-MATRIX.json",
            "technology": "TECHNOLOGY-DECISION-ASSIGNMENTS.json",
        }
        values = {
            "goal": goal,
            "agent": agent,
            "module": module,
            "skill": skill,
            "schedule": schedule,
            "authority": authority,
            "technology": technology,
        }
        for name, value in values.items():
            (register_root / file_names[name]).write_text(
                json.dumps(value), encoding="utf-8"
            )

        decision_root = root / "docs/decisions"
        decision_root.mkdir(parents=True)
        (decision_root / "DECISION-REGISTER.md").write_text(
            "| ID | Decision | Status | Owner |\n"
            "|---|---|---|---|\n"
            "| DEC-0004 | Technology stack | Pending | Architecture Authority |\n"
            "| DEC-0005 | Identity strategy | Pending | Architecture Authority |\n",
            encoding="utf-8",
        )

        template_root = root / "docs/templates"
        template_root.mkdir(parents=True)
        (template_root / "work-package-template.md").write_text(
            """# Work Package
**Maker:**
**Checker:**
**Branch/worktree:**
**Allowed paths:**
**Base SHA:**
**Expiry:**
## Acceptance criteria
## Required checks/evidence
""",
            encoding="utf-8",
        )
        (template_root / "evidence-template.md").write_text(
            """# Evidence
**Evidence ID:**
**Work package:**
**Source/commit:**
**Maker:**
**Checker:**
## Procedure
## Actual result
## Independent verdict
""",
            encoding="utf-8",
        )
        evidence_root = root / "docs/evidence"
        evidence_root.mkdir(parents=True)
        (evidence_root / "EVD-GOV-001-program-g0-controls.md").write_text(
            f"""# EVD-GOV-001
**Evidence ID:** EVD-GOV-001
**Work package:** GOV-P0-01
**Exact SHA:** 0123456789abcdef0123456789abcdef01234567
**Maker:** {maker}
**Checker:** {checker}
**Verdict:** ACCEPT
""",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
