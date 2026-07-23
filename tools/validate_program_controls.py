#!/usr/bin/env python3
"""Fail-closed validation for draft Program G0 control registers."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTER_ROOT = Path("docs/00-governance/registers")
SCHEMA_ROOT = Path("contracts/governance")
REGISTER_SCHEMAS = {
    "AGENT-REGISTER.json": "agent-register.schema.json",
    "GOAL-REGISTER.json": "goal-register.schema.json",
    "MODULE-REGISTER.json": "module-register.schema.json",
    "SKILL-REGISTER.json": "skill-register.schema.json",
    "SCHEDULE-REGISTER.json": "schedule-register.schema.json",
    "AUTHORITY-MATRIX.json": "authority-matrix.schema.json",
    "TECHNOLOGY-DECISION-ASSIGNMENTS.json": "technology-decision-assignment.schema.json",
}
RFC3339 = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
AMBIGUOUS_PHASE = re.compile(r"^(?:G|P|C)\d+$")


def _read_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"INVALID JSON {path}: {exc}")
        return None


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or RFC3339.fullmatch(value) is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _matches_type(value: Any, expected: str) -> bool:
    return {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "boolean": lambda item: isinstance(item, bool),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "null": lambda item: item is None,
    }.get(expected, lambda _item: False)(value)


def _validate_schema(value: Any, schema: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    expected = schema.get("type")
    expected_types = [expected] if isinstance(expected, str) else expected
    if isinstance(expected_types, list) and not any(
        isinstance(item, str) and _matches_type(value, item) for item in expected_types
    ):
        return [f"PROGRAM CONTROL TYPE INVALID {label}"]
    if value is None:
        return errors
    if "const" in schema and value != schema["const"]:
        errors.append(f"PROGRAM CONTROL CONSTANT INVALID {label}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"PROGRAM CONTROL ENUM INVALID {label}")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"PROGRAM CONTROL STRING TOO SHORT {label}")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.fullmatch(pattern, value) is None:
            errors.append(f"PROGRAM CONTROL PATTERN INVALID {label}")
        if schema.get("format") == "date-time" and _parse_datetime(value) is None:
            errors.append(f"PROGRAM CONTROL DATE-TIME INVALID {label}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"PROGRAM CONTROL ARRAY TOO SHORT {label}")
        if schema.get("uniqueItems"):
            normalized = [json.dumps(item, sort_keys=True) for item in value]
            if len(normalized) != len(set(normalized)):
                errors.append(f"PROGRAM CONTROL ARRAY ITEMS NOT UNIQUE {label}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(_validate_schema(item, item_schema, f"{label}[{index}]"))
    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required if isinstance(required, list) else []:
            if key not in value:
                errors.append(f"PROGRAM CONTROL FIELD MISSING {label}: {key}")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            if schema.get("additionalProperties") is False:
                for key in sorted(set(value).difference(properties)):
                    errors.append(f"PROGRAM CONTROL UNKNOWN FIELD {label}: {key}")
            for key, item in value.items():
                definition = properties.get(key)
                if isinstance(definition, dict):
                    errors.extend(_validate_schema(item, definition, f"{label}.{key}"))
    return errors


def _all_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _all_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _all_strings(item)


def _entry_map(register: dict[str, Any], key: str, label: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    entries = register.get("entries", [])
    if not isinstance(entries, list):
        return result
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or not isinstance(entry.get(key), str):
            continue
        identifier = entry[key]
        if identifier in result:
            errors.append(f"PROGRAM CONTROL DUPLICATE ID {label}: {identifier}")
        result[identifier] = entry
    return result


def _scope_valid(scope: str) -> bool:
    if scope in {"", ".", "/", "*", "**"} or "\\" in scope:
        return False
    path = PurePosixPath(scope)
    if path.is_absolute() or ".." in path.parts or PureWindowsPath(scope).drive:
        return False
    return not any(part in {"*", "**"} for part in path.parts)


def _scopes_overlap(left: str, right: str) -> bool:
    left = left.rstrip("/")
    right = right.rstrip("/")
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def _decision_exists(root: Path, decision_id: str) -> bool:
    if decision_id.startswith("ADR-"):
        return (root / "docs/adr" / f"{decision_id}.md").is_file()
    if (root / "docs/decisions" / f"{decision_id}.md").is_file():
        return True
    register = root / "docs/decisions/DECISION-REGISTER.md"
    return register.is_file() and f"| {decision_id} |" in register.read_text(encoding="utf-8")


def _has_cycle(entries: dict[str, dict[str, Any]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(identifier: str) -> bool:
        if identifier in visiting:
            return True
        if identifier in visited:
            return False
        visiting.add(identifier)
        for dependency in entries[identifier].get("depends_on", []):
            if dependency in entries and visit(dependency):
                return True
        visiting.remove(identifier)
        visited.add(identifier)
        return False

    return any(visit(identifier) for identifier in entries)


def validate_program_controls(
    root: Path = ROOT, as_of: datetime | None = None
) -> list[str]:
    as_of = as_of or datetime.now(timezone.utc)
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    errors: list[str] = []
    registers: dict[str, dict[str, Any]] = {}

    for register_name, schema_name in REGISTER_SCHEMAS.items():
        register_path = root / REGISTER_ROOT / register_name
        schema_path = root / SCHEMA_ROOT / schema_name
        if not register_path.is_file():
            errors.append(f"PROGRAM CONTROL REGISTER MISSING: {register_path.relative_to(root)}")
            continue
        if not schema_path.is_file():
            errors.append(f"PROGRAM CONTROL SCHEMA MISSING: {schema_path.relative_to(root)}")
            continue
        register = _read_json(register_path, errors)
        schema = _read_json(schema_path, errors)
        if not isinstance(register, dict) or not isinstance(schema, dict):
            continue
        if register.get("$schema") != schema.get("$id"):
            errors.append(f"PROGRAM CONTROL SCHEMA REFERENCE INVALID: {register_name}")
        errors.extend(_validate_schema(register, schema, register_name))
        approval_fields = ("approved_by", "approved_at", "approval_ref")
        if register.get("status") == "approved":
            if any(not register.get(field) for field in approval_fields):
                errors.append(f"APPROVED REGISTER LACKS APPROVAL PROVENANCE: {register_name}")
            if isinstance(register.get("version"), str) and register["version"].endswith("-draft"):
                errors.append(f"APPROVED REGISTER USES DRAFT VERSION: {register_name}")
        elif register.get("status") == "draft":
            if any(register.get(field) is not None for field in approval_fields):
                errors.append(f"DRAFT REGISTER MUST NOT CARRY APPROVAL: {register_name}")
        for value in _all_strings(register):
            if AMBIGUOUS_PHASE.fullmatch(value):
                errors.append(f"AMBIGUOUS PROGRAM PHASE IDENTIFIER {register_name}: {value}")
        registers[register_name] = register

    agents = _entry_map(registers.get("AGENT-REGISTER.json", {}), "agent_id", "agent", errors)
    goals = _entry_map(registers.get("GOAL-REGISTER.json", {}), "goal_id", "goal", errors)
    modules = _entry_map(registers.get("MODULE-REGISTER.json", {}), "module_id", "module", errors)
    skills = _entry_map(registers.get("SKILL-REGISTER.json", {}), "skill_id", "skill", errors)
    schedule = _entry_map(registers.get("SCHEDULE-REGISTER.json", {}), "schedule_id", "schedule", errors)
    actions = _entry_map(registers.get("AUTHORITY-MATRIX.json", {}), "action_id", "authority action", errors)
    technology = _entry_map(registers.get("TECHNOLOGY-DECISION-ASSIGNMENTS.json", {}), "assignment_id", "technology assignment", errors)

    active_scopes: list[tuple[str, str]] = []
    for agent_id, agent in agents.items():
        if set(agent.get("maker_work_item_ids", [])).intersection(agent.get("checker_work_item_ids", [])):
            errors.append(f"AGENT SELF REVIEW PROHIBITED: {agent_id}")
        for scope in agent.get("allowed_scope_paths", []):
            if isinstance(scope, str) and not _scope_valid(scope):
                errors.append(f"AGENT SCOPE INVALID {agent_id}: {scope}")
            if agent.get("status") == "ACTIVE" and isinstance(scope, str):
                active_scopes.append((agent_id, scope))
        if agent.get("status") == "ACTIVE":
            for field in ("review_due_at", "expires_at"):
                parsed = _parse_datetime(agent.get(field))
                if parsed is None or parsed <= as_of:
                    errors.append(f"ACTIVE AGENT {field.upper()} INVALID: {agent_id}")
    for index, (left_id, left_scope) in enumerate(active_scopes):
        for right_id, right_scope in active_scopes[index + 1 :]:
            if left_id != right_id and _scopes_overlap(left_scope, right_scope):
                errors.append(f"ACTIVE AGENT SCOPE OVERLAP: {left_id} / {right_id}")

    phase_ids = set(schedule)
    for goal_id, goal in goals.items():
        for phase_id in goal.get("phase_ids", []):
            if phase_id not in phase_ids:
                errors.append(f"GOAL PHASE REFERENCE MISSING {goal_id}: {phase_id}")
        if goal.get("status") != "Approved" and goal.get("implementation_authority") is not False:
            errors.append(f"UNAPPROVED GOAL GRANTS IMPLEMENTATION AUTHORITY: {goal_id}")
        if goal.get("status") == "Approved" and (not goal.get("approval_ref") or not goal.get("approved_at")):
            errors.append(f"APPROVED GOAL LACKS APPROVAL EVIDENCE: {goal_id}")

    for module_id, module in modules.items():
        for dependency in module.get("dependency_ids", []):
            if dependency not in modules:
                errors.append(f"MODULE DEPENDENCY MISSING {module_id}: {dependency}")
        if module.get("certification_state") == "CERTIFIED":
            required = (
                "contract_ref", "capability_refs", "permission_refs", "entitlement_refs",
                "isolation_evidence_refs", "test_evidence_refs", "runbook_ref",
                "independent_acceptance_ref",
            )
            if any(not module.get(field) for field in required):
                errors.append(f"MODULE CERTIFICATION PREREQUISITES MISSING: {module_id}")
        if module.get("lifecycle_state") == "ACTIVE" or module.get("certification_state") == "CERTIFIED":
            expiry = _parse_datetime(module.get("expires_at")) if module.get("expires_at") else None
            if module.get("expires_at") is not None and (expiry is None or expiry <= as_of):
                errors.append(f"ACTIVE MODULE EXPIRY INVALID: {module_id}")

    for skill_id, skill in skills.items():
        if skill.get("status") == "ACTIVE":
            required = ("sandbox_evidence_ref", "evaluation_evidence_ref", "promoted_by", "promoted_at")
            if any(not skill.get(field) for field in required):
                errors.append(f"ACTIVE SKILL PROMOTION EVIDENCE MISSING: {skill_id}")
            for field in ("review_due_at", "expires_at"):
                parsed = _parse_datetime(skill.get(field))
                if parsed is None or parsed <= as_of:
                    errors.append(f"ACTIVE SKILL {field.upper()} INVALID: {skill_id}")

    for schedule_id, item in schedule.items():
        if item.get("phase_id") != schedule_id:
            errors.append(f"SCHEDULE PHASE ID MISMATCH: {schedule_id}")
        for dependency in item.get("depends_on", []):
            if dependency not in schedule:
                errors.append(f"SCHEDULE DEPENDENCY MISSING {schedule_id}: {dependency}")
        start = _parse_datetime(item.get("planned_start")) if item.get("planned_start") else None
        end = _parse_datetime(item.get("planned_end")) if item.get("planned_end") else None
        if (start is None and end is not None) or (start and end and end < start):
            errors.append(f"SCHEDULE WINDOW INVALID: {schedule_id}")
    if _has_cycle(schedule):
        errors.append("SCHEDULE DEPENDENCY CYCLE DETECTED")

    for action_id, action in actions.items():
        if action.get("self_approval_allowed") is not False:
            errors.append(f"AUTHORITY SELF APPROVAL PROHIBITED: {action_id}")

    for assignment_id, assignment in technology.items():
        decision_id = assignment.get("decision_id")
        if isinstance(decision_id, str) and not _decision_exists(root, decision_id):
            errors.append(f"TECHNOLOGY DECISION REFERENCE MISSING {assignment_id}: {decision_id}")
        phase = assignment.get("required_before_phase")
        if phase not in phase_ids:
            errors.append(f"TECHNOLOGY PHASE REFERENCE MISSING {assignment_id}: {phase}")
        if assignment.get("status") in {"READY_FOR_REVIEW", "DECIDED"}:
            if not assignment.get("checker_authorities") or not assignment.get("due_at"):
                errors.append(f"TECHNOLOGY ASSIGNMENT REVIEW CONTROLS MISSING: {assignment_id}")

    return errors


def main() -> int:
    errors = validate_program_controls()
    if errors:
        print("bOPEN program-control validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("bOPEN program-control validation: PASS")
    print(f"Checked {len(REGISTER_SCHEMAS)} governed registers with fail-closed semantic controls.")
    print("Program G0 readiness is not asserted by this validator.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
