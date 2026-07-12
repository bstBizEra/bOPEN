#!/usr/bin/env python3
"""Validate draft machine-readable contracts without external dependencies."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOTS = (ROOT / "docs" / "06-contracts", ROOT / "contracts")


def iter_contract_files(root: Path = ROOT) -> list[Path]:
    roots = (root / "docs" / "06-contracts", root / "contracts")
    files: list[Path] = []
    for contract_root in roots:
        if contract_root.exists():
            files.extend(contract_root.rglob("*.json"))
            files.extend(contract_root.rglob("*.yaml"))
            files.extend(contract_root.rglob("*.yml"))
    return sorted({p for p in files if p.is_file()})


def read_json(path: Path) -> tuple[object | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:  # pragma: no cover - exact JSON exception text varies
        return None, str(exc)


def top_level_yaml_value(path: Path, key: str) -> str | None:
    prefix = f"{key}:"
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip().strip("'\"")
    return None


def validate_json_contract(path: Path, root: Path = ROOT) -> list[str]:
    rel = path.relative_to(root)
    data, parse_error = read_json(path)
    if parse_error:
        return [f"INVALID JSON {rel}: {parse_error}"]

    if not isinstance(data, dict):
        return [f"CONTRACT JSON MUST BE OBJECT: {rel}"]

    errors: list[str] = []
    schema_id = data.get("$id")
    status = data.get("status")

    if path.name.endswith(".schema.json"):
        for required_key in ("$schema", "$id", "title", "type"):
            if required_key not in data:
                errors.append(f"SCHEMA METADATA MISSING {rel}: {required_key}")

    if path.name.endswith(".acceptance.json"):
        errors.extend(validate_acceptance_fixture(data, rel))

    if schema_id is not None and not isinstance(schema_id, str):
        errors.append(f"SCHEMA ID MUST BE STRING: {rel}")
    elif isinstance(schema_id, str):
        if not schema_id.startswith("bopen://"):
            errors.append(f"SCHEMA ID MUST USE bopen:// URI: {rel}")
        if "draft" in schema_id and status != "draft":
            errors.append(f"DRAFT CONTRACT STATUS MISSING: {rel}")

    if status is not None and status not in {"draft", "approved", "deprecated"}:
        errors.append(f"UNKNOWN CONTRACT STATUS {rel}: {status}")

    return errors


def validate_acceptance_fixture(data: dict, rel: Path) -> list[str]:
    errors: list[str] = []
    required_top_level = ("id", "status", "work_package", "chain", "scenarios")
    for key in required_top_level:
        if key not in data:
            errors.append(f"ACCEPTANCE FIXTURE FIELD MISSING {rel}: {key}")

    if data.get("status") != "draft":
        errors.append(f"ACCEPTANCE FIXTURE MUST BE DRAFT: {rel}")

    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        errors.append(f"ACCEPTANCE FIXTURE SCENARIOS MISSING: {rel}")
        return errors

    saw_deny = False
    for index, scenario in enumerate(scenarios, start=1):
        prefix = f"{rel} scenario {index}"
        if not isinstance(scenario, dict):
            errors.append(f"ACCEPTANCE SCENARIO MUST BE OBJECT: {prefix}")
            continue

        for key in ("id", "title", "authorization_decision", "audit_event"):
            if key not in scenario:
                errors.append(f"ACCEPTANCE SCENARIO FIELD MISSING {prefix}: {key}")

        decision = scenario.get("authorization_decision")
        audit_event = scenario.get("audit_event")
        if not isinstance(decision, dict) or not isinstance(audit_event, dict):
            continue

        for key in ("decision", "reason_code", "policy_version", "correlation_id"):
            if key not in decision:
                errors.append(f"AUTHORIZATION DECISION FIELD MISSING {prefix}: {key}")

        if decision.get("decision") == "DENY":
            saw_deny = True
        elif decision.get("decision") != "ALLOW":
            errors.append(f"AUTHORIZATION DECISION INVALID {prefix}: decision")

        for key in (
            "event_id",
            "event_type",
            "event_version",
            "occurred_at",
            "principal_id",
            "tenant_id",
            "resource_type",
            "resource_id",
            "action",
            "result",
            "correlation_id",
        ):
            if key not in audit_event:
                errors.append(f"AUDIT EVENT FIELD MISSING {prefix}: {key}")

        if decision.get("correlation_id") != audit_event.get("correlation_id"):
            errors.append(f"CORRELATION ID MISMATCH: {prefix}")

    if not saw_deny:
        errors.append(f"ACCEPTANCE FIXTURE MUST INCLUDE DENY SCENARIO: {rel}")

    return errors


def validate_yaml_contract(path: Path, root: Path = ROOT) -> list[str]:
    rel = path.relative_to(root)
    status = top_level_yaml_value(path, "status")
    version = top_level_yaml_value(path, "version")
    errors: list[str] = []

    if version and "draft" in version and status != "draft":
        errors.append(f"DRAFT YAML CONTRACT STATUS MISSING: {rel}")

    if status and status not in {"draft", "approved", "deprecated"}:
        errors.append(f"UNKNOWN YAML CONTRACT STATUS {rel}: {status}")

    return errors


def validate_contracts(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for path in iter_contract_files(root):
        if path.suffix == ".json":
            errors.extend(validate_json_contract(path, root))
        elif path.suffix in {".yaml", ".yml"}:
            errors.extend(validate_yaml_contract(path, root))
    return errors


def main() -> int:
    errors = validate_contracts()
    if errors:
        print("bOPEN contract validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("bOPEN contract validation: PASS")
    print(f"Checked {len(iter_contract_files())} machine-readable contract files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
