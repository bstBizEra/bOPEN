#!/usr/bin/env python3
"""Validate the fail-closed QUAL-INTEG-001 review candidate.

This validator relies on Git objects for integration lineage and byte preservation.
It does not confer approval, merge authority, release authority, or runtime authority.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

from generate_document_manifest import validate_manifest_index


ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_MANIFEST = Path("docs/manifests/QUAL-INTEG-001-INTEGRATION-MANIFEST.json")
MANIFEST_INDEX = Path("docs/manifests/MANIFEST-INDEX.jsonl")
RES_SOURCE_HEAD = "4b1cb217f183c0b983a935f45317cabe82bb6fac"
RES_REPLAY_HEAD = "43f0b8b84c5bcd3ad8f6a713a44aadd722bb9c78"
AUTHORITY_FLAGS = {
    "technology_approved",
    "qualification_executed",
    "gate_passed",
    "merge_authorized",
    "release_authorized",
    "production_implementation_authorized",
}

PACKAGE_BINDINGS = (
    ("GOV-P0-03", "a29ec1d8ab28d38621dc4db176b7b2abf2ea44cb", "docs/manifests/GOV-P0-03-PACKAGE-MANIFEST.json"),
    ("QUAL-P0-00", "a2fc4b1f907b17911ffbd3cb8e0992b806c90bb6", "docs/manifests/QUAL-P0-00-PACKAGE-MANIFEST.json"),
    ("TECH-P0-01", "7b11f9da913a65041dd4a8ac245d39ca10f27b02", "docs/manifests/TECH-P0-01-PACKAGE-MANIFEST.json"),
    ("QUAL-P0-02", "74daac85d1ce4c08371c7bae787bc2de91c00bf9", "docs/manifests/QUAL-P0-02-PACKAGE-MANIFEST.json"),
)

WORKFLOW_REQUIRED = (
    "fetch-depth: 0",
    "tools/validate_repository.py",
    "tools/validate_contracts.py",
    "tools/validate_program_controls.py",
    "tools/report_program_g0.py --check",
    "tools/validate_pg_g0_authority_docket.py --check",
    "tools/report_pg_g0_current_tree_readiness.py --check",
    "tools/generate_document_manifest.py --check-index",
    "tools/validate_root_control_surfaces.py --check",
    "tools/validate_qualification_common.py --check --check-manifest",
    "tools/validate_technology_qualification.py --check --check-manifest",
    "tools/validate_identity_qualification.py --check",
    "tools/validate_research_g3_design.py",
    "tools/validate_qual_integ_001.py",
    "tools/report_qual_integ_001.py --check",
    "tools/check_clean_room.py",
    "tools/check_secrets.py",
    "tools/check_supply_chain.py",
    "unittest discover",
)

PACKAGE_REQUIRED = tuple(
    item for item in WORKFLOW_REQUIRED if item not in {"fetch-depth: 0", "unittest discover"}
)

REPOSITORY_VALIDATOR_REQUIRED = (
    "docs/manifests/GOV-P0-03-PACKAGE-MANIFEST.json",
    "docs/manifests/QUAL-P0-00-PACKAGE-MANIFEST.json",
    "docs/manifests/TECH-P0-01-PACKAGE-MANIFEST.json",
    "docs/manifests/QUAL-P0-02-PACKAGE-MANIFEST.json",
    "docs/manifests/RES-P0-05-DOCUMENT-MANIFEST.json",
    "docs/manifests/QUAL-INTEG-001-INTEGRATION-MANIFEST.json",
    "docs/manifests/QUAL-INTEG-001-AGGREGATE-MANIFEST.json",
    "docs/manifests/QUAL-INTEG-001-REWORK-001-AGGREGATE-MANIFEST.json",
    "docs/manifests/QUAL-INTEG-001-REWORK-002-AGGREGATE-MANIFEST.json",
    "docs/manifests/QUAL-INTEG-001-REWORK-003-AGGREGATE-MANIFEST.json",
    "docs/manifests/QUAL-INTEG-001-REWORK-004-AGGREGATE-MANIFEST.json",
    "docs/manifests/MANIFEST-INDEX.jsonl",
    "docs/work-packages/QUAL-INTEG-001.md",
    "docs/evidence/EVD-QUAL-INTEG-001-review-candidate.md",
    "tools/validate_qual_integ_001.py",
    "tests/governance/test_qual_integ_001.py",
    "artifacts/validation/qual-integ-001-rework-001-readiness.json",
    "contracts/governance/pg-g0-current-tree-readiness.schema.json",
    "tools/report_pg_g0_current_tree_readiness.py",
    "tests/governance/test_pg_g0_current_tree_readiness.py",
    "artifacts/validation/pg-g0-current-tree-readiness-001.json",
)


def git_bytes(root: Path, *args: str, input_bytes: bytes | None = None) -> bytes | None:
    process = subprocess.run(
        ["git", *args],
        cwd=root,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return process.stdout if process.returncode == 0 else None


def git_text(root: Path, *args: str) -> str | None:
    payload = git_bytes(root, *args)
    if payload is None:
        return None
    try:
        return payload.decode("utf-8").strip()
    except UnicodeDecodeError:
        return None


def commit_exists(root: Path, commit: str) -> bool:
    return git_bytes(root, "cat-file", "-e", f"{commit}^{{commit}}") is not None


def commit_parent(root: Path, commit: str) -> str | None:
    line = git_text(root, "rev-list", "--parents", "-n", "1", commit)
    if line is None:
        return None
    fields = line.split()
    return fields[1] if len(fields) == 2 else None


def changed_paths(root: Path, old: str, new: str) -> list[str] | None:
    payload = git_bytes(root, "diff", "--name-only", "-z", old, new)
    if payload is None:
        return None
    return sorted(part.decode("utf-8") for part in payload.split(b"\0") if part)


def stable_patch_id(root: Path, commit: str, excluded: Iterable[str] = ()) -> str | None:
    parent = commit_parent(root, commit)
    if parent is None:
        return None
    args = ["diff", "--binary", "--full-index", parent, commit, "--", "."]
    args.extend(f":(exclude){path}" for path in excluded)
    patch = git_bytes(root, *args)
    if patch is None:
        return None
    result = git_bytes(root, "patch-id", "--stable", input_bytes=patch)
    if result is None:
        return None
    fields = result.decode("ascii", errors="replace").split()
    return fields[0] if fields else None


def scope_exclusions(scope: str, shared_paths: list[str]) -> tuple[str, ...] | None:
    if scope == "full":
        return ()
    if scope == "exclude_ten_shared_paths":
        return tuple(shared_paths) if len(shared_paths) == 10 else None
    if scope == "exclude_historical_canonical_manifest":
        return ("docs/DOCUMENT-MANIFEST.json",)
    return None


def validate_authority(manifest: Any) -> list[str]:
    authority = manifest.get("authority") if isinstance(manifest, dict) else None
    if not isinstance(authority, dict) or not authority:
        return ["integration authority flags missing"]
    errors = [
        f"integration authority flag must remain false: {name}"
        for name, value in sorted(authority.items())
        if value is not False
    ]
    for name in sorted(AUTHORITY_FLAGS - set(authority)):
        errors.append(f"integration authority flag missing: {name}")
    for name in sorted(set(authority) - AUTHORITY_FLAGS):
        errors.append(f"integration authority flag unknown: {name}")
    if manifest.get("status") != "draft" or manifest.get("lifecycle") != "inactive":
        errors.append("integration manifest must remain draft and inactive")
    return errors


def validate_mappings(manifest: Any, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["integration manifest must be an object"]
    shared = manifest.get("shared_paths")
    chains = manifest.get("source_chains")
    if not isinstance(shared, list) or not all(isinstance(item, str) for item in shared):
        return ["integration shared_paths invalid"]
    if len(shared) != 10 or len(shared) != len(set(shared)):
        errors.append("integration shared_paths must contain ten unique paths")
    if not isinstance(chains, list) or not chains:
        return errors + ["integration source_chains invalid"]
    head = git_text(root, "rev-parse", "HEAD")
    for chain in chains:
        package = chain.get("package") if isinstance(chain, dict) else "unknown"
        mappings = chain.get("mappings") if isinstance(chain, dict) else None
        if not isinstance(mappings, list) or not mappings:
            errors.append(f"{package} mappings missing")
            continue
        for mapping in mappings:
            if not isinstance(mapping, dict):
                errors.append(f"{package} mapping malformed")
                continue
            source = mapping.get("source")
            replay = mapping.get("replay")
            scope = mapping.get("scope")
            if not all(isinstance(value, str) for value in (source, replay, scope)):
                errors.append(f"{package} mapping identifiers invalid")
                continue
            excluded = scope_exclusions(scope, shared)
            if excluded is None:
                errors.append(f"{package} mapping scope unknown: {scope}")
                continue
            for label, commit in (("source", source), ("replay", replay)):
                if not commit_exists(root, commit):
                    errors.append(f"{package} {label} commit unavailable: {commit}")
            if head is not None and commit_exists(root, replay):
                if git_bytes(root, "merge-base", "--is-ancestor", replay, head) is None:
                    errors.append(f"{package} replay is not an ancestor of HEAD: {replay}")
            for label, commit in (("source", source), ("replay", replay)):
                calculated = stable_patch_id(root, commit, excluded)
                declared = mapping.get(f"{label}_patch_id")
                if calculated is None:
                    errors.append(f"{package} {label} patch-id unavailable: {commit}")
                elif calculated != declared:
                    errors.append(f"{package} {label} patch-id mismatch: {commit}")
            if mapping.get("source_patch_id") != mapping.get("replay_patch_id"):
                errors.append(f"{package} source/replay patch-id mismatch: {source}")
    return sorted(set(errors))


def source_blob(root: Path, commit: str, path: str) -> bytes | None:
    return git_bytes(root, "cat-file", "blob", f"{commit}:{path}")


def package_record_paths(payload: Any) -> list[str] | None:
    if not isinstance(payload, dict):
        return None
    records = payload.get("files", payload.get("records"))
    if not isinstance(records, list):
        return None
    paths = [record.get("path") for record in records if isinstance(record, dict)]
    if len(paths) != len(records) or not all(isinstance(path, str) for path in paths):
        return None
    return paths


def validate_package_bytes(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for package, commit, manifest_path in PACKAGE_BINDINGS:
        raw_manifest = source_blob(root, commit, manifest_path)
        if raw_manifest is None:
            errors.append(f"{package} source package manifest unavailable")
            continue
        try:
            manifest = json.loads(raw_manifest.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            errors.append(f"{package} source package manifest invalid")
            continue
        paths = package_record_paths(manifest)
        if paths is None:
            errors.append(f"{package} source package records invalid")
            continue
        for path in [manifest_path, *paths]:
            expected = source_blob(root, commit, path)
            try:
                actual = (root / path).read_bytes()
            except OSError:
                errors.append(f"{package} package file unavailable: {path}")
                continue
            if expected is None or actual != expected:
                errors.append(f"{package} package byte drift: {path}")
    return sorted(set(errors))


def validate_res_replay_bytes(manifest: Any, root: Path = ROOT) -> list[str]:
    shared = manifest.get("shared_paths", []) if isinstance(manifest, dict) else []
    if not isinstance(shared, list):
        return ["RES-P0-05 shared path set invalid"]
    parent = commit_parent(root, "8bc3e2ac8d24aa8b1a02aec6c4cce576665b1ed9")
    if parent is None:
        return ["RES-P0-05 source parent unavailable"]
    paths = changed_paths(root, parent, RES_SOURCE_HEAD)
    if paths is None:
        return ["RES-P0-05 changed path set unavailable"]
    errors: list[str] = []
    for path in sorted(set(paths) - set(shared)):
        if source_blob(root, RES_SOURCE_HEAD, path) != source_blob(root, RES_REPLAY_HEAD, path):
            errors.append(f"RES-P0-05 replay byte mismatch: {path}")
    return errors


def tracked_text_conflicts(root: Path = ROOT) -> list[str]:
    payload = git_bytes(root, "ls-files", "-z")
    if payload is None:
        return ["tracked path inventory unavailable"]
    markers = ("<" * 7, "=" * 7, ">" * 7)
    errors: list[str] = []
    for raw_name in payload.split(b"\0"):
        if not raw_name:
            continue
        path = root / raw_name.decode("utf-8")
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if any(line.startswith(markers) for line in text.splitlines()):
            errors.append(f"unresolved conflict marker: {path.relative_to(root).as_posix()}")
    return errors


def require_tokens(path: Path, tokens: Iterable[str], label: str) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{label} unavailable: {exc}"]
    return [f"{label} semantic union missing: {token}" for token in tokens if token not in text]


def validate_semantic_union(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for path in (Path(".github/workflows/bootstrap-governance.yml"), Path(".gitea/workflows/governance.yml")):
        errors.extend(require_tokens(root / path, WORKFLOW_REQUIRED, path.as_posix()))
    errors.extend(require_tokens(root / "package.json", PACKAGE_REQUIRED, "package.json"))
    errors.extend(require_tokens(root / "tools/validate_repository.py", REPOSITORY_VALIDATOR_REQUIRED, "validate_repository.py"))
    return errors


def load_integration_manifest(root: Path = ROOT) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        payload = json.loads((root / INTEGRATION_MANIFEST).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"integration manifest unavailable or invalid: {exc}"]
    return payload if isinstance(payload, dict) else None, ([] if isinstance(payload, dict) else ["integration manifest must be object"])


def validate_candidate(root: Path = ROOT, *, check_index: bool = True) -> list[str]:
    manifest, errors = load_integration_manifest(root)
    if manifest is None:
        return errors
    errors.extend(validate_authority(manifest))
    errors.extend(validate_mappings(manifest, root))
    errors.extend(validate_package_bytes(root))
    errors.extend(validate_res_replay_bytes(manifest, root))
    if check_index:
        errors.extend(validate_manifest_index(MANIFEST_INDEX, root))
    errors.extend(tracked_text_conflicts(root))
    errors.extend(validate_semantic_union(root))
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-index", action="store_true", help="Diagnostic only; CI must not use this option.")
    args = parser.parse_args()
    errors = validate_candidate(check_index=not args.skip_index)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("QUAL-INTEG-001 integration validation: PASS (draft; all authority flags false)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
