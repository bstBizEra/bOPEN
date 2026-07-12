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
