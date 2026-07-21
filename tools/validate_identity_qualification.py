#!/usr/bin/env python3
"""Validate the draft QUAL-P0-02 synthetic identity qualification subject.

This is a standard-library, offline validator for the schema subject only. It
does not execute OIDC, accept evidence, select a provider, or create runtime
identity/session behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from validate_qualification_common import (
    exact_keys,
    read_json,
    sha256_file,
    validate_catalog_graph,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path("contracts/qualification/identity/QUAL-P0-02-SCHEMA-CATALOG.json")
MANIFEST = Path("docs/manifests/QUAL-P0-02-PACKAGE-MANIFEST.json")
COMMON_CATALOG = "contracts/qualification/common/QUAL-P0-00-SCHEMA-CATALOG.json"
COMMON_CATALOG_SHA256 = "803500ff8dd12e17531872482875dcf67fa8f617de45c11318a55ba8ed8b8450"
AUTHORIZED_BASE_COMMIT = "a2fc4b1f907b17911ffbd3cb8e0992b806c90bb6"
AUTHORIZED_BASE_TREE = "a5a63d2fb882939f176139c9f276a8d44faaf6d9"

SCHEMA_FILES = {
    "account-link-state.projection.schema.json": "bopen://schemas/qualification/identity/account-link-state-projection/0.1.0-draft",
    "assurance-evidence.observation.schema.json": "bopen://schemas/qualification/identity/assurance-evidence-observation/0.1.0-draft",
    "auth-assertion.observation.schema.json": "bopen://schemas/qualification/identity/auth-assertion-observation/0.1.0-draft",
    "external-identity-binding.projection.schema.json": "bopen://schemas/qualification/identity/external-identity-binding-projection/0.1.0-draft",
    "migration-evidence.observation.schema.json": "bopen://schemas/qualification/identity/migration-evidence-observation/0.1.0-draft",
    "principal-session.projection.schema.json": "bopen://schemas/qualification/identity/principal-session-projection/0.1.0-draft",
    "provider-connection.observation.schema.json": "bopen://schemas/qualification/identity/provider-connection-observation/0.1.0-draft",
    "test-case-result.observation.schema.json": "bopen://schemas/qualification/identity/test-case-result-observation/0.1.0-draft",
}

PACKAGE_PATHS = (
    "contracts/qualification/identity/QUAL-P0-02-SCHEMA-CATALOG.json",
    *tuple(f"contracts/qualification/identity/{name}" for name in sorted(SCHEMA_FILES)),
    "docs/07-security/identity/DEC-0005-QUAL-001.md",
    "docs/evidence/EVD-QUAL-002-identity-qualification.md",
    "docs/work-packages/QUAL-P0-02.md",
    "tests/qualification/test_identity_qualification.py",
    "tools/validate_identity_qualification.py",
)

COMMON_REQUIRED = {
    "$schema", "record_id", "version", "status", "work_package_id",
    "qualification_id", "qualification_only", "synthetic_data_only",
    "qualification_envelope", "correlation_id", "audit_event_ref",
    "determinism", "downstream_effects",
}
DOWNSTREAM_EFFECTS = {
    "principal_runtime", "tenant", "membership", "role", "permission",
    "entitlement", "active_context", "release", "runtime_activation",
}
NEGATIVE_CATEGORIES = {
    "OIDC_ISSUER_MIXUP", "ISSUER_NORMALIZATION", "SUBJECT_CASE",
    "SAME_EMAIL_CROSS_ISSUER", "SAME_SUBJECT_CROSS_ISSUER", "MISSING_SUBJECT",
    "WRONG_AUDIENCE", "WRONG_AUTHORIZED_PARTY", "ALG_NONE",
    "ALGORITHM_CONFUSION", "UNKNOWN_KEY_ID", "DUPLICATE_KEY_ID",
    "INVALID_SIGNATURE", "STALE_JWKS", "JWKS_ROTATION", "STATE_MISMATCH",
    "NONCE_MISMATCH", "PKCE_FAILURE", "CODE_REPLAY", "ASSERTION_REPLAY",
    "EXPIRED_ASSERTION", "FUTURE_ASSERTION", "DISABLED_PROVIDER",
    "REVOKED_BINDING", "INACTIVE_PRINCIPAL", "REVOKED_SESSION",
    "LINK_WITHOUT_DUAL_REAUTH", "LINK_CSRF", "SESSION_FIXATION",
    "KEY_ALREADY_BOUND", "CLAIM_TENANT_AUTHORITY", "RAW_SECRET_LEAK",
    "MIGRATION_AMBIGUITY", "MIGRATION_COLLISION", "MIGRATION_COUNT_MISMATCH",
    "MIGRATION_ROLLBACK_GAP",
}
PROHIBITED_ACCEPTANCE_FIELDS = {
    "accepted_by", "approved_by", "checker", "verifier", "acceptance_status",
    "provider_approved", "runtime_authorized", "release_authorized",
}


def canonical_json_bytes(data: Any) -> bytes:
    return (json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def build_manifest(root: Path = ROOT) -> dict[str, Any]:
    records = []
    for relative in PACKAGE_PATHS:
        path = root / relative
        raw = path.read_bytes()
        records.append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
    return {
        "manifest_id": "QUAL-P0-02-PACKAGE-MANIFEST",
        "version": "0.1.0-draft",
        "status": "draft",
        "work_package_id": "QUAL-P0-02",
        "qualification_id": "DEC-0005-QUAL-001",
        "generated_at": "2026-07-22T00:00:00+07:00",
        "generation_base": {"commit_sha": AUTHORIZED_BASE_COMMIT, "tree_sha": AUTHORIZED_BASE_TREE},
        "records": records,
        "non_authority_flags": {
            "identity_provider_approved": False,
            "pg_g0_passed": False,
            "production_implementation_authorized": False,
            "merge_authorized": False,
            "release_authorized": False,
            "runtime_activation_authorized": False,
            "authority_effective": False,
        },
    }


def walk_keys(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            found.add(key)
            found.update(walk_keys(nested))
    elif isinstance(value, list):
        for nested in value:
            found.update(walk_keys(nested))
    return found


def validate_downstream(schema: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    definition = schema.get("$defs", {}).get("downstreamEffects", {})
    if set(definition.get("required", [])) != DOWNSTREAM_EFFECTS:
        errors.append(f"{label} downstream effects incomplete")
    properties = definition.get("properties", {})
    if set(properties) != DOWNSTREAM_EFFECTS:
        errors.append(f"{label} downstream effect properties drift")
    for name in DOWNSTREAM_EFFECTS:
        if properties.get(name) != {"const": "NONE"}:
            errors.append(f"{label} downstream effect must be NONE: {name}")
    return errors


def validate_claim_authority(schema: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    keys = walk_keys(schema)
    required_markers = {
        "email_linking_authorized", "domain_linking_authorized",
        "group_linking_authorized", "role_linking_authorized",
        "tenant_authority_authorized",
    }
    if "claim_authority" in keys:
        serialized = json.dumps(schema, sort_keys=True)
        for marker in required_markers:
            token = f'"{marker}": {{"const": false}}'
            if token not in serialized:
                errors.append(f"{label} claim authority not fail-closed: {marker}")
    return errors


def validate_identity_schema(schema: Any, filename: str) -> list[str]:
    if not isinstance(schema, dict):
        return [f"{filename} must be an object"]
    errors: list[str] = []
    expected_id = SCHEMA_FILES[filename]
    if schema.get("$id") != expected_id:
        errors.append(f"{filename} schema id mismatch")
    if schema.get("status") != "draft":
        errors.append(f"{filename} must remain draft")
    title = schema.get("title", "")
    description = schema.get("description", "")
    if "Synthetic" not in title or "qualification-only" not in description or "runtime" not in description:
        errors.append(f"{filename} synthetic non-runtime classification missing")
    required = set(schema.get("required", []))
    if not COMMON_REQUIRED.issubset(required):
        errors.append(f"{filename} common qualification fields missing")
    props = schema.get("properties", {})
    expected_consts = {
        "work_package_id": "QUAL-P0-02", "qualification_id": "DEC-0005-QUAL-001",
        "qualification_only": True, "synthetic_data_only": True,
    }
    for field, expected in expected_consts.items():
        if props.get(field) != {"const": expected}:
            errors.append(f"{filename} {field} must be constant {expected!r}")
    expected_envelope = {"$ref": "bopen://schemas/qualification/common/qualification-envelope/0.1.0-draft"}
    if props.get("qualification_envelope") != expected_envelope:
        errors.append(f"{filename} common envelope ref mismatch")
    errors.extend(validate_downstream(schema, filename))
    errors.extend(validate_claim_authority(schema, filename))
    if set(props).intersection(PROHIBITED_ACCEPTANCE_FIELDS):
        errors.append(f"{filename} contains prohibited acceptance metadata")
    return errors


def validate_semantics(schemas: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    provider = schemas["provider-connection.observation.schema.json"]
    if provider["properties"].get("identity_key_policy") != {"const": "EXACT_ISSUER_AND_SUBJECT"}:
        errors.append("provider identity key policy must be exact issuer+subject")
    if provider["properties"].get("credential_material_present") != {"const": False}:
        errors.append("provider schema must prohibit credential material")

    for name in ("external-identity-binding.projection.schema.json", "auth-assertion.observation.schema.json", "account-link-state.projection.schema.json"):
        canonicalization = schemas[name].get("$defs", {}).get("identityKey", {}).get("properties", {}).get("canonicalization")
        if canonicalization != {"const": "RFC8785_EXACT_ISSUER_AND_SUBJECT"}:
            errors.append(f"{name} identity key canonicalization drift")

    assertion = schemas["auth-assertion.observation.schema.json"]
    if assertion["properties"].get("raw_token_present") != {"const": False}:
        errors.append("raw tokens must be prohibited")
    required_checks = {"ISSUER", "SUBJECT", "SIGNATURE", "ALGORITHM", "KEY_ID", "AUDIENCE", "AUTHORIZED_PARTY", "STATE", "NONCE", "PKCE", "ISSUED_AT", "NOT_BEFORE", "EXPIRY", "REPLAY", "PROVIDER_LIFECYCLE"}
    check_enum = set(assertion["properties"]["checks"]["items"]["properties"]["check_id"]["enum"])
    if check_enum != required_checks:
        errors.append("assertion validation check inventory incomplete")

    session = schemas["principal-session.projection.schema.json"]
    if session["properties"].get("tenant_context_ref") != {"type": "null"}:
        errors.append("identity qualification must not create tenant context")
    if session["properties"].get("raw_credential_present") != {"const": False}:
        errors.append("session projection must not contain credentials")

    link = schemas["account-link-state.projection.schema.json"]
    methods = set(link["properties"]["link_method"]["enum"])
    if not {"EXPLICIT_DUAL_REAUTHENTICATION", "MIGRATION_EXACT_KEY", "PROHIBITED_CLAIM_MATCH"}.issubset(methods):
        errors.append("account-link method controls incomplete")

    migration = schemas["migration-evidence.observation.schema.json"]
    if migration["properties"].get("identity_mapping_strategy") != {"const": "EXACT_ISSUER_AND_SUBJECT_ONLY"}:
        errors.append("migration must use exact issuer+subject only")

    testcase = schemas["test-case-result.observation.schema.json"]
    categories = set(testcase["properties"]["category"]["enum"])
    missing = NEGATIVE_CATEGORIES - categories
    if missing:
        errors.append("mandatory negative categories missing: " + ", ".join(sorted(missing)))
    forbidden = walk_keys(testcase).intersection(PROHIBITED_ACCEPTANCE_FIELDS)
    if forbidden:
        errors.append("test observations cannot carry acceptance fields: " + ", ".join(sorted(forbidden)))
    if testcase["properties"].get("skipped") != {"const": False}:
        errors.append("skipped cases must not count as qualification results")
    return errors


def validate_catalog(root: Path = ROOT) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    catalog_path = root / CATALOG
    try:
        catalog = read_json(catalog_path)
    except Exception as exc:
        return {}, [f"identity catalog invalid: {exc}"]
    imports = catalog.get("imports", []) if isinstance(catalog, dict) else []
    expected_import = [{"catalog_id": "QUAL-P0-00-SCHEMA-CATALOG", "path": COMMON_CATALOG, "sha256": COMMON_CATALOG_SHA256}]
    if imports != expected_import:
        errors.append("identity catalog must pin the exact accepted common catalog")
    resolved, graph_errors = validate_catalog_graph(root, CATALOG)
    errors.extend(graph_errors)
    schemas: dict[str, dict[str, Any]] = {}
    identity_root = root / "contracts/qualification/identity"
    actual_files = {path.name for path in identity_root.glob("*.schema.json")}
    if actual_files != set(SCHEMA_FILES):
        errors.append("identity schema file catalog mismatch")
    for filename, schema_id in SCHEMA_FILES.items():
        path = resolved.get(schema_id)
        if path is None:
            errors.append(f"identity schema unresolved: {schema_id}")
            continue
        data = read_json(path)
        schemas[filename] = data
        errors.extend(validate_identity_schema(data, filename))
    if set(schemas) == set(SCHEMA_FILES):
        errors.extend(validate_semantics(schemas))
    return schemas, sorted(set(errors))


def validate_manifest(root: Path = ROOT) -> list[str]:
    path = root / MANIFEST
    if not path.is_file():
        return ["QUAL-P0-02 package manifest missing"]
    try:
        actual = read_json(path)
    except Exception as exc:
        return [f"QUAL-P0-02 package manifest invalid: {exc}"]
    expected = build_manifest(root)
    return [] if actual == expected else ["QUAL-P0-02 package manifest raw-byte snapshot drift"]


def validate_documents(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    required_markers = {
        "docs/work-packages/QUAL-P0-02.md": ["QUAL-P0-02", "DEC-0005-QUAL-001", "production implementation", "not accepted"],
        "docs/07-security/identity/DEC-0005-QUAL-001.md": ["DEC-0005-QUAL-001", "exact issuer", "subject", "email", "tenant"],
        "docs/evidence/EVD-QUAL-002-identity-qualification.md": ["EVD-QUAL-002", "maker evidence", "independent", "no provider"],
    }
    for relative, markers in required_markers.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"controlled document missing: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker.lower() not in text.lower():
                errors.append(f"controlled document marker missing {relative}: {marker}")
    return errors


def validate_identity_package(root: Path = ROOT, check_manifest: bool = True) -> list[str]:
    _, errors = validate_catalog(root)
    errors.extend(validate_documents(root))
    for relative in PACKAGE_PATHS:
        if not (root / relative).is_file():
            errors.append(f"package file missing: {relative}")
    if check_manifest:
        errors.extend(validate_manifest(root))
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate the identity qualification package")
    parser.add_argument("--print-manifest", action="store_true", help="print the raw-byte package manifest without writing")
    args = parser.parse_args()
    if args.print_manifest:
        print(canonical_json_bytes(build_manifest()).decode("utf-8"), end="")
        return 0
    errors = validate_identity_package(check_manifest=True)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"QUAL-P0-02 identity qualification subject valid: {len(SCHEMA_FILES)} schemas; execution/provider/runtime effects absent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
