#!/usr/bin/env python3
"""Validate the closed, repo-local bOPEN skill registry without mutation."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import argparse
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / ".agents" / "skills"
REGISTRY_PATH = ROOT / "docs" / "registers" / "skill-registry.json"
WORKFLOWS_ROOT = ROOT / ".agents" / "workflows"
REQUIREMENTS_LOCK = ROOT / ".agents" / "requirements.lock"
SKILL_SBOM = ROOT / ".agents" / "supply-chain" / "sbom.spdx.json"
ADAPTERS = {
    "codex": ROOT / "AGENTS.md",
    "claude": ROOT / "CLAUDE.md",
    "antigravity": ROOT / ".antigravity" / "AGENTS.md",
    "copilot": ROOT / ".github" / "copilot-instructions.md",
}

REQUIRED_ENTRY_KEYS = {
    "id", "canonical_id", "version", "owner", "risk_class", "state",
    "package_validation", "activation", "invocation", "routing_role", "path",
    "package_sha256", "source", "source_revision", "dependencies",
    "activation_decision",
}
EXPLICIT_ONLY = {
    "bopen-git-delivery",
    "bopen-repository-harness",
    "bopen-skill-authoring",
    "bopen-skill-admission",
    "bopen-release-readiness",
    "bopen-p0-conformance-gate",
}
VALID_RISKS = {"SKR1", "SKR2", "SKR3"}
VALID_STATES = {"candidate", "reviewed", "sandboxed", "evaluated", "approved", "published", "deprecated", "revoked"}
VALID_ACTIVATION = {"inactive", "active", "revoked"}
VALID_INVOCATION = {"advisory_only", "explicit_only", "eligible"}
VALID_ROUTING = {"specialist", "orchestrator"}
VALID_PACKAGE_VALIDATION = {"passed", "not_run"}
VALID_SOURCES = {"bopen-full-skills-pack-0.1.0", "local-working-tree-snapshot", "merged-candidate"}


def package_digest(directory: Path) -> str:
    rows: list[str] = []
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        rel = path.relative_to(directory).as_posix()
        rows.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {rel}")
    payload = ("\n".join(rows) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def frontmatter_name(skill_md: Path) -> str | None:
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(?P<body>.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        return None
    for line in match.group("body").splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip('"\'')
    return None


def has_indirection(path: Path) -> bool:
    cursor = Path(path.anchor)
    for part in path.parts[1:]:
        cursor /= part
        if cursor.exists() and (cursor.is_symlink() or getattr(cursor, "is_junction", lambda: False)()):
            return True
    return False


def workflow_requirements(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(?P<body>.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        raise ValueError("missing machine-readable frontmatter")
    required: list[str] = []
    in_skills = False
    for line in match.group("body").splitlines():
        if line.strip() == "skills:":
            in_skills = True
            continue
        if in_skills and re.match(r"^\s{4}-\s+", line):
            required.append(re.sub(r"^\s{4}-\s+", "", line).strip())
        elif in_skills and line.strip() and not line.startswith("    "):
            in_skills = False
    return required


def manifest_metadata(directory: Path) -> dict[str, object] | None:
    path = directory / "bopen.skill.yaml"
    if not path.is_file():
        return None
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or not isinstance(document.get("metadata"), dict):
        raise ValueError("invalid bopen.skill.yaml metadata")
    return document["metadata"]


def adapter_errors() -> list[str]:
    errors: list[str] = []
    required_markers = ("AGENTS.md", "docs/registers/skill-registry.json", ".agents/SKILL-ROUTING.md")
    for harness, path in ADAPTERS.items():
        if not path.is_file():
            errors.append(f"missing {harness} discovery adapter: {path.relative_to(ROOT).as_posix()}")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in required_markers:
            if marker not in text and not (harness == "codex" and marker == "AGENTS.md"):
                errors.append(f"{harness} adapter does not reference {marker}")
    return errors


def validate() -> list[str]:
    errors: list[str] = []
    try:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot load registry: {exc}"]

    if registry.get("artifact") != "BOPEN-SKILL-REGISTRY-001":
        errors.append("registry artifact ID mismatch")
    if registry.get("status") != "PROPOSED":
        errors.append("admission registry must remain PROPOSED")
    if registry.get("policy") != "SKILLS.md" or not (ROOT / "SKILLS.md").is_file():
        errors.append("registry policy must resolve to SKILLS.md")
    if registry.get("routing") != ".agents/SKILL-ROUTING.md" or not (ROOT / ".agents/SKILL-ROUTING.md").is_file():
        errors.append("registry routing path is missing or non-canonical")
    if not REQUIREMENTS_LOCK.is_file():
        errors.append("pinned skill requirements lock is missing")
    else:
        requirement_lines = [line for line in REQUIREMENTS_LOCK.read_text(encoding="utf-8").splitlines() if line and not line.startswith("#")]
        if not requirement_lines or any("==" not in line for line in requirement_lines):
            errors.append("skill validation dependencies must be exactly pinned")
    if not SKILL_SBOM.is_file():
        errors.append("skill-pack SBOM is missing")
    entries = registry.get("skills")
    if not isinstance(entries, list):
        return errors + ["registry skills must be an array"]

    directories = {p.name for p in SKILLS_ROOT.iterdir() if p.is_dir()}
    registered: set[str] = set()
    canonical_ids: set[str] = set()
    paths: set[str] = set()

    for index, entry in enumerate(entries):
        label = f"skills[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue
        missing = REQUIRED_ENTRY_KEYS - set(entry)
        extra = set(entry) - REQUIRED_ENTRY_KEYS
        if missing:
            errors.append(f"{label} missing keys: {', '.join(sorted(missing))}")
        if extra:
            errors.append(f"{label} has unknown keys: {', '.join(sorted(extra))}")
        skill_id = entry.get("id")
        if not isinstance(skill_id, str) or not re.fullmatch(r"[a-z0-9-]+", skill_id):
            errors.append(f"{label} has invalid id")
            continue
        if skill_id in registered:
            errors.append(f"duplicate skill id: {skill_id}")
        registered.add(skill_id)
        canonical = entry.get("canonical_id")
        if not isinstance(canonical, str) or not canonical.startswith("io.bizera.bopen."):
            errors.append(f"{skill_id} has invalid canonical_id")
        elif canonical in canonical_ids:
            errors.append(f"duplicate canonical_id: {canonical}")
        canonical_ids.add(str(canonical))
        rel = entry.get("path")
        expected_rel = f".agents/skills/{skill_id}"
        if rel != expected_rel:
            errors.append(f"{skill_id} path must be {expected_rel}")
            continue
        if rel in paths:
            errors.append(f"duplicate path: {rel}")
        paths.add(str(rel))
        directory = ROOT.joinpath(*Path(rel).parts)
        try:
            directory.resolve(strict=True).relative_to(SKILLS_ROOT.resolve(strict=True))
        except (OSError, ValueError):
            errors.append(f"{skill_id} path escapes or is missing")
            continue
        if has_indirection(directory):
            errors.append(f"{skill_id} path traverses a symlink or junction")
        skill_md = directory / "SKILL.md"
        if not skill_md.is_file() or frontmatter_name(skill_md) != skill_id:
            errors.append(f"{skill_id} directory/frontmatter name mismatch")
        actual_digest = package_digest(directory)
        if entry.get("package_sha256") != actual_digest:
            errors.append(f"{skill_id} package digest drift")
        if entry.get("risk_class") not in VALID_RISKS:
            errors.append(f"{skill_id} risk_class invalid")
        if entry.get("state") not in VALID_STATES:
            errors.append(f"{skill_id} state invalid")
        if entry.get("activation") not in VALID_ACTIVATION:
            errors.append(f"{skill_id} activation invalid")
        if entry.get("invocation") not in VALID_INVOCATION:
            errors.append(f"{skill_id} invocation invalid")
        if entry.get("routing_role") not in VALID_ROUTING:
            errors.append(f"{skill_id} routing_role invalid")
        if entry.get("package_validation") not in VALID_PACKAGE_VALIDATION:
            errors.append(f"{skill_id} package_validation invalid")
        if not isinstance(entry.get("version"), str) or not re.fullmatch(r"\d+\.\d+\.\d+", entry["version"]):
            errors.append(f"{skill_id} version must be semantic")
        if not isinstance(entry.get("owner"), str) or not entry["owner"].strip():
            errors.append(f"{skill_id} owner must be non-empty")
        if entry.get("source") not in VALID_SOURCES:
            errors.append(f"{skill_id} source invalid")
        dependencies = entry.get("dependencies")
        if not isinstance(dependencies, list) or any(not isinstance(item, str) for item in dependencies):
            errors.append(f"{skill_id} dependencies must be a string array")
        elif skill_id in dependencies or len(dependencies) != len(set(dependencies)):
            errors.append(f"{skill_id} dependencies contain self-reference or duplicates")
        if skill_id in EXPLICIT_ONLY and entry.get("invocation") != "explicit_only":
            errors.append(f"{skill_id} must be explicit_only")
        if entry.get("activation") == "inactive" and entry.get("invocation") == "eligible":
            errors.append(f"{skill_id} inactive skill cannot be eligible")
        if entry.get("state") != "candidate" or entry.get("activation") != "inactive":
            errors.append(f"{skill_id} candidate-admission registry cannot activate or promote skills")
        if entry.get("activation") == "active" and not re.fullmatch(r"[0-9a-f]{40}", str(entry.get("source_revision"))):
            errors.append(f"{skill_id} active skill requires exact committed source_revision")
        decision = entry.get("activation_decision")
        if entry.get("activation") == "inactive":
            if decision is not None:
                errors.append(f"{skill_id} inactive skill cannot carry an activation decision")
            if entry.get("source_revision") != f"package-sha256:{entry.get('package_sha256')}":
                errors.append(f"{skill_id} inactive source_revision must bind its exact package digest")
        else:
            required_decision = {"id", "status", "maker", "checker", "decision_sha256"}
            if not isinstance(decision, dict) or set(decision) != required_decision:
                errors.append(f"{skill_id} active/revoked skill requires a closed activation decision")
            elif (decision.get("status") != "approved" or decision.get("maker") == decision.get("checker")
                  or not re.fullmatch(r"[0-9a-f]{64}", str(decision.get("decision_sha256")))):
                errors.append(f"{skill_id} activation decision is ineffective")
        try:
            metadata = manifest_metadata(directory)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"{skill_id} manifest invalid: {exc}")
            metadata = None
        if metadata is not None:
            expected = {
                "id": entry.get("canonical_id"), "name": skill_id,
                "version": entry.get("version"), "owner": entry.get("owner"),
            }
            for key, value in expected.items():
                if str(metadata.get(key)) != str(value):
                    errors.append(f"{skill_id} manifest {key} mismatch")
            manifest = yaml.safe_load((directory / "bopen.skill.yaml").read_text(encoding="utf-8"))
            manifest_risk = manifest.get("spec", {}).get("riskClass")
            if manifest_risk != entry.get("risk_class"):
                errors.append(f"{skill_id} manifest riskClass mismatch")
            lifecycle = str(metadata.get("lifecycle", metadata.get("status", ""))).upper()
            if entry.get("activation") == "inactive" and lifecycle not in {"CANDIDATE", "CANDIDATE_INACTIVE"}:
                errors.append(f"{skill_id} inactive manifest lifecycle mismatch")
            if str(metadata.get("sourceRevision", "")) != "UNCOMMITTED-CANDIDATE":
                errors.append(f"{skill_id} candidate manifest sourceRevision mismatch")
            spec_lifecycle = manifest.get("spec", {}).get("lifecycle", {}).get("stage")
            if spec_lifecycle is not None and str(spec_lifecycle).upper() != "CANDIDATE":
                errors.append(f"{skill_id} spec lifecycle stage mismatch")
        skill_text = skill_md.read_text(encoding="utf-8") if skill_md.is_file() else ""
        lifecycle_match = re.search(r"^\s*bopen\.lifecycle\.stage:\s*(\S+)\s*$", skill_text, re.MULTILINE)
        if lifecycle_match and lifecycle_match.group(1).upper() != "CANDIDATE":
            errors.append(f"{skill_id} SKILL frontmatter lifecycle mismatch")
        readme = directory / "README.md"
        if readme.is_file():
            readme_text = readme.read_text(encoding="utf-8")
            readme_lifecycle = re.search(r"Lifecycle(?: stage)?:\*?\*?\s*`([^`]+)`", readme_text, re.IGNORECASE)
            if readme_lifecycle and readme_lifecycle.group(1).upper() != "CANDIDATE":
                errors.append(f"{skill_id} README lifecycle mismatch")
        openai = directory / "agents" / "openai.yaml"
        if openai.is_file():
            try:
                harness = yaml.safe_load(openai.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                errors.append(f"{skill_id} OpenAI metadata invalid: {exc}")
            else:
                implicit = harness.get("allow_implicit_invocation")
                if implicit is None and isinstance(harness.get("policy"), dict):
                    implicit = harness["policy"].get("allow_implicit_invocation")
                if entry.get("activation") == "inactive" and implicit is not False:
                    errors.append(f"{skill_id} inactive candidate permits implicit invocation")
        for residue in directory.rglob("*"):
            if residue.name == "__pycache__" or residue.suffix == ".pyc":
                errors.append(f"{skill_id} contains generated Python residue: {residue.relative_to(ROOT).as_posix()}")

    if registered != directories:
        missing = sorted(directories - registered)
        stale = sorted(registered - directories)
        if missing:
            errors.append(f"unregistered skill directories: {', '.join(missing)}")
        if stale:
            errors.append(f"registry entries without directories: {', '.join(stale)}")

    by_id = {entry.get("id"): entry for entry in entries if isinstance(entry, dict)}
    for skill_id, entry in by_id.items():
        dependencies = entry.get("dependencies") if isinstance(entry.get("dependencies"), list) else []
        for dependency in dependencies:
            if dependency not in by_id:
                errors.append(f"{skill_id} references unknown dependency {dependency}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(skill_id: str) -> None:
        if skill_id in visiting:
            errors.append(f"dependency cycle includes {skill_id}")
            return
        if skill_id in visited or skill_id not in by_id:
            return
        visiting.add(skill_id)
        dependencies = by_id[skill_id].get("dependencies")
        for dependency in dependencies if isinstance(dependencies, list) else []:
            visit(dependency)
        visiting.remove(skill_id)
        visited.add(skill_id)

    for skill_id in sorted(by_id):
        visit(skill_id)

    for workflow in sorted(WORKFLOWS_ROOT.glob("*.md")):
        try:
            requirements = workflow_requirements(workflow)
        except ValueError as exc:
            errors.append(f"{workflow.relative_to(ROOT).as_posix()}: {exc}")
            continue
        if not requirements:
            errors.append(f"{workflow.relative_to(ROOT).as_posix()} has no required skills")
        for skill_id in requirements:
            if skill_id not in registered:
                errors.append(f"{workflow.name} references unknown skill {skill_id}")

    errors.extend(adapter_errors())

    return errors


def resolve_workflow(name: str, explicitly_requested: set[str] | None = None) -> list[str]:
    errors = validate()
    if errors:
        return errors
    path = WORKFLOWS_ROOT / f"{name}.md"
    if not path.is_file():
        return [f"unknown workflow: {name}"]
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    by_id = {entry["id"]: entry for entry in registry["skills"]}
    explicitly_requested = explicitly_requested or set()
    closure: set[str] = set()

    def collect(skill_id: str) -> None:
        if skill_id in closure:
            return
        closure.add(skill_id)
        for dependency in by_id[skill_id]["dependencies"]:
            collect(dependency)

    for skill_id in workflow_requirements(path):
        collect(skill_id)
    for skill_id in sorted(closure):
        entry = by_id[skill_id]
        if entry["activation"] != "active" or entry["state"] not in {"approved", "published"}:
            errors.append(f"{name}: {skill_id} is not active and approved")
        if entry["invocation"] == "explicit_only" and skill_id not in explicitly_requested:
            errors.append(f"{name}: {skill_id} requires explicit user invocation")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resolve-workflow")
    parser.add_argument("--explicit-skill", action="append", default=[])
    parser.add_argument("--check-discovery", choices=sorted(ADAPTERS))
    args = parser.parse_args()
    errors = resolve_workflow(args.resolve_workflow, set(args.explicit_skill)) if args.resolve_workflow else validate()
    if args.check_discovery:
        errors.extend(adapter_errors())
    if errors:
        print("bOPEN skill registry validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    count = len(json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))["skills"])
    print(f"bOPEN skill registry validation: PASS ({count} registered inactive candidates)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
