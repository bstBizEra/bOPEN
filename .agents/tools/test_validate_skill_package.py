#!/usr/bin/env python3
"""Fail-closed tests for validate_skill_package.py (stdlib unittest only).

Each test builds a synthetic .agents-shaped tree in a temp directory and asserts
that the validator reports the expected error code and a non-zero exit status.
Nothing under the real repository is read or written.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_skill_package as v  # noqa: E402

GOOD_DESC = (
    "Review bOPEN tenant isolation controls for an authorized change. "
    "Use when a change touches tenant-owned data, membership resolution or RLS."
)


def skill_md(name: str, description: str = GOOD_DESC, body: str = "\n# Heading\n\nGuidance body.\n") -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n{body}"


class ValidatorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="bopen-skill-lint-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.skills = self.tmp / "skills"
        self.skills.mkdir(parents=True)
        self.repo = self.tmp / "repo"
        (self.repo / "docs").mkdir(parents=True)
        (self.repo / "docs" / "REAL.md").write_text("real\n", encoding="utf-8", newline="\n")
        self.schema = Path(__file__).resolve().parent.parent / "schemas" / "skill-manifest.schema.json"

    def write(self, skill: str, rel: str, content: str, *, binary: bytes | None = None) -> Path:
        path = self.skills / skill / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if binary is not None:
            path.write_bytes(binary)
        else:
            path.write_text(content, encoding="utf-8", newline="\n")
        return path

    def run_validator(self, **kwargs) -> dict:
        return v.validate(
            self.skills,
            self.repo,
            self.schema,
            kwargs.get("strict_triggers", False),
            kwargs.get("repo_paths_warn", False),
        )

    def codes(self, report: dict, severity: str = "error") -> set[str]:
        return {f["code"] for f in report["findings"] if f["severity"] == severity}

    def assert_fails_with(self, code: str, report: dict) -> None:
        self.assertIn(code, self.codes(report), msg=json.dumps(report["findings"], indent=2))
        self.assertEqual(report["status"], "fail")
        self.assertGreater(report["errorCount"], 0)


class HappyPathTests(ValidatorTestCase):
    def test_valid_l0_skill_passes(self) -> None:
        self.write("bopen-good", "SKILL.md", skill_md("bopen-good"))
        report = self.run_validator()
        self.assertEqual(report["status"], "pass", msg=json.dumps(report["findings"], indent=2))
        self.assertEqual(report["errorCount"], 0)
        self.assertEqual(report["skills"][0]["tier"], "L0")

    def test_exit_code_zero_on_pass(self) -> None:
        self.write("bopen-good", "SKILL.md", skill_md("bopen-good"))
        rc = v.main(
            ["--skills-root", str(self.skills), "--repo-root", str(self.repo), "--schema", str(self.schema), "--quiet"]
        )
        self.assertEqual(rc, 0)

    def test_valid_cross_references_pass(self) -> None:
        body = "\n# Body\n\nRun `bopen-peer` first. See `docs/REAL.md`.\n"
        self.write("bopen-good", "SKILL.md", skill_md("bopen-good", body=body))
        self.write("bopen-peer", "SKILL.md", skill_md("bopen-peer"))
        report = self.run_validator()
        self.assertEqual(report["status"], "pass", msg=json.dumps(report["findings"], indent=2))


class FailClosedTests(ValidatorTestCase):
    def test_missing_frontmatter_fails(self) -> None:
        self.write("bopen-bad", "SKILL.md", "# No frontmatter here\n\nJust prose.\n")
        self.assert_fails_with("FRONTMATTER", self.run_validator())

    def test_unterminated_frontmatter_fails(self) -> None:
        self.write("bopen-bad", "SKILL.md", "---\nname: bopen-bad\ndescription: x\n\n# Body\n")
        self.assert_fails_with("FRONTMATTER", self.run_validator())

    def test_name_directory_mismatch_fails(self) -> None:
        self.write("bopen-bad", "SKILL.md", skill_md("bopen-other"))
        self.assert_fails_with("NAME_DIR_MISMATCH", self.run_validator())

    def test_missing_name_fails(self) -> None:
        self.write("bopen-bad", "SKILL.md", f"---\ndescription: {GOOD_DESC}\n---\n\n# Body\n")
        self.assert_fails_with("NAME_MISSING", self.run_validator())

    def test_empty_description_fails(self) -> None:
        self.write("bopen-bad", "SKILL.md", '---\nname: bopen-bad\ndescription: ""\n---\n\n# Body\n')
        self.assert_fails_with("DESC_MISSING", self.run_validator())

    def test_missing_description_fails(self) -> None:
        self.write("bopen-bad", "SKILL.md", "---\nname: bopen-bad\n---\n\n# Body\n")
        self.assert_fails_with("DESC_MISSING", self.run_validator())

    def test_overlong_description_fails(self) -> None:
        self.write("bopen-bad", "SKILL.md", skill_md("bopen-bad", "Use when " + "x" * 1100))
        self.assert_fails_with("DESC_TOO_LONG", self.run_validator())

    def test_empty_body_fails(self) -> None:
        self.write("bopen-bad", "SKILL.md", skill_md("bopen-bad", body="\n   \n"))
        self.assert_fails_with("BODY_EMPTY", self.run_validator())

    def test_crlf_line_endings_fail(self) -> None:
        raw = skill_md("bopen-bad").replace("\n", "\r\n").encode("utf-8")
        self.write("bopen-bad", "SKILL.md", "", binary=raw)
        self.assert_fails_with("HYGIENE_CRLF", self.run_validator())

    def test_cp1252_0x97_byte_fails(self) -> None:
        raw = skill_md("bopen-bad", body="\n# Body\n\nA cp1252 dash: \x97 here.\n").encode("utf-8")
        raw = raw.replace("\u0097".encode("utf-8"), b"\x97")
        self.write("bopen-bad", "SKILL.md", "", binary=raw)
        report = self.run_validator()
        self.assertIn("HYGIENE_CP1252", self.codes(report), msg=json.dumps(report["findings"], indent=2))
        self.assertEqual(report["status"], "fail")

    def test_dangling_skill_cross_reference_fails(self) -> None:
        body = "\n# Body\n\nAlways run `bopen-does-not-exist` before mutating.\n"
        self.write("bopen-bad", "SKILL.md", skill_md("bopen-bad", body=body))
        self.assert_fails_with("XREF_SKILL_DANGLING", self.run_validator())

    def test_dangling_repo_path_fails(self) -> None:
        body = "\n# Body\n\nWrite the receipt to `docs/06-evidence/EVIDENCE-ENVELOPE.md`.\n"
        self.write("bopen-bad", "SKILL.md", skill_md("bopen-bad", body=body))
        report = self.run_validator()
        self.assert_fails_with("XREF_PATH_MISSING", report)
        location = [f["location"] for f in report["findings"] if f["code"] == "XREF_PATH_MISSING"][0]
        self.assertTrue(location.endswith(":8"), msg=location)

    def test_repo_path_placeholder_is_not_reported(self) -> None:
        body = "\n# Body\n\nWrite to `docs/evidence/EVD-<TRACK>-NNN-<slug>.md`.\n"
        self.write("bopen-good", "SKILL.md", skill_md("bopen-good", body=body))
        self.assertEqual(self.run_validator()["status"], "pass")

    def test_windows_path_is_not_a_skill_reference(self) -> None:
        body = "\n# Body\n\n    git worktree add ..\\bopen-worktrees\\item -b br sha\n"
        self.write("bopen-good", "SKILL.md", skill_md("bopen-good", body=body))
        report = self.run_validator()
        self.assertNotIn("XREF_SKILL_DANGLING", self.codes(report))

    def test_missing_skill_md_fails(self) -> None:
        (self.skills / "bopen-empty").mkdir()
        self.assert_fails_with("SKILL_MD_MISSING", self.run_validator())

    def test_weak_description_fails_under_strict_triggers(self) -> None:
        self.write("bopen-bad", "SKILL.md", skill_md("bopen-bad", "Detect and repair drift in generated artifacts."))
        report = self.run_validator(strict_triggers=True)
        self.assert_fails_with("DESC_NO_TRIGGER", report)

    def test_weak_description_is_only_a_warning_at_l0(self) -> None:
        self.write("bopen-ok", "SKILL.md", skill_md("bopen-ok", "Detect and repair drift in generated artifacts."))
        report = self.run_validator()
        self.assertEqual(report["status"], "pass")
        self.assertIn("DESC_NO_TRIGGER", self.codes(report, "warning"))

    def test_exit_code_one_on_failure(self) -> None:
        self.write("bopen-bad", "SKILL.md", skill_md("bopen-other"))
        rc = v.main(
            ["--skills-root", str(self.skills), "--repo-root", str(self.repo), "--schema", str(self.schema), "--quiet"]
        )
        self.assertEqual(rc, 1)

    def test_embedded_secret_fails(self) -> None:
        self.write("bopen-bad", "SKILL.md", skill_md("bopen-bad"))
        self.write("bopen-bad", "notes.md", "token: " + "AKIA" + "ABCDEFGHIJKLMNOP" + "\n")
        self.assert_fails_with("SECRET_SUSPECTED", self.run_validator())


MANIFEST = """apiVersion: skills.bopen.io/v1alpha1
kind: Skill
metadata:
  id: io.bizera.bopen.demo
  name: bopen-demo
  version: 0.1.0
  owner: bopen-demo-authority
  classification: internal
  status: validated
  license: Proprietary
  createdAt: "2026-07-22"
