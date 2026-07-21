"""Fail-closed tests for the PG-G0 current-tree blocker projection.

The historical authority-readiness artifact is evidence about its bound commit.
These tests require the current-tree projection to preserve that evidence while
classifying later technical observations without manufacturing human authority.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.report_pg_g0_current_tree_readiness import (
    build_projection,
    classify_blocker,
    rendered_projection,
    validate_projection,
    validate_projection_root_controls,
)


ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_REPORT = Path("artifacts/validation/program-g0-authority-readiness.json")
DOCKET = Path("docs/00-governance/authority-dockets/PG-G0-AUTH-001.json")
ROOT_CONTROLS = (
    "Roadmap.md",
    "Master_Standards.md",
    "Progress_Log.md",
    "Backlog.md",
    "Recap_Today.md",
)
AUTHORITY_FLAGS = (
    "pg_g0_passed",
    "ready_for_human_gate_decision",
    "governance_baseline_approved",
    "work_package_accepted",
    "technology_approved",
    "identity_provider_approved",
    "qualification_executed",
    "merge_authorized",
    "release_authorized",
    "runtime_activation_authorized",
    "production_implementation_authorized",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def find_projection_item(data: dict, blocker_text: str) -> dict:
    return next(
        item
        for item in data["blocker_assessments"]
        if item["original_text"] == blocker_text
    )


class PgG0CurrentTreeReadinessTests(unittest.TestCase):
    maxDiff = None

    def test_current_repository_projection_is_valid_and_deterministic(self):
        first = build_projection(ROOT)
        second = build_projection(ROOT)

        self.assertEqual(first, second)
        self.assertEqual(validate_projection(first, ROOT), [])
        rendered = rendered_projection(ROOT)
        self.assertEqual(rendered, rendered_projection(ROOT))
        self.assertEqual(json.loads(rendered), first)
        self.assertTrue(rendered.endswith("\n"))

    def test_historical_report_hash_blockers_and_bound_commit_are_preserved(self):
        projection = build_projection(ROOT)
        historical_bytes = (ROOT / HISTORICAL_REPORT).read_bytes()
        historical = json.loads(historical_bytes)
        docket_bytes = (ROOT / DOCKET).read_bytes()
        docket = json.loads(docket_bytes)
        binding = projection["historical_view"]

        self.assertEqual(binding["artifact_ref"], HISTORICAL_REPORT.as_posix())
        self.assertEqual(binding["artifact_sha256"], sha256_bytes(historical_bytes))
        self.assertEqual(binding["artifact_bytes"], len(historical_bytes))
        self.assertEqual(binding["docket_ref"], DOCKET.as_posix())
        self.assertEqual(binding["docket_sha256"], sha256_bytes(docket_bytes))
        self.assertEqual(binding["docket_bytes"], len(docket_bytes))
        self.assertEqual(binding["bound_commit_sha"], docket["repository_binding"]["commit_sha"])
        self.assertEqual(binding["bound_tree_sha"], docket["repository_binding"]["tree_sha"])
        self.assertEqual(binding["blocker_count"], len(historical["blockers"]))
        self.assertEqual(
            [item["original_text"] for item in projection["blocker_assessments"]],
            historical["blockers"],
        )
        for item, blocker in zip(projection["blocker_assessments"], historical["blockers"]):
            self.assertEqual(item["original_sha256"], sha256_bytes(blocker.encode("utf-8")))

        self.assertEqual(
            projection["current_tree"]["evaluation_commit_sha"],
            "4a98cb45748ded2b209786bcb9242664aa0795aa",
        )
        self.assertEqual(
            projection["current_tree"]["evaluation_tree_sha"],
            "8900b871e1f436d5ee21919764a31f955f42d5bf",
        )
        self.assertTrue(projection["current_tree"]["evaluation_commit_is_ancestor"])

    def test_root_controls_resolve_only_as_exact_valid_regular_files(self):
        self.assertEqual(validate_projection_root_controls(ROOT), [])

        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp)
            for name in ROOT_CONTROLS:
                shutil.copy2(ROOT / name, fixture / name)
            (fixture / "Roadmap.md").unlink()
            self.assertTrue(validate_projection_root_controls(fixture))

            wrong_case = fixture / "roadmap.md"
            shutil.copy2(ROOT / "Roadmap.md", wrong_case)
            self.assertTrue(validate_projection_root_controls(fixture))

            malformed = fixture / "Roadmap.md"
            malformed.write_text("not a root-control record\n", encoding="utf-8")
            self.assertTrue(validate_projection_root_controls(fixture))

            malformed.write_text(
                (ROOT / "Roadmap.md").read_text(encoding="utf-8").replace(
                    "**PG-G0 passed:** false", "**PG-G0 passed:** true"
                ),
                encoding="utf-8",
            )
            self.assertTrue(validate_projection_root_controls(fixture))

            with mock.patch.object(Path, "is_symlink", return_value=True):
                self.assertTrue(validate_projection_root_controls(ROOT))

    def test_invalid_root_control_keeps_historical_root_blocker_active(self):
        projection = build_projection(ROOT)
        blocker = (
            "Roadmap.md, Master_Standards.md, Progress_Log.md, Backlog.md and "
            "Recap_Today.md are absent and no equivalents are approved"
        )
        item = find_projection_item(projection, blocker)
        self.assertEqual(item["classification"], "RESOLVED_TECHNICALLY_IN_CURRENT_TREE")

        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp)
            for name in ROOT_CONTROLS:
                shutil.copy2(ROOT / name, fixture / name)
            (fixture / "Roadmap.md").unlink()
            invalid = classify_blocker(blocker, fixture)
        self.assertEqual(invalid["classification"], "STILL_ACTIVE")

    def test_human_trust_root_missing_action_and_ineffective_blockers_never_auto_resolve(self):
        human_only = (
            "BOPEN-GOV-001 and the authority matrix are draft and ineffective",
            "an approved authority identity registry with hash-bound human role records is absent",
            "attributable Product, Architecture, Security, Data and Engineering human authority identities are absent",
            "authority source is not effective",
            "the authority matrix has no action for approving BOPEN-GOV-001",
            "the authority matrix has no action for approving the seven program registers",
            "the authority matrix has no action for passing PG-G0",
            "PG-G0-DEC-001 remains ineffective",
        )
        for blocker in human_only:
            with self.subTest(blocker=blocker):
                self.assertEqual(
                    classify_blocker(blocker, ROOT)["classification"],
                    "HUMAN_DISPOSITION_REQUIRED",
                )

    def test_ci_or_pr_text_cannot_resolve_exact_sha_technical_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp)
            (fixture / "ci-success.txt").write_text(
                "CI passed; PR approved; exact-SHA technical review accepted\n", encoding="utf-8"
            )
            for blocker in (
                "exact-SHA technical review is not accepted",
                "technical review of this exact docket candidate is pending",
            ):
                self.assertEqual(classify_blocker(blocker, fixture)["classification"], "STILL_ACTIVE")

    def test_unknown_blocker_defaults_to_still_active(self):
        unknown = "future unrecognized blocker must fail closed"
        assessment = classify_blocker(unknown, ROOT)
        self.assertEqual(assessment["classification"], "STILL_ACTIVE")
        self.assertEqual(assessment["original_text"], unknown)

    def test_all_authority_flags_remain_false(self):
        projection = build_projection(ROOT)
        self.assertEqual(set(projection["authority"]), set(AUTHORITY_FLAGS))
        self.assertTrue(all(projection["authority"][flag] is False for flag in AUTHORITY_FLAGS))

        for flag in AUTHORITY_FLAGS:
            with self.subTest(flag=flag):
                mutated = copy.deepcopy(projection)
                mutated["authority"][flag] = True
                self.assertTrue(validate_projection(mutated, ROOT))

    def test_readiness_stays_false_while_human_blockers_remain(self):
        projection = build_projection(ROOT)
        self.assertTrue(
            any(
                item["classification"] == "HUMAN_DISPOSITION_REQUIRED"
                for item in projection["blocker_assessments"]
            )
        )
        self.assertFalse(projection["authority"]["ready_for_human_gate_decision"])

        mutated = copy.deepcopy(projection)
        mutated["authority"]["ready_for_human_gate_decision"] = True
        self.assertTrue(validate_projection(mutated, ROOT))

    def test_projection_schema_is_closed_at_every_object_boundary(self):
        projection = build_projection(ROOT)
        mutations = []
        for path in (
            (),
            ("historical_view",),
            ("current_tree",),
            ("summary",),
            ("authority",),
            ("blocker_assessments", 0),
        ):
            mutated = copy.deepcopy(projection)
            target = mutated
            for component in path:
                target = target[component]
            target["unexpected"] = "must be rejected"
            mutations.append(mutated)

        for mutated in mutations:
            with self.subTest(keys=mutated.keys()):
                self.assertTrue(validate_projection(mutated, ROOT))


if __name__ == "__main__":
    unittest.main()
