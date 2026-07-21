#!/usr/bin/env python3
"""Fail-closed validator for the draft TECH-P0-01 qualification contracts."""

from __future__ import annotations

import argparse
import json
import math
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

try:
    from tools.validate_qualification_common import (
        NON_AUTHORITY_FLAGS,
        exact_keys,
        normalized_path,
        read_json,
        resolve_repo_path,
        sha256_file,
        validate_catalog_graph,
        validate_digest_binding,
    )
except ModuleNotFoundError:
    from validate_qualification_common import (
        NON_AUTHORITY_FLAGS,
        exact_keys,
        normalized_path,
        read_json,
        resolve_repo_path,
        sha256_file,
        validate_catalog_graph,
        validate_digest_binding,
    )


ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path("contracts/qualification/technology/TECH-P0-01-SCHEMA-CATALOG.json")
COMMON_CATALOG = Path("contracts/qualification/common/QUAL-P0-00-SCHEMA-CATALOG.json")
PROGRAM_GOAL = Path("contracts/governance/program-goal.requirements.json")
MANIFEST = Path("docs/manifests/TECH-P0-01-PACKAGE-MANIFEST.json")
COMMON_CATALOG_SHA256 = "803500ff8dd12e17531872482875dcf67fa8f617de45c11318a55ba8ed8b8450"
BASE_COMMIT = "a2fc4b1f907b17911ffbd3cb8e0992b806c90bb6"
BASE_TREE = "a5a63d2fb882939f176139c9f276a8d44faaf6d9"

PACKAGE_PATHS = (
    "contracts/qualification/technology/TECH-P0-01-SCHEMA-CATALOG.json",
    "contracts/qualification/technology/artifact-digest-inventory.schema.json",
    "contracts/qualification/technology/candidate-scorecard.schema.json",
    "contracts/qualification/technology/case-result.schema.json",
    "contracts/qualification/technology/command-evidence.schema.json",
    "docs/evidence/EVD-TECH-001-technology-qualification.md",
    "docs/work-packages/TECH-P0-01.md",
    "tests/qualification/test_technology_qualification.py",
    "tools/validate_technology_qualification.py",
)

REQUIRED_CASE_CATEGORIES = {
    "TENANT_RLS_NEGATIVE",
    "TENANT_POOL_NEGATIVE",
    "TENANT_CONTEXT_NEGATIVE",
    "OBSERVABILITY",
    "OUTBOX",
    "RECOVERY",
    "SUPPLY_CHAIN",
}
NEGATIVE_CATEGORIES = {
    "TENANT_RLS_NEGATIVE",
    "TENANT_POOL_NEGATIVE",
    "TENANT_CONTEXT_NEGATIVE",
}
EVIDENCE_CATEGORIES = {"OBSERVABILITY", "OUTBOX", "RECOVERY", "SUPPLY_CHAIN"}


def validate_false_flags(value: Any, label: str) -> list[str]:
    errors = exact_keys(value, NON_AUTHORITY_FLAGS, label)
    if isinstance(value, dict):
        errors.extend(
            f"{label} {name} must be false"
            for name in sorted(NON_AUTHORITY_FLAGS)
            if value.get(name) is not False
        )
    return errors


def program_goal_ids(root: Path = ROOT) -> set[str]:
    data = read_json(root / PROGRAM_GOAL)
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise ValueError("Program Goal item catalog missing")
    identifiers = [item.get("id") for item in items if isinstance(item, dict)]
    if len(identifiers) != len(items) or any(not isinstance(item, str) for item in identifiers):
        raise ValueError("Program Goal item ID invalid")
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Program Goal item ID duplicate")
    return set(identifiers)