spec:
  purpose: Demonstrate a manifest that satisfies the portable bOPEN skill manifest schema.
  type: advisory
  riskClass: SKR1
  scope:
    allowed:
      - platform
    tenantContext: conditional
  contracts:
    inputSchema: schemas/input.schema.json
    outputSchema: schemas/output.schema.json
    evidenceSchema: schemas/evidence.schema.json
  requires:
    products: []
    modules: []
    capabilities:
      - demo.read
    tools:
      - id: filesystem
        operations:
          - read
        access: conditional
  runtime:
    sandboxProfile: bopen-read-mostly
    networkPolicy: restricted
    filesystemPolicy: workspace-output-only
    maxDuration: PT30M
    maxSteps: 80
    maxToolCalls: 60
  approval:
    mode: conditional
    requiredFor:
      - production-change
  data:
    maximumClassification: confidential
    crossTenantAccess: prohibited
    secretsInPackage: prohibited
  failure:
    retryPolicy: bounded
    compensationRequired: false
  evaluation:
    suite: evals/cases.yaml
    minimumSuccessRate: 0.95
    crossTenantFailuresAllowed: 0
  lifecycle:
    stage: validated
    deprecationPolicy: policies/revocation-policy.yaml
    revocationPolicy: policies/revocation-policy.yaml
  distribution:
    formats:
      - directory
    immutableVersionRequired: true
    signatureRequiredForPublication: true
    provenanceRequiredForPublication: true
