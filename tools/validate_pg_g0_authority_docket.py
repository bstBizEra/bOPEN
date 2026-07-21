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
}
EXPECTED_SUBJECT_REFS = {
    "DEC-0007": "docs/decisions/DEC-0007.md",
    "GOV-P0-01": "docs/work-packages/GOV-P0-01.md",
    "DEC-0010": "docs/decisions/DEC-0010.md",
    "BOPEN-GOAL-001": "docs/01-product/BOPEN-GOAL-001-DRAFT.md",
    "EVD-GOV-001": "docs/evidence/EVD-GOV-001-program-g0-controls.md",
}
EXPECTED_ACTION_CONFIG = {
    "APPROVE_ARCHITECTURE": ("architecture_approval", False, {"Security Authority", "Data Authority"}),
    "ACCEPT_WORK_ITEM": ("work_item_acceptance", True, set()),
    "APPROVE_GOAL": ("normative_goal_approval", False, {"Architecture Authority"}),
    "ACCEPT_EVIDENCE": ("evidence_acceptance", False, set()),
    "CERTIFY_MODULE": ("module_certification", False, {"Product Authority", "Security Authority"}),
    "PROMOTE_SKILL": ("skill_promotion", True, set()),
    "AUTHORIZE_RELEASE": ("release_authorization", True, {"Security Authority", "Product Authority"}),
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
    "DRAFT": {"TECHNICAL_REVIEW", "WITHDRAWN", "EXPIRED", "SUPERSEDED"},
    "TECHNICAL_REVIEW": {"PENDING_HUMAN_DECISIONS", "WITHDRAWN", "EXPIRED", "SUPERSEDED"},
    "PENDING_HUMAN_DECISIONS": {"READY_FOR_FINAL_DISPOSITION", "WITHDRAWN", "EXPIRED", "SUPERSEDED"},
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
    if authority_mode not in {"DIRECT", "DELEGATED"}:
        errors.append(f"{label} authority mode invalid")
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
    elif authority_mode == "DELEGATED":
        if not non_placeholder(delegation_ref) or not isinstance(delegation, dict):
            errors.append(f"{label} delegated authority requires reference and binding")
        else:
            delegation_schema = schema.get("$defs", {}).get("delegationBinding", {})
            required = set(delegation_schema.get("required", [])) if isinstance(delegation_schema, dict) else set()
            errors.extend(exact_keys(delegation, required, f"{label} delegation"))
            if delegation.get("authority_role") != required_role:
                errors.append(f"{label} delegation authority role mismatch")
            if normalized_identity(delegation.get("delegate_human_identity_ref")) != normalized_identity(actor.get("human_identity_ref")):
                errors.append(f"{label} delegation delegate identity mismatch")
            if normalized_identity(delegation.get("grantor_human_identity_ref")) in {"", normalized_identity(actor.get("human_identity_ref"))}:
                errors.append(f"{label} delegation grantor must be a different human")
            delegation_actions = delegation.get("action_ids")
            if not isinstance(delegation_actions, list) or action_id not in delegation_actions:
                errors.append(f"{label} delegation action scope missing")
            delegation_subjects = delegation.get("subject_refs")
            if not isinstance(delegation_subjects, list) or subject_ref not in delegation_subjects:
                errors.append(f"{label} delegation subject scope missing")
            expected_delegation_ref = f"{delegation.get('artifact_ref')}#{delegation.get('delegation_id')}"
            if delegation_ref != expected_delegation_ref:
                errors.append(f"{label} delegation_ref does not match binding")
            valid_from = parse_datetime(delegation.get("valid_from"))
            delegated_expiry = parse_datetime(delegation.get("expires_at"))
            if valid_from is None or delegated_expiry is None or not (valid_from <= as_of < delegated_expiry):
                errors.append(f"{label} delegation is not currently effective")
            if delegation.get("revoked_at") is not None:
                errors.append(f"{label} delegation is revoked")
            artifact_ref = delegation.get("artifact_ref")
            artifact_path, path_errors = safe_relative_path(root, artifact_ref, f"{label} delegation artifact_ref")
            errors.extend(path_errors)
            artifact_digest = delegation.get("artifact_sha256")
            delegation_commit = str(delegation.get("commit_sha", ""))
            delegation_tree = str(delegation.get("tree_sha", ""))
            head = resolve_head(root)
            if resolve_tree(root, delegation_commit) != delegation_tree:
                errors.append(f"{label} delegation commit/tree mismatch")
            if head is None or not is_ancestor(root, delegation_commit, head):
                errors.append(f"{label} delegation commit must be an ancestor of HEAD")
            committed = read_file_at_commit(root, delegation_commit, str(artifact_ref)) if artifact_ref else None
            if committed is None or not isinstance(artifact_digest, str) or SHA256_PATTERN.fullmatch(artifact_digest) is None or bytes_sha256(committed) != artifact_digest:
                errors.append(f"{label} delegation bound artifact sha256 mismatch")
            if artifact_path is not None:
                if not artifact_path.is_file() or not is_tracked_path(root, str(artifact_ref)):
                    errors.append(f"{label} delegation artifact missing or untracked")
                elif not isinstance(artifact_digest, str) or SHA256_PATTERN.fullmatch(artifact_digest) is None or file_sha256(artifact_path) != artifact_digest:
                    errors.append(f"{label} delegation artifact sha256 mismatch")
                record_bytes = committed if committed is not None else artifact_path.read_bytes()
                try:
                    delegation_document = json.loads(record_bytes.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    delegation_document = None
                record = _find_record(delegation_document, str(delegation.get("delegation_id")))
                match_fields = (
                    "grantor_human_identity_ref", "delegate_human_identity_ref",
                    "authority_role", "action_ids", "subject_refs", "valid_from",
                    "expires_at", "revoked_at", "evidence_refs",
                )
                if record is None or any(record.get(field) != delegation.get(field) for field in match_fields):
                    errors.append(f"{label} delegation record does not match binding")
            registry_ref = str(actor.get("role_binding_ref", "")).split("#", 1)[0]
            registry_bytes = read_file_at_commit(root, str(actor.get("role_binding_commit_sha", "")), registry_ref) if registry_ref else None
            try:
                registry_document = json.loads(registry_bytes.decode("utf-8")) if registry_bytes is not None else None
            except (UnicodeDecodeError, json.JSONDecodeError):
                registry_document = None
            grantor = _find_identity_record(registry_document, delegation.get("grantor_human_identity_ref"))
            if grantor is None or str(grantor.get("status", "")).casefold() != "approved":
                errors.append(f"{label} delegation grantor is not an approved identity")
            else:
                grantor_roles = grantor.get("authority_roles")
                grantor_role_matches = required_role in grantor_roles if isinstance(grantor_roles, list) else grantor.get("authority_role") == required_role
                if not grantor_role_matches or grantor.get("can_delegate") is not True:
                    errors.append(f"{label} delegation grantor lacks role or delegation authority")
                grantor_actions = grantor.get("delegation_action_ids")
                if not isinstance(grantor_actions, list) or action_id not in grantor_actions:
                    errors.append(f"{label} delegation grantor action scope missing")
                grantor_subjects = grantor.get("delegation_subject_refs")
                if not isinstance(grantor_subjects, list) or subject_ref not in grantor_subjects:
                    errors.append(f"{label} delegation grantor subject scope missing")
                valid_from = parse_datetime(grantor.get("valid_from"))
                expires = parse_datetime(grantor.get("expires_at"))
                if valid_from is None or expires is None or not (valid_from <= as_of < expires):
                    errors.append(f"{label} delegation grantor is not currently effective")
                if "revoked_at" not in grantor or grantor.get("revoked_at") is not None:
                    errors.append(f"{label} delegation grantor is revoked or lacks revocation state")
                errors.extend(validate_evidence_at_commit(
                    root,
                    grantor.get("evidence_refs"),
                    f"{label} delegation grantor",
                    str(actor.get("role_binding_commit_sha", "")),
                ))
            errors.extend(validate_evidence_at_commit(
                root,
                delegation.get("evidence_refs"),
                f"{label} delegation",
                delegation_commit,
            ))
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

    errors.extend(validate_schema_instance(docket, schema, schema, "authority docket"))
    if docket.get("$schema") != schema.get("$id"):
        errors.append("authority docket schema binding mismatch")
    if docket.get("docket_id") != "PG-G0-AUTH-001" or docket.get("version") != "0.1.0-draft":
        errors.append("authority docket identity/version invalid")
    if docket.get("status") != "draft" or docket.get("state") != "DRAFT":
        errors.append("draft authority docket must remain DRAFT")

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
        if not non_placeholder(binding.get("branch")):
            errors.append("repository binding branch invalid")
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

    source = docket.get("authority_source")
    source_keys = {"matrix_id", "artifact_ref", "version", "status", "sha256", "effective"}
    errors.extend(exact_keys(source, source_keys, "authority source"))
    if isinstance(source, dict):
        errors.extend(validate_artifact_binding(root, {
            "artifact_id": source.get("matrix_id"),
            "version": source.get("version"),
            "status": source.get("status"),
            "artifact_ref": source.get("artifact_ref"),
            "sha256": source.get("sha256"),
        }, "authority source", commit_sha))
        source_pair = (source.get("status"), source.get("effective"))
        if source_pair not in {("draft", False), ("approved", True)}:
            errors.append("authority source status/effectiveness mismatch")

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

    decisions = docket.get("decision_requests")
    if not isinstance(decisions, list):
        errors.append("decision_requests must be an array")
        decisions = []
    decision_ids = [item.get("decision_id") for item in decisions if isinstance(item, dict)]
    if set(decision_ids) != set(EXPECTED_DECISIONS) or len(decision_ids) != len(EXPECTED_DECISIONS):
        errors.append("authority docket decision set must match the five live mapped actions")

    for decision in decisions:
        if not isinstance(decision, dict):
            errors.append("decision request must be an object")
            continue
        decision_id = str(decision.get("decision_id"))
        expected = EXPECTED_DECISIONS.get(decision_id)
        if expected is None:
            continue
        action_id, artifact_id, authority_role, concurrence_roles = expected
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
            if subject.get("commit_sha") != commit_sha or subject.get("tree_sha") != tree_sha:
                errors.append(f"{decision_id} subject repository binding mismatch")
            if governing is None or any(subject.get(field) != governing.get(field) for field in ("version", "artifact_ref", "sha256")):
                errors.append(f"{decision_id} subject must exactly match governing artifact binding")
            errors.extend(validate_artifact_binding(root, {
                "artifact_id": subject.get("artifact_id"),
                "version": subject.get("version"),
                "status": governing.get("status") if governing else "bound",
                "artifact_ref": subject.get("artifact_ref"),
                "sha256": subject.get("sha256"),
            }, f"{decision_id} subject", commit_sha))

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
        if action is not None and not set(action.get("required_concurrence", [])).issubset(set(actual_roles)):
            errors.append(f"{decision_id} misses authority-matrix concurrence")
        concurrence_identities: set[str] = set()
        for concurrence in concurrences:
            if not isinstance(concurrence, dict):
                errors.append(f"{decision_id} concurrence must be an object")
                continue
            role = str(concurrence.get("authority_role"))
            if concurrence.get("bound_commit_sha") != commit_sha or concurrence.get("bound_tree_sha") != tree_sha:
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
                    repository_commit_sha=commit_sha,
                    repository_tree_sha=tree_sha,
                ))
                identity = actor_identity(concurrence.get("authority_actor"))
                if not identity or identity == prepared_identity or identity in concurrence_identities:
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
                repository_commit_sha=commit_sha,
                repository_tree_sha=tree_sha,
            ))
            errors.extend(validate_actor(decision.get("checked_by"), f"{decision_id} checker"))
            if action is not None and isinstance(decision.get("checked_by"), dict):
                if decision["checked_by"].get("role") not in action.get("permitted_checker_roles", []):
                    errors.append(f"{decision_id} checker role is not permitted by matrix")
            checker_identity = actor_identity(decision.get("checked_by"))
            authority_identity = actor_identity(decision.get("final_authority_actor"))
            identities = [prepared_identity, checker_identity, authority_identity]
            if any(not item for item in identities) or len(set(identities)) != 3:
                errors.append(f"{decision_id} maker, checker and final authority must be distinct")
            if authority_identity in concurrence_identities or checker_identity in concurrence_identities:
                errors.append(f"{decision_id} final/checker actors must differ from concurrence actors")
            decided = parse_datetime(final.get("decided_at"))
            errors.extend(_validate_current_window(decided, decision_expiry, as_of, f"{decision_id} final disposition", str(value)))
            if final.get("effective") is not False or not non_placeholder(final.get("decision_ref")):
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
    if isinstance(outcomes, dict) and any(value is not False for value in outcomes.values()):
        errors.append("draft authority docket cannot assert an effective outcome")
    flags = docket.get("non_authority_flags")
    errors.extend(exact_keys(flags, NON_AUTHORITY_KEYS, "non-authority flags"))
    if isinstance(flags, dict) and any(value is not False for value in flags.values()):
        errors.append("draft authority docket cannot grant authority")

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
            blockers.append("exact-SHA technical review is not accepted")
        if not docket["authority_source"]["effective"]:
            blockers.append("authority source is not effective")
        for decision in docket["decision_requests"]:
            if decision["final_disposition"]["value"] != "APPROVE" or not decision["final_disposition"]["effective"]:
                blockers.append(f"{decision['decision_id']} remains ineffective")
    blockers.extend(f"validation error: {error}" for error in errors)
    blockers = sorted(set(blockers))
    return {
        "docket_id": docket.get("docket_id") if docket else "missing",
        "status": "INVALID" if errors else "NOT_READY",
        "ready_for_human_gate_decision": False,
        "pg_g0_passed": False,
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
    mode.add_argument("--require-ready", action="store_true")
    args = parser.parse_args(argv)
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