def validate_case_result(data: Any, root: Path | None = None) -> list[str]:
    required = {
        "$schema", "case_id", "version", "status", "work_package_id",
        "qualification_run_id", "candidate_id", "category", "mandatory", "result",
        "requirement_ids", "command_evidence_refs", "artifact_refs", "negative_case",
        "limitation", "non_authority_flags",
    }
    errors = exact_keys(data, required, "case")
    if not isinstance(data, dict):
        return errors
    category = data.get("category")
    if category not in REQUIRED_CASE_CATEGORIES | {"OTHER_PROGRAM_GOAL"}:
        errors.append("case category invalid")
    if data.get("status") != "draft" or data.get("work_package_id") != "TECH-P0-01":
        errors.append("case must remain TECH-P0-01 draft")
    errors.extend(validate_false_flags(data.get("non_authority_flags"), "case flags"))
    if category in NEGATIVE_CATEGORIES:
        if data.get("negative_case") is not True or data.get("mandatory") is not True:
            errors.append(f"{category} must be declared mandatory negative case")
    elif data.get("negative_case") is not False:
        errors.append(f"{category} cannot be declared negative case")
    if data.get("result") == "PASS":
        if not data.get("command_evidence_refs") or not data.get("artifact_refs"):
            errors.append("passing case requires command and artifact evidence")
    if category in EVIDENCE_CATEGORIES and (
        not data.get("command_evidence_refs") or not data.get("artifact_refs")
    ):
        errors.append(f"{category} requires command and artifact evidence")
    if not isinstance(data.get("limitation"), str) or not data["limitation"].strip():
        errors.append("case coverage limitation required")
    for index, reference in enumerate(data.get("command_evidence_refs", [])):
        if not normalized_path(reference):
            errors.append(f"case command evidence ref {index} invalid")
    for index, binding in enumerate(data.get("artifact_refs", [])):
        if root is None:
            if not isinstance(binding, dict):
                errors.append(f"case artifact ref {index} malformed")
        else:
            errors.extend(validate_digest_binding(binding, root, f"case artifact ref {index}"))
    return sorted(set(errors))


def validate_command_evidence(data: Any, root: Path | None = None) -> list[str]:
    required = {
        "$schema", "command_evidence_id", "version", "status", "work_package_id",
        "qualification_run_id", "candidate_id", "case_id", "argv", "working_directory", "started_at",
        "completed_at", "exit_code", "stdout_artifact", "stderr_artifact",
        "environment_manifest", "secret_scan_passed", "synthetic_data_only",
        "deterministic_replay", "non_authority_flags",
    }
    errors = exact_keys(data, required, "command evidence")
    if not isinstance(data, dict):
        return errors
    if data.get("status") != "draft" or data.get("work_package_id") != "TECH-P0-01":
        errors.append("command evidence must remain TECH-P0-01 draft")
    argv = data.get("argv")
    if not isinstance(argv, list) or not argv or any(not isinstance(item, str) or not item for item in argv):
        errors.append("command evidence argv must be non-empty string array")
    if not normalized_path(data.get("working_directory")):
        errors.append("command evidence working directory invalid")
    for field in ("secret_scan_passed", "synthetic_data_only", "deterministic_replay"):
        if data.get(field) is not True:
            errors.append(f"command evidence {field} must be true")
    errors.extend(validate_false_flags(data.get("non_authority_flags"), "command evidence flags"))
    if root is not None:
        for field in ("stdout_artifact", "stderr_artifact", "environment_manifest"):
            errors.extend(validate_digest_binding(data.get(field), root, f"command evidence {field}"))
    return sorted(set(errors))


def validate_inventory(data: Any, root: Path = ROOT) -> list[str]:
    required = {
        "$schema", "inventory_id", "version", "status", "work_package_id",
        "qualification_run_id", "generated_at", "raw_bytes", "records",
        "non_authority_flags",
    }
    errors = exact_keys(data, required, "inventory")
    if not isinstance(data, dict):
        return errors
    if data.get("raw_bytes") is not True:
        errors.append("inventory must bind raw bytes")
    if data.get("status") != "draft" or data.get("work_package_id") != "TECH-P0-01":
        errors.append("inventory must remain TECH-P0-01 draft")
    errors.extend(validate_false_flags(data.get("non_authority_flags"), "inventory flags"))
    seen: set[str] = set()
    for index, record in enumerate(data.get("records", [])):
        label = f"inventory record {index}"
        if not isinstance(record, dict):
            errors.append(f"{label} must be object")
            continue
        errors.extend(validate_digest_binding(record, root, label))
        path_value = record.get("path")
        if path_value in seen:
            errors.append(f"{label} duplicate path")
        if isinstance(path_value, str):
            seen.add(path_value)
        path = resolve_repo_path(root, path_value)
        if path is None or not path.is_file():
            errors.append(f"{label} path missing or invalid")
            continue
        raw = path.read_bytes()
        if record.get("canonicalization") != "RAW_BYTES":
            errors.append(f"{label} canonicalization must be RAW_BYTES")
        if record.get("byte_length") != len(raw):
            errors.append(f"{label} byte length mismatch")
        if record.get("sha256") != sha256(raw).hexdigest():
            errors.append(f"{label} digest mismatch")
    return sorted(set(errors))


