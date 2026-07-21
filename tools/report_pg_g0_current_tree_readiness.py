#!/usr/bin/env python3
"""Build/check a fail-closed PG-G0 current-tree readiness projection."""

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
SCHEMA_ID = "bopen://schemas/governance/pg-g0-current-tree-readiness/0.1.0-draft"
SCHEMA_PATH = Path("contracts/governance/pg-g0-current-tree-readiness.schema.json")
HISTORICAL_PATH = Path("artifacts/validation/program-g0-authority-readiness.json")
DOCKET_PATH = Path("docs/00-governance/authority-dockets/PG-G0-AUTH-001.json")
REPORT_PATH = Path("artifacts/validation/pg-g0-current-tree-readiness-001.json")
EVALUATION_COMMIT = "4a98cb45748ded2b209786bcb9242664aa0795aa"
EVALUATION_TREE = "8900b871e1f436d5ee21919764a31f955f42d5bf"
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
CLASSIFICATIONS = {
    "STILL_ACTIVE", "RESOLVED_TECHNICALLY_IN_CURRENT_TREE",
    "HUMAN_DISPOSITION_REQUIRED", "NOT_REEVALUABLE",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)


def _parse_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for key, value in FIELD_PATTERN.findall(text):
        fields.setdefault(key.strip(), value.strip())
    return fields


def validate_projection_root_controls(root: Path = ROOT) -> list[str]:
    """Validate only the exact current-tree root surfaces; no package/history inference."""
    errors: list[str] = []
    try:
        names = [item.name for item in root.iterdir() if item.is_file() or item.is_symlink()]
    except OSError as exc:
        return [f"ROOT CONTROL DIRECTORY INVALID: {exc}"]
    folded: dict[str, list[str]] = {}
    for name in names:
        folded.setdefault(name.casefold(), []).append(name)
    for rel, document_id in ROOT_CONTROLS.items():
        actual = folded.get(rel.casefold(), [])
        if actual != [rel]:
            errors.append(f"ROOT CONTROL EXACT NAME INVALID: {rel} -> {actual}")
            continue
        path = root / rel
        if path.is_symlink() or not path.is_file():
            errors.append(f"ROOT CONTROL MUST BE REGULAR FILE: {rel}")
            continue
        try:
            data = path.read_bytes()
            text = data.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"ROOT CONTROL MUST BE READABLE UTF-8: {rel}: {exc}")
            continue
        if data.startswith(b"\xef\xbb\xbf") or b"\r" in data:
            errors.append(f"ROOT CONTROL MUST USE UTF-8 WITHOUT BOM AND LF: {rel}")
        fields = _parse_fields(text)
        if fields.get("Document ID") != document_id:
            errors.append(f"ROOT CONTROL DOCUMENT ID INVALID: {rel}")
        for key, expected in ROOT_FIELDS.items():
            if fields.get(key) != expected:
                errors.append(f"ROOT CONTROL FIELD INVALID {rel}: {key}")
        for required in ("Owner", "Issued", "Source", "Governing artifacts", "Dependent artifacts"):
            if not fields.get(required):
                errors.append(f"ROOT CONTROL FIELD MISSING {rel}: {required}")
        for linked in (*ROOT_CONTROLS, "README.md"):
            if f"]({linked})" not in text:
                errors.append(f"ROOT CONTROL LINK MISSING {rel}: {linked}")
        for config in (
            "/opt/bizera-smartthink/config/agents.yaml",
            "/opt/bizera-smartthink/config/routing.yaml",
            "/opt/bizera-smartthink/config/system.yaml",
        ):
            if config not in text:
                errors.append(f"ROOT CONTROL CONFIG REFERENCE MISSING {rel}: {config}")
        if "UNRESOLVED_EXTERNAL_DEPENDENCY" not in text:
            errors.append(f"ROOT CONTROL CONFIG STATE MISSING: {rel}")
    return errors


def classify_blocker(text: str, root: Path = ROOT) -> dict[str, Any]:
    """Classify one historical blocker; unknown and review claims fail closed."""
    classification = "STILL_ACTIVE"
    observation = "No bounded machine rule resolves this historical blocker."
    evidence: list[str] = []
    root_blocker = all(name in text for name in ROOT_CONTROLS)
    if root_blocker:
        root_errors = validate_projection_root_controls(root)
        if not root_errors:
            classification = "RESOLVED_TECHNICALLY_IN_CURRENT_TREE"
            observation = "The five exact current-tree root controls pass bounded regular-file and metadata checks."
            evidence = [*ROOT_CONTROLS, "tools/validate_root_control_surfaces.py"]
        else:
            observation = "The current-tree root controls fail one or more bounded checks."
            evidence = ["tools/report_pg_g0_current_tree_readiness.py"]
    elif "exact-SHA technical review" in text or "technical review of this exact docket" in text:
        observation = "No structured independent exact-SHA review receipt is bound to the historical docket; CI or PR text is not authority."
        evidence = [DOCKET_PATH.as_posix()]
    else:
        human_markers = (
            "draft and ineffective", "remain ineffective", "remains ineffective",
            "remain proposed", "human authority identities", "authority identity registry",
            "authority source is not effective", "authority matrix has no action",
            "lack named checkers", "sources conflict", "concurrence",
        )
        if any(marker in text for marker in human_markers):
            classification = "HUMAN_DISPOSITION_REQUIRED"
            observation = "This blocker requires attributable human disposition or an effective authority source and cannot be machine-resolved."
            evidence = [DOCKET_PATH.as_posix()]
    return {
        "blocker_id": "PG-G0-HIST-000",
        "original_text": text,
        "original_sha256": _sha256(text.encode("utf-8")),
        "classification": classification,
        "current_observation": observation,
        "machine_evidence_refs": evidence,
    }


