#!/usr/bin/env python3
"""Validate the draft PG-G0 authority docket without granting authority."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DOCKET_PATH = Path("docs/00-governance/authority-dockets/PG-G0-AUTH-001.json")
SCHEMA_PATH = Path("contracts/governance/pg-g0-authority-docket.schema.json")
AUTHORITY_MATRIX_PATH = Path("docs/00-governance/registers/AUTHORITY-MATRIX.json")
BINDING_INVENTORY_PATH = Path("docs/00-governance/authority-dockets/PG-G0-AUTH-001-V0.5-BINDING-INVENTORY.json")
PREDECESSOR_DOCKET_PATH = "docs/00-governance/authority-dockets/PG-G0-AUTH-001.json"
V03_SUBSTRATE_COMMIT = "60c4831f4fcdfabb876d62f4eb98949b4a1a5a66"
V03_SUBSTRATE_TREE = "75775a659f1c36c1cc5b489be572a347e1ea496b"
V03_SUBSTRATE_BRANCH = "operator/PG-G0-signing-pass-2"
SIGNED_SUBSTRATE_COMMIT = "7834c48f84c01be8a03cf00380dd06f2bdea0b81"
SIGNED_SUBSTRATE_TREE = "6988941a5afacd3ea2ca6d0dd62f3ff8ebf4c256"
SIGNED_SUBSTRATE_BRANCH = "operator/PG-G0-signing-pass-3"
SIGNED_AT = "2026-07-23T09:14:00+07:00"
SIGNED_DECISION_REF = "docs/00-governance/signing/SIGNING-PASS-3.md#signed-decisions"
SIGNED_EVIDENCE_REFS = {
    "docs/00-governance/signing/SIGNING-PASS-3.md",
    "docs/evidence/EVD-GOV-010-docket-v03-independent-review.md",
}
TERMINAL_SUBSTRATE_COMMIT = "7995d171ccaf43074155828c6a6bcca5c75d8359"
TERMINAL_SUBSTRATE_TREE = "f545ca2f4eb44ff81adad6de3627434187d25023"
TERMINAL_SUBSTRATE_BRANCH = "operator/PG-G0-signing-pass-4"
TERMINAL_SIGNED_AT = "2026-07-24T00:20:36+07:00"
TERMINAL_DECISION_REF = "docs/00-governance/signing/SIGNING-PASS-4.md#signed-gate-decision"
TERMINAL_EVIDENCE_REFS = {
    "docs/00-governance/signing/SIGNING-PASS-4.md",
    "docs/evidence/EVD-GOV-015-docket-v04-remediation-v3-acceptance.md",
}
V03_SIGNED_AT = "2026-07-23T00:45:00+07:00"
V03_SIGNED_DECISION_REF = "docs/00-governance/signing/SIGNING-PASS-2.md#append-only-batch-2-signing-record--2026-07-23"
V03_SIGNED_EVIDENCE_REFS = {
    "docs/00-governance/signing/SIGNING-PASS-2.md",
    "docs/evidence/EVD-GOV-008-docket-v02-independent-review.md",
}
EXTRA_INVENTORY_RECORDS = (
    ("AUTHORITY-MATRIX-V0.2", "0.2.0-draft", "draft", "docs/00-governance/registers/AUTHORITY-MATRIX.json"),
    ("PG-G0-AUTH-001-V0.2-BINDINGS", "0.2.0", "frozen_substrate_inventory", "docs/00-governance/authority-dockets/PG-G0-AUTH-001-V0.2-BINDING-INVENTORY.json"),
    ("PG-G0-DOCKET-SCHEMA-V0.2", "0.2.0-draft", "predecessor", "contracts/governance/pg-g0-authority-docket.schema.json"),
    ("AUTHORITY-MATRIX-SCHEMA-V0.2", "0.2.0-draft", "approved-state-capable", "contracts/governance/authority-matrix.schema.json"),
    ("ROOT-CONTROL-SCHEMA-V0.2", "0.2.0-draft", "predecessor", "contracts/governance/root-control-surface.schema.json"),
    ("SIGNING-PASS-2", "0.1", "signed_batch_2", "docs/00-governance/signing/SIGNING-PASS-2.md"),
    ("EVD-GOV-007", "0.1", "maker_candidate", "docs/evidence/EVD-GOV-007-pg-g0-authority-docket-v02-candidate.md"),
    ("EVD-GOV-008", "0.1", "ACCEPT_EXACT_SHA", "docs/evidence/EVD-GOV-008-docket-v02-independent-review.md"),
    ("BOPEN-BOOT-001", "0.1", "Approved", "BOPEN-BOOT-001.md"),
    ("BOOTSTRAP-GATES", "0.1", "B7 pending at substrate", "docs/work-packages/BOOTSTRAP-GATES.md"),
    ("PG-G0-AUTH-001-V0.3", "0.3.0-draft", "signed_state_candidate", PREDECESSOR_DOCKET_PATH),
    ("PG-G0-AUTH-001-V0.3-BINDINGS", "0.3.0", "frozen_signed_substrate_inventory", "docs/00-governance/authority-dockets/PG-G0-AUTH-001-V0.3-BINDING-INVENTORY.json"),
    ("EVD-GOV-009", "0.1", "signed_state_candidate", "docs/evidence/EVD-GOV-009-pg-g0-authority-docket-v03-signed-state-candidate.md"),
    ("EVD-GOV-010", "0.1", "ACCEPT_EXACT_SHA", "docs/evidence/EVD-GOV-010-docket-v03-independent-review.md"),
    ("SIGNING-PASS-3", "0.1", "signed_b8", "docs/00-governance/signing/SIGNING-PASS-3.md"),
    ("PG-G0-GATE-001", "0.1-draft", "draft", "docs/00-governance/PG-G0-GATE-CONTRACT-DRAFT.md"),
    ("SIGNING-PASS-4", "0.1", "signed_b9_gate", "docs/00-governance/signing/SIGNING-PASS-4.md"),
    ("EVD-GOV-013", "0.1", "remediated_candidate", "docs/evidence/EVD-GOV-013-pg-g0-authority-docket-v04-rf-remediated-candidate.md"),
    ("EVD-GOV-015", "0.1", "ACCEPT_EXACT_SHA", "docs/evidence/EVD-GOV-015-docket-v04-remediation-v3-acceptance.md"),
)
SIGNED_TRANSFORM_PATHS = {
    "Roadmap.md",
    "Master_Standards.md",
    "Backlog.md",
    "Progress_Log.md",
    "Recap_Today.md",
    "docs/00-governance/BOPEN-GOV-001-DRAFT.md",
    "docs/00-governance/registers/AUTHORITY-MATRIX.json",
    "docs/00-governance/registers/GOAL-REGISTER.json",
    "docs/00-governance/registers/AGENT-REGISTER.json",
    "docs/00-governance/registers/MODULE-REGISTER.json",
    "docs/00-governance/registers/SKILL-REGISTER.json",
    "docs/00-governance/registers/SCHEDULE-REGISTER.json",
    "docs/00-governance/registers/TECHNOLOGY-DECISION-ASSIGNMENTS.json",
    "docs/decisions/DEC-0007.md",
    "docs/decisions/DEC-0013.md",
    "docs/work-packages/GOV-P0-01.md",
    "docs/work-packages/GOV-P0-03.md",
    "docs/work-packages/GOV-P0-04.md",
}
DEFAULT_REPORT_PATH = Path("artifacts/validation/program-g0-authority-readiness.json")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
PLACEHOLDERS = {"", "pending", "tbd", "unknown", "unassigned", "none", "n/a"}

EXPECTED_DECISIONS = {
    "PG-G0-DEC-001": ("APPROVE_ARCHITECTURE", "DEC-0007", "Architecture Authority", {"Security Authority", "Data Authority"}),
    "PG-G0-DEC-002": ("ACCEPT_WORK_ITEM", "GOV-P0-01", "Engineering Authority", {"Product Authority"}),
    "PG-G0-DEC-003": ("APPROVE_ARCHITECTURE", "DEC-0010", "Architecture Authority", {"Product Authority", "Security Authority", "Data Authority"}),
    "PG-G0-DEC-004": ("APPROVE_GOAL", "BOPEN-GOAL-001", "Product Authority", {"Architecture Authority", "Security Authority", "Data Authority"}),
    "PG-G0-DEC-005": ("ACCEPT_EVIDENCE", "EVD-GOV-001", "Engineering Authority", set()),
    "PG-G0-DEC-006": ("PASS_PG_G0", "PG-G0-GATE-001", "Engineering Authority", {"Product Authority", "Architecture Authority", "Security Authority", "Data Authority"}),
}
B8_DECISION_IDS = {"PG-G0-DEC-001", "PG-G0-DEC-002", "PG-G0-DEC-003", "PG-G0-DEC-004", "PG-G0-DEC-005"}
EXPECTED_SUBJECT_REFS = {
    "DEC-0007": "docs/decisions/DEC-0007.md",
    "GOV-P0-01": "docs/work-packages/GOV-P0-01.md",
    "DEC-0010": "docs/decisions/DEC-0010.md",
    "BOPEN-GOAL-001": "docs/01-product/BOPEN-GOAL-001-DRAFT.md",
    "EVD-GOV-001": "docs/evidence/EVD-GOV-001-program-g0-controls.md",
    "PG-G0-GATE-001": "docs/00-governance/PG-G0-GATE-CONTRACT-DRAFT.md",
}
EXPECTED_ACTION_CONFIG = {
    "APPROVE_ARCHITECTURE": ("architecture_approval", False, {"Security Authority", "Data Authority"}),
    "ACCEPT_WORK_ITEM": ("work_item_acceptance", True, {"Owning Artifact Authority"}),
    "APPROVE_GOAL": ("normative_goal_approval", False, {"Architecture Authority"}),
    "ACCEPT_EVIDENCE": ("evidence_acceptance", False, set()),
    "CERTIFY_MODULE": ("module_certification", False, {"Product Authority", "Security Authority"}),
    "PROMOTE_SKILL": ("skill_promotion", True, set()),
    "AUTHORIZE_RELEASE": ("release_authorization", True, {"Security Authority", "Product Authority"}),
    "APPROVE_GOVERNANCE_BASELINE": ("governance_baseline_approval", True, {"Product Authority", "Architecture Authority", "Security Authority", "Data Authority"}),
    "APPROVE_PROGRAM_REGISTERS": ("program_register_approval", True, {"Product Authority", "Architecture Authority", "Security Authority", "Data Authority"}),
    "PASS_PG_G0": ("program_gate_passage", True, {"Product Authority", "Architecture Authority", "Security Authority", "Data Authority"}),
}
EXPECTED_PREPARED_DISPOSITIONS = {
    "PG-G0-PREP-001": ("B2", "APPROVE_GOVERNANCE_BASELINE", "BOPEN-GOV-001", "APPROVED", "Engineering Authority", {"Product Authority", "Architecture Authority", "Security Authority", "Data Authority"}),
    "PG-G0-PREP-002": ("B2", "APPROVE_PROGRAM_REGISTERS", "AUTHORITY-MATRIX-V0.2-PROPOSAL", "APPROVED", "Engineering Authority", {"Product Authority", "Architecture Authority", "Security Authority", "Data Authority"}),
    "PG-G0-PREP-003": ("B2", "APPROVE_GOVERNANCE_BASELINE", "DEC-0013", "ACCEPTED", "Engineering Authority", {"Product Authority", "Architecture Authority", "Security Authority", "Data Authority"}),
    "PG-G0-PREP-004": ("B3", "APPROVE_PROGRAM_REGISTERS", "GOAL-REGISTER", "APPROVED", "Engineering Authority", {"Product Authority", "Architecture Authority", "Security Authority", "Data Authority"}),
    "PG-G0-PREP-005": ("B3", "APPROVE_PROGRAM_REGISTERS", "AGENT-REGISTER", "APPROVED", "Engineering Authority", {"Product Authority", "Architecture Authority", "Security Authority", "Data Authority"}),
    "PG-G0-PREP-006": ("B3", "APPROVE_PROGRAM_REGISTERS", "MODULE-REGISTER", "APPROVED", "Engineering Authority", {"Product Authority", "Architecture Authority", "Security Authority", "Data Authority"}),
    "PG-G0-PREP-007": ("B3", "APPROVE_PROGRAM_REGISTERS", "SKILL-REGISTER", "APPROVED", "Engineering Authority", {"Product Authority", "Architecture Authority", "Security Authority", "Data Authority"}),
    "PG-G0-PREP-008": ("B3", "APPROVE_PROGRAM_REGISTERS", "SCHEDULE-REGISTER", "APPROVED", "Engineering Authority", {"Product Authority", "Architecture Authority", "Security Authority", "Data Authority"}),
    "PG-G0-PREP-009": ("B3", "APPROVE_PROGRAM_REGISTERS", "TECHNOLOGY-DECISION-ASSIGNMENTS", "APPROVED", "Engineering Authority", {"Product Authority", "Architecture Authority", "Security Authority", "Data Authority"}),
    "PG-G0-PREP-010": ("B4", "ACCEPT_WORK_ITEM", "GOV-P0-01", "ACCEPTED", "Engineering Authority", {"Product Authority"}),
    "PG-G0-PREP-011": ("B4", "ACCEPT_WORK_ITEM", "GOV-P0-04", "ACCEPTED", "Engineering Authority", {"Engineering Authority"}),
    "PG-G0-PREP-012": ("B5", "APPROVE_ARCHITECTURE", "DEC-0007", "APPROVED", "Architecture Authority", {"Security Authority", "Data Authority"}),
    "PG-G0-PREP-013": ("B6", "APPROVE_GOVERNANCE_BASELINE", "GOV-P0-03", "ACTIVE", "Engineering Authority", {"Product Authority", "Architecture Authority", "Security Authority", "Data Authority"}),
}
MISSING_CONTROL_PATHS = (
    "Roadmap.md",
    "Master_Standards.md",
    "Progress_Log.md",
    "Backlog.md",
    "Recap_Today.md",
)
NON_AUTHORITY_KEYS = {
    "pg_g0_passed",
    "production_implementation_authorized",
    "merge_authorized",
    "release_authorized",
    "deployment_authorized",
    "runtime_activation_authorized",
    "module_certified",
    "skill_promoted",
}
EFFECTIVE_OUTCOME_KEYS = {
    "program_goal_approved",
    "governance_baseline_approved",
    "work_package_accepted",
    "evidence_accepted",
    "ready_for_pg_g0_gate_decision",
}
TERMINAL_DECISIONS = {"APPROVE", "REJECT", "DEFER", "WITHDRAW", "EXPIRE"}
TERMINAL_CONCURRENCES = {"CONCUR", "NONCONCUR", "DEFER", "WITHDRAW", "EXPIRE"}
TERMINAL_REVIEWS = {"ACCEPT_EXACT_SHA", "REQUEST_CHANGES", "REJECT"}
STATE_TRANSITIONS = {
    "DRAFT": {"TECHNICAL_REVIEW", "PENDING_HUMAN_DECISIONS", "WITHDRAWN", "EXPIRED", "SUPERSEDED"},
    "TECHNICAL_REVIEW": {"PENDING_HUMAN_DECISIONS", "WITHDRAWN", "EXPIRED", "SUPERSEDED"},
    "PENDING_HUMAN_DECISIONS": {"TECHNICAL_REVIEW", "READY_FOR_FINAL_DISPOSITION", "DISPOSED", "WITHDRAWN", "EXPIRED", "SUPERSEDED"},
    "READY_FOR_FINAL_DISPOSITION": {"DISPOSED"},
    "DISPOSED": set(),
    "WITHDRAWN": set(),
    "EXPIRED": set(),
    "SUPERSEDED": set(),
}


def read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "missing"
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"invalid: {exc}"
    return (value, None) if isinstance(value, dict) else (None, "must be a JSON object")


def parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def non_placeholder(value: object) -> bool:
    return isinstance(value, str) and value.strip().casefold() not in PLACEHOLDERS


def normalized_identity(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def actor_identity(actor: object) -> str:
    if not isinstance(actor, dict):
        return ""
    return normalized_identity(actor.get("human_identity_ref") or actor.get("identity_ref"))


def exact_keys(value: object, expected: set[str], label: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    errors: list[str] = []
    missing = expected - set(value)
    unknown = set(value) - expected
    if missing:
        errors.append(f"{label} missing fields: {', '.join(sorted(missing))}")
    if unknown:
        errors.append(f"{label} unknown fields: {', '.join(sorted(unknown))}")
    return errors


def _matches_type(value: object, expected: str) -> bool:
    return {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "boolean": lambda item: isinstance(item, bool),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "null": lambda item: item is None,
    }.get(expected, lambda _item: False)(value)


def _resolve_schema_ref(schema_root: dict[str, Any], ref: str) -> dict[str, Any] | None:
    if not ref.startswith("#/"):
        return None
    current: object = schema_root
    for part in ref[2:].split("/"):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current if isinstance(current, dict) else None


def validate_schema_instance(
    value: object,
    schema: dict[str, Any],
    schema_root: dict[str, Any],
    label: str,
) -> list[str]:
    if "$ref" in schema:
        resolved = _resolve_schema_ref(schema_root, str(schema["$ref"]))
        return [f"{label} schema reference invalid"] if resolved is None else validate_schema_instance(value, resolved, schema_root, label)
    if "oneOf" in schema:
        branches = schema.get("oneOf")
        if not isinstance(branches, list):
            return [f"{label} oneOf invalid"]
        matches = [validate_schema_instance(value, item, schema_root, label) for item in branches if isinstance(item, dict)]
        if sum(not item for item in matches) != 1:
            return [f"{label} must match exactly one schema alternative"]
        return []

    errors: list[str] = []
    all_of = schema.get("allOf")
    if isinstance(all_of, list):
        for branch in all_of:
            if isinstance(branch, dict):
                errors.extend(validate_schema_instance(value, branch, schema_root, label))
    condition = schema.get("if")
    if isinstance(condition, dict):
        condition_matches = not validate_schema_instance(value, condition, schema_root, label)
        selected = schema.get("then") if condition_matches else schema.get("else")
        if isinstance(selected, dict):
            errors.extend(validate_schema_instance(value, selected, schema_root, label))
    expected = schema.get("type")
    types = [expected] if isinstance(expected, str) else expected
    if isinstance(types, list) and not any(isinstance(item, str) and _matches_type(value, item) for item in types):
        return [f"{label} type invalid"]
    if value is None:
        return errors
    if "const" in schema and value != schema["const"]:
        errors.append(f"{label} constant invalid")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{label} enum invalid")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{label} string too short")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.fullmatch(pattern, value) is None:
            errors.append(f"{label} pattern invalid")
        if schema.get("format") == "date-time" and parse_datetime(value) is None:
            errors.append(f"{label} date-time invalid")
    if isinstance(value, int) and not isinstance(value, bool) and "minimum" in schema and value < schema["minimum"]:
        errors.append(f"{label} below minimum")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{label} array too short")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{label} array too long")
        if schema.get("uniqueItems"):
            normalized = [json.dumps(item, sort_keys=True) for item in value]
            if len(normalized) != len(set(normalized)):
                errors.append(f"{label} array items not unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(validate_schema_instance(item, item_schema, schema_root, f"{label}[{index}]"))
    if isinstance(value, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in value:
                    errors.append(f"{label} missing field: {key}")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            if schema.get("additionalProperties") is False:
                for key in sorted(set(value) - set(properties)):
                    errors.append(f"{label} unknown field: {key}")
            for key, item in value.items():
                definition = properties.get(key)
                if isinstance(definition, dict):
                    errors.extend(validate_schema_instance(item, definition, schema_root, f"{label}.{key}"))
    return errors


def _run_git(root: Path, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def resolve_head(root: Path) -> str | None:
    completed = _run_git(root, ["rev-parse", "HEAD"])
    value = completed.stdout.strip()
    return value if completed.returncode == 0 and SHA_PATTERN.fullmatch(value) else None


def resolve_tree(root: Path, commit_sha: str) -> str | None:
    if SHA_PATTERN.fullmatch(commit_sha) is None:
        return None
    completed = _run_git(root, ["show", "-s", "--format=%T", commit_sha])
    value = completed.stdout.strip()
    return value if completed.returncode == 0 and SHA_PATTERN.fullmatch(value) else None


def commit_datetime(root: Path, commit_sha: str) -> datetime | None:
    completed = _run_git(root, ["show", "-s", "--format=%cI", commit_sha])
    return parse_datetime(completed.stdout.strip()) if completed.returncode == 0 else None


def is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    return _run_git(root, ["merge-base", "--is-ancestor", ancestor, descendant]).returncode == 0


def read_file_at_commit(root: Path, commit_sha: str, relative: str) -> bytes | None:
    completed = subprocess.run(
        ["git", "-C", str(root), "show", f"{commit_sha}:{relative}"],
        capture_output=True,
        check=False,
    )
    return completed.stdout if completed.returncode == 0 else None


def build_v04_binding_inventory(root: Path = ROOT) -> dict[str, Any]:
    predecessor_bytes = read_file_at_commit(root, SIGNED_SUBSTRATE_COMMIT, PREDECESSOR_DOCKET_PATH)
    if predecessor_bytes is None:
        raise ValueError("signed predecessor docket missing")
    predecessor = json.loads(predecessor_bytes.decode("utf-8"))
    metadata = [
        (item["artifact_id"], item["version"], item["status"], item["artifact_ref"])
        for item in predecessor["governing_artifacts"]
    ]
    metadata.extend(EXTRA_INVENTORY_RECORDS)
    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for artifact_id, version, status, relative in metadata:
        if artifact_id in seen_ids or relative in seen_paths:
            raise ValueError(f"duplicate inventory metadata: {artifact_id} {relative}")
        content = read_file_at_commit(root, TERMINAL_SUBSTRATE_COMMIT, relative)
        if content is None:
            raise ValueError(f"signed substrate path missing: {relative}")
        seen_ids.add(artifact_id)
        seen_paths.add(relative)
        records.append({
            "artifact_id": artifact_id,
            "version": version,
            "status": status,
            "path": relative,
            "sha256": bytes_sha256(content),
            "bytes": len(content),
        })
    return {
        "inventory_id": "PG-G0-AUTH-001-V0.5-BINDINGS",
        "version": "0.5.0",
        "status": "frozen_signed_substrate_inventory",
        "generated_at": TERMINAL_SIGNED_AT,
        "repository_ref": "bstBizEra/bopen",
        "substrate_commit_sha": TERMINAL_SUBSTRATE_COMMIT,
        "substrate_tree_sha": TERMINAL_SUBSTRATE_TREE,
        "substrate_branch": TERMINAL_SUBSTRATE_BRANCH,
        "records": records,
    }


def signed_authority_actor(role: str, registry_sha256: str) -> dict[str, Any]:
    return {
        "actor_kind": "HUMAN",
        "human_identity_ref": "human:operator-001",
        "identity_provider": "bopen-authority-identity-registry",
        "identity_subject": "HUMAN-OPERATOR-001",
        "authority_role": role,
        "role_binding_ref": "docs/00-governance/registers/AUTHORITY-IDENTITY-REGISTER.json#HUMAN-OPERATOR-001",
        "role_binding_sha256": registry_sha256,
        "role_binding_commit_sha": SIGNED_SUBSTRATE_COMMIT,
        "role_binding_tree_sha": SIGNED_SUBSTRATE_TREE,
        "role_binding_status": "approved",
        "authority_mode": "DIRECT",
        "delegation_ref": None,
        "delegation_binding": None,
    }


def build_v04_docket(root: Path = ROOT) -> dict[str, Any]:
    predecessor_bytes = read_file_at_commit(root, SIGNED_SUBSTRATE_COMMIT, PREDECESSOR_DOCKET_PATH)
    if predecessor_bytes is None:
        raise ValueError("signed predecessor docket missing")
    docket = json.loads(predecessor_bytes.decode("utf-8"))
    inventory = build_v04_binding_inventory(root)
    inventory_by_path = {item["path"]: item for item in inventory["records"]}
    registry_path = "docs/00-governance/registers/AUTHORITY-IDENTITY-REGISTER.json"
    registry_sha256 = inventory_by_path[registry_path]["sha256"]

    docket.update({
        "$schema": "bopen://schemas/governance/pg-g0-authority-docket/0.4.0-draft",
        "version": "0.4.0-draft",
        "status": "signed_state_candidate",
        "updated_at": SIGNED_AT,
        "repository_binding": {
            "commit_sha": SIGNED_SUBSTRATE_COMMIT,
            "tree_sha": SIGNED_SUBSTRATE_TREE,
            "branch": SIGNED_SUBSTRATE_BRANCH,
            "repository_ref": "bstBizEra/bopen",
        },
        "binding_inventory": {
            "inventory_ref": BINDING_INVENTORY_PATH.as_posix(),
            "inventory_id": inventory["inventory_id"],
            "substrate_commit_sha": SIGNED_SUBSTRATE_COMMIT,
            "substrate_tree_sha": SIGNED_SUBSTRATE_TREE,
            "record_count": len(inventory["records"]),
        },
        "technical_review": {
            "candidate_commit_sha": None,
            "candidate_tree_sha": None,
            "maker": {
                "actor_kind": "AGENT",
                "identity_ref": "BST-Codex-Motor",
                "role": "Orchestrator Agent",
                "registration_ref": None,
                "session_ref": None,
            },
            "checker": None,
            "independence_asserted": False,
            "verdict": "PENDING",
            "reviewed_at": None,
            "evidence_refs": [],
        },
        "state": "PENDING_HUMAN_DECISIONS",
        "effective_outcome": {
            "program_goal_approved": True,
            "governance_baseline_approved": True,
            "work_package_accepted": True,
            "evidence_accepted": True,
            "ready_for_pg_g0_gate_decision": True,
        },
        "blockers": [
            "independent exact-SHA technical review of the v0.4 signed-state successor is pending",
            "B9 PASS_PG_G0 remains PENDING until a fresh independent conformance receipt is bound",
            "solo-operator authority concentration remains disclosed and provides no inter-human concurrence independence",
            "merge, release, deployment, runtime and production implementation remain unauthorized",
        ],
    })
    for artifact in docket["governing_artifacts"]:
        record = inventory_by_path.get(artifact["artifact_ref"])
        if record is None:
            raise ValueError(f"governing artifact missing from v0.4 inventory: {artifact['artifact_ref']}")
        artifact["sha256"] = record["sha256"]

    gate_record = inventory_by_path["docs/00-governance/PG-G0-GATE-CONTRACT-DRAFT.md"]
    docket["governing_artifacts"].append({
        "artifact_id": "PG-G0-GATE-001",
        "version": "0.1-draft",
        "status": "Draft; ineffective",
        "artifact_ref": "docs/00-governance/PG-G0-GATE-CONTRACT-DRAFT.md",
        "sha256": gate_record["sha256"],
    })

    matrix_bytes = (root / AUTHORITY_MATRIX_PATH).read_bytes()
    docket["authority_source"] = {
        "matrix_id": "PG-REG-AUTHORITY-001",
        "artifact_ref": AUTHORITY_MATRIX_PATH.as_posix(),
        "proposal_ref": "docs/00-governance/AUTHORITY-MATRIX-0.2.0-PROPOSAL.json",
        "version": "0.2.0",
        "status": "approved",
        "sha256": bytes_sha256(matrix_bytes),
        "signing_ref": V03_SIGNED_DECISION_REF,
        "effective": True,
    }
    for decision in docket["decision_requests"]:
        decision_id = decision["decision_id"]
        if decision_id == "PG-G0-DEC-006":
            continue
        role = decision["final_decision_role"]
        decision["checked_by"] = None
        decision["final_authority_actor"] = signed_authority_actor(role, registry_sha256)
        for concurrence in decision["required_concurrences"]:
            concurrence["authority_actor"] = signed_authority_actor(concurrence["authority_role"], registry_sha256)
            concurrence["disposition"] = "CONCUR"
            concurrence["decided_at"] = SIGNED_AT
            concurrence["expires_at"] = decision["expires_at"]
            concurrence["evidence_refs"] = sorted(SIGNED_EVIDENCE_REFS)
        decision["final_disposition"] = {
            "value": "APPROVE",
            "decided_at": SIGNED_AT,
            "reason_code": "OPERATOR_SIGNED_B8_APPROVE",
            "decision_ref": SIGNED_DECISION_REF,
            "evidence_refs": sorted(SIGNED_EVIDENCE_REFS),
            "effective": True,
        }
    docket["decision_requests"].append({
        "decision_id": "PG-G0-DEC-006",
        "action_id": "PASS_PG_G0",
        "subject": {
            "artifact_id": "PG-G0-GATE-001",
            "version": "0.1-draft",
            "artifact_ref": "docs/00-governance/PG-G0-GATE-CONTRACT-DRAFT.md",
            "sha256": gate_record["sha256"],
            "commit_sha": SIGNED_SUBSTRATE_COMMIT,
            "tree_sha": SIGNED_SUBSTRATE_TREE,
        },
        "prepared_by": {
            "actor_kind": "AGENT",
            "identity_ref": "BST-Codex-Motor",
            "role": "QA & Evidence Agent",
            "registration_ref": None,
            "session_ref": None,
        },
        "checked_by": None,
        "accountable_authority_role": "Engineering Authority",
        "final_decision_role": "Engineering Authority",
        "final_authority_actor": None,
        "required_concurrences": [
            {
                "authority_role": role,
                "required": True,
                "source_refs": ["docs/00-governance/AUTHORITY-MATRIX-0.2.0-PROPOSAL.json"],
                "bound_commit_sha": SIGNED_SUBSTRATE_COMMIT,
                "bound_tree_sha": SIGNED_SUBSTRATE_TREE,
                "authority_actor": None,
                "disposition": "PENDING",
                "decided_at": None,
                "expires_at": None,
                "evidence_refs": [],
            }
            for role in ("Product Authority", "Architecture Authority", "Security Authority", "Data Authority")
        ],
        "expires_at": "2026-08-21T00:00:00+07:00",
        "prerequisite_refs": [
            "ready_for_pg_g0_gate_decision=true",
            "fresh independent conformance receipt covering the PG-G0 requirements",
            "independent conformance receipt must be bound before any B9 final disposition",
        ],
        "final_disposition": {
            "value": "PENDING",
            "decided_at": None,
            "reason_code": "PENDING_INDEPENDENT_CONFORMANCE_AND_HUMAN_B9_DECISION",
            "decision_ref": None,
            "evidence_refs": [],
            "effective": False,
        },
    })
    docket["state_history"].append({
        "sequence": len(docket["state_history"]) + 1,
        "from": "TECHNICAL_REVIEW",
        "to": "PENDING_HUMAN_DECISIONS",
        "changed_at": SIGNED_AT,
        "changed_by": {
            "actor_kind": "HUMAN",
            "identity_ref": "HUMAN-OPERATOR-001",
            "role": "Engineering Authority",
            "registration_ref": "docs/00-governance/registers/AUTHORITY-IDENTITY-REGISTER.json#HUMAN-OPERATOR-001",
            "session_ref": None,
        },
        "reason_code": "B8_SIGNED_B9_SURFACED_PENDING_INDEPENDENT_CONFORMANCE",
        "commit_sha": SIGNED_SUBSTRATE_COMMIT,
        "tree_sha": SIGNED_SUBSTRATE_TREE,
        "evidence_refs": sorted(SIGNED_EVIDENCE_REFS),
    })
    docket["$schema"] = "bopen://schemas/governance/pg-g0-authority-docket/0.5.0-terminal"
    docket["version"] = "0.5.0-terminal"
    docket["status"] = "gate_passed"
    docket["updated_at"] = TERMINAL_SIGNED_AT
    docket["state"] = "DISPOSED"
    docket["repository_binding"] = {
        "commit_sha": TERMINAL_SUBSTRATE_COMMIT,
        "tree_sha": TERMINAL_SUBSTRATE_TREE,
        "branch": TERMINAL_SUBSTRATE_BRANCH,
        "repository_ref": "bstBizEra/bopen",
    }
    docket["binding_inventory"] = {
        "inventory_ref": "docs/00-governance/authority-dockets/PG-G0-AUTH-001-V0.5-BINDING-INVENTORY.json",
        "inventory_id": inventory["inventory_id"],
        "substrate_commit_sha": TERMINAL_SUBSTRATE_COMMIT,
        "substrate_tree_sha": TERMINAL_SUBSTRATE_TREE,
        "record_count": len(inventory["records"]),
    }
    docket["blockers"] = [
        "independent exact-SHA technical review of the terminal gate-passed successor is pending",
        "merge, release, deployment, runtime and production implementation remain unauthorized",
        "solo-operator authority concentration remains disclosed and provides no inter-human concurrence independence",
    ]
    b9 = next(item for item in docket["decision_requests"] if item["decision_id"] == "PG-G0-DEC-006")
    b9["final_authority_actor"] = {
        **signed_authority_actor("Engineering Authority", registry_sha256),
        "role_binding_commit_sha": TERMINAL_SUBSTRATE_COMMIT,
        "role_binding_tree_sha": TERMINAL_SUBSTRATE_TREE,
    }
    for concurrence in b9["required_concurrences"]:
        concurrence["authority_actor"] = {
            **signed_authority_actor(concurrence["authority_role"], registry_sha256),
            "role_binding_commit_sha": TERMINAL_SUBSTRATE_COMMIT,
            "role_binding_tree_sha": TERMINAL_SUBSTRATE_TREE,
        }
        concurrence["bound_commit_sha"] = b9["subject"]["commit_sha"]
        concurrence["bound_tree_sha"] = b9["subject"]["tree_sha"]
        concurrence["disposition"] = "CONCUR"
        concurrence["decided_at"] = TERMINAL_SIGNED_AT
        concurrence["expires_at"] = b9["expires_at"]
        concurrence["evidence_refs"] = sorted(TERMINAL_EVIDENCE_REFS)
    b9["final_disposition"] = {
        "value": "APPROVE",
        "decided_at": TERMINAL_SIGNED_AT,
        "reason_code": "OPERATOR_SIGNED_B9_PASS_PG_G0_APPROVE",
        "decision_ref": TERMINAL_DECISION_REF,
        "evidence_refs": sorted(TERMINAL_EVIDENCE_REFS),
        "effective": True,
    }
    docket["state_history"].append({
        "sequence": len(docket["state_history"]) + 1,
        "from": "PENDING_HUMAN_DECISIONS",
        "to": "DISPOSED",
        "changed_at": TERMINAL_SIGNED_AT,
        "changed_by": {
            "actor_kind": "HUMAN",
            "identity_ref": "HUMAN-OPERATOR-001",
            "role": "Engineering Authority",
            "registration_ref": "docs/00-governance/registers/AUTHORITY-IDENTITY-REGISTER.json#HUMAN-OPERATOR-001",
            "session_ref": None,
        },
        "reason_code": "B9_SIGNED_PG_G0_PASSED",
        "commit_sha": TERMINAL_SUBSTRATE_COMMIT,
        "tree_sha": TERMINAL_SUBSTRATE_TREE,
        "evidence_refs": sorted(TERMINAL_EVIDENCE_REFS),
    })
    return docket


def validate_signed_artifact_transforms(root: Path) -> list[str]:
    errors: list[str] = []
    register_paths = (
        "docs/00-governance/registers/AUTHORITY-MATRIX.json",
        "docs/00-governance/registers/GOAL-REGISTER.json",
        "docs/00-governance/registers/AGENT-REGISTER.json",
        "docs/00-governance/registers/MODULE-REGISTER.json",
        "docs/00-governance/registers/SKILL-REGISTER.json",
        "docs/00-governance/registers/SCHEDULE-REGISTER.json",
        "docs/00-governance/registers/TECHNOLOGY-DECISION-ASSIGNMENTS.json",
    )
    for relative in register_paths:
        source = read_file_at_commit(root, V03_SUBSTRATE_COMMIT, relative)
        try:
            expected = json.loads(source.decode("utf-8")) if source is not None else None
            current = json.loads((root / relative).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            errors.append(f"signed register transformation invalid: {relative}")
            continue
        if not isinstance(expected, dict):
            errors.append(f"signed register substrate invalid: {relative}")
            continue
        expected["version"] = str(expected.get("version", "")).removesuffix("-draft")
        expected["status"] = "approved"
        expected["updated_at"] = V03_SIGNED_AT
        expected["approved_by"] = "HUMAN-OPERATOR-001"
        expected["approved_at"] = V03_SIGNED_AT
        expected["approval_ref"] = V03_SIGNED_DECISION_REF
        if relative == AUTHORITY_MATRIX_PATH.as_posix():
            for entry in expected.get("entries", []):
                if isinstance(entry, dict):
                    entry["status"] = "approved"
        if current != expected:
            errors.append(f"signed register transformation differs from signed outcome: {relative}")

    append_markers = {
        "docs/00-governance/BOPEN-GOV-001-DRAFT.md": ("## Append-only approval record — 2026-07-23", "**Outcome:** APPROVED; effective"),
        "docs/decisions/DEC-0013.md": ("## Append-only accepted decision — 2026-07-23", "**Outcome:** ACCEPTED; option 1; effective"),
        "docs/work-packages/GOV-P0-01.md": ("## Append-only acceptance record — 2026-07-23", "**Outcome:** ACCEPTED; effective"),
        "docs/work-packages/GOV-P0-04.md": ("## Append-only acceptance record — 2026-07-23", "**Outcome:** ACCEPTED; effective"),
        "docs/decisions/DEC-0007.md": ("## Append-only accepted decision — 2026-07-23", "**Outcome:** APPROVED; option 1; BOOT-B7 approved"),
        "docs/work-packages/GOV-P0-03.md": ("## Append-only activation record — 2026-07-23", "**Outcome:** ACTIVE; effective through the atomic five-ledger activation event"),
    }
    common_markers = (
        "HUMAN-OPERATOR-001",
        V03_SIGNED_AT,
        V03_SIGNED_DECISION_REF,
        "EVD-GOV-008",
    )
    for relative, specific_markers in append_markers.items():
        source = read_file_at_commit(root, V03_SUBSTRATE_COMMIT, relative)
        path = root / relative
        if source is None or not path.is_file():
            errors.append(f"signed append-only artifact missing: {relative}")
            continue
        current = path.read_bytes()
        if not current.startswith(source):
            errors.append(f"signed append-only artifact rewrites substrate: {relative}")
            continue
        appended = current[len(source):].decode("utf-8", errors="replace")
        for marker in specific_markers:
            if appended.count(marker) != 1:
                errors.append(f"signed append-only artifact marker invalid {relative}: {marker}")
        for marker in common_markers:
            if marker not in appended:
                errors.append(f"signed append-only artifact marker missing {relative}: {marker}")
    return errors


def is_tracked_path(root: Path, relative: str) -> bool:
    return _run_git(root, ["ls-files", "--error-unmatch", "--", relative]).returncode == 0


def safe_relative_path(root: Path, value: object, label: str) -> tuple[Path | None, list[str]]:
    if not non_placeholder(value):
        return None, [f"{label} is required"]
    relative = str(value)
    pure = PurePosixPath(relative)
    if "\\" in relative or pure.is_absolute() or ".." in pure.parts or PureWindowsPath(relative).drive:
        return None, [f"{label} escapes repository"]
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return None, [f"{label} escapes repository"]
    return path, []


def validate_evidence_refs(root: Path, refs: object, label: str, *, required: bool) -> list[str]:
    if not isinstance(refs, list):
        return [f"{label} must be an array"]
    if required and not refs:
        return [f"{label} requires evidence"]
    errors: list[str] = []
    if len(refs) != len(set(str(item) for item in refs)):
        errors.append(f"{label} evidence refs must be unique")
    for index, item in enumerate(refs):
        path, path_errors = safe_relative_path(root, item, f"{label} evidence[{index}]")
        errors.extend(path_errors)
        if path is None:
            continue
        relative = str(item)
        if not path.is_file():
            errors.append(f"{label} evidence missing: {relative}")
        elif not is_tracked_path(root, relative):
            errors.append(f"{label} evidence untracked: {relative}")
    return errors


def validate_evidence_binding(root: Path, refs: object, label: str, commit_sha: str) -> list[str]:
    errors = validate_evidence_refs(root, refs, label, required=True)
    if not isinstance(refs, list):
        return errors
    bound = False
    for item in refs:
        path, _ = safe_relative_path(root, item, f"{label} evidence")
        if path is not None and path.is_file():
            try:
                if commit_sha in path.read_text(encoding="utf-8"):
                    bound = True
            except (OSError, UnicodeDecodeError):
                continue
    if not bound:
        errors.append(f"{label} evidence must contain exact candidate SHA {commit_sha}")
    return errors


def validate_evidence_at_commit(
    root: Path,
    refs: object,
    label: str,
    commit_sha: str,
) -> list[str]:
    errors = validate_evidence_refs(root, refs, label, required=True)
    if not isinstance(refs, list):
        return errors
    for item in refs:
        path, path_errors = safe_relative_path(root, item, f"{label} evidence")
        if path_errors or path is None:
            continue
        relative = path.relative_to(root).as_posix()
        if read_file_at_commit(root, commit_sha, relative) is None:
            errors.append(f"{label} evidence absent at bound commit: {relative}")
    return errors


def validate_actor(actor: object, label: str, *, human_only: bool = False) -> list[str]:
    expected = {"actor_kind", "identity_ref", "role", "registration_ref", "session_ref"}
    errors = exact_keys(actor, expected, label)
    if errors or not isinstance(actor, dict):
        return errors
    if actor.get("actor_kind") not in {"HUMAN", "AGENT"}:
        errors.append(f"{label} actor_kind invalid")
    if human_only and actor.get("actor_kind") != "HUMAN":
        errors.append(f"{label} must be a human")
    if not non_placeholder(actor.get("identity_ref")) or not non_placeholder(actor.get("role")):
        errors.append(f"{label} identity and role are required")
    return errors


def _split_fragment_ref(value: object, label: str) -> tuple[str | None, str | None, list[str]]:
    if not isinstance(value, str) or value.count("#") != 1:
        return None, None, [f"{label} must contain one record fragment"]
    relative, record_id = value.split("#", 1)
    if not relative or not record_id:
        return None, None, [f"{label} path and record id are required"]
    return relative, record_id, []


def _find_record(document: object, record_id: str) -> dict[str, Any] | None:
    if not isinstance(document, dict):
        return None
    candidates = document.get("entries")
    if not isinstance(candidates, list):
        candidates = [document]
    matches = [
        item for item in candidates
        if isinstance(item, dict)
        and record_id in {
            item.get("record_id"), item.get("identity_id"),
            item.get("authority_identity_id"), item.get("delegation_id"),
        }
    ]
    return matches[0] if len(matches) == 1 else None


def _find_identity_record(document: object, human_identity_ref: object) -> dict[str, Any] | None:
    if not isinstance(document, dict):
        return None
    entries = document.get("entries")
    if not isinstance(entries, list):
        return None
    expected = normalized_identity(human_identity_ref)
    matches = [
        item for item in entries
        if isinstance(item, dict)
        and normalized_identity(item.get("human_identity_ref")) == expected
    ]
    return matches[0] if len(matches) == 1 else None


def validate_role_binding(
    root: Path,
    actor: dict[str, Any],
    label: str,
    required_role: str,
    as_of: datetime,
    authority_source: dict[str, Any],
    governing_artifacts: dict[str, dict[str, Any]],
    repository_commit_sha: str,
    repository_tree_sha: str,
    action_id: str,
    subject_ref: str,
) -> list[str]:
    errors: list[str] = []
    relative, record_id, ref_errors = _split_fragment_ref(actor.get("role_binding_ref"), f"{label} role_binding_ref")
    errors.extend(ref_errors)
    expected_path = "docs/00-governance/registers/AUTHORITY-IDENTITY-REGISTER.json"
    if relative is not None and relative != expected_path:
        errors.append(f"{label} role binding must use the approved identity registry path")
    if actor.get("role_binding_status") != "approved":
        errors.append(f"{label} role binding status must be approved")
    if authority_source.get("status") != "approved" or authority_source.get("effective") is not True:
        errors.append(f"{label} requires an approved effective authority source")
    registry_binding = next(
        (
            item for item in governing_artifacts.values()
            if item.get("artifact_ref") == expected_path
        ),
        None,
    )
    if registry_binding is None or str(registry_binding.get("status", "")).casefold() != "approved":
        errors.append(f"{label} identity registry must be an approved governing artifact")
    commit_sha = str(actor.get("role_binding_commit_sha", ""))
    tree_sha = str(actor.get("role_binding_tree_sha", ""))
    digest = actor.get("role_binding_sha256")
    if commit_sha != repository_commit_sha or tree_sha != repository_tree_sha:
        errors.append(f"{label} role binding must match repository binding commit/tree")
    if registry_binding is not None and digest != registry_binding.get("sha256"):
        errors.append(f"{label} role binding digest must match governing artifact")
    head = resolve_head(root)
    if resolve_tree(root, commit_sha) != tree_sha:
        errors.append(f"{label} role binding commit/tree mismatch")
    if head is None or not is_ancestor(root, commit_sha, head):
        errors.append(f"{label} role binding commit must be an ancestor of HEAD")
    if relative is None:
        return errors
    path, path_errors = safe_relative_path(root, relative, f"{label} role binding path")
    errors.extend(path_errors)
    committed = read_file_at_commit(root, commit_sha, relative)
    if committed is None:
        errors.append(f"{label} approved identity registry absent at bound commit")
        return errors
    if not isinstance(digest, str) or SHA256_PATTERN.fullmatch(digest) is None or bytes_sha256(committed) != digest:
        errors.append(f"{label} role binding sha256 mismatch")
    if path is None or not path.is_file() or not is_tracked_path(root, relative):
        errors.append(f"{label} approved identity registry missing or untracked")
        return errors
    if file_sha256(path) != digest:
        errors.append(f"{label} current identity registry drift")
    try:
        registry = json.loads(committed.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        errors.append(f"{label} approved identity registry invalid")
        return errors
    if not isinstance(registry, dict) or str(registry.get("status", "")).casefold() != "approved":
        errors.append(f"{label} identity registry is not approved")
    record = _find_record(registry, str(record_id))
    if record is None or str(record.get("status", "")).casefold() != "approved":
        errors.append(f"{label} approved identity record missing")
        return errors
    roles = record.get("authority_roles")
    role_matches = required_role in roles if isinstance(roles, list) else record.get("authority_role") == required_role
    expected_pairs = {
        "human_identity_ref": actor.get("human_identity_ref"),
        "identity_provider": actor.get("identity_provider"),
        "identity_subject": actor.get("identity_subject"),
    }
    if any(normalized_identity(record.get(key)) != normalized_identity(value) for key, value in expected_pairs.items()) or not role_matches:
        errors.append(f"{label} identity registry record does not match actor")
    actions = record.get("action_ids")
    subjects = record.get("subject_refs")
    if not isinstance(actions, list) or action_id not in actions:
        errors.append(f"{label} identity role binding action scope missing")
    if not isinstance(subjects, list) or subject_ref not in subjects:
        errors.append(f"{label} identity role binding subject scope missing")
    valid_from = parse_datetime(record.get("valid_from"))
    expires = parse_datetime(record.get("expires_at"))
    if valid_from is None or expires is None or not (valid_from <= as_of < expires):
        errors.append(f"{label} identity role binding is not currently effective")
    if "revoked_at" not in record or record.get("revoked_at") is not None:
        errors.append(f"{label} identity role binding is revoked or lacks revocation state")
    errors.extend(validate_evidence_at_commit(
        root,
        record.get("evidence_refs"),
        f"{label} identity role binding",
        commit_sha,
    ))
    return errors


def validate_authority_actor(
    actor: object,
    label: str,
    required_role: str,
    schema: dict[str, Any],
    *,
    root: Path,
    as_of: datetime,
    action_id: str,
    subject_ref: str,
    authority_source: dict[str, Any],
    governing_artifacts: dict[str, dict[str, Any]],
    repository_commit_sha: str,
    repository_tree_sha: str,
) -> list[str]:
    actor_schema = schema.get("$defs", {}).get("authorityActor", {})
    expected = set(actor_schema.get("required", [])) if isinstance(actor_schema, dict) else set()
    errors = exact_keys(actor, expected, label)
    if errors or not isinstance(actor, dict):
        return errors
    if actor.get("actor_kind") != "HUMAN":
        errors.append(f"{label} final authority must be human")
    if not non_placeholder(actor.get("human_identity_ref")):
        errors.append(f"{label} human identity is required")
    if actor.get("authority_role") != required_role:
        errors.append(f"{label} authority role must be {required_role}")
    authority_mode = actor.get("authority_mode")
    if authority_mode != "DIRECT":
        errors.append(f"{label} authority mode must be DIRECT")
    for field in ("identity_provider", "identity_subject", "role_binding_ref"):
        if field in expected and not non_placeholder(actor.get(field)):
            errors.append(f"{label} {field} is required")
    if "role_binding_ref" in expected:
        errors.extend(validate_role_binding(
            root,
            actor,
            label,
            required_role,
            as_of,
            authority_source,
            governing_artifacts,
            repository_commit_sha,
            repository_tree_sha,
            action_id,
            subject_ref,
        ))
    delegation_ref = actor.get("delegation_ref")
    delegation = actor.get("delegation_binding")
    if authority_mode == "DIRECT":
        if delegation_ref is not None or delegation is not None:
            errors.append(f"{label} direct authority cannot carry delegation")
    return errors


def validate_artifact_binding(
    root: Path,
    binding: object,
    label: str,
    commit_sha: str,
) -> list[str]:
    expected = {"artifact_id", "version", "status", "artifact_ref", "sha256"}
    errors = exact_keys(binding, expected, label)
    if errors or not isinstance(binding, dict):
        return errors
    relative = binding.get("artifact_ref")
    digest = binding.get("sha256")
    path, path_errors = safe_relative_path(root, relative, f"{label} artifact_ref")
    errors.extend(path_errors)
    if path is None:
        return errors
    if not isinstance(digest, str) or SHA256_PATTERN.fullmatch(digest) is None:
        errors.append(f"{label} sha256 invalid")
        return errors
    committed = read_file_at_commit(root, commit_sha, str(relative))
    if committed is None:
        errors.append(f"{label} missing at bound commit: {relative}")
    elif bytes_sha256(committed) != digest:
        errors.append(f"{label} bound commit sha256 mismatch: {relative}")
    if not path.is_file():
        errors.append(f"{label} artifact missing: {relative}")
    elif file_sha256(path) != digest:
        if str(relative) not in SIGNED_TRANSFORM_PATHS:
            errors.append(f"{label} current artifact drift: {relative}")
    if not is_tracked_path(root, str(relative)):
        errors.append(f"{label} artifact untracked: {relative}")
    return errors


def _validate_current_window(
    decided_at: datetime | None,
    expires_at: datetime | None,
    as_of: datetime,
    label: str,
    disposition: str,
) -> list[str]:
    errors: list[str] = []
    if decided_at is None or expires_at is None:
        return [f"{label} requires decided_at and expires_at"]
    if disposition == "EXPIRE":
        if expires_at > as_of or decided_at < expires_at or decided_at > as_of:
            errors.append(f"{label} expiry chronology invalid")
    elif not (decided_at <= as_of < expires_at):
        errors.append(f"{label} is future or expired")
    if disposition != "EXPIRE" and decided_at >= expires_at:
        errors.append(f"{label} time window invalid")
    return errors


def validate_pg_g0_authority_docket(root: Path = ROOT, as_of: datetime | None = None) -> list[str]:
    as_of = as_of or datetime.now(timezone.utc)
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    errors: list[str] = []
    docket, docket_error = read_json(root / DOCKET_PATH)
    schema, schema_error = read_json(root / SCHEMA_PATH)
    matrix, matrix_error = read_json(root / AUTHORITY_MATRIX_PATH)
    if docket_error:
        return [f"authority docket {docket_error}"]
    if schema_error:
        return [f"authority docket schema {schema_error}"]
    if matrix_error:
        return [f"authority matrix {matrix_error}"]
    assert docket is not None and schema is not None and matrix is not None
    predecessor_bytes = read_file_at_commit(root, SIGNED_SUBSTRATE_COMMIT, PREDECESSOR_DOCKET_PATH)
    try:
        predecessor = json.loads(predecessor_bytes.decode("utf-8")) if predecessor_bytes is not None else None
    except (UnicodeDecodeError, json.JSONDecodeError):
        predecessor = None
    if not isinstance(predecessor, dict):
        errors.append("signed predecessor docket missing or invalid")
        predecessor = {}

    errors.extend(validate_schema_instance(docket, schema, schema, "authority docket"))
    if docket.get("$schema") != schema.get("$id"):
        errors.append("authority docket schema binding mismatch")
    if docket.get("docket_id") != "PG-G0-AUTH-001" or docket.get("version") != "0.5.0-terminal":
        errors.append("authority docket identity/version invalid")
    if docket.get("status") != "gate_passed" or docket.get("state") != "DISPOSED":
        errors.append("v0.5 terminal docket must remain gate_passed and DISPOSED")
    errors.extend(validate_signed_artifact_transforms(root))

    updated_at = parse_datetime(docket.get("updated_at"))
    expires_at = parse_datetime(docket.get("expires_at"))
    if updated_at is None or expires_at is None or updated_at >= expires_at:
        errors.append("authority docket time window invalid")
    else:
        if updated_at > as_of:
            errors.append("authority docket updated_at is in the future")
        if as_of >= expires_at:
            errors.append("authority docket expired")

    binding = docket.get("repository_binding")
    binding_keys = {"commit_sha", "tree_sha", "branch", "repository_ref"}
    errors.extend(exact_keys(binding, binding_keys, "repository binding"))
    if isinstance(binding, dict):
        commit_sha = str(binding.get("commit_sha", ""))
        tree_sha = str(binding.get("tree_sha", ""))
        resolved_tree = resolve_tree(root, commit_sha)
        head_sha = resolve_head(root)
        if resolved_tree is None:
            errors.append("repository binding commit does not resolve")
        elif resolved_tree != tree_sha:
            errors.append("repository binding commit/tree mismatch")
        if head_sha is None or (resolved_tree is not None and not is_ancestor(root, commit_sha, head_sha)):
            errors.append("repository binding commit must be an ancestor of HEAD")
        if binding.get("repository_ref") != "bstBizEra/bopen":
            errors.append("repository binding repository_ref invalid")
        if commit_sha != TERMINAL_SUBSTRATE_COMMIT or tree_sha != TERMINAL_SUBSTRATE_TREE or binding.get("branch") != TERMINAL_SUBSTRATE_BRANCH:
            errors.append("repository binding must match Signing Pass 4 substrate")
    else:
        commit_sha = tree_sha = ""

    artifacts = docket.get("governing_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("governing artifacts missing")
        artifacts = []
    artifact_map: dict[str, dict[str, Any]] = {}
    for index, artifact in enumerate(artifacts):
        errors.extend(validate_artifact_binding(root, artifact, f"governing artifact {index + 1}", commit_sha))
        if isinstance(artifact, dict):
            artifact_id = str(artifact.get("artifact_id", ""))
            if artifact_id in artifact_map:
                errors.append(f"governing artifact ID duplicated: {artifact_id}")
            artifact_map[artifact_id] = artifact

    inventory_binding = docket.get("binding_inventory")
    inventory_keys = {"inventory_ref", "inventory_id", "substrate_commit_sha", "substrate_tree_sha", "record_count"}
    errors.extend(exact_keys(inventory_binding, inventory_keys, "binding inventory"))
    inventory, inventory_error = read_json(root / BINDING_INVENTORY_PATH)
    if inventory_error:
        errors.append(f"binding inventory {inventory_error}")
    elif isinstance(inventory_binding, dict) and isinstance(inventory, dict):
        try:
            expected_inventory = build_v04_binding_inventory(root)
        except (ValueError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            expected_inventory = None
            errors.append(f"binding inventory regeneration failed: {exc}")
        inventory_matches_regeneration = expected_inventory is not None and inventory == expected_inventory
        if expected_inventory is not None and not inventory_matches_regeneration:
            errors.append("binding inventory differs from exact signed-substrate regeneration")
        if inventory_binding.get("inventory_ref") != BINDING_INVENTORY_PATH.as_posix():
            errors.append("binding inventory path invalid")
        if inventory_binding.get("inventory_id") != inventory.get("inventory_id"):
            errors.append("binding inventory identity mismatch")
        if inventory_binding.get("substrate_commit_sha") != commit_sha or inventory.get("substrate_commit_sha") != commit_sha:
            errors.append("binding inventory commit mismatch")
        if inventory_binding.get("substrate_tree_sha") != tree_sha or inventory.get("substrate_tree_sha") != tree_sha:
            errors.append("binding inventory tree mismatch")
        records = inventory.get("records")
        if not isinstance(records, list) or inventory_binding.get("record_count") != len(records):
            errors.append("binding inventory record count mismatch")
            records = []
        seen_inventory_ids: set[str] = set()
        seen_inventory_paths: set[str] = set()
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                errors.append(f"binding inventory record {index + 1} invalid")
                continue
            record_id = str(record.get("artifact_id", ""))
            relative = str(record.get("path", ""))
            if not record_id or record_id in seen_inventory_ids:
                errors.append(f"binding inventory artifact ID invalid or duplicated: {record_id}")
            if not relative or relative in seen_inventory_paths:
                errors.append(f"binding inventory path invalid or duplicated: {relative}")
            seen_inventory_ids.add(record_id)
            seen_inventory_paths.add(relative)
            # Exact regeneration already read and hashed every substrate object. Only
            # repeat object-level diagnostics when the supplied inventory differs.
            if not inventory_matches_regeneration:
                committed = read_file_at_commit(root, commit_sha, relative) if relative else None
                if committed is None:
                    errors.append(f"binding inventory source missing at substrate: {relative}")
                else:
                    if record.get("sha256") != bytes_sha256(committed):
                        errors.append(f"binding inventory digest mismatch: {relative}")
                    if record.get("bytes") != len(committed):
                        errors.append(f"binding inventory byte count mismatch: {relative}")
        for artifact_id, artifact in artifact_map.items():
            match = next((item for item in records if isinstance(item, dict) and item.get("artifact_id") == artifact_id), None)
            if match is None or artifact.get("artifact_ref") != match.get("path") or artifact.get("sha256") != match.get("sha256"):
                errors.append(f"governing artifact not exactly represented in binding inventory: {artifact_id}")

    source = docket.get("authority_source")
    source_keys = {"matrix_id", "artifact_ref", "proposal_ref", "version", "status", "sha256", "signing_ref", "effective"}
    errors.extend(exact_keys(source, source_keys, "authority source"))
    if isinstance(source, dict):
        if source.get("artifact_ref") != AUTHORITY_MATRIX_PATH.as_posix():
            errors.append("authority source artifact path invalid")
        if source.get("proposal_ref") != "docs/00-governance/AUTHORITY-MATRIX-0.2.0-PROPOSAL.json":
            errors.append("authority source proposal path invalid")
        if source.get("version") != "0.2.0" or source.get("status") != "approved" or source.get("effective") is not True:
            errors.append("authority source must be approved v0.2 and effective")
        if source.get("sha256") != file_sha256(root / AUTHORITY_MATRIX_PATH):
            errors.append("authority source current matrix digest mismatch")
        if source.get("signing_ref") != V03_SIGNED_DECISION_REF:
            errors.append("authority source signing reference mismatch")
        committed_source = read_file_at_commit(root, commit_sha, str(source.get("proposal_ref", "")))
        try:
            source_matrix = json.loads(committed_source.decode("utf-8")) if committed_source is not None else None
        except (UnicodeDecodeError, json.JSONDecodeError):
            source_matrix = None
        proposal_entries = source_matrix.get("entries") if isinstance(source_matrix, dict) else None
        normalized_current = [dict(item, status="draft") for item in matrix.get("entries", []) if isinstance(item, dict)]
        if not isinstance(proposal_entries, list) or proposal_entries != normalized_current:
            errors.append("adopted authority matrix entries differ from signed substrate proposal")

    matrix_entries = matrix.get("entries")
    if matrix.get("register_id") != "PG-REG-AUTHORITY-001" or not isinstance(matrix_entries, list):
        errors.append("authority matrix identity or entries invalid")
        matrix_entries = []
    if isinstance(source, dict) and matrix.get("status") != source.get("status"):
        errors.append("authority matrix status must match authority source")
    matrix_actions: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(matrix_entries):
        if not isinstance(item, dict):
            errors.append(f"authority matrix entry {index + 1} must be an object")
            continue
        action_id = item.get("action_id")
        if not isinstance(action_id, str) or action_id in matrix_actions:
            errors.append(f"authority matrix action ID invalid or duplicated: {action_id}")
            continue
        matrix_actions[action_id] = item
        if item.get("self_approval_allowed") is not False or item.get("evidence_required") is not True:
            errors.append(f"authority matrix action safeguards invalid: {action_id}")
        action_config = EXPECTED_ACTION_CONFIG.get(action_id)
        if item.get("status") not in {"draft", "approved"}:
            errors.append(f"authority matrix action {action_id} status invalid")
        elif isinstance(source, dict) and item.get("status") != source.get("status"):
            errors.append(f"authority matrix action {action_id} status mismatches source")
        if action_config is not None and item.get("action_class") != action_config[0]:
            errors.append(f"authority matrix action {action_id} action_class invalid")
        for field in ("accountable_human_authority", "final_decision_role"):
            if not non_placeholder(item.get(field)):
                errors.append(f"authority matrix action {action_id} {field} invalid")
        for field in ("permitted_maker_roles", "permitted_checker_roles", "required_concurrence"):
            values = item.get(field)
            if not isinstance(values, list) or len(values) != len(set(str(value) for value in values)) or any(not non_placeholder(value) for value in values):
                errors.append(f"authority matrix action {action_id} {field} invalid")
        if not isinstance(item.get("expiry_required"), bool):
            errors.append(f"authority matrix action {action_id} expiry_required invalid")
        elif action_config is not None and item.get("expiry_required") is not action_config[1]:
            errors.append(f"authority matrix action {action_id} expiry_required mismatches expected policy")
        if action_config is not None and set(item.get("required_concurrence", [])) != action_config[2]:
            errors.append(f"authority matrix action {action_id} required_concurrence mismatches expected policy")

    review = docket.get("technical_review")
    review_keys = {"candidate_commit_sha", "candidate_tree_sha", "maker", "checker", "independence_asserted", "verdict", "reviewed_at", "evidence_refs"}
    errors.extend(exact_keys(review, review_keys, "technical review"))
    if isinstance(review, dict):
        errors.extend(validate_actor(review.get("maker"), "technical review maker"))
        verdict = review.get("verdict")
        if verdict == "PENDING":
            if review.get("candidate_commit_sha") is not None or review.get("candidate_tree_sha") is not None:
                errors.append("pending technical review cannot claim a candidate binding")
            if review.get("checker") is not None or review.get("reviewed_at") is not None or review.get("independence_asserted") is not False or review.get("evidence_refs"):
                errors.append("pending technical review cannot claim checker, independence, time or evidence")
        elif verdict in TERMINAL_REVIEWS:
            candidate_sha = str(review.get("candidate_commit_sha", ""))
            candidate_tree = str(review.get("candidate_tree_sha", ""))
            head_sha = resolve_head(root)
            if candidate_sha == commit_sha:
                errors.append("technical review candidate must not equal repository binding")
            if resolve_tree(root, candidate_sha) != candidate_tree:
                errors.append("technical review candidate commit/tree mismatch")
            if head_sha is None or not is_ancestor(root, commit_sha, candidate_sha) or not is_ancestor(root, candidate_sha, head_sha):
                errors.append("technical review candidate must be between repository binding and HEAD")
            errors.extend(validate_actor(review.get("checker"), "technical review checker"))
            checker_identity = actor_identity(review.get("checker"))
            maker_identity = actor_identity(review.get("maker"))
            if not checker_identity or checker_identity == maker_identity:
                errors.append("technical review maker and checker must differ")
            reviewed_at = parse_datetime(review.get("reviewed_at"))
            candidate_time = commit_datetime(root, candidate_sha)
            if reviewed_at is None or reviewed_at > as_of or (candidate_time is not None and reviewed_at < candidate_time):
                errors.append("technical review reviewed_at chronology invalid")
            if verdict == "ACCEPT_EXACT_SHA" and review.get("independence_asserted") is not True:
                errors.append("accepted technical review requires independence")
            errors.extend(validate_evidence_binding(root, review.get("evidence_refs"), "technical review", candidate_sha))
        else:
            errors.append("technical review verdict invalid")

    prepared = docket.get("prepared_dispositions")
    if not isinstance(prepared, list):
        errors.append("prepared_dispositions must be an array")
        prepared = []
    prepared_ids = [item.get("disposition_id") for item in prepared if isinstance(item, dict)]
    if set(prepared_ids) != set(EXPECTED_PREPARED_DISPOSITIONS) or len(prepared_ids) != len(EXPECTED_PREPARED_DISPOSITIONS):
        errors.append("prepared disposition set must match Batch 2 B2 through B6 surfaces")
    prepared_keys = {
        "disposition_id", "batch_item", "action_id", "subject", "requested_state",
        "accountable_authority_role", "required_concurrence", "authority_actor",
        "concurrences", "disposition", "decided_at", "expires_at", "decision_ref", "evidence_refs", "effective",
    }
    predecessor_prepared = {
        item.get("disposition_id"): item
        for item in predecessor.get("prepared_dispositions", [])
        if isinstance(item, dict)
    }
    immutable_prepared_fields = {
        "disposition_id", "batch_item", "action_id", "subject", "requested_state",
        "accountable_authority_role", "required_concurrence", "expires_at",
    }
    for item in prepared:
        if not isinstance(item, dict):
            errors.append("prepared disposition must be an object")
            continue
        disposition_id = str(item.get("disposition_id", ""))
        errors.extend(exact_keys(item, prepared_keys, f"{disposition_id} prepared disposition"))
        expected = EXPECTED_PREPARED_DISPOSITIONS.get(disposition_id)
        if expected is None:
            continue
        batch_item, action_id, artifact_id, requested_state, authority_role, concurrence = expected
        if item.get("batch_item") != batch_item or item.get("action_id") != action_id:
            errors.append(f"{disposition_id} batch/action mismatch")
        if item.get("requested_state") != requested_state:
            errors.append(f"{disposition_id} requested state mismatch")
        if item.get("accountable_authority_role") != authority_role:
            errors.append(f"{disposition_id} authority role mismatch")
        if set(item.get("required_concurrence", [])) != concurrence:
            errors.append(f"{disposition_id} concurrence mismatch")
        predecessor_item = predecessor_prepared.get(disposition_id)
        if not isinstance(predecessor_item, dict) or any(item.get(field) != predecessor_item.get(field) for field in immutable_prepared_fields):
            errors.append(f"{disposition_id} alters the signed v0.2 subject or requested outcome")
        if item.get("disposition") != "APPROVE" or item.get("effective") is not True:
            errors.append(f"{disposition_id} signed disposition/effect mismatch")
        if item.get("decided_at") != V03_SIGNED_AT or item.get("decision_ref") != V03_SIGNED_DECISION_REF:
            errors.append(f"{disposition_id} signed time/reference mismatch")
        if set(item.get("evidence_refs", [])) != V03_SIGNED_EVIDENCE_REFS:
            errors.append(f"{disposition_id} signed evidence mismatch")
        disposition_expiry = parse_datetime(item.get("expires_at"))
        if disposition_expiry is None or (expires_at is not None and disposition_expiry > expires_at):
            errors.append(f"{disposition_id} expiry invalid")
        subject = item.get("subject")
        subject_keys = {"artifact_id", "version", "artifact_ref", "sha256", "commit_sha", "tree_sha"}
        errors.extend(exact_keys(subject, subject_keys, f"{disposition_id} subject"))
        if isinstance(subject, dict):
            if subject.get("artifact_id") != artifact_id:
                errors.append(f"{disposition_id} subject identity mismatch")
            subject_commit = str(subject.get("commit_sha", ""))
            subject_tree = str(subject.get("tree_sha", ""))
            subject_ref = str(subject.get("artifact_ref", ""))
            subject_bytes = read_file_at_commit(root, subject_commit, subject_ref)
            if resolve_tree(root, subject_commit) != subject_tree:
                errors.append(f"{disposition_id} signed subject commit/tree mismatch")
            if subject_bytes is None or bytes_sha256(subject_bytes) != subject.get("sha256"):
                errors.append(f"{disposition_id} signed subject digest mismatch")
        action = matrix_actions.get(action_id)
        if action is None or action.get("accountable_human_authority") != authority_role:
            errors.append(f"{disposition_id} action/authority absent from matrix")
        actor_subject_ref = AUTHORITY_MATRIX_PATH.as_posix() if disposition_id == "PG-G0-PREP-002" else str(subject.get("artifact_ref", "")) if isinstance(subject, dict) else ""
        errors.extend(validate_authority_actor(
            item.get("authority_actor"),
            f"{disposition_id} final authority",
            authority_role,
            schema,
            root=root,
            as_of=as_of,
            action_id=action_id,
            subject_ref=actor_subject_ref,
            authority_source=source,
            governing_artifacts=artifact_map,
            repository_commit_sha=V03_SUBSTRATE_COMMIT,
            repository_tree_sha=V03_SUBSTRATE_TREE,
        ))
        signed_concurrences = item.get("concurrences")
        if not isinstance(signed_concurrences, list):
            errors.append(f"{disposition_id} concurrences must be an array")
            signed_concurrences = []
        concurrence_roles = [entry.get("authority_role") for entry in signed_concurrences if isinstance(entry, dict)]
        if set(concurrence_roles) != concurrence or len(concurrence_roles) != len(concurrence):
            errors.append(f"{disposition_id} signed concurrence set mismatch")
        for signed_concurrence in signed_concurrences:
            if not isinstance(signed_concurrence, dict):
                errors.append(f"{disposition_id} concurrence must be an object")
                continue
            role = str(signed_concurrence.get("authority_role", ""))
            if signed_concurrence.get("disposition") != "CONCUR" or signed_concurrence.get("effective") is not True:
                errors.append(f"{disposition_id} {role} concurrence effect mismatch")
            if signed_concurrence.get("decided_at") != V03_SIGNED_AT or signed_concurrence.get("decision_ref") != V03_SIGNED_DECISION_REF:
                errors.append(f"{disposition_id} {role} concurrence time/reference mismatch")
            if set(signed_concurrence.get("evidence_refs", [])) != V03_SIGNED_EVIDENCE_REFS:
                errors.append(f"{disposition_id} {role} concurrence evidence mismatch")
            errors.extend(validate_authority_actor(
                signed_concurrence.get("authority_actor"),
                f"{disposition_id} {role} concurrence",
                role,
                schema,
                root=root,
                as_of=as_of,
                action_id=action_id,
                subject_ref=actor_subject_ref,
                authority_source=source,
                governing_artifacts=artifact_map,
                repository_commit_sha=V03_SUBSTRATE_COMMIT,
                repository_tree_sha=V03_SUBSTRATE_TREE,
            ))

    decisions = docket.get("decision_requests")
    if not isinstance(decisions, list):
        errors.append("decision_requests must be an array")
        decisions = []
    decision_ids = [item.get("decision_id") for item in decisions if isinstance(item, dict)]
    if set(decision_ids) != set(EXPECTED_DECISIONS) or len(decision_ids) != len(EXPECTED_DECISIONS):
        errors.append("authority docket decision set must preserve five B8 decisions and surface one B9 decision")
    predecessor_decisions = {
        item.get("decision_id"): item
        for item in predecessor.get("decision_requests", [])
        if isinstance(item, dict)
    }

    for decision in decisions:
        if not isinstance(decision, dict):
            errors.append("decision request must be an object")
            continue
        decision_id = str(decision.get("decision_id"))
        expected = EXPECTED_DECISIONS.get(decision_id)
        if expected is None:
            continue
        action_id, artifact_id, authority_role, concurrence_roles = expected
        if decision_id in B8_DECISION_IDS:
            predecessor_decision = predecessor_decisions.get(decision_id)
            immutable_fields = {
                "decision_id", "action_id", "subject", "prepared_by",
                "accountable_authority_role", "final_decision_role", "expires_at",
            }
            if not isinstance(predecessor_decision, dict) or any(
                decision.get(field) != predecessor_decision.get(field) for field in immutable_fields
            ):
                errors.append(f"{decision_id} alters the signed v0.3 subject binding or request")
        if decision.get("action_id") != action_id:
            errors.append(f"{decision_id} action mismatch")
        action = matrix_actions.get(action_id)
        if action is None:
            errors.append(f"{decision_id} action absent from authority matrix")
        else:
            if action.get("accountable_human_authority") != authority_role or action.get("final_decision_role") != authority_role:
                errors.append(f"{decision_id} authority role mismatch with matrix")
        if decision.get("accountable_authority_role") != authority_role or decision.get("final_decision_role") != authority_role:
            errors.append(f"{decision_id} final authority role invalid")

        subject = decision.get("subject")
        subject_keys = {"artifact_id", "version", "artifact_ref", "sha256", "commit_sha", "tree_sha"}
        errors.extend(exact_keys(subject, subject_keys, f"{decision_id} subject"))
        governing = artifact_map.get(artifact_id)
        if isinstance(subject, dict):
            if subject.get("artifact_id") != artifact_id or subject.get("artifact_ref") != EXPECTED_SUBJECT_REFS[artifact_id]:
                errors.append(f"{decision_id} subject artifact/path mismatch")
            subject_commit = str(subject.get("commit_sha", ""))
            subject_tree = str(subject.get("tree_sha", ""))
            if resolve_tree(root, subject_commit) != subject_tree:
                errors.append(f"{decision_id} subject commit/tree mismatch")
            errors.extend(validate_artifact_binding(root, {
                "artifact_id": subject.get("artifact_id"),
                "version": subject.get("version"),
                "status": governing.get("status") if governing else "bound",
                "artifact_ref": subject.get("artifact_ref"),
                "sha256": subject.get("sha256"),
            }, f"{decision_id} subject", subject_commit))

        errors.extend(validate_actor(decision.get("prepared_by"), f"{decision_id} prepared_by"))
        prepared_identity = actor_identity(decision.get("prepared_by"))
        if action is not None and isinstance(decision.get("prepared_by"), dict):
            if decision["prepared_by"].get("role") not in action.get("permitted_maker_roles", []):
                errors.append(f"{decision_id} prepared_by role is not permitted by matrix")
        decision_expiry = parse_datetime(decision.get("expires_at"))
        if decision_expiry is None:
            errors.append(f"{decision_id} expires_at invalid")
        elif decision_expiry > expires_at if expires_at is not None else False:
            errors.append(f"{decision_id} expiry exceeds docket expiry")

        concurrences = decision.get("required_concurrences")
        if not isinstance(concurrences, list):
            errors.append(f"{decision_id} required_concurrences must be an array")
            concurrences = []
        actual_roles = [item.get("authority_role") for item in concurrences if isinstance(item, dict)]
        if set(actual_roles) != concurrence_roles or len(actual_roles) != len(concurrence_roles):
            errors.append(f"{decision_id} concurrence roles invalid")
        matrix_concurrence = set(action.get("required_concurrence", [])) if action is not None else set()
        if action_id == "ACCEPT_WORK_ITEM" and matrix_concurrence == {"Owning Artifact Authority"}:
            matrix_concurrence = concurrence_roles
        if action is not None and not matrix_concurrence.issubset(set(actual_roles)):
            errors.append(f"{decision_id} misses authority-matrix concurrence")
        concurrence_identities: set[str] = set()
        for concurrence in concurrences:
            if not isinstance(concurrence, dict):
                errors.append(f"{decision_id} concurrence must be an object")
                continue
            role = str(concurrence.get("authority_role"))
            expected_subject_commit = subject.get("commit_sha") if isinstance(subject, dict) else None
            expected_subject_tree = subject.get("tree_sha") if isinstance(subject, dict) else None
            if concurrence.get("bound_commit_sha") != expected_subject_commit or concurrence.get("bound_tree_sha") != expected_subject_tree:
                errors.append(f"{decision_id} {role} concurrence binding mismatch")
            errors.extend(validate_evidence_refs(root, concurrence.get("source_refs"), f"{decision_id} {role} source", required=True))
            disposition = concurrence.get("disposition")
            if disposition == "PENDING":
                if any(concurrence.get(field) is not None for field in ("authority_actor", "decided_at", "expires_at")) or concurrence.get("evidence_refs"):
                    errors.append(f"{decision_id} pending {role} concurrence claims authority")
            elif disposition in TERMINAL_CONCURRENCES:
                errors.extend(validate_authority_actor(
                    concurrence.get("authority_actor"),
                    f"{decision_id} {role} concurrence",
                    role,
                    schema,
                    root=root,
                    as_of=as_of,
                    action_id=action_id,
                    subject_ref=EXPECTED_SUBJECT_REFS[artifact_id],
                    authority_source=source,
                    governing_artifacts=artifact_map,
                    repository_commit_sha=SIGNED_SUBSTRATE_COMMIT if decision_id in B8_DECISION_IDS else commit_sha,
                    repository_tree_sha=SIGNED_SUBSTRATE_TREE if decision_id in B8_DECISION_IDS else tree_sha,
                ))
                identity = actor_identity(concurrence.get("authority_actor"))
                if not identity or identity == prepared_identity or (
                    decision_id not in B8_DECISION_IDS and decision_id != "PG-G0-DEC-006" and identity in concurrence_identities
                ):
                    errors.append(f"{decision_id} {role} concurrence actor is not independent")
                concurrence_identities.add(identity)
                decided = parse_datetime(concurrence.get("decided_at"))
                concurrence_expiry = parse_datetime(concurrence.get("expires_at"))
                errors.extend(_validate_current_window(decided, concurrence_expiry, as_of, f"{decision_id} {role} concurrence", str(disposition)))
                errors.extend(validate_evidence_refs(root, concurrence.get("evidence_refs"), f"{decision_id} {role} concurrence", required=True))
            else:
                errors.append(f"{decision_id} {role} concurrence disposition invalid")

        final = decision.get("final_disposition")
        final_keys = {"value", "decided_at", "reason_code", "decision_ref", "evidence_refs", "effective"}
        errors.extend(exact_keys(final, final_keys, f"{decision_id} final disposition"))
        if not isinstance(final, dict):
            continue
        if not non_placeholder(final.get("reason_code")):
            errors.append(f"{decision_id} final disposition reason_code required")
        if decision_id in B8_DECISION_IDS:
            if final.get("value") != "APPROVE":
                errors.append(f"{decision_id} signed B8 outcome must remain APPROVE")
            if final.get("decided_at") != SIGNED_AT or final.get("decision_ref") != SIGNED_DECISION_REF:
                errors.append(f"{decision_id} signed B8 time/reference mismatch")
            if set(final.get("evidence_refs", [])) != SIGNED_EVIDENCE_REFS:
                errors.append(f"{decision_id} signed B8 evidence mismatch")
            if final.get("effective") is not True:
                errors.append(f"{decision_id} signed B8 outcome must be effective")
        elif decision_id == "PG-G0-DEC-006":
            if final.get("value") != "APPROVE" or final.get("effective") is not True:
                errors.append("PG-G0-DEC-006 signed B9 outcome must remain APPROVE and effective")
            if final.get("decided_at") != TERMINAL_SIGNED_AT or final.get("decision_ref") != TERMINAL_DECISION_REF:
                errors.append("PG-G0-DEC-006 signed B9 time/reference mismatch")
            if set(final.get("evidence_refs", [])) != TERMINAL_EVIDENCE_REFS:
                errors.append("PG-G0-DEC-006 signed B9 evidence mismatch")
        value = final.get("value")
        if value == "PENDING":
            if decision.get("final_authority_actor") is not None or decision.get("checked_by") is not None:
                errors.append(f"{decision_id} pending decision claims final/checker actor")
            if final.get("effective") is not False or final.get("decided_at") is not None or final.get("decision_ref") is not None or final.get("evidence_refs"):
                errors.append(f"{decision_id} pending disposition claims effect")
            if decision_expiry is not None and as_of >= decision_expiry:
                errors.append(f"{decision_id} expired")
        elif value in TERMINAL_DECISIONS:
            errors.extend(validate_authority_actor(
                decision.get("final_authority_actor"),
                f"{decision_id} final authority",
                authority_role,
                schema,
                root=root,
                as_of=as_of,
                action_id=action_id,
                subject_ref=EXPECTED_SUBJECT_REFS[artifact_id],
                authority_source=source,
                governing_artifacts=artifact_map,
                repository_commit_sha=SIGNED_SUBSTRATE_COMMIT if decision_id in B8_DECISION_IDS else commit_sha,
                repository_tree_sha=SIGNED_SUBSTRATE_TREE if decision_id in B8_DECISION_IDS else tree_sha,
            ))
            if decision.get("checked_by") is not None:
                errors.extend(validate_actor(decision.get("checked_by"), f"{decision_id} checker"))
            if action is not None and isinstance(decision.get("checked_by"), dict):
                if decision["checked_by"].get("role") not in action.get("permitted_checker_roles", []):
                    errors.append(f"{decision_id} checker role is not permitted by matrix")
            checker_identity = actor_identity(decision.get("checked_by"))
            authority_identity = actor_identity(decision.get("final_authority_actor"))
            identities = [prepared_identity, checker_identity, authority_identity]
            if not checker_identity:
                identities = [prepared_identity, authority_identity]
            if any(not item for item in identities) or len(set(identities)) != len(identities):
                errors.append(f"{decision_id} maker, checker and final authority must be distinct")
            if checker_identity and checker_identity in concurrence_identities:
                errors.append(f"{decision_id} final/checker actors must differ from concurrence actors")
            decided = parse_datetime(final.get("decided_at"))
            errors.extend(_validate_current_window(decided, decision_expiry, as_of, f"{decision_id} final disposition", str(value)))
            if decision_id in B8_DECISION_IDS and (final.get("effective") is not True or not non_placeholder(final.get("decision_ref"))):
                errors.append(f"{decision_id} terminal receipt incomplete")
            errors.extend(validate_evidence_refs(root, final.get("evidence_refs"), f"{decision_id} final disposition", required=True))
            if value == "APPROVE" and any(item.get("disposition") != "CONCUR" for item in concurrences if isinstance(item, dict)):
                errors.append(f"{decision_id} approval lacks required concurrence")
        else:
            errors.append(f"{decision_id} final disposition invalid")

    history = docket.get("state_history")
    if not isinstance(history, list) or not history:
        errors.append("state history missing")
    else:
        sequences = [item.get("sequence") for item in history if isinstance(item, dict)]
        if sequences != list(range(1, len(history) + 1)):
            errors.append("state history sequence must be contiguous")
        previous_state: str | None = None
        previous_time: datetime | None = None
        for index, item in enumerate(history):
            if not isinstance(item, dict):
                continue
            label = f"state history {index + 1}"
            if item.get("from") != previous_state:
                errors.append(f"{label} from-state does not match prior state")
            target_state = str(item.get("to", ""))
            if previous_state is None:
                if target_state != "DRAFT":
                    errors.append("state history must begin at DRAFT")
            elif target_state not in STATE_TRANSITIONS.get(previous_state, set()):
                errors.append(f"{label} transition {previous_state}->{target_state} invalid")
            changed_at = parse_datetime(item.get("changed_at"))
            if changed_at is None or changed_at > as_of or (previous_time is not None and changed_at <= previous_time):
                errors.append(f"{label} chronology invalid")
            previous_time = changed_at or previous_time
            previous_state = target_state
            errors.extend(validate_actor(item.get("changed_by"), f"{label} changed_by"))
            history_commit = str(item.get("commit_sha", ""))
            history_tree = str(item.get("tree_sha", ""))
            if resolve_tree(root, history_commit) != history_tree or not is_ancestor(root, history_commit, resolve_head(root) or ""):
                errors.append(f"{label} Git binding invalid")
            errors.extend(validate_evidence_refs(root, item.get("evidence_refs"), label, required=True))
        if not isinstance(history[-1], dict) or history[-1].get("to") != docket.get("state"):
            errors.append("docket state must match final history state")

    outcomes = docket.get("effective_outcome")
    errors.extend(exact_keys(outcomes, EFFECTIVE_OUTCOME_KEYS, "effective outcome"))
    expected_outcomes = {
        "program_goal_approved": True,
        "governance_baseline_approved": True,
        "work_package_accepted": True,
        "evidence_accepted": True,
        "ready_for_pg_g0_gate_decision": True,
    }
    if outcomes != expected_outcomes:
        errors.append("v0.4 effective outcomes must match the signed Batch 2 and B8 scope exactly")
    flags = docket.get("non_authority_flags")
    errors.extend(exact_keys(flags, NON_AUTHORITY_KEYS, "non-authority flags"))
    if isinstance(flags, dict) and any(value is not False for value in flags.values()):
        errors.append("v0.4 signed-state docket cannot grant B9, runtime or release authority")

    blockers = docket.get("blockers")
    if not isinstance(blockers, list) or not blockers or any(not non_placeholder(item) for item in blockers):
        errors.append("authority docket blockers must be non-empty strings")
        blockers = []
    blocker_text = " ".join(str(item) for item in blockers)
    for path in MISSING_CONTROL_PATHS:
        if not (root / path).exists() and path not in blocker_text:
            errors.append(f"missing controlled path must be disclosed: {path}")
    return sorted(set(errors))


def build_readiness_report(root: Path = ROOT, as_of: datetime | None = None) -> dict[str, Any]:
    errors = validate_pg_g0_authority_docket(root, as_of)
    docket, _ = read_json(root / DOCKET_PATH)
    blockers = list(docket.get("blockers", [])) if docket else []
    if docket:
        if docket["technical_review"]["verdict"] != "ACCEPT_EXACT_SHA":
            blockers.append("exact-SHA technical review of the v0.4 signed-state successor is pending")
        if not docket["authority_source"]["effective"]:
            blockers.append("authority source is not effective")
        for prepared in docket.get("prepared_dispositions", []):
            if prepared.get("disposition") != "APPROVE" or not prepared.get("effective"):
                blockers.append(f"{prepared.get('disposition_id', 'prepared disposition')} remains ineffective")
        for decision in docket["decision_requests"]:
            if decision["decision_id"] in B8_DECISION_IDS and (
                decision["final_disposition"]["value"] != "APPROVE" or not decision["final_disposition"]["effective"]
            ):
                blockers.append(f"{decision['decision_id']} remains ineffective")
            if decision["decision_id"] == "PG-G0-DEC-006" and decision["final_disposition"]["value"] == "PENDING":
                blockers.append("B9 PASS_PG_G0 remains PENDING")
                blockers.append("B9 requires a fresh independent conformance receipt before final disposition")
    terminal = bool(
        docket
        and docket.get("state") == "DISPOSED"
        and any(
            item.get("decision_id") == "PG-G0-DEC-006"
            and item.get("final_disposition", {}).get("value") == "APPROVE"
            and item.get("final_disposition", {}).get("effective") is True
            for item in docket.get("decision_requests", [])
        )
    )
    ready = bool(
        docket
        and docket.get("effective_outcome", {}).get("ready_for_pg_g0_gate_decision") is True
        and not errors
    )
    blockers.extend(f"validation error: {error}" for error in errors)
    blockers = sorted(set(blockers))
    return {
        "docket_id": docket.get("docket_id") if docket else "missing",
        "status": "INVALID" if errors else ("PG_G0_PASSED" if terminal and ready else ("READY_FOR_HUMAN_GATE_DECISION" if ready else "NOT_READY")),
        "ready_for_human_gate_decision": bool(ready and not terminal),
        "pg_g0_passed": bool(terminal and ready),
        "production_implementation_authorized": False,
        "validation_errors": errors,
        "blockers": blockers,
    }


def format_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def check_report(path: Path, expected: str) -> list[str]:
    try:
        actual = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [f"PG-G0 authority readiness report missing: {path}"]
    if actual != expected:
        return ["PG-G0 authority readiness report is stale"]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", nargs="?", const=DEFAULT_REPORT_PATH, type=Path)
    mode.add_argument("--check", nargs="?", const=DEFAULT_REPORT_PATH, type=Path)
    mode.add_argument("--write-inventory", nargs="?", const=BINDING_INVENTORY_PATH, type=Path)
    mode.add_argument("--write-docket", nargs="?", const=DOCKET_PATH, type=Path)
    mode.add_argument("--require-ready", action="store_true")
    args = parser.parse_args(argv)
    if args.write_inventory:
        output = args.write_inventory if args.write_inventory.is_absolute() else ROOT / args.write_inventory
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(build_v04_binding_inventory(), indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {output}")
        return 0
    if args.write_docket:
        output = args.write_docket if args.write_docket.is_absolute() else ROOT / args.write_docket
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(build_v04_docket(), indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {output}")
        return 0
    report = build_readiness_report()
    rendered = format_report(report)
    if args.write:
        output = args.write if args.write.is_absolute() else ROOT / args.write
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        print(f"Wrote {output}")
    elif args.check:
        output = args.check if args.check.is_absolute() else ROOT / args.check
        errors = check_report(output, rendered)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(f"PG-G0 authority readiness report current: {output}")
    else:
        print(rendered, end="")
    if report["validation_errors"]:
        return 1
    if args.require_ready and not report["ready_for_human_gate_decision"]:
        print("ERROR: PG-G0 authority docket is NOT_READY", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