def _binding_key(binding: Any) -> str | None:
    if not isinstance(binding, dict):
        return None
    return json.dumps(binding, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def validate_scorecard(
    data: Any,
    cases: list[dict[str, Any]],
    root: Path = ROOT,
    inventory: Any | None = None,
) -> list[str]:
    required = {
        "$schema", "scorecard_id", "version", "status", "work_package_id",
        "qualification_run_id", "candidate_id", "candidate_name", "vendor_disposition",
        "common_catalog_binding", "program_goal_catalog_binding", "mandatory_criteria",
        "weighted_criteria", "program_goal_coverage", "weighted_score",
        "recommendation", "limitations", "non_authority_flags",
    }
    errors = exact_keys(data, required, "scorecard")
    if not isinstance(data, dict):
        return errors
    if data.get("status") != "draft" or data.get("work_package_id") != "TECH-P0-01":
        errors.append("scorecard must remain TECH-P0-01 draft")
    if data.get("vendor_disposition") != "UNDECIDED":
        errors.append("scorecard cannot select a vendor")
    errors.extend(validate_false_flags(data.get("non_authority_flags"), "scorecard flags"))

    common = data.get("common_catalog_binding")
    errors.extend(validate_digest_binding(common, root, "scorecard common catalog binding"))
    if not isinstance(common, dict) or common.get("path") != COMMON_CATALOG.as_posix() or common.get("sha256") != COMMON_CATALOG_SHA256:
        errors.append("scorecard common catalog binding drift")
    goal = data.get("program_goal_catalog_binding")
    errors.extend(validate_digest_binding(goal, root, "scorecard Program Goal binding"))
    expected_goal_sha = sha256_file(root / PROGRAM_GOAL)
    if not isinstance(goal, dict) or goal.get("path") != PROGRAM_GOAL.as_posix() or goal.get("sha256") != expected_goal_sha:
        errors.append("scorecard Program Goal binding drift")

    expected_goal_ids = program_goal_ids(root)
    coverage = data.get("program_goal_coverage")
    if not isinstance(coverage, list):
        errors.append("scorecard Program Goal coverage missing")
    else:
        ids = [item.get("requirement_id") for item in coverage if isinstance(item, dict)]
        expected = expected_goal_ids
        if len(ids) != len(coverage) or len(ids) != len(set(ids)):
            errors.append("Program Goal coverage IDs must be unique")
        if set(ids) != expected:
            errors.append("Program Goal coverage must include every catalog item exactly once")
        for item in coverage:
            if not isinstance(item, dict) or not isinstance(item.get("coverage_limit"), str) or not item["coverage_limit"].strip():
                errors.append("every Program Goal coverage item requires an explicit limit")
            elif item.get("coverage_level") == "DIRECT" and not item.get("case_ids"):
                errors.append("direct Program Goal coverage requires case IDs")

    case_by_id = {item.get("case_id"): item for item in cases if isinstance(item, dict)}
    if len(case_by_id) != len(cases):
        errors.append("case IDs must be unique")
    if isinstance(coverage, list):
        for item in coverage:
            item_case_ids = item.get("case_ids", []) if isinstance(item, dict) else []
            for case_id in item_case_ids:
                if case_id not in case_by_id:
                    errors.append(f"Program Goal coverage references unknown case: {case_id}")
            if isinstance(item, dict) and item.get("coverage_level") == "DIRECT":
                requirement_id = item.get("requirement_id")
                if not any(
                    requirement_id in case_by_id.get(case_id, {}).get("requirement_ids", [])
                    for case_id in item_case_ids
                ):
                    errors.append(f"DIRECT coverage lacks a relevant case: {requirement_id}")
    categories = {item.get("category") for item in cases if isinstance(item, dict)}
    missing_categories = REQUIRED_CASE_CATEGORIES - categories
    if missing_categories:
        errors.append("required qualification case categories missing: " + ", ".join(sorted(missing_categories)))
    for case in cases:
        errors.extend(validate_case_result(case, root))
        if case.get("qualification_run_id") != data.get("qualification_run_id") or case.get("candidate_id") != data.get("candidate_id"):
            errors.append("case run/candidate binding mismatch")
        if not set(case.get("requirement_ids", [])).issubset(expected_goal_ids):
            errors.append(f"case references unknown Program Goal item: {case.get('case_id')}")

    inventory_records: dict[str, dict[str, Any]] = {}
    if inventory is None:
        errors.append("scorecard evidence inventory required")
    else:
        errors.extend(validate_inventory(inventory, root))
        if isinstance(inventory, dict):
            if inventory.get("qualification_run_id") != data.get("qualification_run_id"):
                errors.append("inventory run binding mismatch")
            for record in inventory.get("records", []):
                if isinstance(record, dict) and isinstance(record.get("path"), str):
                    inventory_records[record["path"]] = record

    def reconcile(binding: Any, label: str) -> None:
        if not isinstance(binding, dict) or not isinstance(binding.get("path"), str):
            errors.append(f"{label} malformed or missing artifact binding")
            return
        inventory_binding = inventory_records.get(binding["path"])
        if inventory_binding is None or _binding_key(inventory_binding) != _binding_key(binding):
            errors.append(f"{label} not reconciled with inventory")

    for case in cases:
        case_id = case.get("case_id")
        for index, binding in enumerate(case.get("artifact_refs", [])):
            reconcile(binding, f"case {case_id} artifact {index}")
        for command_ref in case.get("command_evidence_refs", []):
            command_path = resolve_repo_path(root, command_ref)
            if command_path is None or not command_path.is_file():
                errors.append(f"case {case_id} command evidence missing or invalid: {command_ref}")
                continue
            try:
                command = read_json(command_path)
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"case {case_id} command evidence unreadable: {command_ref}: {exc}")
                continue
            errors.extend(validate_command_evidence(command, root))
            if not isinstance(command, dict) or (
                command.get("qualification_run_id") != data.get("qualification_run_id")
                or command.get("candidate_id") != data.get("candidate_id")
                or command.get("case_id") != case_id
            ):
                errors.append(f"case {case_id} command evidence binding mismatch: {command_ref}")
            if isinstance(command, dict):
                for field in ("stdout_artifact", "stderr_artifact", "environment_manifest"):
                    reconcile(command.get(field), f"command {command_ref} {field}")

    mandatory = data.get("mandatory_criteria")
    weighted = data.get("weighted_criteria")
    if not isinstance(mandatory, list) or not mandatory:
        errors.append("mandatory criteria missing")
        mandatory_failed = True
    else:
        referenced_list = [case_id for item in mandatory if isinstance(item, dict) for case_id in item.get("case_ids", [])]
        referenced = set(referenced_list)
        mandatory_case_ids = {item.get("case_id") for item in cases if item.get("mandatory") is True}
        if referenced != mandatory_case_ids or len(referenced_list) != len(referenced):
            errors.append("mandatory criteria must cover every mandatory case exactly")
        mandatory_failed = any(case_by_id.get(case_id, {}).get("result") != "PASS" for case_id in mandatory_case_ids)
        for item in mandatory:
            item_case_ids = item.get("case_ids", []) if isinstance(item, dict) else []
            for case_id in item_case_ids:
                if case_id not in case_by_id:
                    errors.append(f"mandatory criterion references unknown case: {case_id}")
            results = [case_by_id[case_id].get("result") for case_id in item_case_ids if case_id in case_by_id]
            expected_result = "FAIL" if "FAIL" in results else ("NOT_RUN" if "NOT_RUN" in results else "PASS")
            if isinstance(item, dict) and item.get("result") != expected_result:
                errors.append(f"mandatory criterion result mismatch: {item.get('criterion_id')}")

    if not isinstance(weighted, list) or not weighted:
        errors.append("weighted criteria missing")
    else:
        weights = [item.get("weight") for item in weighted if isinstance(item, dict)]
        if len(weights) != len(weighted) or any(not isinstance(value, (int, float)) for value in weights) or not math.isclose(sum(weights), 100.0):
            errors.append("weighted criteria weights must total 100")
        for item in weighted:
            for case_id in item.get("case_ids", []) if isinstance(item, dict) else []:
                if case_id not in case_by_id:
                    errors.append(f"weighted criterion references unknown case: {case_id}")

    if mandatory_failed:
        if data.get("weighted_score") is not None:
            errors.append("mandatory failure must stop before weighted score")
        if isinstance(weighted, list) and any(item.get("score") is not None for item in weighted if isinstance(item, dict)):
            errors.append("mandatory failure must leave weighted criterion scores null")
        if data.get("recommendation") != "NOT_QUALIFIED":
            errors.append("mandatory failure requires NOT_QUALIFIED")
    elif isinstance(weighted, list):
        if any(item.get("score") is None for item in weighted if isinstance(item, dict)):
            errors.append("weighted scores required after mandatory pass")
        else:
            calculated = sum(item["weight"] * item["score"] for item in weighted) / 100
            if not isinstance(data.get("weighted_score"), (int, float)) or not math.isclose(data["weighted_score"], calculated):
                errors.append("weighted score calculation mismatch")
        if data.get("recommendation") != "PROPOSAL_ONLY":
            errors.append("passing scorecard recommendation remains PROPOSAL_ONLY")
    return sorted(set(errors))


