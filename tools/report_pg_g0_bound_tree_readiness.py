#!/usr/bin/env python3
"""Build/check the exact-Git-object-bound PG-G0 readiness successor."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ID = "bopen://schemas/governance/pg-g0-bound-tree-readiness/0.2.0-draft"
REPORT_PATH = Path("artifacts/validation/pg-g0-bound-tree-readiness-002.json")
HISTORICAL_PATH = "artifacts/validation/program-g0-authority-readiness.json"
DOCKET_PATH = "docs/00-governance/authority-dockets/PG-G0-AUTH-001.json"
REJECTED_PROJECTION_PATH = "artifacts/validation/pg-g0-current-tree-readiness-001.json"
SUBJECT_COMMIT = "4a98cb45748ded2b209786bcb9242664aa0795aa"
SUBJECT_TREE = "8900b871e1f436d5ee21919764a31f955f42d5bf"
CARRIER_COMMIT = "bb64ba60345539d5f592d0b99d066240d813d7ae"
CARRIER_TREE = "832cf238be3721d1efaa3b7526c9f297738d60fa"
GENERATED_AT = "2026-07-22T00:00:00+07:00"
ROOT_CONTROLS = {
    "Roadmap.md": "GOV-P0-03-ROOT-ROADMAP",
    "Master_Standards.md": "GOV-P0-03-ROOT-STANDARDS",
    "Progress_Log.md": "GOV-P0-03-ROOT-PROGRESS",
    "Backlog.md": "GOV-P0-03-ROOT-BACKLOG",
    "Recap_Today.md": "GOV-P0-03-ROOT-RECAP",
}
ROOT_FIELDS = {
    "Version": "0.1", "Status": "Draft", "Lifecycle": "Inactive",
    "PG-G0 passed": "false", "Production implementation authorized": "false",
    "Merge authorized": "false", "Release authorized": "false",
}
FIELD_PATTERN = re.compile(r"^\*\*([^*]+):\*\*\s*(.*?)\s*$", re.MULTILINE)
AUTHORITY_KEYS = (
    "pg_g0_passed", "ready_for_human_gate_decision", "governance_baseline_approved",
    "work_package_accepted", "technology_approved", "identity_provider_approved",
    "qualification_executed", "merge_authorized", "release_authorized",
    "runtime_activation_authorized", "production_implementation_authorized",
)
CLASSIFICATIONS = (
    "STILL_ACTIVE", "RESOLVED_TECHNICALLY_IN_SUBJECT_TREE",
    "HUMAN_DISPOSITION_REQUIRED", "NOT_REEVALUABLE",
)


class BoundInputError(ValueError):
    """Raised when an exact Git-object binding cannot be proven."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )


def _git_text(root: Path, *args: str) -> str | None:
    result = _git(root, *args)
    if result.returncode != 0:
        return None
    try:
        return result.stdout.decode("ascii").strip()
    except UnicodeDecodeError:
        return None


def _object_type(root: Path, object_id: str) -> str | None:
    return _git_text(root, "cat-file", "-t", object_id)


def _commit_tree(root: Path, commit: str) -> str | None:
    if _object_type(root, commit) != "commit":
        return None
    value = _git_text(root, "show", "-s", "--format=%T", commit)
    return value if value and re.fullmatch(r"[0-9a-f]{40}", value) else None


def _is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    return _git(root, "merge-base", "--is-ancestor", ancestor, descendant).returncode == 0


def _tree_entries(root: Path, commit: str) -> tuple[dict[str, dict[str, str]], list[str]]:
    result = _git(root, "ls-tree", "-z", commit)
    if result.returncode != 0:
        return {}, ["SUBJECT ROOT TREE UNAVAILABLE"]
    entries: dict[str, dict[str, str]] = {}
    errors: list[str] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        try:
            header, path_bytes = raw.split(b"\t", 1)
            mode, kind, oid = header.decode("ascii").split(" ", 2)
            path = path_bytes.decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            errors.append("SUBJECT ROOT TREE ENTRY INVALID")
            continue
        entries[path] = {"mode": mode, "type": kind, "blob_oid": oid}
    return entries, errors


def _blob_bytes(root: Path, oid: str) -> bytes | None:
    if _object_type(root, oid) != "blob":
        return None
    result = _git(root, "cat-file", "blob", oid)
    return result.stdout if result.returncode == 0 else None


