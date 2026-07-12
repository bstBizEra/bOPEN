import tempfile
import unittest
from pathlib import Path

from tools.report_bootstrap_gates import build_report, format_report


class BootstrapGateReportTests(unittest.TestCase):
    def test_repository_report_requires_review_and_blocks_production_implementation(self):
        report = build_report()

        self.assertEqual(report["bootstrap_review_state"], "review_required")
        self.assertFalse(report["production_implementation_authorized"])
        self.assertEqual(report["b7_status"], "Pending execution review")
        self.assertGreaterEqual(len(report["blockers"]), 1)

    def test_report_flags_pending_evidence_and_no_implementation_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs/work-packages").mkdir(parents=True)
            (root / "docs/evidence").mkdir(parents=True)
            (root / "docs/work-packages/BOOTSTRAP-GATES.md").write_text(
                """# Bootstrap Gates

| Gate | Criteria | Status |
|---|---|---|
| B7 Exit | Validation evidence reviewed and next work authorized | Pending execution review |
""",
                encoding="utf-8",
            )
            (root / "docs/evidence/EVIDENCE-INDEX.md").write_text(
                """# Evidence Index

| Evidence ID | Work package | Description | Path | Status |
|---|---|---|---|---|
| EVD-BOOT-001 | BOOT-P0-02 | AGENTS hierarchy validation | `artifacts/validation/agents-validation.txt` | To generate |
""",
                encoding="utf-8",
            )
            (root / "docs/DOCUMENT-STATUS.md").write_text(
                """# Document Status Register

| Artifact | Status | Implementation authority | Next action |
|---|---|---:|---|
| BOPEN-REQ-001 | Draft shell | No | Product authority review |
""",
                encoding="utf-8",
            )

            report = build_report(root)

        self.assertEqual(report["bootstrap_review_state"], "review_required")
        self.assertEqual(len(report["pending_evidence"]), 1)
        self.assertEqual(len(report["implementation_blocking_docs"]), 1)

    def test_markdown_report_is_non_authorizing(self):
        report = format_report(
            {
                "bootstrap_review_state": "review_required",
                "production_implementation_authorized": False,
                "gate_count": 8,
                "b7_status": "Pending execution review",
                "pending_evidence": [],
                "implementation_blocking_docs": [],
                "blockers": ["B7 exit gate is not approved."],
            }
        )

        self.assertIn("readiness evidence only", report)
        self.assertIn("does not authorize production", report)


if __name__ == "__main__":
    unittest.main()
