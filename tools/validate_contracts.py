#!/usr/bin/env python3
"""Validate draft machine-readable contracts without external dependencies."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOTS = (ROOT / "docs" / "06-contracts", ROOT / "contracts")
RFC3339_DATETIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
TRUSTED_CONTEXT_SOURCES = {"server_session", "trusted_service"}


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
        if path.name == "multitenant-dev-readiness.acceptance.json":
            errors.extend(validate_multitenant_readiness_fixture(data, rel, root))

    if path.parent.name == "tenancy" and path.name.endswith(".schema.json"):
        errors.extend(validate_tenancy_schema(data, rel, path.name))

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


def validate_tenancy_schema(data: dict, rel: Path, name: str) -> list[str]:
    errors: list[str] = []
    required_value = data.get("required", [])
    required = set(required_value) if isinstance(required_value, list) else set()
    properties = data.get("properties", {})
    if not isinstance(required_value, list):
        errors.append(f"TENANCY SCHEMA REQUIRED MUST BE ARRAY: {rel}")
    if not isinstance(properties, dict):
        return errors + [f"TENANCY SCHEMA PROPERTIES MUST BE OBJECT: {rel}"]
    if data.get("additionalProperties") is not False:
        errors.append(f"TENANCY SCHEMA MUST DENY UNKNOWN FIELDS: {rel}")

    if name == "membership.schema.json":
        expected = {"membership_id", "principal_id", "tenant_id", "state"}
        if not expected.issubset(required):
            errors.append(f"MEMBERSHIP IDENTITY FIELDS MISSING: {rel}")
        forbidden = {"role", "role_id", "permission", "permissions", "entitlement", "entitlements"}
        if forbidden.intersection(properties):
            errors.append(f"MEMBERSHIP MUST NOT EMBED AUTHORIZATION OR ENTITLEMENT: {rel}")

    if name == "active-context.schema.json":
        expected = {"context_id", "principal_id", "tenant_id", "membership_id", "validation_source"}
        if not expected.issubset(required):
            errors.append(f"ACTIVE CONTEXT IDENTITY FIELDS MISSING: {rel}")
        source_definition = properties.get("validation_source", {})
        sources = source_definition.get("enum", []) if isinstance(source_definition, dict) else []
        if not isinstance(sources, list) or set(sources) != TRUSTED_CONTEXT_SOURCES:
            errors.append(f"ACTIVE CONTEXT MUST BE SERVER VALIDATED: {rel}")

    if name == "tenant-ownership.schema.json":
        expected = {"tenant_id", "resource_type", "resource_id", "ownership_version"}
        if not expected.issubset(required):
            errors.append(f"TENANT OWNERSHIP FIELDS MISSING: {rel}")

    return errors


def validate_schema_instance(instance: object, schema: dict, label: str) -> list[str]:
    """Validate the JSON Schema subset used by the DEV-P0-01 contracts."""
    errors: list[str] = []
    if not isinstance(instance, dict):
        return [f"CONTRACT INSTANCE MUST BE OBJECT: {label}"]

    properties = schema.get("properties", {})
    required = schema.get("required", [])
    if not isinstance(properties, dict):
        return [f"CONTRACT SCHEMA PROPERTIES MUST BE OBJECT: {label}"]
    if not isinstance(required, list):
        return [f"CONTRACT SCHEMA REQUIRED MUST BE ARRAY: {label}"]
    for key in required:
        if key not in instance:
            errors.append(f"CONTRACT INSTANCE FIELD MISSING {label}: {key}")
    if schema.get("additionalProperties") is False:
        for key in set(instance).difference(properties):
            errors.append(f"CONTRACT INSTANCE UNKNOWN FIELD {label}: {key}")

    type_checks = {
        "string": lambda value: isinstance(value, str),
        "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
        "null": lambda value: value is None,
        "object": lambda value: isinstance(value, dict),
        "array": lambda value: isinstance(value, list),
        "boolean": lambda value: isinstance(value, bool),
    }
    for key, value in instance.items():
        definition = properties.get(key)
        if not isinstance(definition, dict):
            continue
        allowed_types = definition.get("type")
        if isinstance(allowed_types, str):
            allowed_types = [allowed_types]
        if isinstance(allowed_types, list) and not any(
            type_checks.get(item, lambda _value: False)(value) for item in allowed_types
        ):
            errors.append(f"CONTRACT INSTANCE TYPE INVALID {label}: {key}")
            continue
        if "enum" in definition and (
            not isinstance(definition["enum"], list) or value not in definition["enum"]
        ):
            errors.append(f"CONTRACT INSTANCE ENUM INVALID {label}: {key}")
        if isinstance(value, str) and len(value) < definition.get("minLength", 0):
            errors.append(f"CONTRACT INSTANCE STRING TOO SHORT {label}: {key}")
        if isinstance(value, int) and not isinstance(value, bool) and value < definition.get("minimum", value):
            errors.append(f"CONTRACT INSTANCE MINIMUM INVALID {label}: {key}")
        if definition.get("format") == "date-time" and isinstance(value, str):
            if parse_rfc3339_datetime(value) is None:
                errors.append(f"CONTRACT INSTANCE DATE-TIME INVALID {label}: {key}")
    return errors


def parse_rfc3339_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    if RFC3339_DATETIME.fullmatch(value) is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def validate_multitenant_readiness_fixture(
    data: dict, rel: Path, root: Path = ROOT
) -> list[str]:
    errors: list[str] = []
    if data.get("work_package") != "DEV-P0-01":
        errors.append(f"MULTITENANT FIXTURE WORK PACKAGE INVALID: {rel}")

    required_contracts = {
        "bopen://schemas/tenancy/membership/0.1.0-draft",
        "bopen://schemas/tenancy/active-context/0.1.0-draft",
        "bopen://schemas/tenancy/tenant-ownership/0.1.0-draft",
    }
    contracts = data.get("contracts")
    if not isinstance(contracts, list) or not all(isinstance(item, str) for item in contracts):
        errors.append(f"MULTITENANT FIXTURE CONTRACT REFERENCES INVALID: {rel}")
        contracts = []
    if not required_contracts.issubset(set(contracts)):
        errors.append(f"MULTITENANT FIXTURE CONTRACT REFERENCES MISSING: {rel}")

    instances = data.get("instances")
    if not isinstance(instances, dict):
        return errors + [f"MULTITENANT CONTRACT INSTANCES MISSING: {rel}"]
    instance_groups = {
        "membership": ("memberships", "membership.schema.json"),
        "active_context": ("active_contexts", "active-context.schema.json"),
        "resource_ownership": ("resource_ownership", "tenant-ownership.schema.json"),
    }
    schemas: dict[str, dict] = {}
    for ref_name, (group_name, schema_name) in instance_groups.items():
        schema_path = root / "docs/06-contracts/tenancy" / schema_name
        schema, parse_error = read_json(schema_path)
        if parse_error or not isinstance(schema, dict):
            errors.append(f"MULTITENANT INSTANCE SCHEMA INVALID {rel}: {schema_name}")
            continue
        schemas[ref_name] = schema
        group = instances.get(group_name)
        if not isinstance(group, dict) or not group:
            errors.append(f"MULTITENANT INSTANCE GROUP MISSING {rel}: {group_name}")
            continue
        for instance_id, instance in group.items():
            errors.extend(
                validate_schema_instance(instance, schema, f"{rel} {group_name}.{instance_id}")
            )

    evaluated_at = parse_rfc3339_datetime(data.get("evaluated_at"))
    if evaluated_at is None:
        errors.append(f"MULTITENANT EVALUATION TIME INVALID: {rel}")

    scenarios = data.get("scenarios", [])
    if not isinstance(scenarios, list):
        return errors + [f"MULTITENANT FIXTURE SCENARIOS INVALID: {rel}"]
    expected_ids = [f"MTD-{index:03d}" for index in range(1, 10)]
    actual_ids = [scenario.get("id") for scenario in scenarios if isinstance(scenario, dict)]
    if actual_ids != expected_ids:
        errors.append(f"MULTITENANT FIXTURE SCENARIOS INVALID: {rel}")
        return errors

    by_id = {scenario["id"]: scenario for scenario in scenarios}
    resolved: dict[str, dict[str, object | None]] = {}
    for scenario_id, scenario in by_id.items():
        context = scenario.get("context")
        resource = scenario.get("resource")
        layer = scenario.get("enforcement_layer")
        decision = scenario.get("authorization_decision", {})
        if not isinstance(context, dict) or not isinstance(resource, dict):
            errors.append(f"MULTITENANT CONTEXT OR RESOURCE MISSING {rel}: {scenario_id}")
            continue
        if not isinstance(decision, dict):
            errors.append(f"MULTITENANT AUTHORIZATION DECISION INVALID {rel}: {scenario_id}")
            decision = {}
        if layer not in {"api", "database"}:
            errors.append(f"MULTITENANT ENFORCEMENT LAYER INVALID {rel}: {scenario_id}")
        refs = scenario.get("instance_refs")
        if not isinstance(refs, dict):
            errors.append(f"MULTITENANT INSTANCE REFS MISSING {rel}: {scenario_id}")
            continue
        resolved[scenario_id] = {}
        for ref_name, (group_name, _schema_name) in instance_groups.items():
            ref = refs.get(ref_name)
            if ref is None:
                resolved[scenario_id][ref_name] = None
                continue
            group = instances.get(group_name, {})
            if not isinstance(ref, str) or not isinstance(group, dict) or ref not in group:
                errors.append(f"MULTITENANT INSTANCE REF INVALID {rel}: {scenario_id}.{ref_name}")
                continue
            resolved[scenario_id][ref_name] = group[ref]
        if scenario_id == "MTD-001":
            if decision.get("decision") != "ALLOW":
                errors.append(f"VALID TENANT CONTEXT MUST ALLOW {rel}: {scenario_id}")
            membership = resolved[scenario_id].get("membership")
            active_context = resolved[scenario_id].get("active_context")
            ownership = resolved[scenario_id].get("resource_ownership")
            if not all(isinstance(item, dict) for item in (membership, active_context, ownership)):
                errors.append(f"VALID CONTRACT COMPOSITION MISSING {rel}: {scenario_id}")
                continue
            if active_context.get("tenant_id") != ownership.get("tenant_id"):
                errors.append(f"VALID TENANT OWNERSHIP MUST MATCH {rel}: {scenario_id}")
            if membership.get("state") != "active":
                errors.append(f"VALID MEMBERSHIP MUST BE ACTIVE {rel}: {scenario_id}")
            if active_context.get("membership_id") != membership.get("membership_id"):
                errors.append(f"VALID CONTEXT MEMBERSHIP MUST MATCH {rel}: {scenario_id}")
            if active_context.get("principal_id") != membership.get("principal_id"):
                errors.append(f"VALID CONTEXT PRINCIPAL MUST MATCH {rel}: {scenario_id}")
            if active_context.get("tenant_id") != membership.get("tenant_id"):
                errors.append(f"VALID CONTEXT TENANT MUST MATCH {rel}: {scenario_id}")
            if active_context.get("status") != "active":
                errors.append(f"VALID CONTEXT MUST BE ACTIVE {rel}: {scenario_id}")
            if active_context.get("validation_source") not in TRUSTED_CONTEXT_SOURCES:
                errors.append(f"VALID CONTEXT MUST BE SERVER VALIDATED {rel}: {scenario_id}")
            issued_at = parse_rfc3339_datetime(active_context.get("issued_at", ""))
            expires_at = parse_rfc3339_datetime(active_context.get("expires_at", ""))
            if (
                issued_at is None
                or expires_at is None
                or evaluated_at is None
                or issued_at > evaluated_at
                or evaluated_at >= expires_at
            ):
                errors.append(f"VALID CONTEXT TIME WINDOW INVALID {rel}: {scenario_id}")
            valid_until = membership.get("valid_until")
            membership_expires = (
                parse_rfc3339_datetime(valid_until) if valid_until is not None else None
            )
            if valid_until is not None and (
                membership_expires is None
                or evaluated_at is None
                or evaluated_at >= membership_expires
            ):
                errors.append(f"VALID MEMBERSHIP LIFETIME INVALID {rel}: {scenario_id}")
            expected_context_claims = {
                "principal_id": active_context.get("principal_id"),
                "tenant_id": active_context.get("tenant_id"),
                "membership_id": membership.get("membership_id"),
                "membership_state": membership.get("state"),
                "validation_source": active_context.get("validation_source"),
            }
            if any(context.get(key) != value for key, value in expected_context_claims.items()):
                errors.append(f"VALID SCENARIO CONTEXT CLAIMS MUST MATCH {rel}: {scenario_id}")
            expected_resource_claims = {
                "tenant_id": ownership.get("tenant_id"),
                "resource_type": ownership.get("resource_type"),
                "resource_id": ownership.get("resource_id"),
            }
            if any(resource.get(key) != value for key, value in expected_resource_claims.items()):
                errors.append(f"VALID SCENARIO RESOURCE CLAIMS MUST MATCH {rel}: {scenario_id}")
        elif decision.get("decision") != "DENY":
            errors.append(f"NEGATIVE MULTITENANT SCENARIO MUST DENY {rel}: {scenario_id}")

    expected_reasons = {
        "MTD-002": "NO_ACTIVE_MEMBERSHIP",
        "MTD-003": "MEMBERSHIP_NOT_ACTIVE",
        "MTD-004": "CLIENT_TENANT_OVERRIDE_DENIED",
        "MTD-005": "MEMBERSHIP_TENANT_MISMATCH",
        "MTD-006": "CROSS_TENANT_ACCESS_DENIED",
        "MTD-007": "DATABASE_TENANT_POLICY_DENIED",
        "MTD-008": "ACTIVE_CONTEXT_EXPIRED",
        "MTD-009": "MEMBERSHIP_EXPIRED",
    }
    for scenario_id, reason in expected_reasons.items():
        if by_id[scenario_id].get("authorization_decision", {}).get("reason_code") != reason:
            errors.append(f"MULTITENANT DENIAL REASON INVALID {rel}: {scenario_id}")

    if resolved.get("MTD-002", {}).get("membership") is not None or resolved.get("MTD-002", {}).get("active_context") is not None:
        errors.append(f"MISSING MEMBERSHIP SCENARIO INVALID: {rel}")
    suspended = resolved.get("MTD-003", {}).get("membership")
    if not isinstance(suspended, dict) or suspended.get("state") != "suspended":
        errors.append(f"SUSPENDED MEMBERSHIP SCENARIO INVALID: {rel}")
    forged_claim = by_id["MTD-004"].get("context", {})
    server_context = resolved.get("MTD-004", {}).get("active_context")
    if (
        not isinstance(server_context, dict)
        or forged_claim.get("validation_source") != "client_input"
        or forged_claim.get("tenant_id") == server_context.get("tenant_id")
    ):
        errors.append(f"FORGED CONTEXT SCENARIO INVALID: {rel}")
    mismatch_membership = resolved.get("MTD-005", {}).get("membership")
    mismatch_context = resolved.get("MTD-005", {}).get("active_context")
    if (
        not isinstance(mismatch_membership, dict)
        or not isinstance(mismatch_context, dict)
        or mismatch_membership.get("tenant_id") == mismatch_context.get("tenant_id")
    ):
        errors.append(f"MEMBERSHIP TENANT MISMATCH SCENARIO INVALID: {rel}")

    cross_tenant_layers = {
        by_id[scenario_id].get("enforcement_layer")
        for scenario_id in ("MTD-006", "MTD-007")
        if isinstance(resolved.get(scenario_id, {}).get("active_context"), dict)
        and isinstance(resolved.get(scenario_id, {}).get("resource_ownership"), dict)
        and resolved[scenario_id]["active_context"].get("tenant_id")
        != resolved[scenario_id]["resource_ownership"].get("tenant_id")
        and by_id[scenario_id].get("authorization_decision", {}).get("decision") == "DENY"
    }
    if cross_tenant_layers != {"api", "database"}:
        errors.append(f"API AND DATABASE CROSS-TENANT DENIAL REQUIRED: {rel}")

    for scenario_id in ("MTD-006", "MTD-007"):
        scenario = by_id[scenario_id]
        active_context = resolved.get(scenario_id, {}).get("active_context")
        ownership = resolved.get(scenario_id, {}).get("resource_ownership")
        if not isinstance(active_context, dict) or not isinstance(ownership, dict):
            continue
        expected_context = {
            "principal_id": active_context.get("principal_id"),
            "tenant_id": active_context.get("tenant_id"),
            "membership_id": active_context.get("membership_id"),
            "validation_source": active_context.get("validation_source"),
        }
        expected_resource = {
            "tenant_id": ownership.get("tenant_id"),
            "resource_type": ownership.get("resource_type"),
            "resource_id": ownership.get("resource_id"),
        }
        scope = scenario.get("authorization_decision", {}).get("evaluated_scope", {})
        audit = scenario.get("audit_event", {})
        if any(scenario["context"].get(key) != value for key, value in expected_context.items()):
            errors.append(f"CROSS-TENANT CONTEXT CLAIMS MUST MATCH {rel}: {scenario_id}")
        if any(scenario["resource"].get(key) != value for key, value in expected_resource.items()):
            errors.append(f"CROSS-TENANT RESOURCE CLAIMS MUST MATCH {rel}: {scenario_id}")
        if not isinstance(scope, dict) or (
            scope.get("active_tenant_id") != active_context.get("tenant_id")
            or scope.get("resource_tenant_id") != ownership.get("tenant_id")
            or scope.get("enforcement_layer") != scenario.get("enforcement_layer")
        ):
            errors.append(f"CROSS-TENANT EVALUATED SCOPE MUST MATCH {rel}: {scenario_id}")
        if not isinstance(audit, dict) or (
            audit.get("tenant_id") != active_context.get("tenant_id")
            or audit.get("context_id") != active_context.get("context_id")
            or audit.get("context_tenant_id") != active_context.get("tenant_id")
            or audit.get("resource_tenant_id") != ownership.get("tenant_id")
        ):
            errors.append(f"CROSS-TENANT AUDIT ATTRIBUTION INVALID {rel}: {scenario_id}")

    expired_context = resolved.get("MTD-008", {}).get("active_context")
    expired_membership = resolved.get("MTD-009", {}).get("membership")
    if not isinstance(expired_context, dict) or evaluated_at is None or (
        (parse_rfc3339_datetime(expired_context.get("expires_at")) or evaluated_at) > evaluated_at
    ):
        errors.append(f"EXPIRED CONTEXT SCENARIO INVALID: {rel}")
    if not isinstance(expired_membership, dict) or evaluated_at is None or (
        (parse_rfc3339_datetime(expired_membership.get("valid_until")) or evaluated_at)
        > evaluated_at
    ):
        errors.append(f"EXPIRED MEMBERSHIP SCENARIO INVALID: {rel}")

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

        correlation_fields = {
            "correlation_id": "CORRELATION ID",
            "decision": "DECISION RESULT",
            "reason_code": "REASON CODE",
            "policy_version": "POLICY VERSION",
        }
        audit_keys = {"decision": "result"}
        for decision_key, label in correlation_fields.items():
            audit_key = audit_keys.get(decision_key, decision_key)
            if decision.get(decision_key) != audit_event.get(audit_key):
                errors.append(f"{label} MISMATCH: {prefix}")

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