def _entry_for_path(
    root: Path, commit: str, path: str
) -> tuple[dict[str, str] | None, bytes | None, list[str]]:
    result = _git(root, "ls-tree", "-z", commit, "--", path)
    if result.returncode != 0:
        return None, None, [f"BOUND PATH LOOKUP FAILED: {path}"]
    records = [item for item in result.stdout.split(b"\0") if item]
    if len(records) != 1:
        return None, None, [f"BOUND PATH MISSING OR AMBIGUOUS: {path}"]
    try:
        header, raw_path = records[0].split(b"\t", 1)
        mode, kind, oid = header.decode("ascii").split(" ", 2)
        actual_path = raw_path.decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None, None, [f"BOUND PATH ENTRY INVALID: {path}"]
    if actual_path != path:
        return None, None, [f"BOUND PATH CASE OR NAME INVALID: {path} -> {actual_path}"]
    entry = {"path": actual_path, "mode": mode, "type": kind, "blob_oid": oid}
    if mode != "100644" or kind != "blob":
        return entry, None, [f"BOUND PATH MUST BE REGULAR 100644 BLOB: {path}"]
    data = _blob_bytes(root, oid)
    return entry, data, [] if data is not None else [f"BOUND BLOB UNAVAILABLE: {path}"]


def _parse_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for key, value in FIELD_PATTERN.findall(text):
        fields.setdefault(key.strip(), value.strip())
    return fields


def validate_bound_subject(root: Path, commit: str, expected_tree: str) -> list[str]:
    errors: list[str] = []
    if _object_type(root, commit) != "commit":
        errors.append("SUBJECT COMMIT OBJECT UNAVAILABLE OR NOT A COMMIT")
        return errors
    actual_tree = _commit_tree(root, commit)
    if actual_tree != expected_tree:
        errors.append(f"SUBJECT TREE MISMATCH: expected {expected_tree}, got {actual_tree}")
    if _object_type(root, expected_tree) != "tree":
        errors.append("SUBJECT TREE OBJECT UNAVAILABLE OR NOT A TREE")
    return errors


def bound_input_record(root: Path, commit: str, path: str) -> tuple[dict[str, Any] | None, bytes | None, list[str]]:
    entry, data, errors = _entry_for_path(root, commit, path)
    if entry is None or data is None:
        return None, None, errors
    return {
        "path": path, "mode": entry["mode"], "type": entry["type"],
        "blob_oid": entry["blob_oid"], "bytes": len(data), "sha256": _sha256(data),
    }, data, errors


def inspect_bound_root_controls(
    root: Path, commit: str, expected_tree: str
) -> tuple[list[dict[str, Any]], list[str]]:
    errors = validate_bound_subject(root, commit, expected_tree)
    if errors:
        return [], errors
    entries, tree_errors = _tree_entries(root, commit)
    errors.extend(tree_errors)
    folded: dict[str, list[str]] = {}
    for name in entries:
        folded.setdefault(name.casefold(), []).append(name)
    records: list[dict[str, Any]] = []
    for path, document_id in ROOT_CONTROLS.items():
        actual = folded.get(path.casefold(), [])
        if actual != [path]:
            errors.append(f"BOUND ROOT EXACT NAME INVALID: {path} -> {actual}")
            continue
        entry, data, entry_errors = _entry_for_path(root, commit, path)
        errors.extend(entry_errors)
        if entry is None or data is None:
            continue
        record: dict[str, Any] = {
            "path": path, "mode": entry["mode"], "type": entry["type"],
            "blob_oid": entry["blob_oid"], "bytes": len(data), "sha256": _sha256(data),
            "metadata_valid": False,
        }
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"BOUND ROOT MUST BE UTF-8: {path}")
            records.append(record)
            continue
        if data.startswith(b"\xef\xbb\xbf") or b"\r" in data:
            errors.append(f"BOUND ROOT MUST USE UTF-8 WITHOUT BOM AND LF: {path}")
        fields = _parse_fields(text)
        before = len(errors)
        if fields.get("Document ID") != document_id:
            errors.append(f"BOUND ROOT DOCUMENT ID INVALID: {path}")
        for key, expected in ROOT_FIELDS.items():
            if fields.get(key) != expected:
                errors.append(f"BOUND ROOT FIELD INVALID {path}: {key}")
        for key in ("Owner", "Issued", "Source", "Governing artifacts", "Dependent artifacts"):
            if not fields.get(key):
                errors.append(f"BOUND ROOT FIELD MISSING {path}: {key}")
        for linked in (*ROOT_CONTROLS, "README.md"):
            if f"]({linked})" not in text:
                errors.append(f"BOUND ROOT LINK MISSING {path}: {linked}")
        for config in (
            "/opt/bizera-smartthink/config/agents.yaml",
            "/opt/bizera-smartthink/config/routing.yaml",
            "/opt/bizera-smartthink/config/system.yaml",
        ):
            if config not in text:
                errors.append(f"BOUND ROOT CONFIG REFERENCE MISSING {path}: {config}")
        if "UNRESOLVED_EXTERNAL_DEPENDENCY" not in text:
            errors.append(f"BOUND ROOT CONFIG STATE MISSING: {path}")
        record["metadata_valid"] = len(errors) == before
        records.append(record)
    return records, errors


