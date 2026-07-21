#!/usr/bin/env python3
"""Validate the draft QUAL-P0-00 offline qualification contract set.

The checker is deliberately standard-library only. JSON Schema defines the public
shape; this module enforces repository, digest, ordering, reference-closure and
lineage invariants that JSON Schema cannot express.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZED_BASE_COMMIT = "82ed6b38b118aab14a9961c5d75a33e515cb136a"
AUTHORIZED_BASE_TREE = "cad6b595fb74a70cc706a78d45778e15524aebd9"
DEFAULT_CATALOG = Path(
    "contracts/qualification/common/QUAL-P0-00-SCHEMA-CATALOG.json"
)
DEFAULT_MANIFEST = Path("docs/manifests/QUAL-P0-00-PACKAGE-MANIFEST.json")
OFFICIAL_META_SCHEMA = "https://json-schema.org/draft/2020-12/schema"
SHA1 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SCHEMA_REF = re.compile(r"^bopen://schemas/qualification/[a-z0-9._/-]+$")
RFC3339 = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)

COMMON_SCHEMA_FILES = {
    "checker-receipt.schema.json",
    "digest-binding.schema.json",
    "environment-binding.schema.json",
    "normalized-path.schema.json",
    "offline-catalog.schema.json",
    "provenance.schema.json",
    "qualification-envelope.schema.json",
    "redaction.schema.json",
    "repository-binding.schema.json",
}

PACKAGE_PATHS = (
    "contracts/qualification/common/QUAL-P0-00-SCHEMA-CATALOG.json",
    "contracts/qualification/common/checker-receipt.schema.json",
    "contracts/qualification/common/digest-binding.schema.json",
    "contracts/qualification/common/environment-binding.schema.json",
    "contracts/qualification/common/normalized-path.schema.json",
    "contracts/qualification/common/offline-catalog.schema.json",
    "contracts/qualification/common/provenance.schema.json",
    "contracts/qualification/common/qualification-envelope.schema.json",
    "contracts/qualification/common/redaction.schema.json",
    "contracts/qualification/common/repository-binding.schema.json",
    "docs/evidence/EVD-QUAL-001-qualification-common.md",
    "docs/work-packages/QUAL-P0-00.md",
    "tests/qualification/__init__.py",
    "tests/qualification/test_qualification_common.py",
    "tools/validate_qualification_common.py",
)

NON_AUTHORITY_FLAGS = {
    "technology_stack_approved",
    "technology_stack_frozen",
    "identity_provider_approved",
    "pg_g0_passed",
    "production_implementation_authorized",
    "merge_authorized",
    "release_authorized",
    "runtime_activation_authorized",
    "authority_effective",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_payload_sha256(data: dict[str, Any], excluded_key: str) -> str:
    payload = {key: value for key, value in data.items() if key != excluded_key}
    rendered = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")
    return sha256_bytes(rendered)


def parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or RFC3339.fullmatch(value) is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def normalized_path(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value) or "\\" in value:
        return False
    if "//" in value or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", value):
        return False
    return all(part not in {"", ".", ".."} for part in value.split("/"))


def resolve_repo_path(root: Path, value: str) -> Path | None:
    if not normalized_path(value):
        return None
    candidate = root.joinpath(*value.split("/"))
    try:
        candidate.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    current = root.resolve()
    for part in value.split("/"):
        current = current / part
        if current.exists() and current.is_symlink():
            return None
    return candidate


def exact_keys(value: Any, required: set[str], label: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    actual = set(value)
    errors = [f"{label} missing field: {key}" for key in sorted(required - actual)]
    errors.extend(f"{label} unknown field: {key}" for key in sorted(actual - required))
    return errors


def sorted_unique(values: Any, key, label: str) -> list[str]:
    if not isinstance(values, list):
        return [f"{label} must be an array"]
    try:
        keys = [key(item) for item in values]
    except (KeyError, TypeError):
        return [f"{label} contains malformed items"]
    errors: list[str] = []
    if keys != sorted(keys):
        errors.append(f"{label} must use deterministic ordering")
    if len(keys) != len(set(keys)):
        errors.append(f"{label} contains duplicate identifiers")
    return errors


def iter_refs(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        ref = value.get("$ref")
        if isinstance(ref, str):
            yield ref
        for nested in value.values():
            yield from iter_refs(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from iter_refs(nested)


def validate_closed_objects(value: Any, label: str = "schema") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        if value.get("type") == "object" and value.get("additionalProperties") is not False:
            errors.append(f"{label} object is not closed")
        for key, nested in value.items():
            errors.extend(validate_closed_objects(nested, f"{label}/{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            errors.extend(validate_closed_objects(nested, f"{label}/{index}"))
    return errors


def validate_catalog_graph(
    root: Path = ROOT, catalog_path: Path = DEFAULT_CATALOG
) -> tuple[dict[str, Path], list[str]]:
    """Load a closed catalog and its pinned imports without network fallback."""

    errors: list[str] = []
    resolved: dict[str, Path] = {}
    visited: set[Path] = set()
    active: set[Path] = set()

    def load(path: Path, expected_digest: str | None = None) -> None:
        absolute = path if path.is_absolute() else root / path
        absolute = absolute.resolve()
        if absolute in active:
            errors.append(f"catalog import cycle: {absolute.relative_to(root)}")
            return
        if absolute in visited:
            return
        if not absolute.is_file():
            errors.append(f"catalog missing: {absolute}")
            return
        if expected_digest is not None and sha256_file(absolute) != expected_digest:
            errors.append(f"catalog import digest mismatch: {absolute.relative_to(root)}")
            return
        try:
            data = read_json(absolute)
        except Exception as exc:
            errors.append(f"catalog invalid JSON: {absolute}: {exc}")
            return
        required = {
            "$schema", "catalog_id", "version", "status", "work_package_id",
            "updated_at", "imports", "entries",
        }
        errors.extend(exact_keys(data, required, f"catalog {absolute.name}"))
        if not isinstance(data, dict):
            return
        if data.get("status") != "draft" or data.get("version") != "0.1.0-draft":
            errors.append(f"catalog must remain draft: {absolute.name}")
        if parse_datetime(data.get("updated_at")) is None:
            errors.append(f"catalog timestamp invalid: {absolute.name}")
        active.add(absolute)
        imports = data.get("imports", [])
        errors.extend(sorted_unique(imports, lambda item: item["catalog_id"], f"{absolute.name} imports"))
        for item in imports if isinstance(imports, list) else []:
            item_errors = exact_keys(item, {"catalog_id", "path", "sha256"}, "catalog import")
            errors.extend(item_errors)
            if item_errors:
                continue
            imported = resolve_repo_path(root, item["path"])
            if imported is None or not SHA256.fullmatch(item["sha256"]):
                errors.append(f"catalog import binding invalid: {item}")
                continue
            load(imported, item["sha256"])
        entries = data.get("entries", [])
        errors.extend(sorted_unique(entries, lambda item: item["schema_id"], f"{absolute.name} entries"))
        for entry in entries if isinstance(entries, list) else []:
            entry_errors = exact_keys(entry, {"schema_id", "path", "sha256"}, "catalog entry")
            errors.extend(entry_errors)
            if entry_errors:
                continue
            schema_id = entry["schema_id"]
            schema_path = resolve_repo_path(root, entry["path"])
            if not isinstance(schema_id, str) or SCHEMA_REF.fullmatch(schema_id) is None:
                errors.append(f"catalog schema id invalid: {schema_id}")
                continue
            if schema_path is None or not schema_path.is_file():
                errors.append(f"catalog schema path invalid: {entry['path']}")
                continue
            if not SHA256.fullmatch(entry["sha256"]) or sha256_file(schema_path) != entry["sha256"]:
                errors.append(f"catalog schema digest mismatch: {entry['path']}")
            if schema_id in resolved:
                errors.append(f"catalog duplicate schema id: {schema_id}")
            else:
                resolved[schema_id] = schema_path
        active.remove(absolute)
        visited.add(absolute)

    load(catalog_path)

    for schema_id, schema_path in sorted(resolved.items()):
        try:
            schema = read_json(schema_path)
        except Exception as exc:
            errors.append(f"schema invalid JSON {schema_path.relative_to(root)}: {exc}")
            continue
        if not isinstance(schema, dict):
            errors.append(f"schema must be an object: {schema_path.relative_to(root)}")
            continue
        if schema.get("$schema") != OFFICIAL_META_SCHEMA:
            errors.append(f"schema meta URI invalid: {schema_path.relative_to(root)}")
        if schema.get("$id") != schema_id:
            errors.append(f"schema id/catalog mismatch: {schema_path.relative_to(root)}")
        if schema.get("status") != "draft":
            errors.append(f"schema must remain draft: {schema_path.relative_to(root)}")
        errors.extend(validate_closed_objects(schema, str(schema_path.relative_to(root))))
        for ref in iter_refs(schema):
            if ref.startswith("#"):
                continue
            base = ref.split("#", 1)[0]
            if base.startswith("http://") or base.startswith("https://"):
                errors.append(f"network schema ref prohibited: {ref}")
            elif base not in resolved:
                errors.append(f"offline schema ref unresolved: {ref}")

    return resolved, sorted(set(errors))


def git_output(root: Path, *args: str) -> str | None:
    process = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )
    return process.stdout.strip() if process.returncode == 0 else None


def git_bytes(root: Path, *args: str) -> bytes | None:
    process = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=False
    )
    return process.stdout if process.returncode == 0 else None


def validate_repository_binding(binding: Any, root: Path, label: str) -> list[str]:
    required = {"repository_ref", "commit_sha", "tree_sha", "branch_ref", "dirty"}
    errors = exact_keys(binding, required, label)
    if errors or not isinstance(binding, dict):
        return errors
    if binding.get("repository_ref") != "bstBizEra/bopen":
        errors.append(f"{label} repository_ref invalid")
    commit = binding.get("commit_sha")
    tree = binding.get("tree_sha")
    if not isinstance(commit, str) or SHA1.fullmatch(commit) is None:
        errors.append(f"{label} commit_sha invalid")
    if not isinstance(tree, str) or SHA1.fullmatch(tree) is None:
        errors.append(f"{label} tree_sha invalid")
    if binding.get("dirty") is not False:
        errors.append(f"{label} dirty binding denied")
    if isinstance(commit, str) and SHA1.fullmatch(commit) and isinstance(tree, str):
        actual_tree = git_output(root, "rev-parse", f"{commit}^{{tree}}")
        if actual_tree is None:
            errors.append(f"{label} commit does not resolve")
        elif actual_tree != tree:
            errors.append(f"{label} commit/tree mismatch")
    return errors


def validate_actor(actor: Any, label: str) -> list[str]:
    required = {"actor_kind", "identity_ref", "role", "registration_ref", "session_ref"}
    errors = exact_keys(actor, required, label)
    if errors or not isinstance(actor, dict):
        return errors
    if actor.get("actor_kind") not in {"HUMAN", "AGENT"}:
        errors.append(f"{label} actor_kind invalid")
    for field in ("identity_ref", "role", "registration_ref", "session_ref"):
        if not isinstance(actor.get(field), str) or not actor[field]:
            errors.append(f"{label} {field} invalid")
    return errors


def validate_environment_binding(binding: Any, root: Path, label: str) -> list[str]:
    required = {
        "environment_id", "manifest_ref", "manifest_sha256", "os_family", "os_version",
        "architecture", "locale", "timezone", "network_mode", "runner_kind",
        "runner_image_digest", "toolchain", "captured_at",
    }
    errors = exact_keys(binding, required, label)
    if errors or not isinstance(binding, dict):
        return errors
    manifest_ref = binding.get("manifest_ref")
    manifest = resolve_repo_path(root, manifest_ref) if isinstance(manifest_ref, str) else None
    digest = binding.get("manifest_sha256")
    if manifest is None or not manifest.is_file():
        errors.append(f"{label} environment manifest missing")
    elif not isinstance(digest, str) or sha256_file(manifest) != digest:
        errors.append(f"{label} environment manifest digest mismatch")
    if binding.get("environment_id") != f"sha256:{digest}":
        errors.append(f"{label} environment_id mismatch")
    if parse_datetime(binding.get("captured_at")) is None:
        errors.append(f"{label} captured_at invalid")
    tools = binding.get("toolchain")
    errors.extend(sorted_unique(tools, lambda item: item["name"], f"{label} toolchain"))
    for tool in tools if isinstance(tools, list) else []:
        errors.extend(exact_keys(tool, {"name", "version", "executable_sha256"}, f"{label} tool"))
        if not isinstance(tool, dict) or not isinstance(tool.get("executable_sha256"), str) or SHA256.fullmatch(tool["executable_sha256"]) is None:
            errors.append(f"{label} tool digest invalid")
    return errors


def validate_digest_binding(binding: Any, root: Path, label: str) -> list[str]:
    required = {
        "artifact_id", "path", "sha256", "byte_length", "media_type",
        "canonicalization", "source_repository_binding",
    }
    errors = exact_keys(binding, required, label)
    if errors or not isinstance(binding, dict):
        return errors
    path_value = binding.get("path")
    digest = binding.get("sha256")
    byte_length = binding.get("byte_length")
    if not normalized_path(path_value):
        errors.append(f"{label} path invalid")
        return errors
    if not isinstance(digest, str) or SHA256.fullmatch(digest) is None:
        errors.append(f"{label} sha256 invalid")
    if not isinstance(byte_length, int) or isinstance(byte_length, bool) or byte_length < 0:
        errors.append(f"{label} byte_length invalid")
    source = binding.get("source_repository_binding")
    data: bytes | None = None
    if source is None:
        path = resolve_repo_path(root, path_value)
        if path is None or not path.is_file():
            errors.append(f"{label} artifact missing")
        else:
            data = path.read_bytes()
    else:
        errors.extend(validate_repository_binding(source, root, f"{label} source binding"))
        if isinstance(source, dict):
            data = git_bytes(root, "show", f"{source.get('commit_sha')}:{path_value}")
            if data is None:
                errors.append(f"{label} committed artifact missing")
    if data is not None:
        if binding.get("canonicalization") == "LF_UTF8":
            try:
                text = data.decode("utf-8")
                data = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
            except UnicodeDecodeError:
                errors.append(f"{label} LF_UTF8 artifact is not UTF-8")
        elif binding.get("canonicalization") == "CANONICAL_JSON":
            try:
                parsed = json.loads(data.decode("utf-8"))
                data = json.dumps(parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
            except (UnicodeDecodeError, ValueError, TypeError):
                errors.append(f"{label} canonical JSON invalid")
        if sha256_bytes(data) != digest:
            errors.append(f"{label} artifact digest mismatch")
        if len(data) != byte_length:
            errors.append(f"{label} artifact byte length mismatch")
    return errors


def validate_non_authority_flags(value: Any, label: str) -> list[str]:
    errors = exact_keys(value, NON_AUTHORITY_FLAGS, label)
    if isinstance(value, dict):
        errors.extend(f"{label} {key} must be false" for key in sorted(NON_AUTHORITY_FLAGS) if value.get(key) is not False)
    return errors


def validate_qualification_envelope(data: Any, root: Path = ROOT) -> list[str]:
    required = {
        "$schema", "envelope_id", "version", "status", "work_package_id",
        "qualification_run_id", "subject_repository_binding", "environment_binding",
        "provenance", "redaction", "evidence_root", "artifact_inventory_ref",
        "requirement_bindings", "governing_artifact_bindings", "adr_bindings",
        "authority_binding", "execution_scope", "exception_refs", "coverage_claims",
        "gate_context", "created_at", "non_authority_flags",
    }
    errors = exact_keys(data, required, "qualification envelope")
    if errors or not isinstance(data, dict):
        return sorted(errors)
    if data.get("$schema") != "bopen://schemas/qualification/common/qualification-envelope/0.1.0-draft":
        errors.append("qualification envelope schema URI invalid")
    if data.get("version") != "0.1.0-draft" or data.get("status") != "draft":
        errors.append("qualification envelope must remain draft")
    if parse_datetime(data.get("created_at")) is None:
        errors.append("qualification envelope created_at invalid")
    errors.extend(validate_repository_binding(data.get("subject_repository_binding"), root, "subject binding"))
    errors.extend(validate_environment_binding(data.get("environment_binding"), root, "environment binding"))
    evidence_root = data.get("evidence_root")
    if not normalized_path(evidence_root):
        errors.append("qualification envelope evidence_root invalid")
    errors.extend(validate_digest_binding(data.get("artifact_inventory_ref"), root, "artifact inventory binding"))

    provenance = data.get("provenance")
    provenance_keys = {"generated_by", "checked_by", "tools", "source_refs", "created_at"}
    errors.extend(exact_keys(provenance, provenance_keys, "provenance"))
    if isinstance(provenance, dict):
        tools = provenance.get("tools")
        errors.extend(sorted_unique(tools, lambda item: item["tool_id"], "provenance tools"))
        refs = provenance.get("source_refs")
        if not isinstance(refs, list) or refs != sorted(refs) or len(refs) != len(set(refs)):
            errors.append("provenance source_refs must be sorted and unique")
        maker = provenance.get("generated_by")
        checker = provenance.get("checked_by")
        errors.extend(validate_actor(maker, "provenance generated_by"))
        if checker is not None:
            errors.extend(validate_actor(checker, "provenance checked_by"))
        if isinstance(maker, dict) and isinstance(checker, dict) and (
            maker.get("identity_ref") == checker.get("identity_ref")
            or maker.get("session_ref") == checker.get("session_ref")
        ):
            errors.append("provenance maker/checker independence violated")

    redaction = data.get("redaction")
    redaction_keys = {"policy_id", "credential_mode", "redacted_fields", "secret_scan_result", "production_credentials_present", "scanner_ref"}
    errors.extend(exact_keys(redaction, redaction_keys, "redaction"))
    if isinstance(redaction, dict):
        if redaction.get("production_credentials_present") is not False:
            errors.append("production credentials are prohibited")
        if redaction.get("secret_scan_result") != "PASS":
            errors.append("secret scan must pass")
        fields = redaction.get("redacted_fields")
        if not isinstance(fields, list) or fields != sorted(fields) or len(fields) != len(set(fields)):
            errors.append("redacted_fields must be sorted and unique")

    for field in ("requirement_bindings", "governing_artifact_bindings", "adr_bindings"):
        values = data.get(field)
        errors.extend(sorted_unique(values, lambda item: item["artifact_id"], field))
        for item in values if isinstance(values, list) else []:
            item_errors = exact_keys(item, {"artifact_id", "version", "status", "artifact_ref", "sha256"}, f"{field} item")
            errors.extend(item_errors)
            if item_errors or not isinstance(item, dict):
                continue
            ref = item.get("artifact_ref")
            digest = item.get("sha256")
            subject = data.get("subject_repository_binding")
            committed = git_bytes(root, "show", f"{subject.get('commit_sha')}:{ref}") if isinstance(subject, dict) and normalized_path(ref) else None
            if committed is None:
                errors.append(f"{field} committed artifact missing: {ref}")
            elif not isinstance(digest, str) or SHA256.fullmatch(digest) is None or sha256_bytes(committed) != digest:
                errors.append(f"{field} committed artifact digest mismatch: {ref}")
    claims = data.get("coverage_claims")
    errors.extend(sorted_unique(claims, lambda item: item["requirement_id"], "coverage_claims"))
    for claim in claims if isinstance(claims, list) else []:
        claim_errors = exact_keys(claim, {"requirement_id", "coverage_level", "evidence_refs", "coverage_limit"}, "coverage claim")
        errors.extend(claim_errors)
        if isinstance(claim, dict):
            refs = claim.get("evidence_refs")
            if not isinstance(refs, list) or refs != sorted(refs) or len(refs) != len(set(refs)):
                errors.append(f"coverage claim evidence refs invalid: {claim.get('requirement_id')}")
            if claim.get("coverage_level") == "DIRECT" and not refs:
                errors.append(f"direct coverage lacks evidence: {claim.get('requirement_id')}")

    authority = data.get("authority_binding")
    authority_keys = {"authorization_status", "authority_source_ref", "authority_source_sha256", "accepted_by", "accepted_at", "expires_at", "authority_effective"}
    errors.extend(exact_keys(authority, authority_keys, "authority binding"))
    if isinstance(authority, dict):
        if authority.get("authority_effective") is not False:
            errors.append("qualification envelope cannot assert authority effect")
        expires = parse_datetime(authority.get("expires_at"))
        if expires is None:
            errors.append("authority expiry invalid")
        accepted_by = authority.get("accepted_by")
        if accepted_by is not None:
            errors.extend(validate_actor(accepted_by, "authority accepted_by"))
        if (accepted_by is None) != (authority.get("accepted_at") is None):
            errors.append("authority accepted_by/accepted_at must be populated together")
        if authority.get("accepted_at") is not None and parse_datetime(authority.get("accepted_at")) is None:
            errors.append("authority accepted_at invalid")
        authority_ref = authority.get("authority_source_ref")
        subject = data.get("subject_repository_binding")
        committed = git_bytes(root, "show", f"{subject.get('commit_sha')}:{authority_ref}") if isinstance(subject, dict) and normalized_path(authority_ref) else None
        if committed is None or sha256_bytes(committed) != authority.get("authority_source_sha256"):
            errors.append("authority source binding mismatch")

    scope = data.get("execution_scope")
    scope_keys = {"branch_ref", "worktree_ref", "base_repository_binding", "allowed_paths", "prohibited_paths"}
    errors.extend(exact_keys(scope, scope_keys, "execution scope"))
    if isinstance(scope, dict):
        errors.extend(validate_repository_binding(scope.get("base_repository_binding"), root, "base binding"))
        allowed = scope.get("allowed_paths")
        prohibited = scope.get("prohibited_paths")
        for label, values in (("allowed_paths", allowed), ("prohibited_paths", prohibited)):
            if not isinstance(values, list) or values != sorted(values) or len(values) != len(set(values)) or not all(normalized_path(item) for item in values):
                errors.append(f"execution scope {label} invalid")
        if isinstance(allowed, list) and isinstance(prohibited, list) and set(allowed).intersection(prohibited):
            errors.append("execution scope allowed/prohibited overlap")

    exceptions = data.get("exception_refs")
    errors.extend(sorted_unique(exceptions, lambda item: item["exception_id"], "exception_refs"))
    for item in exceptions if isinstance(exceptions, list) else []:
        errors.extend(exact_keys(item, {"exception_id", "status", "artifact_ref", "sha256", "expires_at"}, "exception ref"))
        if isinstance(item, dict) and parse_datetime(item.get("expires_at")) is None:
            errors.append(f"exception expiry invalid: {item.get('exception_id')}")
    gate = data.get("gate_context")
    gate_keys = {"gate_id", "prerequisites", "gate_effective"}
    errors.extend(exact_keys(gate, gate_keys, "gate context"))
    if isinstance(gate, dict):
        if gate.get("gate_effective") is not False:
            errors.append("qualification envelope cannot pass a program gate")
        prerequisites = gate.get("prerequisites")
        errors.extend(sorted_unique(prerequisites, lambda item: item["requirement_id"], "gate prerequisites"))
        for item in prerequisites if isinstance(prerequisites, list) else []:
            errors.extend(exact_keys(item, {"requirement_id", "status", "evidence_refs"}, "gate prerequisite"))
    errors.extend(validate_non_authority_flags(data.get("non_authority_flags"), "envelope non_authority_flags"))
    return sorted(set(errors))


def validate_checker_receipt(
    data: Any,
    root: Path = ROOT,
    receipt_storage_commit: str | None = None,
    receipt_path: str | None = None,
) -> list[str]:
    required = {
        "$schema", "checker_receipt_id", "version", "status", "work_package_id",
        "qualification_run_id", "reviewed_subject_binding", "reviewed_evidence_binding",
        "storage_parent_binding", "scorecard_binding", "inventory_binding",
        "environment_binding", "maker", "checker", "independence_asserted", "checks",
        "findings", "coverage_verdicts", "specialist_domains", "scope_complete",
        "unresolved_high_or_critical_count", "verdict", "reason_codes", "reviewed_at",
        "receipt_payload_sha256", "non_authority_flags",
    }
    errors = exact_keys(data, required, "checker receipt")
    if errors or not isinstance(data, dict):
        return sorted(errors)
    if data.get("$schema") != "bopen://schemas/qualification/common/checker-receipt/0.1.0-draft":
        errors.append("checker receipt schema URI invalid")
    if data.get("version") != "0.1.0-draft" or data.get("status") != "draft":
        errors.append("checker receipt must remain draft")
    for field in ("reviewed_subject_binding", "reviewed_evidence_binding", "storage_parent_binding"):
        errors.extend(validate_repository_binding(data.get(field), root, field))
    evidence = data.get("reviewed_evidence_binding")
    storage_parent = data.get("storage_parent_binding")
    if isinstance(evidence, dict) and isinstance(storage_parent, dict) and evidence != storage_parent:
        errors.append("receipt storage parent must equal reviewed evidence binding")
    errors.extend(validate_digest_binding(data.get("scorecard_binding"), root, "receipt scorecard binding"))
    errors.extend(validate_digest_binding(data.get("inventory_binding"), root, "receipt inventory binding"))
    errors.extend(validate_environment_binding(data.get("environment_binding"), root, "receipt environment"))
    maker = data.get("maker")
    checker = data.get("checker")
    errors.extend(validate_actor(maker, "receipt maker"))
    errors.extend(validate_actor(checker, "receipt checker"))
    if not isinstance(maker, dict) or not isinstance(checker, dict):
        errors.append("receipt maker/checker invalid")
    elif maker.get("identity_ref") == checker.get("identity_ref") or maker.get("session_ref") == checker.get("session_ref"):
        errors.append("receipt maker/checker independence violated")
    checks = data.get("checks")
    findings = data.get("findings")
    coverage = data.get("coverage_verdicts")
    errors.extend(sorted_unique(checks, lambda item: item["check_id"], "receipt checks"))
    errors.extend(sorted_unique(findings, lambda item: (item["severity"], item["finding_id"]), "receipt findings"))
    errors.extend(sorted_unique(coverage, lambda item: item["requirement_id"], "receipt coverage_verdicts"))
    for check in checks if isinstance(checks, list) else []:
        errors.extend(exact_keys(check, {"check_id", "required", "result", "evidence_refs", "reason_code"}, "receipt check"))
    for finding in findings if isinstance(findings, list) else []:
        errors.extend(exact_keys(finding, {"finding_id", "severity", "summary", "evidence_refs"}, "receipt finding"))
    for item in coverage if isinstance(coverage, list) else []:
        errors.extend(exact_keys(item, {"requirement_id", "verdict", "evidence_refs"}, "receipt coverage verdict"))
    domains = data.get("specialist_domains")
    if not isinstance(domains, list) or domains != sorted(domains) or len(domains) != len(set(domains)):
        errors.append("receipt specialist_domains must be sorted and unique")
    verdict = data.get("verdict")
    terminal = verdict in {"ACCEPT_EXACT_SHA", "REQUEST_CHANGES", "REJECT"}
    if terminal and (data.get("independence_asserted") is not True or parse_datetime(data.get("reviewed_at")) is None):
        errors.append("terminal receipt requires independent checker and reviewed_at")
    if verdict == "PENDING" and data.get("reviewed_at") is not None:
        errors.append("pending receipt cannot claim reviewed_at")
    reasons = data.get("reason_codes")
    if not isinstance(reasons, list) or reasons != sorted(reasons) or len(reasons) != len(set(reasons)):
        errors.append("receipt reason_codes must be sorted and unique")
    if verdict == "ACCEPT_EXACT_SHA":
        for check in checks if isinstance(checks, list) else []:
            if isinstance(check, dict) and check.get("required") is True and (
                check.get("result") != "PASS" or not check.get("evidence_refs")
            ):
                errors.append(f"accepted receipt required check not evidenced: {check.get('check_id')}")
        blocking = {"HIGH", "CRITICAL", "BLOCKING"}
        if any(isinstance(item, dict) and item.get("severity") in blocking for item in findings if isinstance(findings, list)):
            errors.append("accepted receipt contains blocking finding")
        if data.get("unresolved_high_or_critical_count") != 0:
            errors.append("accepted receipt unresolved severe findings must be zero")
    expected_digest = canonical_payload_sha256(data, "receipt_payload_sha256")
    if data.get("receipt_payload_sha256") != expected_digest:
        errors.append("checker receipt payload digest mismatch")
    errors.extend(validate_non_authority_flags(data.get("non_authority_flags"), "receipt non_authority_flags"))

    if receipt_storage_commit is not None:
        if SHA1.fullmatch(receipt_storage_commit) is None:
            errors.append("receipt storage commit invalid")
        elif isinstance(evidence, dict):
            subject = data.get("reviewed_subject_binding")
            evidence_sha = evidence.get("commit_sha")
            subject_sha = subject.get("commit_sha") if isinstance(subject, dict) else None
            if git_output(root, "rev-parse", f"{evidence_sha}^") != subject_sha:
                errors.append("A->B lineage invalid: evidence must be direct child of subject")
            if git_output(root, "rev-parse", f"{receipt_storage_commit}^") != evidence_sha:
                errors.append("B->C lineage invalid: receipt must be direct child of evidence")
            if receipt_path is None or not normalized_path(receipt_path) or not receipt_path.endswith("checker-receipt.json"):
                errors.append("receipt storage path invalid")
            else:
                changed = git_output(root, "diff", "--name-only", evidence_sha, receipt_storage_commit)
                changed_paths = changed.splitlines() if changed else []
                if changed_paths != [receipt_path]:
                    errors.append("receipt commit must add only checker-receipt.json")
                if git_output(root, "cat-file", "-e", f"{evidence_sha}:{receipt_path}") is not None:
                    errors.append("checker receipt must be absent from evidence snapshot B")
                if git_output(root, "cat-file", "-e", f"{receipt_storage_commit}:{receipt_path}") is None:
                    errors.append("checker receipt missing from storage snapshot C")
    return sorted(set(errors))


def canonical_document_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    if path.suffix.lower() not in {".md", ".json", ".py"}:
        return data
    text = data.decode("utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def build_package_manifest(root: Path = ROOT) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for relative in PACKAGE_PATHS:
        path = resolve_repo_path(root, relative)
        if path is None or not path.is_file():
            raise FileNotFoundError(relative)
        data = canonical_document_bytes(path)
        records.append({"path": relative, "sha256": sha256_bytes(data), "bytes": len(data)})
    return {
        "manifest_id": "QUAL-P0-00-PACKAGE-MANIFEST",
        "version": "0.1.0-draft",
        "status": "draft",
        "work_package_id": "QUAL-P0-00",
        "generated_at": "2026-07-21T00:00:00+07:00",
        "generation_base": {
            "commit_sha": AUTHORIZED_BASE_COMMIT,
            "tree_sha": AUTHORIZED_BASE_TREE,
        },
        "records": records,
    }


def rendered_manifest(root: Path = ROOT) -> str:
    return json.dumps(build_package_manifest(root), indent=2, ensure_ascii=True) + "\n"


def validate_common_package(
    root: Path = ROOT,
    catalog_path: Path = DEFAULT_CATALOG,
    manifest_path: Path | None = None,
) -> list[str]:
    resolved, errors = validate_catalog_graph(root, catalog_path)
    if git_output(root, "rev-parse", f"{AUTHORIZED_BASE_COMMIT}^{{tree}}") != AUTHORIZED_BASE_TREE:
        errors.append("authorized QUAL-P0-00 base commit/tree binding invalid")
    if git_output(root, "merge-base", "--is-ancestor", AUTHORIZED_BASE_COMMIT, "HEAD") is None:
        errors.append("current HEAD is not descended from the authorized QUAL-P0-00 base")
    common_dir = root / "contracts/qualification/common"
    actual_schema_files = {path.name for path in common_dir.glob("*.schema.json")}
    if actual_schema_files != COMMON_SCHEMA_FILES:
        errors.append("QUAL-P0-00 common schema file set differs from the authorized set")
    expected_ids = {
        f"bopen://schemas/qualification/common/{name[:-12]}/0.1.0-draft"
        for name in COMMON_SCHEMA_FILES
    }
    if set(resolved) != expected_ids:
        errors.append("QUAL-P0-00 catalog does not contain the exact common schema set")
    envelope_schema = read_json(common_dir / "qualification-envelope.schema.json")
    flag_properties = envelope_schema.get("$defs", {}).get("nonAuthorityFlags", {}).get("properties", {})
    if set(flag_properties) != NON_AUTHORITY_FLAGS or any(
        definition.get("const") is not False for definition in flag_properties.values()
    ):
        errors.append("qualification non-authority flags must be complete and false")
    if manifest_path is not None:
        absolute = manifest_path if manifest_path.is_absolute() else root / manifest_path
        if not absolute.is_file():
            errors.append(f"package manifest missing: {manifest_path}")
        elif absolute.read_text(encoding="utf-8") != rendered_manifest(root):
            errors.append(f"package manifest stale: {manifest_path}")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--envelope", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--receipt-commit")
    parser.add_argument("--receipt-path")
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--check-manifest", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    errors = validate_common_package(
        ROOT,
        args.catalog,
        DEFAULT_MANIFEST if args.check_manifest else None,
    )
    if args.envelope:
        errors.extend(validate_qualification_envelope(read_json(ROOT / args.envelope), ROOT))
    if args.receipt:
        errors.extend(
            validate_checker_receipt(
                read_json(ROOT / args.receipt), ROOT, args.receipt_commit, args.receipt_path
            )
        )
    if errors:
        print("QUAL-P0-00 common qualification validation: FAIL")
        for error in sorted(set(errors)):
            print(f"- {error}")
        return 1
    if args.write_manifest:
        output = ROOT / DEFAULT_MANIFEST
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered_manifest(ROOT), encoding="utf-8", newline="\n")
        print(f"Wrote immutable package manifest: {DEFAULT_MANIFEST}")
    print(f"QUAL-P0-00 common qualification validation: PASS ({len(COMMON_SCHEMA_FILES)} schemas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
