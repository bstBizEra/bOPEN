"""Adversarial tests for the immutable PG-G0 bound-tree projection.

The projection must be a function of named Git objects, not of the checkout
that happens to carry the reporting tool.  These tests deliberately mutate
working files and descendant commits and construct invalid Git trees without
requiring Windows symbolic-link privileges.
"""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.report_pg_g0_bound_tree_readiness import (
    CARRIER_COMMIT,
    CARRIER_TREE,
    SUBJECT_COMMIT,
    SUBJECT_TREE,
    build_projection,
    classify_blocker,
    rendered_projection,
    validate_bound_root_controls,
    validate_projection,
)


ROOT = Path(__file__).resolve().parents[2]
OLD_PROJECTION = Path("artifacts/validation/pg-g0-current-tree-readiness-001.json")
HISTORICAL_READINESS = Path("artifacts/validation/program-g0-authority-readiness.json")
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
ROOT_BLOCKER = (
    "Roadmap.md, Master_Standards.md, Progress_Log.md, Backlog.md and "
    "Recap_Today.md are absent and no equivalents are approved"
)


def git(root: Path, *args: str, input_bytes: bytes | None = None) -> str:
    process = subprocess.run(
        ["git", "-C", str(root), *args],
        input=input_bytes,
        capture_output=True,
        check=False,
    )
    if process.returncode:
        raise AssertionError(
            f"git {' '.join(args)} failed ({process.returncode}): "
            f"{process.stderr.decode('utf-8', errors='replace')}"
        )
    return process.stdout.decode("utf-8").strip()


def init_fixture(*, missing: str | None = None, wrong_case: str | None = None,
                 malformed: str | None = None, symlink: str | None = None) -> tuple[tempfile.TemporaryDirectory, Path, str, str]:
    """Create one exact fixture commit and return its commit/tree object IDs."""
    owner = tempfile.TemporaryDirectory()
    root = Path(owner.name)
    git(root, "init", "--quiet")
    git(root, "config", "user.name", "bOPEN Bound Tree Test")
    git(root, "config", "user.email", "bound-tree-test@bst.invalid")
    for name in ROOT_CONTROLS:
        if name == missing or name == symlink:
            continue
        destination = wrong_case if name == wrong_case else name.lower()
        # wrong_case is the expected canonical filename; write it with a
        # different case to expose Windows case-folding mistakes in Git trees.
        if name == wrong_case:
            destination = name.lower()
        else:
            destination = name
        data = (ROOT / name).read_bytes()
        if name == malformed:
            data = b"not a governed root-control record\n"
        (root / destination).write_bytes(data)
    git(root, "add", "--all")
    if symlink is not None:
        blob = git(root, "hash-object", "-w", "--stdin", input_bytes=b"Roadmap.md\n")
        git(root, "update-index", "--add", "--cacheinfo", "120000", blob, symlink)
    git(root, "commit", "--quiet", "-m", "fixture")
    commit = git(root, "rev-parse", "HEAD")
    tree = git(root, "show", "-s", "--format=%T", commit)
    return owner, root, commit, tree


