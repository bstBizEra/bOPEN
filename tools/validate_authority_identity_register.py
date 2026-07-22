#!/usr/bin/env python3
"""Fail-closed validation for the draft authority identity register."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DRAFT_PATH = Path("docs/00-governance/AUTHORITY-IDENTITY-REGISTER-DRAFT.json")
BOUND_PATH = Path("docs/00-governance/registers/AUTHORITY-IDENTITY-REGISTER.json")
SCHEMA_PATH = Path("contracts/governance/authority-identity-register.schema.json")
SCHEMA_URI = "bopen://schemas/governance/authority-identity-register/0.1.0-draft"
IDENTITY_PROVIDER = "bopen-authority-identity-registry"
SUBJECT_PATTERN = re.compile(r"^HUMAN-[A-Z0-9][A-Z0-9_-]*$")
ACTION_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]+$")
REGISTER_ID_PATTERN = re.compile(r"^PG-REG-IDENTITY-[0-9]{3}$")
RFC3339 = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
KNOWN_AUTHORITY_ROLES = {
    "Product Authority",
    "Architecture Authority",
    "Security Authority",
    "Data Authority",
    "Engineering Authority",
}
REGISTER_KEYS = {
    "$schema", "register_id", "version", "status", "owner_authority",
    "updated_at", "approved_by", "approved_at", "approval_ref",
    "independence_disclosure", "entries",
}
ENTRY_KEYS = {
    "identity_id", "status", "display_name", "contact_ref",
    "human_identity_ref", "identity_provider", "identity_subject",
    "authority_roles", "authority_mode", "action_ids", "subject_refs",
    "valid_from", "expires_at", "revoked_at", "evidence_refs",
}


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or RFC3339.fullmatch(value) is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _validate_entry(entry: Any, register_status: str, index: int, root: Path) -> list[str]:
    label = f"entry[{index}]"
    if not isinstance(entry, dict):
        return [f"{label}: must be an object"]
    errors: list[str] = []
    actual = set(entry)
    if actual != ENTRY_KEYS:
        missing = sorted(ENTRY_KEYS - actual)
        unknown = sorted(actual - ENTRY_KEYS)
        if missing:
            errors.append(f"{label}: missing keys {missing}")
        if unknown:
            errors.append(f"{label}: unknown keys {unknown}")
        return errors

    status = entry.get("status")
    if status not in {"pending", "approved", "revoked"}:
        errors.append(f"{label}: status must be pending, approved or revoked")
    identity_id = entry.get("identity_id")
    identity_subject = entry.get("identity_subject")
    if not isinstance(identity_id, str) or SUBJECT_PATTERN.fullmatch(identity_id) is None:
        errors.append(f"{label}: identity_id must match HUMAN-* pattern")
    if not isinstance(identity_subject, str) or SUBJECT_PATTERN.fullmatch(identity_subject) is None:
        errors.append(f"{label}: identity_subject must match HUMAN-* pattern")
    if identity_id != identity_subject:
        errors.append(f"{label}: identity_id and identity_subject must be identical")
    if entry.get("identity_provider") != IDENTITY_PROVIDER:
        errors.append(f"{label}: identity_provider must be {IDENTITY_PROVIDER}")
    if entry.get("authority_mode") != "DIRECT":
        errors.append(f"{label}: authority_mode must be DIRECT in this revision")
    for field in ("display_name", "contact_ref", "human_identity_ref"):
        if not _non_empty_string(entry.get(field)):
            errors.append(f"{label}: {field} is required")

    roles = entry.get("authority_roles")
    if not isinstance(roles, list) or not roles or len(set(roles)) != len(roles):
        errors.append(f"{label}: authority_roles must be a non-empty unique list")
    else:
        unknown_roles = sorted(set(roles) - KNOWN_AUTHORITY_ROLES)
        if unknown_roles:
            errors.append(f"{label}: unknown authority roles {unknown_roles}")

    actions = entry.get("action_ids")
    if not isinstance(actions, list) or not actions or len(set(actions)) != len(actions):
        errors.append(f"{label}: action_ids must be a non-empty unique list")
    else:
        for action in actions:
            if not isinstance(action, str) or ACTION_PATTERN.fullmatch(action) is None:
                errors.append(f"{label}: invalid action id {action!r}")

    subjects = entry.get("subject_refs")
    if not isinstance(subjects, list) or not subjects or len(set(subjects)) != len(subjects):
        errors.append(f"{label}: subject_refs must be a non-empty unique list")
    else:
        for subject in subjects:
            if not _non_empty_string(subject):
                errors.append(f"{label}: subject_refs entries must be non-empty strings")
            elif not (root / subject).is_file():
                errors.append(f"{label}: subject ref missing on disk: {subject}")

    evidence = entry.get("evidence_refs")
    if not isinstance(evidence, list) or not evidence or len(set(evidence)) != len(evidence):
        errors.append(f"{label}: evidence_refs must be a non-empty unique list")
    else:
        for reference in evidence:
            if not _non_empty_string(reference):
                errors.append(f"{label}: evidence_refs entries must be non-empty strings")
            elif not (root / reference).is_file():
                errors.append(f"{label}: evidence ref missing on disk: {reference}")

    valid_from = _parse_datetime(entry.get("valid_from"))
    expires_at = _parse_datetime(entry.get("expires_at"))
    if valid_from is None:
        errors.append(f"{label}: valid_from must be a timezone-aware RFC3339 timestamp")
    if expires_at is None:
        errors.append(f"{label}: expires_at must be a timezone-aware RFC3339 timestamp")
    if valid_from is not None and expires_at is not None and valid_from >= expires_at:
        errors.append(f"{label}: valid_from must precede expires_at")

    revoked_at = entry.get("revoked_at")
    if status == "revoked":
        if _parse_datetime(revoked_at) is None:
            errors.append(f"{label}: revoked entries require a revoked_at timestamp")
    elif revoked_at is not None:
        errors.append(f"{label}: non-revoked entries must keep revoked_at null")

    if status == "approved" and register_status != "approved":
        errors.append(f"{label}: entry cannot be approved while the register is not approved")

    return errors


def validate_authority_identity_register(root: Path = ROOT) -> list[str]:
    errors: list[str] = []

    bound = root / BOUND_PATH
    draft = root / DRAFT_PATH
    if not bound.is_file() and not draft.is_file():
        return [f"AUTHORITY IDENTITY REGISTER MISSING: {DRAFT_PATH} or {BOUND_PATH}"]

    targets: list[tuple[Path, bool]] = []
    if draft.is_file():
        targets.append((draft, False))
    if bound.is_file():
        targets.append((bound, True))

    for path, is_bound in targets:
        rel = path.relative_to(root)
        try:
            register = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"INVALID JSON {rel}: {exc}")
            continue
        if not isinstance(register, dict):
            errors.append(f"REGISTER MUST BE OBJECT: {rel}")
            continue

        actual = set(register)
        if actual != REGISTER_KEYS:
            missing = sorted(REGISTER_KEYS - actual)
            unknown = sorted(actual - REGISTER_KEYS)
            if missing:
                errors.append(f"{rel}: missing keys {missing}")
            if unknown:
                errors.append(f"{rel}: unknown keys {unknown}")
            continue

        if register.get("$schema") != SCHEMA_URI:
            errors.append(f"{rel}: $schema must be {SCHEMA_URI}")
        register_id = register.get("register_id")
        if not isinstance(register_id, str) or REGISTER_ID_PATTERN.fullmatch(register_id) is None:
            errors.append(f"{rel}: register_id must match PG-REG-IDENTITY-NNN")
        if not _non_empty_string(register.get("owner_authority")):
            errors.append(f"{rel}: owner_authority is required")
        if _parse_datetime(register.get("updated_at")) is None:
            errors.append(f"{rel}: updated_at must be a timezone-aware RFC3339 timestamp")
        if not _non_empty_string(register.get("independence_disclosure")):
            errors.append(f"{rel}: independence_disclosure is required")

        status = register.get("status")
        if status not in {"draft", "approved"}:
            errors.append(f"{rel}: status must be draft or approved")
            status = "draft"
        approvals = (
            register.get("approved_by"),
            register.get("approved_at"),
            register.get("approval_ref"),
        )
        if status == "approved":
            if not _non_empty_string(approvals[0]):
                errors.append(f"{rel}: approved register requires approved_by")
            if _parse_datetime(approvals[1]) is None:
                errors.append(f"{rel}: approved register requires approved_at")
            if not _non_empty_string(approvals[2]):
                errors.append(f"{rel}: approved register requires approval_ref")
            version = register.get("version")
            if isinstance(version, str) and version.endswith("-draft"):
                errors.append(f"{rel}: approved register must not use a draft version")
        else:
            if any(item is not None for item in approvals):
                errors.append(f"{rel}: draft register must not carry approval provenance")

        if is_bound and status != "approved":
            errors.append(
                f"{rel}: a register at the validator-bound path must be approved; "
                "unapproved drafts belong at the DRAFT path"
            )

        entries = register.get("entries")
        if not isinstance(entries, list) or not entries:
            errors.append(f"{rel}: entries must be a non-empty list")
            continue
        seen_ids: set[str] = set()
        for index, entry in enumerate(entries):
            entry_errors = _validate_entry(entry, status, index, root)
            errors.extend(f"{rel}: {item}" for item in entry_errors)
            if isinstance(entry, dict):
                identity_id = entry.get("identity_id")
                if isinstance(identity_id, str):
                    if identity_id in seen_ids:
                        errors.append(f"{rel}: duplicate identity_id {identity_id}")
                    seen_ids.add(identity_id)

    return errors


def main() -> int:
    errors = validate_authority_identity_register()
    if errors:
        print("bOPEN authority identity register validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("bOPEN authority identity register validation: PASS")
    print("Approval, gate and authority effects are not asserted by this validator.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