def build_projection(root: Path = ROOT) -> dict[str, Any]:
    historical_bytes = (root / HISTORICAL_PATH).read_bytes()
    docket_bytes = (root / DOCKET_PATH).read_bytes()
    historical = json.loads(historical_bytes)
    docket = json.loads(docket_bytes)
    blockers = historical.get("blockers")
    if not isinstance(blockers, list) or not all(isinstance(item, str) and item for item in blockers):
        raise ValueError("historical blocker array must contain non-empty strings")
    binding = docket.get("repository_binding", {})
    root_errors = validate_projection_root_controls(root)
    head = _git(root, "rev-parse", "HEAD")
    ancestor = head.returncode == 0 and _git(root, "merge-base", "--is-ancestor", EVALUATION_COMMIT, head.stdout.strip()).returncode == 0
    tree = _git(root, "show", "-s", "--format=%T", EVALUATION_COMMIT)
    if tree.returncode != 0 or tree.stdout.strip() != EVALUATION_TREE:
        ancestor = False
    assessments = []
    for index, blocker in enumerate(blockers, 1):
        item = classify_blocker(blocker, root)
        item["blocker_id"] = f"PG-G0-HIST-{index:03d}"
        assessments.append(item)
    counts = {name: sum(item["classification"] == name for item in assessments) for name in CLASSIFICATIONS}
    active = len(assessments) - counts["RESOLVED_TECHNICALLY_IN_CURRENT_TREE"]
    return {
        "$schema": SCHEMA_ID,
        "projection_id": "PG-G0-CURRENT-TREE-READINESS-001",
        "version": "0.1.0-draft",
        "status": "NOT_READY",
        "generated_at": GENERATED_AT,
        "historical_view": {
            "artifact_ref": HISTORICAL_PATH.as_posix(), "artifact_sha256": _sha256(historical_bytes), "artifact_bytes": len(historical_bytes),
            "docket_ref": DOCKET_PATH.as_posix(), "docket_sha256": _sha256(docket_bytes), "docket_bytes": len(docket_bytes),
            "bound_commit_sha": binding.get("commit_sha"), "bound_tree_sha": binding.get("tree_sha"), "blocker_count": len(blockers),
        },
        "current_tree": {
            "repository_ref": "bstBizEra/bopen", "evaluation_commit_sha": EVALUATION_COMMIT, "evaluation_tree_sha": EVALUATION_TREE,
            "evaluation_commit_is_ancestor": ancestor, "root_controls_valid": not root_errors, "root_control_errors": root_errors,
        },
        "blocker_assessments": assessments,
        "summary": {
            "historical_blockers": len(assessments), "still_active": counts["STILL_ACTIVE"],
            "resolved_technically_in_current_tree": counts["RESOLVED_TECHNICALLY_IN_CURRENT_TREE"],
            "human_disposition_required": counts["HUMAN_DISPOSITION_REQUIRED"], "not_reevaluable": counts["NOT_REEVALUABLE"],
            "active_blockers": active, "ready_for_human_gate_decision": False,
        },
        "authority": {key: False for key in AUTHORITY_KEYS},
        "limitation": "This deterministic projection records current-tree technical observations only. It does not amend historical evidence, accept a review, supply human authority, pass PG-G0, authorize qualification, merge, release, runtime activation, or production implementation.",
    }


def rendered_projection(root: Path = ROOT) -> str:
    return json.dumps(build_projection(root), indent=2, ensure_ascii=False) + "\n"


def validate_projection(data: object, root: Path = ROOT) -> list[str]:
    """Fail closed by requiring exact deterministic structure and current values."""
    if not isinstance(data, dict):
        return ["projection must be an object"]
    try:
        expected = build_projection(root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"projection source invalid: {exc}"]
    errors: list[str] = []
    if data != expected:
        errors.append("projection differs from deterministic current-tree projection")
    if any(data.get("authority", {}).get(key) is not False for key in AUTHORITY_KEYS):
        errors.append("all authority flags must remain false")
    if data.get("summary", {}).get("ready_for_human_gate_decision") is not False:
        errors.append("human gate readiness must remain false")
    if data.get("current_tree", {}).get("evaluation_commit_is_ancestor") is not True:
        errors.append("authorized evaluation commit must remain an ancestor")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    output = ROOT / REPORT_PATH
    try:
        rendered = rendered_projection(ROOT)
    except Exception as exc:
        print(f"bOPEN PG-G0 current-tree readiness: FAIL\n- {exc}")
        return 1
    if args.write:
        if output.exists():
            print(f"bOPEN PG-G0 current-tree readiness: REFUSED (create-once artifact exists: {REPORT_PATH.as_posix()})")
            return 1
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"bOPEN PG-G0 current-tree readiness: WROTE {REPORT_PATH.as_posix()}")
        return 0
    if not output.is_file():
        print(f"bOPEN PG-G0 current-tree readiness: FAIL\n- artifact missing: {REPORT_PATH.as_posix()}")
        return 1
    try:
        actual = output.read_text(encoding="utf-8")
        parsed = json.loads(actual)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"bOPEN PG-G0 current-tree readiness: FAIL\n- artifact invalid: {exc}")
        return 1
    errors = validate_projection(parsed, ROOT)
    if actual != rendered:
        errors.append("artifact bytes are stale or non-canonical")
    if errors:
        print("bOPEN PG-G0 current-tree readiness: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("bOPEN PG-G0 current-tree readiness: PASS")
    print(f"Historical blockers: {parsed['summary']['historical_blockers']}; active: {parsed['summary']['active_blockers']}; authority flags: all false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
