#!/usr/bin/env python3
"""Validate the draft PG-G0 authority docket without granting authority."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
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
    "PG-G0-DEC-002": ("ACCEPT_WORK_ITEM", "GOV-P0-01", "Engineering Authority", set()),
    "PG-G0-DEC-003": ("APPROVE_ARCHITECTURE", "DEC-0010", "Architecture Authority", {"Security Authority", "Data Authority"}),
    "PG-G0-DEC-004": ("APPROVE_GOAL", "BOPEN-GOAL-001", "Product Authority", {"Architecture Authority", "Security Authority", "Data Authority"}),
    "PG-G0-DEC-005": ("ACCEPT_EVIDENCE", "EVD-GOV-001", "Engineering Authority", set()),
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


def non_placeholder(value: object) -> bool:
    return isinstance(value, str) and value.strip().casefold() not in PLACEHOLDERS


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


def resolve_tree(root: Path, commit_sha: str) -> str | None:
    if SHA_PATTERN.fullmatch(commit_sha) is None:
        return None
    completed = subprocess.run(
        ["git", "-C", str(root), "show", "-s", "--format=%T", commit_sha],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    tree = completed.stdout.strip()
    return tree if SHA_PATTERN.fullmatch(tree) else None


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


def validate_authority_actor(actor: object, label: str, required_role: str) -> list[str]:
    expected = {"actor_kind", "human_identity_ref", "authority_role", "authority_mode", "delegation_ref"}
    errors = exact_keys(actor, expected, label)
    if errors or not isinstance(actor, dict):
        return errors
    if actor.get("actor_kind") != "HUMAN":
        errors.append(f"{label} final authority must be human")
    if not non_placeholder(actor.get("human_identity_ref")):
        errors.append(f"{label} human identity is required")
    if actor.get("authority_role") != required_role:
        errors.append(f"{label} authority role must be {required_role}")
    if actor.get("authority_mode") not in {"DIRECT", "DELEGATED"}:
        errors.append(f"{label} authority mode invalid")
    if actor.get("authority_mode") == "DELEGATED" and not non_placeholder(actor.get("delegation_ref")):
        errors.append(f"{label} delegated authority requires a delegation reference")
    return errors


def validate_artifact_binding(root: Path, binding: object, label: str) -> list[str]:
    expected = {"artifact_id", "version", "status", "artifact_ref", "sha256"}
    errors = exact_keys(binding, expected, label)
    if errors or not isinstance(binding, dict):
        return errors
    relative = binding.get("artifact_ref")
    digest = binding.get("sha256")
    if not non_placeholder(relative):
        return errors + [f"{label} artifact_ref is required"]
    path = (root / str(relative)).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return errors + [f"{label} artifact_ref escapes repository"]
    if not path.is_file():
        errors.append(f"{label} artifact missing: {relative}")
    elif not isinstance(digest, str) or SHA256_PATTERN.fullmatch(digest) is None:
        errors.append(f"{label} sha256 invalid")
    elif file_sha256(path) != digest:
        errors.append(f"{label} sha256 mismatch: {relative}")
    return errors


def validate_pg_g0_authority_docket(root: Path = ROOT, as_of: datetime | None = None) -> list[str]:
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

    expected_top = {
        "$schema", "docket_id", "version", "status", "owner_authority", "updated_at", "expires_at",
        "repository_binding", "governing_artifacts", "authority_source", "technical_review",
        "decision_requests", "state", "state_history", "effective_outcome", "non_authority_flags", "blockers",
    }
    errors.extend(exact_keys(docket, expected_top, "authority docket"))
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
    if as_of is not None and expires_at is not None and as_of >= expires_at:
        errors.append("authority docket expired")

    binding = docket.get("repository_binding")
    binding_keys = {"commit_sha", "tree_sha", "branch", "repository_ref"}
    errors.extend(exact_keys(binding, binding_keys, "repository binding"))
    if isinstance(binding, dict):
        commit_sha = binding.get("commit_sha", "")
        tree_sha = binding.get("tree_sha", "")
        resolved_tree = resolve_tree(root, commit_sha) if isinstance(commit_sha, str) else None
        if resolved_tree is None:
            errors.append("repository binding commit does not resolve")
        elif resolved_tree != tree_sha:
            errors.append("repository binding commit/tree mismatch")
        if binding.get("repository_ref") != "bstBizEra/bopen":
            errors.append("repository binding repository_ref invalid")
    else:
        commit_sha = tree_sha = ""

    artifacts = docket.get("governing_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("governing artifacts missing")
        artifacts = []
    artifact_ids: list[str] = []
    for index, artifact in enumerate(artifacts):
        errors.extend(validate_artifact_binding(root, artifact, f"governing artifact {index + 1}"))
        if isinstance(artifact, dict):
            artifact_ids.append(str(artifact.get("artifact_id", "")))
    if len(artifact_ids) != len(set(artifact_ids)):
        errors.append("governing artifact IDs must be unique")

    source = docket.get("authority_source")
    source_keys = {"matrix_id", "artifact_ref", "version", "status", "sha256", "effective"}
    errors.extend(exact_keys(source, source_keys, "authority source"))
    if isinstance(source, dict):
        errors.extend(validate_artifact_binding(root, {
            "artifact_id": source.get("matrix_id"), "version": source.get("version"),
            "status": source.get("status"), "artifact_ref": source.get("artifact_ref"), "sha256": source.get("sha256"),
        }, "authority source"))
        if source.get("status") != "draft" or source.get("effective") is not False:
            errors.append("draft docket authority source must remain ineffective")

    review = docket.get("technical_review")
    review_keys = {"candidate_commit_sha", "candidate_tree_sha", "maker", "checker", "independence_asserted", "verdict", "reviewed_at", "evidence_refs"}
    errors.extend(exact_keys(review, review_keys, "technical review"))
    if isinstance(review, dict):
        errors.extend(validate_actor(review.get("maker"), "technical review maker"))
        if review.get("candidate_commit_sha") != commit_sha or review.get("candidate_tree_sha") != tree_sha:
            errors.append("technical review candidate must match repository binding")
        verdict = review.get("verdict")
        if verdict == "PENDING":
            if review.get("checker") is not None or review.get("reviewed_at") is not None or review.get("independence_asserted") is not False:
                errors.append("pending technical review cannot claim checker or independence")
        elif verdict == "ACCEPT_EXACT_SHA":
            errors.extend(validate_actor(review.get("checker"), "technical review checker"))
            checker = review.get("checker")
            maker = review.get("maker")
            if isinstance(checker, dict) and isinstance(maker, dict) and checker.get("identity_ref") == maker.get("identity_ref"):
                errors.append("technical review maker and checker must differ")
            if review.get("independence_asserted") is not True or parse_datetime(review.get("reviewed_at")) is None:
                errors.append("accepted technical review requires independence and reviewed_at")
            if not review.get("evidence_refs"):
                errors.append("accepted technical review requires evidence")
        elif verdict not in {"REQUEST_CHANGES", "REJECT"}:
            errors.append("technical review verdict invalid")

    matrix_actions = {
        item.get("action_id"): item
        for item in matrix.get("entries", [])
        if isinstance(item, dict) and isinstance(item.get("action_id"), str)
    }
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
        decision_id = decision.get("decision_id")
        expected = EXPECTED_DECISIONS.get(str(decision_id))
        if expected is None:
            continue
        action_id, artifact_id, authority_role, concurrence_roles = expected
        if decision.get("action_id") != action_id:
            errors.append(f"{decision_id} action mismatch")
        action = matrix_actions.get(action_id)
        if action is None:
            errors.append(f"{decision_id} action absent from authority matrix")
        elif action.get("accountable_human_authority") != authority_role:
            errors.append(f"{decision_id} authority role mismatch with matrix")
        if decision.get("accountable_authority_role") != authority_role or decision.get("final_decision_role") != authority_role:
            errors.append(f"{decision_id} final authority role invalid")
        subject = decision.get("subject")
        subject_keys = {"artifact_id", "version", "artifact_ref", "sha256", "commit_sha", "tree_sha"}
        errors.extend(exact_keys(subject, subject_keys, f"{decision_id} subject"))
        if isinstance(subject, dict):
            if subject.get("artifact_id") != artifact_id:
                errors.append(f"{decision_id} subject artifact mismatch")
            if subject.get("commit_sha") != commit_sha or subject.get("tree_sha") != tree_sha:
                errors.append(f"{decision_id} subject repository binding mismatch")
            errors.extend(validate_artifact_binding(root, {
                "artifact_id": subject.get("artifact_id"),
                "version": subject.get("version"),
                "status": "bound",
                "artifact_ref": subject.get("artifact_ref"),
                "sha256": subject.get("sha256"),
            }, f"{decision_id} subject"))
        errors.extend(validate_actor(decision.get("prepared_by"), f"{decision_id} prepared_by"))
        concurrences = decision.get("required_concurrences")
        if not isinstance(concurrences, list):
            errors.append(f"{decision_id} required_concurrences must be an array")
            concurrences = []
        actual_roles = [item.get("authority_role") for item in concurrences if isinstance(item, dict)]
        if set(actual_roles) != concurrence_roles or len(actual_roles) != len(concurrence_roles):
            errors.append(f"{decision_id} concurrence roles invalid")
        for concurrence in concurrences:
            if not isinstance(concurrence, dict):
                errors.append(f"{decision_id} concurrence must be an object")
                continue
            role = str(concurrence.get("authority_role"))
            if concurrence.get("bound_commit_sha") != commit_sha or concurrence.get("bound_tree_sha") != tree_sha:
                errors.append(f"{decision_id} {role} concurrence binding mismatch")
            if concurrence.get("disposition") == "PENDING":
                if concurrence.get("authority_actor") is not None or concurrence.get("decided_at") is not None or concurrence.get("evidence_refs"):
                    errors.append(f"{decision_id} pending {role} concurrence claims authority")
            elif concurrence.get("disposition") == "CONCUR":
                errors.extend(validate_authority_actor(concurrence.get("authority_actor"), f"{decision_id} {role} concurrence", role))
                if parse_datetime(concurrence.get("decided_at")) is None or not concurrence.get("evidence_refs"):
                    errors.append(f"{decision_id} effective {role} concurrence lacks time/evidence")
        final = decision.get("final_disposition")
        final_keys = {"value", "decided_at", "reason_code", "decision_ref", "evidence_refs", "effective"}
        errors.extend(exact_keys(final, final_keys, f"{decision_id} final disposition"))
        if isinstance(final, dict) and final.get("value") == "PENDING":
            if decision.get("final_authority_actor") is not None or decision.get("checked_by") is not None:
                errors.append(f"{decision_id} pending decision claims final/checker actor")
            if final.get("effective") is not False or final.get("decided_at") is not None or final.get("decision_ref") is not None or final.get("evidence_refs"):
                errors.append(f"{decision_id} pending disposition claims effect")
        elif isinstance(final, dict) and final.get("value") == "APPROVE":
            errors.extend(validate_authority_actor(decision.get("final_authority_actor"), f"{decision_id} final authority", authority_role))
            errors.extend(validate_actor(decision.get("checked_by"), f"{decision_id} checker"))
            if source.get("effective") is not True or action is None or action.get("status") != "approved":
                errors.append(f"{decision_id} cannot be effective under a draft authority source")
            if final.get("effective") is not True or parse_datetime(final.get("decided_at")) is None or not final.get("evidence_refs"):
                errors.append(f"{decision_id} approval receipt incomplete")
            if any(item.get("disposition") != "CONCUR" for item in concurrences if isinstance(item, dict)):
                errors.append(f"{decision_id} approval lacks required concurrence")

    history = docket.get("state_history")
    if not isinstance(history, list) or not history:
        errors.append("state history missing")
    else:
        sequences = [item.get("sequence") for item in history if isinstance(item, dict)]
        if sequences != list(range(1, len(history) + 1)):
            errors.append("state history sequence must be contiguous")
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
    return errors


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
