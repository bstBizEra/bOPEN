#!/usr/bin/env python3
"""Report Program Goal v0.2 G0 readiness without granting implementation authority."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from tools.validate_program_controls import validate_program_controls
except ModuleNotFoundError:  # Direct execution as python tools/report_program_g0.py
    from validate_program_controls import validate_program_controls


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = Path("contracts/governance/program-goal.requirements.json")
REGISTER_ROOT = Path("docs/00-governance/registers")
REGISTER_PATHS = {
    "goal": REGISTER_ROOT / "GOAL-REGISTER.json",
    "agent": REGISTER_ROOT / "AGENT-REGISTER.json",
    "module": REGISTER_ROOT / "MODULE-REGISTER.json",
    "skill": REGISTER_ROOT / "SKILL-REGISTER.json",
    "schedule": REGISTER_ROOT / "SCHEDULE-REGISTER.json",
    "authority": REGISTER_ROOT / "AUTHORITY-MATRIX.json",
    "technology": REGISTER_ROOT / "TECHNOLOGY-DECISION-ASSIGNMENTS.json",
}
WORK_ITEM_TEMPLATE = Path("docs/templates/work-package-template.md")
EVIDENCE_TEMPLATE = Path("docs/templates/evidence-template.md")
INDEPENDENT_EVIDENCE = Path("docs/evidence/EVD-GOV-001-program-g0-controls.md")
DEFAULT_REPORT_PATH = Path("artifacts/validation/program-g0-readiness.md")

ALLOWED_COVERAGE = {
    "evidenced",
    "draft_only",
    "placeholder",
    "missing",
    "future_evidence",
}
EXPECTED_TYPE_COUNTS = {
    "program_objective": 1,
    "program_principle": 7,
    "operating_model_stage": 11,
    "north_star_objective": 1,
    "formula": 1,
    "phase_target": 4,
    "module_certification_condition": 8,
    "outcome_objective": 8,
    "indicator": 70,
    "platform_capability": 14,
    "success_condition": 5,
    "module_lifecycle_stage": 9,
    "reference_flow_stage": 13,
    "service_level_objective": 6,
    "measurement_policy": 2,
    "productivity_indicator": 6,
    "learning_lifecycle_stage": 8,
    "governance_policy": 1,
    "phase_gate_clause": 50,
    "measurement_rule": 8,
    "final_success_clause": 8,
    "final_success_guardrail": 1,
}
EXPECTED_FAMILY_COUNTS = {
    "PG-GOAL-": 19,
    "PG-NS-": 14,
    "PG-O1-": 10,
    "PG-O2-": 12,
    "PG-O3-": 24,
    "PG-O4-": 19,
    "PG-O5-": 23,
    "PG-O6-": 18,
    "PG-O7-": 18,
    "PG-O8-": 18,
    "PG-GATE-": 50,
    "PG-MEASURE-": 8,
    "PG-FINAL-": 9,
}
CERTIFICATION_CONDITION_IDS = {
    "PG-NS-CERT-APPROVED-CONTRACT",
    "PG-NS-CERT-CAPABILITIES-DEPENDENCIES",
    "PG-NS-CERT-TENANT-ISOLATION",
    "PG-NS-CERT-PERMISSIONS-ENTITLEMENTS",
    "PG-NS-CERT-COMPLETE-TESTS",
    "PG-NS-CERT-EVIDENCE",
    "PG-NS-CERT-RUNBOOK",
    "PG-NS-CERT-INDEPENDENT-ACCEPTANCE",
}
REQUIRED_TECHNOLOGY_DECISIONS = {"DEC-0004", "DEC-0005"}
REQUIRED_ITEM_FIELDS = {
    "id",
    "type",
    "source_section",
    "normalized_statement",
    "target",
    "owner_authority",
    "coverage_classification",
    "evidence_refs",
    "disposition",
}
REGISTER_IDS = {
    "goal": "PG-REG-GOAL-001",
    "agent": "PG-REG-AGENT-001",
    "module": "PG-REG-MODULE-001",
    "skill": "PG-REG-SKILL-001",
    "schedule": "PG-REG-SCHEDULE-001",
    "authority": "PG-REG-AUTHORITY-001",
    "technology": "PG-REG-TECH-001",
}
PLACEHOLDER_VALUES = {"", "tbd", "none", "unassigned", "pending assignment", "n/a"}
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)


def read_json_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "missing"
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"invalid: {exc}"
    if not isinstance(value, dict):
        return None, "must be a JSON object"
    return value, None


def non_placeholder(value: object) -> bool:
    return isinstance(value, str) and value.strip().lower() not in PLACEHOLDER_VALUES


def has_evidence_refs(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(non_placeholder(item) for item in value)
    )


def validate_catalog(catalog: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if catalog.get("id") != "bopen.program-goal.requirements.v0.2":
        errors.append("catalog id must be bopen.program-goal.requirements.v0.2")
    if catalog.get("version") != "0.2":
        errors.append("catalog version must be 0.2")
    if catalog.get("status") != "draft":
        errors.append("catalog must remain draft")
    if catalog.get("implementation_authority") is not False:
        errors.append("catalog must explicitly deny implementation authority")
    if catalog.get("gate_promotion_authority") is not False:
        errors.append("catalog must explicitly deny gate-promotion authority")
    if catalog.get("release_authority") is not False:
        errors.append("catalog must explicitly deny release authority")

    items = catalog.get("items")
    if not isinstance(items, list):
        return errors + ["catalog items must be an array"]

    ids: list[str] = []
    type_counts: dict[str, int] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"catalog item {index} must be an object")
            continue
        missing = REQUIRED_ITEM_FIELDS - set(item)
        if missing:
            errors.append(
                f"catalog item {index} missing fields: {', '.join(sorted(missing))}"
            )
            continue
        item_id = item.get("id")
        if not non_placeholder(item_id):
            errors.append(f"catalog item {index} has invalid id")
            continue
        ids.append(item_id)
        item_type = item.get("type")
        if not non_placeholder(item_type):
            errors.append(f"{item_id} has invalid type")
        else:
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
        if not non_placeholder(item.get("source_section")):
            errors.append(f"{item_id} has invalid source section")
        if not non_placeholder(item.get("normalized_statement")):
            errors.append(f"{item_id} has invalid statement")
        if not non_placeholder(item.get("owner_authority")):
            errors.append(f"{item_id} has invalid owner authority")
        if item.get("coverage_classification") not in ALLOWED_COVERAGE:
            errors.append(f"{item_id} has invalid coverage classification")
        if not isinstance(item.get("evidence_refs"), list):
            errors.append(f"{item_id} evidence_refs must be an array")
        disposition = item.get("disposition")
        if not non_placeholder(disposition):
            errors.append(f"{item_id} has invalid disposition")
        elif disposition.strip().lower() in {"pass", "passed", "approved", "certified"}:
            errors.append(f"{item_id} disposition cannot default to passed")

    if len(ids) != len(set(ids)):
        errors.append("catalog item ids must be unique")
    if len(items) != sum(EXPECTED_TYPE_COUNTS.values()):
        errors.append(
            f"catalog must contain {sum(EXPECTED_TYPE_COUNTS.values())} items"
        )
    if type_counts != EXPECTED_TYPE_COUNTS:
        errors.append("catalog type counts do not match Program Goal v0.2 inventory")
    for prefix, expected in EXPECTED_FAMILY_COUNTS.items():
        actual = sum(item_id.startswith(prefix) for item_id in ids)
        if actual != expected:
            errors.append(f"{prefix} family must contain {expected} items")
    lifecycle_ids = [
        item["id"]
        for item in items
        if isinstance(item, dict)
        and item.get("type") in {"module_lifecycle_stage", "learning_lifecycle_stage"}
    ]
    if any(
        not (
            item_id.startswith("PG-O4-LC-")
            or item_id.startswith("PG-O8-LC-")
        )
        for item_id in lifecycle_ids
    ):
        errors.append("lifecycle ids must be explicitly scoped to Outcome 4 or Outcome 8")
    cert_ids = {
        item["id"]
        for item in items
        if isinstance(item, dict)
        and item.get("type") == "module_certification_condition"
    }
    if cert_ids != CERTIFICATION_CONDITION_IDS:
        errors.append("module certification conditions must contain the exact eight controls")
    return errors


def is_module_certified(condition_results: dict[str, object]) -> bool:
    """Return true only when all eight certification controls are true."""
    return (
        set(condition_results) == CERTIFICATION_CONDITION_IDS
        and all(value is True for value in condition_results.values())
    )


def certified_module_enablement_rate(
    certified_pilot_modules: int, submitted_pilot_modules: int
) -> float:
    """Calculate the North Star rate without allowing an empty or invalid denominator."""
    if not isinstance(certified_pilot_modules, int) or isinstance(
        certified_pilot_modules, bool
    ):
        raise ValueError("certified module count must be an integer")
    if not isinstance(submitted_pilot_modules, int) or isinstance(
        submitted_pilot_modules, bool
    ):
        raise ValueError("submitted module count must be an integer")
    if submitted_pilot_modules <= 0:
        raise ValueError("submitted module denominator must be greater than zero")
    if certified_pilot_modules < 0:
        raise ValueError("certified module count cannot be negative")
    if certified_pilot_modules > submitted_pilot_modules:
        raise ValueError("certified module count cannot exceed submitted modules")
    return certified_pilot_modules / submitted_pilot_modules * 100.0


def common_register_errors(
    name: str, register: dict[str, Any] | None, read_error: str | None
) -> list[str]:
    if read_error:
        return [f"{name} register {read_error}"]
    assert register is not None
    errors: list[str] = []
    if register.get("register_id") != REGISTER_IDS[name]:
        errors.append(f"{name} register id must be {REGISTER_IDS[name]}")
    if register.get("status") != "approved":
        errors.append(f"{name} register status must be approved")
    for field in ("owner_authority", "approved_by", "approved_at"):
        if not non_placeholder(register.get(field)):
            errors.append(f"{name} register {field} is required")
    if not non_placeholder(register.get("approval_ref")):
        errors.append(f"{name} register approval_ref is required")
    return errors


def validate_goal_register(register: dict[str, Any]) -> list[str]:
    goals = register.get("entries")
    if not isinstance(goals, list):
        return ["goal register goals must be an array"]
    matches = [
        goal
        for goal in goals
        if isinstance(goal, dict)
        and goal.get("goal_id") == "BOPEN-GOAL-001"
        and str(goal.get("version", "")).startswith("0.2")
        and str(goal.get("status", "")).lower() == "approved"
        and non_placeholder(goal.get("owner_authority"))
        and non_placeholder(goal.get("approval_ref"))
        and non_placeholder(goal.get("approved_at"))
        and goal.get("implementation_authority") is False
    ]
    return [] if matches else ["BOPEN-GOAL-001 v0.2 must be approved with owner and evidence"]


def validate_agent_register(register: dict[str, Any]) -> list[str]:
    agents = register.get("entries")
    if not isinstance(agents, list):
        return ["agent register agents must be an array"]
    active = [
        agent
        for agent in agents
        if isinstance(agent, dict)
        and agent.get("status") == "ACTIVE"
        and all(
            non_placeholder(agent.get(field))
            for field in (
                "agent_id",
                "harness",
                "role_id",
                "owner_authority",
                "review_due_at",
                "expires_at",
            )
        )
        and bool(
            agent.get("maker_work_item_ids") or agent.get("checker_work_item_ids")
        )
    ]
    return [] if active else ["agent register requires at least one governed active agent"]


def validate_controlled_population(
    register: dict[str, Any], collection_name: str
) -> list[str]:
    records = register.get("entries")
    if not isinstance(records, list):
        return [f"{collection_name} must be an array"]
    # An approved empty register is a controlled G0 baseline, not a claim that a
    # module or skill exists. Approval provenance is enforced at register level.
    return []


def validate_schedule_register(register: dict[str, Any]) -> list[str]:
    schedules = register.get("entries")
    if not isinstance(schedules, list):
        return ["schedule register schedules must be an array"]
    assigned = [
        item
        for item in schedules
        if isinstance(item, dict)
        and item.get("phase_id") == "PG-G0"
        and item.get("status") == "READY_FOR_AUTHORITY_REVIEW"
        and non_placeholder(item.get("owner_authority"))
        and non_placeholder(item.get("planned_end"))
        and bool(item.get("work_item_refs"))
        and has_evidence_refs(item.get("evidence_refs"))
    ]
    return [] if assigned else ["schedule register requires assigned PG-G0 review"]


def validate_authority_matrix(register: dict[str, Any]) -> list[str]:
    assignments = register.get("entries")
    if not isinstance(assignments, list):
        return ["authority matrix assignments must be an array"]
    required_actions = {
        "APPROVE_GOAL",
        "ACCEPT_WORK_ITEM",
        "APPROVE_ARCHITECTURE",
        "ACCEPT_EVIDENCE",
        "CERTIFY_MODULE",
        "PROMOTE_SKILL",
        "AUTHORIZE_RELEASE",
    }
    valid_actions = {
        item.get("action_id")
        for item in assignments
        if isinstance(item, dict)
        and item.get("status") == "approved"
        and non_placeholder(item.get("accountable_human_authority"))
        and non_placeholder(item.get("final_decision_role"))
        and item.get("self_approval_allowed") is False
        and item.get("evidence_required") is True
    }
    missing = required_actions - valid_actions
    return (
        []
        if not missing
        else [f"authority matrix missing approved actions: {', '.join(sorted(missing))}"]
    )


def validate_technology_assignments(register: dict[str, Any]) -> list[str]:
    assignments = register.get("entries")
    if not isinstance(assignments, list):
        return ["technology assignments must be an array"]
    assigned_ids = {
        item.get("decision_id")
        for item in assignments
        if isinstance(item, dict)
        and item.get("status") in {"ASSIGNED", "PENDING_OWNER_ASSIGNED"}
        and non_placeholder(item.get("owner_authority"))
        and has_evidence_refs(item.get("evidence_refs"))
    }
    missing = REQUIRED_TECHNOLOGY_DECISIONS - assigned_ids
    return (
        []
        if not missing
        else [f"technology decisions not assigned: {', '.join(sorted(missing))}"]
    )


def validate_templates(root: Path) -> list[str]:
    required_markers = {
        WORK_ITEM_TEMPLATE: (
            "**Maker:**",
            "**Checker:**",
            "**Branch/worktree:**",
            "**Allowed paths:**",
            "**Base SHA:**",
            "**Expiry:**",
            "## Acceptance criteria",
            "## Required checks/evidence",
        ),
        EVIDENCE_TEMPLATE: (
            "**Evidence ID:**",
            "**Work package:**",
            "**Source/commit:**",
            "**Maker:**",
            "**Checker:**",
            "## Procedure",
            "## Actual result",
            "## Independent verdict",
        ),
    }
    errors: list[str] = []
    for relative, markers in required_markers.items():
        path = root / relative
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            errors.append(f"template missing: {relative.as_posix()}")
            continue
        missing = [marker for marker in markers if marker not in text]
        if missing:
            errors.append(
                f"{relative.as_posix()} missing operational markers: "
                + ", ".join(missing)
            )
    return errors


def parse_bold_markers(text: str) -> dict[str, str]:
    markers: dict[str, str] = {}
    pattern = re.compile(r"^\*\*([^*]+):\*\*\s*(?:`([^`]+)`|(.+?))\s*$")
    for line in text.splitlines():
        match = pattern.match(line.strip())
        if match:
            markers[match.group(1).strip()] = (match.group(2) or match.group(3)).strip()
    return markers


def validate_independent_evidence(root: Path) -> list[str]:
    path = root / INDEPENDENT_EVIDENCE
    try:
        markers = parse_bold_markers(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [f"independent evidence missing: {INDEPENDENT_EVIDENCE.as_posix()}"]
    expected = {
        "Evidence ID": "EVD-GOV-001",
        "Work package": "GOV-P0-01",
        "Verdict": "ACCEPT",
    }
    errors = [
        f"independent evidence {key} must be {value}"
        for key, value in expected.items()
        if markers.get(key) != value
    ]
    maker = markers.get("Maker", "")
    checker = markers.get("Checker", "")
    if not non_placeholder(maker) or not non_placeholder(checker):
        errors.append("independent evidence requires maker and checker")
    elif maker.casefold() == checker.casefold():
        errors.append("independent evidence maker and checker must differ")
    exact_sha = markers.get("Exact SHA", "")
    if not SHA_PATTERN.fullmatch(exact_sha):
        errors.append("independent evidence requires a 40-character Exact SHA")
    return errors


def build_report(root: Path = ROOT) -> dict[str, Any]:
    blockers: list[str] = []
    program_control_errors = validate_program_controls(root)
    blockers.extend(program_control_errors)
    catalog, catalog_read_error = read_json_object(root / CATALOG_PATH)
    if catalog_read_error:
        catalog_errors = [f"program goal catalog {catalog_read_error}"]
    else:
        assert catalog is not None
        catalog_errors = validate_catalog(catalog)
    blockers.extend(catalog_errors)

    register_errors: dict[str, list[str]] = {}
    registers: dict[str, dict[str, Any] | None] = {}
    for name, relative in REGISTER_PATHS.items():
        register, read_error = read_json_object(root / relative)
        registers[name] = register
        errors = common_register_errors(name, register, read_error)
        register_errors[name] = errors
        blockers.extend(errors)

    if not register_errors["goal"] and registers["goal"] is not None:
        errors = validate_goal_register(registers["goal"])
        register_errors["goal"].extend(errors)
        blockers.extend(errors)
    if not register_errors["agent"] and registers["agent"] is not None:
        errors = validate_agent_register(registers["agent"])
        register_errors["agent"].extend(errors)
        blockers.extend(errors)
    for name, collection in (("module", "modules"), ("skill", "skills")):
        if not register_errors[name] and registers[name] is not None:
            errors = validate_controlled_population(registers[name], collection)
            register_errors[name].extend(errors)
            blockers.extend(errors)
    if not register_errors["schedule"] and registers["schedule"] is not None:
        errors = validate_schedule_register(registers["schedule"])
        register_errors["schedule"].extend(errors)
        blockers.extend(errors)
    if not register_errors["authority"] and registers["authority"] is not None:
        errors = validate_authority_matrix(registers["authority"])
        register_errors["authority"].extend(errors)
        blockers.extend(errors)
    if not register_errors["technology"] and registers["technology"] is not None:
        errors = validate_technology_assignments(registers["technology"])
        register_errors["technology"].extend(errors)
        blockers.extend(errors)

    template_errors = validate_templates(root)
    evidence_errors = validate_independent_evidence(root)
    blockers.extend(template_errors)
    blockers.extend(evidence_errors)

    readiness = not blockers
    return {
        "program_g0_status": "READY_FOR_AUTHORITY_REVIEW" if readiness else "NOT_READY",
        "ready_for_authority_review": readiness,
        "production_implementation_authorized": False,
        "catalog_status": catalog.get("status") if catalog else "missing",
        "requirement_count": len(catalog.get("items", [])) if catalog else 0,
        "catalog_errors": catalog_errors,
        "program_control_errors": program_control_errors,
        "register_errors": register_errors,
        "template_errors": template_errors,
        "independent_evidence_errors": evidence_errors,
        "blockers": blockers,
    }


def format_report(report: dict[str, Any]) -> str:
    lines = [
        "# Program G0 Readiness Report",
        "",
        f"**Program G0 status:** `{report['program_g0_status']}`",
        f"**Ready for authority review:** `{str(report['ready_for_authority_review']).lower()}`",
        "**Program G0 approved:** `false`",
        f"**Production implementation authorized:** `{str(report['production_implementation_authorized']).lower()}`",
        f"**Catalog status:** `{report['catalog_status']}`",
        f"**Requirement count:** {report['requirement_count']}",
        "",
        "## Blockers",
        "",
    ]
    blockers = report["blockers"]
    lines.extend(f"- {item}" for item in blockers) if blockers else lines.append("- None")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "This deterministic report is readiness evidence only. It cannot approve Program G0, promote any gate, or authorize production platform-kernel implementation.",
            "",
        ]
    )
    return "\n".join(lines)


def check_report(path: Path, expected: str) -> list[str]:
    """Fail closed when the committed readiness report is missing or stale."""
    try:
        actual = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [f"program G0 readiness report missing: {path}"]
    except OSError as exc:
        return [f"program G0 readiness report unreadable: {path}: {exc}"]
    if actual != expected:
        return [
            "program G0 readiness report is stale; regenerate with "
            "python tools/report_program_g0.py --write"
        ]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write",
        nargs="?",
        const=DEFAULT_REPORT_PATH,
        type=Path,
        help="Write the deterministic report (default: committed artifact path).",
    )
    mode.add_argument(
        "--check",
        nargs="?",
        const=DEFAULT_REPORT_PATH,
        type=Path,
        help="Verify that the committed report exists and is current.",
    )
    args = parser.parse_args(argv)
    report = format_report(build_report())
    if args.check:
        output = args.check if args.check.is_absolute() else ROOT / args.check
        errors = check_report(output, report)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(f"Program G0 readiness report current: {output}")
        return 0
    if args.write:
        output = args.write if args.write.is_absolute() else ROOT / args.write
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
        print(f"Wrote {output}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
