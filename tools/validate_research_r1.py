#!/usr/bin/env python3
"""Validate the sanitized R1 source trace against the pinned external checkout."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

try:
    from tools.validate_research_r0 import ROOT, validate_paths
except ModuleNotFoundError:
    from validate_research_r0 import ROOT, validate_paths


CONTRACT = ROOT / "research/sources/boxyhq-r1-trace-contract.json"
PIN = ROOT / "research/sources/boxyhq-upstream-pin.json"
PACKAGE_IDS = {"RES-P0-04", "RES-P0-05", "RES-P0-06", "RES-P0-07"}


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
        if item.get("evidence_kind", "observation") not in {"observation", "gap-anchor"}:
            errors.append(f"{item.get('id')} has invalid evidence kind")
    for package_id, package in packages.items():
        package_evidence = [item for item in evidence if package_id in item.get("packages", [])]
        covered_cases = {case for item in package_evidence for case in item.get("cases", [])}
        covered_layers = {item.get("layer") for item in package_evidence}
        missing_cases = set(package.get("required_cases", [])) - covered_cases
        missing_layers = set(package.get("required_layers", [])) - covered_layers
        if missing_cases:
            errors.append(f"{package_id} missing cases: {','.join(sorted(missing_cases))}")
        if missing_layers:
            errors.append(f"{package_id} missing layers: {','.join(sorted(missing_layers))}")
    runtime = contract.get("runtime_evidence", {})
    if runtime.get("gate") != "G3" or runtime.get("status") != "open" or runtime.get("executed") is not False:
        errors.append("R1 static trace must keep G3 open and runtime unexecuted")
    return errors


def git_value(target: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(target), *args], text=True).strip()


def validate_checkout(target: Path, contract: dict, pin: dict) -> tuple[list[str], list[dict]]:
    errors: list[str] = []
    records: list[dict] = []
    if git_value(target, "rev-parse", "HEAD") != contract.get("pinned_commit"):
        errors.append("R1 checkout commit mismatch")
    if git_value(target, "remote", "get-url", "origin") != pin.get("repository_url"):
        errors.append("R1 checkout origin mismatch")
    if git_value(target, "status", "--porcelain"):
        errors.append("R1 checkout is dirty")
    for item in contract.get("evidence", []):
        relative = item.get("path", "")
        path = target / relative
        if not path.is_file():
            errors.append(f"missing source path: {relative}")
            continue
        data = path.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"non-UTF-8 source path: {relative}")
            continue
        missing = [marker for marker in item.get("markers", []) if marker not in text]
        if missing:
            errors.append(f"{item.get('id')} missing markers: {','.join(missing)}")
        records.append(
            {
                "evidence_id": item.get("id"),
                "evidence_kind": item.get("evidence_kind", "observation"),
                "path": relative,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "markers_verified": len(item.get("markers", [])) - len(missing),
            }
        )
    return errors, records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--approved-root", type=Path, required=True)
    parser.add_argument("--operator-id", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    pin = json.loads(PIN.read_text(encoding="utf-8"))
    errors = validate_paths(args.target, args.evidence_root, args.approved_root)
    errors.extend(validate_contract(contract))
    records: list[dict] = []
    if not errors:
        checkout_errors, records = validate_checkout(args.target.resolve(), contract, pin)
        errors.extend(checkout_errors)
    receipt = {
        "schema_version": "1.0",
        "operator_id": args.operator_id,
        "validator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "contract_sha256": hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "source_id": contract.get("source_id"),
        "pinned_commit": contract.get("pinned_commit"),
        "work_packages": sorted(PACKAGE_IDS),
        "runtime_executed": False,
        "g3_status": "OPEN",
        "evidence_records": records,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_bytes((json.dumps(receipt, indent=2) + "\n").encode("utf-8"))
    if errors:
        print("Research R1 validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Research R1 validation: PASS ({len(records)} source observations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