"""


class ManifestTests(ValidatorTestCase):
    def scaffold(self, skill: str = "bopen-demo", manifest: str = MANIFEST) -> None:
        self.write(skill, "SKILL.md", skill_md(skill))
        self.write(skill, "README.md", "# Demo\n")
        self.write(skill, "LICENSE.txt", "Proprietary\n")
        self.write(skill, "bopen.skill.yaml", manifest)
        for rel in ("schemas/input.schema.json", "schemas/output.schema.json", "schemas/evidence.schema.json"):
            self.write(skill, rel, '{"$schema": "https://json-schema.org/draft/2020-12/schema"}\n')
        self.write(skill, "evals/cases.yaml", "- id: c1\n")
        self.write(skill, "policies/revocation-policy.yaml", "spec: {}\n")

    def test_valid_manifest_reaches_tier_l1(self) -> None:
        self.scaffold()
        report = self.run_validator()
        self.assertEqual(report["status"], "pass", msg=json.dumps(report["findings"], indent=2))
        self.assertEqual(report["skills"][0]["tier"], "L1")

    def test_manifest_bad_enum_fails(self) -> None:
        self.scaffold(manifest=MANIFEST.replace("riskClass: SKR1", "riskClass: SKR9"))
        self.assert_fails_with("MANIFEST_SCHEMA", self.run_validator())

    def test_manifest_missing_required_field_fails(self) -> None:
        self.scaffold(manifest=MANIFEST.replace("  owner: bopen-demo-authority\n", ""))
        self.assert_fails_with("MANIFEST_SCHEMA", self.run_validator())

    def test_manifest_name_directory_mismatch_fails(self) -> None:
        self.scaffold(manifest=MANIFEST.replace("name: bopen-demo", "name: bopen-elsewhere"))
        self.assert_fails_with("MANIFEST_NAME_DIR_MISMATCH", self.run_validator())

    def test_manifest_contract_path_missing_fails(self) -> None:
        self.scaffold(manifest=MANIFEST.replace("schemas/input.schema.json", "schemas/absent.schema.json"))
        self.assert_fails_with("MANIFEST_PATH_MISSING", self.run_validator())

    def test_corrected_version_pattern_rejects_bare_zero(self) -> None:
        """The in-package schema pattern wrongly accepts any string starting with '0'."""
        self.scaffold(manifest=MANIFEST.replace("version: 0.1.0", 'version: "0abcXYZ"'))
        self.assert_fails_with("MANIFEST_SCHEMA", self.run_validator())


class MiniYamlTests(unittest.TestCase):
    def test_nested_sequence_of_mappings(self) -> None:
        parsed = v.mini_yaml_load(
            "tools:\n  - id: filesystem\n    operations:\n      - read\n      - search\n    access: conditional\n"
        )
        self.assertEqual(
            parsed, {"tools": [{"id": "filesystem", "operations": ["read", "search"], "access": "conditional"}]}
        )

    def test_scalars_and_empty_list(self) -> None:
        parsed = v.mini_yaml_load('a: 1\nb: 0.95\nc: true\nd: []\ne: "quoted # not comment"\nf: plain  # comment\n')
        self.assertEqual(parsed, {"a": 1, "b": 0.95, "c": True, "d": [], "e": "quoted # not comment", "f": "plain"})

    def test_duplicate_key_is_rejected(self) -> None:
        with self.assertRaises(v.MiniYamlError):
            v.mini_yaml_load("a: 1\na: 2\n")

    def test_tab_indentation_is_rejected(self) -> None:
        with self.assertRaises(v.MiniYamlError):
            v.mini_yaml_load("a:\n\tb: 1\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