def build_package_manifest(root: Path = ROOT) -> dict[str, Any]:
    records = []
    for relative in PACKAGE_PATHS:
        path = resolve_repo_path(root, relative)
        if path is None or not path.is_file():
            raise FileNotFoundError(relative)
        raw = path.read_bytes()
        records.append({"path": relative, "sha256": sha256(raw).hexdigest(), "bytes": len(raw)})
    return {
        "manifest_id": "TECH-P0-01-PACKAGE-MANIFEST",
        "version": "0.1.0-draft",
        "status": "draft",
        "work_package_id": "TECH-P0-01",
        "generated_at": "2026-07-22T00:00:00+07:00",
        "generation_base": {"commit_sha": BASE_COMMIT, "tree_sha": BASE_TREE},
        "records": records,
    }


def rendered_manifest(root: Path = ROOT) -> str:
    return json.dumps(build_package_manifest(root), indent=2, ensure_ascii=False) + "\n"


def validate_package(root: Path = ROOT, check_manifest: bool = False) -> list[str]:
    errors: list[str] = []
    if sha256_file(root / COMMON_CATALOG) != COMMON_CATALOG_SHA256:
        errors.append("pinned common catalog digest drift")
    _, catalog_errors = validate_catalog_graph(root, CATALOG)
    errors.extend(catalog_errors)
    try:
        if len(program_goal_ids(root)) != 242:
            errors.append("Program Goal catalog item count drift")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"Program Goal catalog invalid: {exc}")
    if check_manifest:
        try:
            if (root / MANIFEST).read_text(encoding="utf-8") != rendered_manifest(root):
                errors.append("TECH-P0-01 package manifest stale")
        except OSError as exc:
            errors.append(f"TECH-P0-01 package manifest unavailable: {exc}")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--check-manifest", action="store_true")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    if args.write_manifest:
        print(rendered_manifest(), end="")
        return 0
    errors = validate_package(check_manifest=args.check_manifest)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("TECH-P0-01 technology qualification validation: PASS (4 local schemas; 242 Program Goal items)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