class PgG0BoundTreeReadinessTests(unittest.TestCase):
    maxDiff = None

    def test_repository_projection_is_valid_and_deterministic(self):
        first = build_projection(ROOT)
        second = build_projection(ROOT)
        self.assertEqual(first, second)
        self.assertEqual(validate_projection(first, ROOT), [])
        rendered = rendered_projection(ROOT)
        self.assertEqual(rendered, rendered_projection(ROOT))
        self.assertEqual(json.loads(rendered), first)
        self.assertTrue(rendered.endswith("\n"))

    def test_live_checkout_changes_do_not_change_subject_bound_projection(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "clone"
            git(Path(tmp), "clone", "--quiet", "--no-hardlinks", str(ROOT), str(fixture))
            baseline = build_projection(fixture)
            for rel in (OLD_PROJECTION, HISTORICAL_READINESS, DOCKET, Path("Roadmap.md")):
                path = fixture / rel
                path.write_bytes(path.read_bytes() + b"\nUNTRUSTED LIVE CHECKOUT CHANGE\n")
            self.assertEqual(build_projection(fixture), baseline)

    def test_descendant_commit_changes_do_not_change_subject_bound_projection(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "clone"
            git(Path(tmp), "clone", "--quiet", "--no-hardlinks", str(ROOT), str(fixture))
            git(fixture, "config", "user.name", "bOPEN Bound Tree Test")
            git(fixture, "config", "user.email", "bound-tree-test@bst.invalid")
            baseline = build_projection(fixture)
            for rel in (OLD_PROJECTION, HISTORICAL_READINESS, DOCKET, Path("Roadmap.md")):
                path = fixture / rel
                path.write_bytes(path.read_bytes() + b"\nUNTRUSTED DESCENDANT CHANGE\n")
            git(fixture, "add", "--all")
            git(fixture, "commit", "--quiet", "-m", "untrusted descendant")
            self.assertEqual(build_projection(fixture), baseline)

    def test_exact_fixture_missing_wrong_case_and_malformed_controls_stay_active(self):
        cases = (
            {"missing": "Roadmap.md"},
            {"wrong_case": "Roadmap.md"},
            {"malformed": "Roadmap.md"},
        )
        for kwargs in cases:
            owner, root, commit, tree = init_fixture(**kwargs)
            with owner, self.subTest(case=kwargs):
                self.assertTrue(validate_bound_root_controls(root, commit, tree))
                assessment = classify_blocker(ROOT_BLOCKER, root, commit, tree)
                self.assertEqual(assessment["classification"], "STILL_ACTIVE")

    def test_git_mode_120000_is_rejected_without_os_symlink_support(self):
        owner, root, commit, tree = init_fixture(symlink="Roadmap.md")
        with owner:
            self.assertEqual(git(root, "ls-tree", commit, "Roadmap.md").split()[0], "120000")
            self.assertTrue(validate_bound_root_controls(root, commit, tree))
            self.assertEqual(
                classify_blocker(ROOT_BLOCKER, root, commit, tree)["classification"],
                "STILL_ACTIVE",
            )

    def test_wrong_tree_missing_object_and_noncommit_object_fail_closed(self):
        owner, root, commit, tree = init_fixture()
        with owner:
            wrong_tree = "0" * 40
            missing = "f" * 40
            blob = git(root, "hash-object", "-w", "--stdin", input_bytes=b"not a commit")
            for candidate_commit, candidate_tree in (
                (commit, wrong_tree),
                (missing, tree),
                (blob, tree),
            ):
                with self.subTest(commit=candidate_commit, tree=candidate_tree):
                    self.assertTrue(
                        validate_bound_root_controls(root, candidate_commit, candidate_tree)
                    )

    def test_subject_and_carrier_provenance_are_explicit(self):
        projection = build_projection(ROOT)
        subject = projection["subject_tree"]
        carrier = projection["carrier_provenance"]
        self.assertEqual(subject["commit_sha"], SUBJECT_COMMIT)
        self.assertEqual(subject["tree_sha"], SUBJECT_TREE)
        self.assertTrue(subject["commit_object_verified"])
        self.assertTrue(subject["tree_object_verified"])
        self.assertEqual(carrier["base_commit_sha"], CARRIER_COMMIT)
        self.assertEqual(carrier["base_tree_sha"], CARRIER_TREE)
        self.assertTrue(carrier["subject_is_ancestor_of_carrier"])
        self.assertTrue(carrier["carrier_is_ancestor_of_head"])
        self.assertFalse(carrier["live_worktree_bytes_used"])
        self.assertNotEqual(subject["commit_sha"], carrier["base_commit_sha"])

    def test_old_001_projection_is_historical_and_authority_remains_false(self):
        projection = build_projection(ROOT)
        old_bytes = (ROOT / OLD_PROJECTION).read_bytes()
        historical = projection["historical_view"]
        self.assertEqual(historical["rejected_projection_ref"], OLD_PROJECTION.as_posix())
        self.assertEqual(historical["rejected_projection_status"], "REJECTED_REQUEST_CHANGES")
        # The old projection is explicitly historical; the successor inputs are
        # raw blobs from the subject commit, never bytes read from that artifact.
        old = json.loads(old_bytes)
        self.assertEqual(old["status"], "NOT_READY")
        readiness = historical["authority_readiness_input"]
        docket = historical["docket_input"]
        self.assertEqual(readiness["path"], HISTORICAL_READINESS.as_posix())
        self.assertEqual(docket["path"], DOCKET.as_posix())
        self.assertRegex(readiness["sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(docket["sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(set(projection["authority"]), set(AUTHORITY_FLAGS))
        self.assertTrue(all(value is False for value in projection["authority"].values()))

    def test_unknown_human_and_ci_claims_remain_fail_closed(self):
        for text, expected in (
            ("future unrecognized blocker", "STILL_ACTIVE"),
            ("authority source is not effective", "HUMAN_DISPOSITION_REQUIRED"),
            ("exact-SHA technical review is not accepted", "STILL_ACTIVE"),
            ("CI passed and PR approved", "STILL_ACTIVE"),
        ):
            with self.subTest(text=text):
                self.assertEqual(
                    classify_blocker(text, ROOT, SUBJECT_COMMIT, SUBJECT_TREE)["classification"],
                    expected,
                )

    def test_all_authority_flags_and_human_readiness_validate_false(self):
        projection = build_projection(ROOT)
        for flag in AUTHORITY_FLAGS:
            mutated = copy.deepcopy(projection)
            mutated["authority"][flag] = True
            self.assertTrue(validate_projection(mutated, ROOT), flag)
        self.assertFalse(projection["summary"]["ready_for_human_gate_decision"])

    def test_projection_shape_is_closed_at_every_object_boundary(self):
        projection = build_projection(ROOT)
        paths = (
            (),
            ("historical_view",),
            ("subject_tree",),
            ("subject_tree", "root_controls", 0),
            ("historical_view", "authority_readiness_input"),
            ("carrier_provenance",),
            ("summary",),
            ("authority",),
            ("blocker_assessments", 0),
        )
        for path in paths:
            mutated = copy.deepcopy(projection)
            target = mutated
            for component in path:
                target = target[component]
            target["unexpected"] = "must be rejected"
            with self.subTest(path=path):
                self.assertTrue(validate_projection(mutated, ROOT))


if __name__ == "__main__":
    unittest.main()