def validate_bound_root_controls(root: Path, commit: str, expected_tree: str) -> list[str]:
    return inspect_bound_root_controls(root, commit, expected_tree)[1]


def classify_blocker(text: str, root: Path, commit: str, expected_tree: str) -> dict[str, Any]:
    classification = "STILL_ACTIVE"
    observation = "No exact subject-tree machine rule resolves this historical blocker."
    evidence: list[str] = []
    if all(name in text for name in ROOT_CONTROLS):
        root_errors = validate_bound_root_controls(root, commit, expected_tree)
        if not root_errors:
            classification = "RESOLVED_TECHNICALLY_IN_SUBJECT_TREE"
            observation = "The five exact root-control blobs in the bound subject tree pass mode, type, byte and metadata checks."
            evidence = [f"{commit}:{path}" for path in ROOT_CONTROLS]
        else:
            observation = "The bound subject tree fails one or more exact root-control checks."
            evidence = [f"git:{commit}^{'{tree}'}"]
    elif "exact-SHA technical review" in text or "technical review of this exact docket" in text:
        observation = "No structured independent exact-SHA receipt is bound to the historical docket; CI or PR prose is not authority."
        evidence = [f"{commit}:{DOCKET_PATH}"]
    elif any(marker in text for marker in (
        "draft and ineffective", "remain ineffective", "remains ineffective", "remain proposed",
        "human authority identities", "authority identity registry", "authority source is not effective",
        "authority matrix has no action", "lack named checkers", "sources conflict", "concurrence",
    )):
        classification = "HUMAN_DISPOSITION_REQUIRED"
        observation = "This blocker requires attributable human disposition or an effective authority source and cannot be machine-resolved."
        evidence = [f"{commit}:{DOCKET_PATH}"]
    return {
        "blocker_id": "PG-G0-HIST-000", "original_text": text,
        "original_sha256": _sha256(text.encode("utf-8")), "classification": classification,
        "current_observation": observation, "machine_evidence_refs": evidence,
    }


