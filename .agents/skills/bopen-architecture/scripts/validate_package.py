#!/usr/bin/env python3
"""Validate the bOPEN Architecture skill package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource
except ImportError as exc:  # pragma: no cover
    print(f"Missing dependency: {exc}. Run: python -m pip install -r requirements.txt", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[1]
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
SECRET_PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws-access-key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "openai-like-key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    "slack-token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
}
TEXT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json", ".py", ".toml", ".csv", ""}
IGNORED_PARTS = {"__pycache__", ".git", ".venv", "evals/results"}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.passes: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def ok(self, message: str) -> None:
        self.passes.append(message)

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": "fail" if self.errors else "pass",
            "errors": self.errors,
            "warnings": self.warnings,
            "passes": self.passes,
        }


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("SKILL.md frontmatter closing delimiter not found")
    front = yaml.safe_load(text[4:end])
    if not isinstance(front, dict):
        raise ValueError("SKILL.md frontmatter must be a mapping")
    return front, text[end + 5 :]


def validate_skill_md(report: Report, root: Path) -> None:
    path = root / "SKILL.md"
    try:
        front, body = parse_frontmatter(path)
    except Exception as exc:
        report.error(str(exc))
        return

    name = front.get("name")
    desc = front.get("description")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        report.error("SKILL.md name is missing or invalid")
    elif len(name) > 64:
        report.error("SKILL.md name exceeds 64 characters")
    elif name != root.name:
        report.error(f"SKILL.md name '{name}' must match directory '{root.name}'")
    else:
        report.ok("SKILL.md name is valid and matches directory")

    if not isinstance(desc, str) or not desc.strip():
        report.error("SKILL.md description is required")
    elif len(desc) > 1024:
        report.error("SKILL.md description exceeds 1024 characters")
    else:
        report.ok("SKILL.md description is present and within limit")

    compatibility = front.get("compatibility")
    if compatibility is not None and (not isinstance(compatibility, str) or not 1 <= len(compatibility) <= 500):
        report.error("SKILL.md compatibility must be a 1-500 character string")

    metadata = front.get("metadata", {})
    if not isinstance(metadata, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in metadata.items()):
        report.error("SKILL.md metadata must map string keys to string values")

    allowed = front.get("allowed-tools")
    if allowed is not None and not isinstance(allowed, str):
        report.error("SKILL.md allowed-tools must be a space-separated string")

    line_count = len(path.read_text(encoding="utf-8").splitlines())
    if line_count > 500:
        report.warning(f"SKILL.md has {line_count} lines; Agent Skills recommends under 500")
    else:
        report.ok(f"SKILL.md line count is {line_count}")

    if len(body.split()) > 5000:
        report.warning("SKILL.md body may exceed the recommended instruction budget")


def validate_json_schema(report: Report, path: Path) -> None:
    try:
        schema = load_json(path)
        Draft202012Validator.check_schema(schema)
        report.ok(f"Schema valid: {path.relative_to(ROOT)}")
    except Exception as exc:
        report.error(f"Invalid schema {path.relative_to(ROOT)}: {exc}")


def validator_for(schema_path: Path) -> Draft202012Validator:
    schema = load_json(schema_path)
    registry = Registry()
    for sibling in schema_path.parent.glob("*.json"):
        try:
            doc = load_json(sibling)
            resource = Resource.from_contents(doc)
            uri = doc.get("$id", sibling.resolve().as_uri())
            registry = registry.with_resource(uri, resource)
            registry = registry.with_resource(sibling.resolve().as_uri(), resource)
        except Exception:
            continue
    return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())


def validate_instance(report: Report, instance: Any, schema_path: Path, label: str) -> None:
    try:
        errors = sorted(validator_for(schema_path).iter_errors(instance), key=lambda e: list(e.path))
    except Exception as exc:
        report.error(f"Could not validate {label}: {exc}")
        return
    if errors:
        for err in errors:
            where = ".".join(str(p) for p in err.path) or "<root>"
            report.error(f"{label} at {where}: {err.message}")
    else:
        report.ok(f"Validated {label}")


def validate_manifest(report: Report, root: Path) -> None:
    manifest_path = root / "bopen.skill.yaml"
    try:
        manifest = load_yaml(manifest_path)
    except Exception as exc:
        report.error(f"Cannot parse bopen.skill.yaml: {exc}")
        return
    validate_instance(report, manifest, root / "schemas/bopen-skill.schema.json", "bopen.skill.yaml")

    if isinstance(manifest, dict):
        contracts = manifest.get("spec", {}).get("contracts", {})
        lifecycle = manifest.get("spec", {}).get("lifecycle", {})
        evaluation = manifest.get("spec", {}).get("evaluation", {})
        for key, rel in {**contracts, **{"deprecationPolicy": lifecycle.get("deprecationPolicy"), "revocationPolicy": lifecycle.get("revocationPolicy"), "suite": evaluation.get("suite")}}.items():
            if isinstance(rel, str) and not (root / rel).exists():
                report.error(f"Manifest path missing for {key}: {rel}")

        if manifest.get("metadata", {}).get("name") != root.name:
            report.error("Manifest metadata.name must match skill directory")


def validate_examples_and_evals(report: Report, root: Path) -> None:
    validate_instance(report, load_json(root / "evals/example-input.json"), root / "schemas/input.schema.json", "evals/example-input.json")
    validate_instance(report, load_json(root / "evals/example-output.json"), root / "schemas/output.schema.json", "evals/example-output.json")

    case_schema = root / "schemas/evaluation-case.schema.json"
    ids: set[str] = set()
    for rel in ("evals/cases.yaml", "evals/security-cases.yaml"):
        try:
            cases = load_yaml(root / rel)
        except Exception as exc:
            report.error(f"Cannot parse {rel}: {exc}")
            continue
        if not isinstance(cases, list):
            report.error(f"{rel} must contain a list")
            continue
        for index, case in enumerate(cases):
            validate_instance(report, case, case_schema, f"{rel}[{index}]")
            case_id = case.get("id") if isinstance(case, dict) else None
            if case_id in ids:
                report.error(f"Duplicate evaluation case ID: {case_id}")
            elif isinstance(case_id, str):
                ids.add(case_id)
    report.ok(f"Evaluation case IDs checked: {len(ids)} unique")

    for rel in ("evals/trigger-positive.yaml", "evals/trigger-negative.yaml"):
        items = load_yaml(root / rel)
        if not isinstance(items, list) or not items or any(not isinstance(v, str) or not v.strip() for v in items):
            report.error(f"{rel} must be a non-empty list of prompts")
        elif len(items) != len(set(items)):
            report.error(f"{rel} contains duplicate prompts")
        else:
            report.ok(f"Validated trigger prompt set: {rel}")


def validate_required_files(report: Report, root: Path) -> None:
    required = [
        "SKILL.md", "README.md", "bopen.skill.yaml", "LICENSE.txt", "NOTICE.md",
        "agents/openai.yaml", "schemas/bopen-skill.schema.json", "schemas/input.schema.json",
        "schemas/output.schema.json", "schemas/evaluation-case.schema.json",
        "references/architecture-baseline.md", "references/security-and-tenancy.md",
        "policies/execution-policy.yaml", "evals/cases.yaml",
        "scripts/validate_package.py", "scripts/run_static_evals.py",
    ]
    missing = [rel for rel in required if not (root / rel).is_file()]
    if missing:
        report.error("Missing required files: " + ", ".join(missing))
    else:
        report.ok("All required package files are present")


def validate_links(report: Report, root: Path) -> None:
    broken: list[str] = []
    for md in root.rglob("*.md"):
        if any(part in IGNORED_PARTS for part in md.parts):
            continue
        text = md.read_text(encoding="utf-8")
        for target in LINK_RE.findall(text):
            target = target.strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:", "sandbox:")):
                continue
            resolved = (md.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                broken.append(f"{md.relative_to(root)} -> path escapes root: {target}")
                continue
            if not resolved.exists():
                broken.append(f"{md.relative_to(root)} -> {target}")
    if broken:
        for item in broken:
            report.error(f"Broken local link: {item}")
    else:
        report.ok("Local Markdown links resolve")


def validate_paths_and_secrets(report: Report, root: Path) -> None:
    secret_hits: list[str] = []
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if any(part in {"__pycache__", ".git", ".venv"} for part in rel.parts):
            continue
        if path.is_symlink():
            report.error(f"Symlink is not allowed in release package: {rel}")
            continue
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                secret_hits.append(f"{rel}: {label}")
    if secret_hits:
        for item in secret_hits:
            report.error(f"Potential secret detected: {item}")
    else:
        report.ok("No high-confidence embedded secret patterns detected")


def validate_checksums(report: Report, root: Path) -> None:
    checksum_file = root / "SHA256SUMS"
    if not checksum_file.exists():
        report.warning("SHA256SUMS not present; run package_release.py for a release candidate")
        return
    listed: set[str] = set()
    for line_no, line in enumerate(checksum_file.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            report.error(f"Invalid SHA256SUMS line {line_no}")
            continue
        expected, rel = match.groups()
        listed.add(rel)
        path = root / rel
        if not path.is_file():
            report.error(f"Checksum target missing: {rel}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            report.error(f"Checksum mismatch: {rel}")
    if not report.errors:
        report.ok(f"Verified {len(listed)} checksums")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    root = args.root.resolve()
    report = Report()

    validate_required_files(report, root)
    validate_skill_md(report, root)
    for schema in sorted((root / "schemas").glob("*.json")):
        validate_json_schema(report, schema)
    validate_manifest(report, root)
    validate_examples_and_evals(report, root)
    validate_links(report, root)
    validate_paths_and_secrets(report, root)
    validate_checksums(report, root)

    if args.json_output:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        for item in report.passes:
            print(f"PASS: {item}")
        for item in report.warnings:
            print(f"WARN: {item}")
        for item in report.errors:
            print(f"FAIL: {item}")
        print(f"\nResult: {'FAIL' if report.errors else 'PASS'} — {len(report.passes)} pass, {len(report.warnings)} warning, {len(report.errors)} failure")
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
