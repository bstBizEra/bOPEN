#!/usr/bin/env python3
"""Validate the sanitized R1 trace without executing upstream code."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

try:
    from tools.validate_research_r0 import ROOT, is_within, validate_paths
except ModuleNotFoundError:
    from validate_research_r0 import ROOT, is_within, validate_paths


CONTRACT = ROOT / "research/sources/boxyhq-r1-trace-contract.json"
PIN = ROOT / "research/sources/boxyhq-upstream-pin.json"
PACKAGE_IDS = {"RES-P0-04", "RES-P0-05", "RES-P0-06", "RES-P0-07"}
TEST_PATTERN = re.compile(r"^\s*(?:test|setup|teardown)\s*\(", re.MULTILINE)


def validate_contract(contract: dict) -> list[str]:
    errors: list[str] = []
    packages = {item.get("id"): item for item in contract.get("work_packages", [])}
    if set(packages) != PACKAGE_IDS:
        errors.append("R1 work-package set mismatch")
    evidence = contract.get("evidence", [])
    ids = [item.get("id") for item in evidence]
    if len(ids) != len(set(ids)):
        errors.append("duplicate R1 evidence ID")
    for item in evidence:
        kind = item.get("evidence_kind", "observation")
        layer = item.get("layer")
        case_markers = item.get("case_markers")
        item_packages = set(item.get("packages", []))
        if not item_packages or not item_packages <= PACKAGE_IDS:
            errors.append(f"{item.get('id')} has invalid package attribution")
        if kind not in {"observation", "gap-anchor"}:
            errors.append(f"{item.get('id')} has invalid evidence kind")
        if (kind == "gap-anchor") != (layer == "gap"):
            errors.append(f"{item.get('id')} gap kind/layer mismatch")
        if not isinstance(case_markers, dict) or not case_markers:
            errors.append(f"{item.get('id')} requires case-specific markers")
        elif any(
            not isinstance(markers, list)
            or not markers
            or any(not isinstance(marker, str) or not marker for marker in markers)
            for markers in case_markers.values()
        ):
            errors.append(f"{item.get('id')} has invalid case markers")
    for item in evidence:
        allowed_cases: set[str] = set()
        for package_id in item.get("packages", []):
            allowed_cases.update(packages.get(package_id, {}).get("case_layers", {}))
        unknown = set(item.get("case_markers", {})) - allowed_cases
        if unknown:
            errors.append(
                f"{item.get('id')} attributes cases outside its packages: {','.join(sorted(unknown))}"
            )
    for package_id, package in packages.items():
        requirements = package.get("case_layers", {})
        package_evidence = [item for item in evidence if package_id in item.get("packages", [])]
        for case, required_layers in requirements.items():
            covered_layers = {
                item.get("layer")
                for item in package_evidence
                if case in item.get("case_markers", {})
            }
            missing = set(required_layers) - covered_layers
            if missing:
                errors.append(
                    f"{package_id} {case} missing layers: {','.join(sorted(missing))}"
                )
    runtime = contract.get("runtime_evidence", {})
    if runtime.get("gate") != "G3" or runtime.get("status") != "open" or runtime.get("executed") is not False:
        errors.append("R1 static trace must keep G3 open and runtime unexecuted")
    return errors


def git_value(target: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(target), *args], text=True, stderr=subprocess.DEVNULL
    ).strip()


def safe_source_path(target: Path, relative: str) -> Path | None:
    relative_path = Path(relative)
    if relative_path.is_absolute():
        return None
    candidate = (target / relative_path).resolve()
    return candidate if is_within(candidate, target) else None


def validate_checkout(target: Path, contract: dict, pin: dict) -> tuple[list[str], list[dict]]:
    errors: list[str] = []
    records: list[dict] = []
    try:
        if git_value(target, "rev-parse", "HEAD") != contract.get("pinned_commit"):
            errors.append("R1 checkout commit mismatch")
        if git_value(target, "remote", "get-url", "origin") != pin.get("repository_url"):
            errors.append("R1 checkout origin mismatch")
        if git_value(target, "status", "--porcelain", "--untracked-files=all"):
            errors.append("R1 checkout is dirty")
    except (OSError, subprocess.CalledProcessError):
        return ["R1 checkout metadata unavailable"], records
    for item in contract.get("evidence", []):
        relative = item.get("path", "")
        path = safe_source_path(target, relative)
        if path is None:
            errors.append(f"source path escapes checkout: {relative}")
            continue
        if not path.is_file():
            errors.append(f"missing source path: {relative}")
            continue
        data = path.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"non-UTF-8 source path: {relative}")
            continue
        case_results: dict[str, int] = {}
        for case, markers in item.get("case_markers", {}).items():
            missing = [marker for marker in markers if marker not in text]
            if missing:
                errors.append(f"{item.get('id')} {case} missing markers: {','.join(missing)}")
            case_results[case] = len(markers) - len(missing)
        records.append(
            {
                "evidence_id": item.get("id"),
                "evidence_kind": item.get("evidence_kind", "observation"),
                "layer": item.get("layer"),
                "path": relative,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "case_markers_verified": case_results,
            }
        )
    return errors, records


def inventory_tests(target: Path, contract: dict) -> tuple[list[str], list[dict]]:
    errors: list[str] = []
    records: list[dict] = []
    try:
        tracked = git_value(target, "ls-files", "--", "tests/e2e").splitlines()
    except (OSError, subprocess.CalledProcessError):
        return ["tracked test inventory unavailable"], records
    candidates = [
        path
        for path in tracked
        if path.endswith((".spec.ts", ".setup.ts", ".teardown.ts"))
    ]
    total = 0
    for relative in candidates:
        path = safe_source_path(target, relative)
        if path is None or not path.is_file():
            errors.append(f"tracked test path unavailable: {relative}")
            continue
        data = path.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"non-UTF-8 test path: {relative}")
            continue
        declarations = len(TEST_PATTERN.findall(text))
        if declarations:
            total += declarations
            records.append(
                {
                    "path": relative,
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "declaration_count": declarations,
                }
            )
    expected = contract.get("static_test_inventory", {})
    if total != expected.get("expected_declarations"):
        errors.append("static test declaration count mismatch")
    if len(records) != expected.get("expected_files"):
        errors.append("static test file count mismatch")
    return errors, records


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2) + "\n").encode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--approved-root", type=Path, required=True)
    parser.add_argument("--operator-id", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--test-receipt", type=Path, required=True)
    args = parser.parse_args()
    target = args.target.resolve()
    evidence_root = args.evidence_root.resolve()
    receipt = args.receipt.resolve()
    test_receipt = args.test_receipt.resolve()
    path_errors = validate_paths(target, evidence_root, args.approved_root)
    for label, path in (("receipt", receipt), ("test receipt", test_receipt)):
        if not is_within(path, evidence_root):
            path_errors.append(f"{label} escapes evidence root")
    if path_errors:
        print("Research R1 validation: FAIL")
        for error in path_errors:
            print(f"- {error}")
        return 1

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    pin = json.loads(PIN.read_text(encoding="utf-8"))
    errors = validate_contract(contract)
    records: list[dict] = []
    test_records: list[dict] = []
    if not errors:
        checkout_errors, records = validate_checkout(target, contract, pin)
        test_errors, test_records = inventory_tests(target, contract)
        errors.extend(checkout_errors)
        errors.extend(test_errors)
    validator_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    contract_hash = hashlib.sha256(CONTRACT.read_bytes()).hexdigest()
    write_json(
        receipt,
        {
            "schema_version": "1.1",
            "operator_id": args.operator_id,
            "validator_sha256": validator_hash,
            "contract_sha256": contract_hash,
            "source_id": contract.get("source_id"),
            "pinned_commit": contract.get("pinned_commit"),
            "work_packages": sorted(PACKAGE_IDS),
            "runtime_executed": False,
            "g3_status": "OPEN",
            "evidence_records": records,
            "observation_count": sum(item["evidence_kind"] == "observation" for item in records),
            "gap_anchor_count": sum(item["evidence_kind"] == "gap-anchor" for item in records),
            "status": "PASS" if not errors else "FAIL",
            "errors": errors,
        },
    )
    write_json(
        test_receipt,
        {
            "schema_version": "1.0",
            "operator_id": args.operator_id,
            "validator_sha256": validator_hash,
            "contract_sha256": contract_hash,
            "method": "static-regex-over-git-tracked-typescript",
            "upstream_code_executed": False,
            "network_required": False,
            "runtime_executed": False,
            "g3_status": "OPEN",
            "declaration_count": sum(item["declaration_count"] for item in test_records),
            "file_count": len(test_records),
            "files": test_records,
            "status": "PASS" if not errors else "FAIL",
            "errors": errors,
        },
    )
    if errors:
        print("Research R1 validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Research R1 validation: PASS ({len(records)} evidence records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