def build_projection(
    root: Path = ROOT,
    subject_commit: str = SUBJECT_COMMIT,
    subject_tree: str = SUBJECT_TREE,
    carrier_commit: str = CARRIER_COMMIT,
    carrier_tree: str = CARRIER_TREE,
) -> dict[str, Any]:
    subject_errors = validate_bound_subject(root, subject_commit, subject_tree)
    carrier_errors = validate_bound_subject(root, carrier_commit, carrier_tree)
    if subject_errors or carrier_errors:
        raise BoundInputError("; ".join(subject_errors + [f"CARRIER {item}" for item in carrier_errors]))
    historical_record, historical_bytes, historical_errors = bound_input_record(root, subject_commit, HISTORICAL_PATH)
    docket_record, docket_bytes, docket_errors = bound_input_record(root, subject_commit, DOCKET_PATH)
    if historical_errors or docket_errors or historical_record is None or docket_record is None or historical_bytes is None or docket_bytes is None:
        raise BoundInputError("; ".join(historical_errors + docket_errors))
    try:
        historical = json.loads(historical_bytes.decode("utf-8"))
        docket = json.loads(docket_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BoundInputError(f"BOUND JSON INPUT INVALID: {exc}") from exc
    blockers = historical.get("blockers")
    if not isinstance(blockers, list) or not all(isinstance(item, str) and item for item in blockers):
        raise BoundInputError("BOUND HISTORICAL BLOCKERS INVALID")
    binding = docket.get("repository_binding")
    if not isinstance(binding, dict):
        raise BoundInputError("BOUND DOCKET REPOSITORY BINDING INVALID")
    root_records, root_errors = inspect_bound_root_controls(root, subject_commit, subject_tree)
    assessments: list[dict[str, Any]] = []
    for index, blocker in enumerate(blockers, 1):
        item = classify_blocker(blocker, root, subject_commit, subject_tree)
        item["blocker_id"] = f"PG-G0-HIST-{index:03d}"
        assessments.append(item)
    counts = {name: sum(item["classification"] == name for item in assessments) for name in CLASSIFICATIONS}
    active = len(assessments) - counts["RESOLVED_TECHNICALLY_IN_SUBJECT_TREE"]
    head = _git_text(root, "rev-parse", "HEAD")
    return {
        "$schema": SCHEMA_ID,
        "projection_id": "PG-G0-BOUND-TREE-READINESS-002",
        "version": "0.2.0-draft", "status": "NOT_READY", "generated_at": GENERATED_AT,
        "historical_view": {
            "authority_readiness_input": historical_record, "docket_input": docket_record,
            "docket_bound_commit_sha": binding.get("commit_sha"), "docket_bound_tree_sha": binding.get("tree_sha"),
            "blocker_count": len(blockers), "rejected_projection_ref": REJECTED_PROJECTION_PATH,
            "rejected_projection_status": "REJECTED_REQUEST_CHANGES",
        },
        "subject_tree": {
            "repository_ref": "bstBizEra/bopen", "commit_sha": subject_commit, "tree_sha": subject_tree,
            "commit_object_verified": True, "tree_object_verified": True, "root_controls_valid": not root_errors,
            "root_control_errors": root_errors, "root_controls": root_records,
        },
        "carrier_provenance": {
            "base_commit_sha": carrier_commit, "base_tree_sha": carrier_tree,
            "subject_is_ancestor_of_carrier": _is_ancestor(root, subject_commit, carrier_commit),
            "carrier_is_ancestor_of_head": bool(head and _is_ancestor(root, carrier_commit, head)),
            "live_worktree_bytes_used": False,
        },
        "blocker_assessments": assessments,
        "summary": {
            "historical_blockers": len(assessments), "still_active": counts["STILL_ACTIVE"],
            "resolved_technically_in_subject_tree": counts["RESOLVED_TECHNICALLY_IN_SUBJECT_TREE"],
            "human_disposition_required": counts["HUMAN_DISPOSITION_REQUIRED"],
            "not_reevaluable": counts["NOT_REEVALUABLE"], "active_blockers": active,
            "ready_for_human_gate_decision": False,
        },
        "authority": {key: False for key in AUTHORITY_KEYS},
        "limitation": "This successor observes only exact Git objects in the bound subject tree and records the descendant carrier separately. It does not amend historical evidence, accept review, supply human authority, authorize qualification, pass PG-G0, merge, release, activate runtime, or authorize production implementation.",
    }


def rendered_projection(
    root: Path = ROOT,
    subject_commit: str = SUBJECT_COMMIT,
    subject_tree: str = SUBJECT_TREE,
    carrier_commit: str = CARRIER_COMMIT,
    carrier_tree: str = CARRIER_TREE,
) -> str:
    return json.dumps(
        build_projection(root, subject_commit, subject_tree, carrier_commit, carrier_tree),
        indent=2, ensure_ascii=False,
    ) + "\n"


def validate_projection(data: object, root: Path = ROOT) -> list[str]:
    if not isinstance(data, dict):
        return ["projection must be an object"]
    try:
        expected = build_projection(root)
    except BoundInputError as exc:
        return [f"bound projection source invalid: {exc}"]
    errors = [] if data == expected else ["projection differs from deterministic exact-object projection"]
    if any(data.get("authority", {}).get(key) is not False for key in AUTHORITY_KEYS):
        errors.append("all authority flags must remain false")
    if data.get("carrier_provenance", {}).get("live_worktree_bytes_used") is not False:
        errors.append("live worktree bytes must not be attributed to subject tree")
    if data.get("summary", {}).get("ready_for_human_gate_decision") is not False:
        errors.append("human gate readiness must remain false")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    target = ROOT / REPORT_PATH
    try:
        rendered = rendered_projection(ROOT)
    except BoundInputError as exc:
        print(f"bOPEN PG-G0 bound-tree readiness successor: FAIL\n- {exc}")
        return 1
    if args.write:
        if target.exists():
            print(f"bOPEN PG-G0 bound-tree readiness successor: REFUSED (create-once artifact exists: {REPORT_PATH.as_posix()})")
            return 1
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"bOPEN PG-G0 bound-tree readiness successor: WROTE {REPORT_PATH.as_posix()}")
        return 0
    if not target.is_file():
        print(f"bOPEN PG-G0 bound-tree readiness successor: FAIL\n- artifact missing: {REPORT_PATH.as_posix()}")
        return 1
    try:
        actual = target.read_text(encoding="utf-8")
        parsed = json.loads(actual)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"bOPEN PG-G0 bound-tree readiness successor: FAIL\n- artifact invalid: {exc}")
        return 1
    errors = validate_projection(parsed, ROOT)
    if actual != rendered:
        errors.append("artifact bytes are stale or non-canonical")
    if errors:
        print("bOPEN PG-G0 bound-tree readiness successor: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("bOPEN PG-G0 bound-tree readiness successor: PASS")
    print(f"Historical blockers: {parsed['summary']['historical_blockers']}; active: {parsed['summary']['active_blockers']}; live bytes used: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
