#!/usr/bin/env python3
"""Fail-closed semantic validation for the non-executing G3 research design."""
from __future__ import annotations

import json
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "research/sources/boxyhq-g3-runtime-design.json"
DEFAULT_SCHEMA = ROOT / "research/sources/boxyhq-g3-runtime-design.schema.json"
DEFAULT_REPORT = ROOT / "artifacts/validation/research-g3-design-readiness.md"
RESEARCH_ROOT = ROOT / "docs/resources/open-source-research/BOPEN-RES-001"
ARTIFACT_INVENTORY = RESEARCH_ROOT / "ARTIFACT-INVENTORY.json"
EXPECTED_PIN = "abc9b686823cbfb4973c79bc36fea37a3244be6c"
EXPECTED_FAMILIES = 19
EXPECTED_CASES = 126
EXPECTED_SCHEMA_DIGEST = "a5ef07fbfbacc518da5e8bb8e3b17ea38f619f795798b3c9158a471b9a9e1e7f"
EXPECTED_CATALOG_DIGEST = "02db3ddca42a892e920345f5cdfcda44398e5ec1f71829afe682e3827b0194da"
ALLOWED_DECISIONS = {"ALLOW", "DENY", "ERROR_ROLLED_BACK", "ERROR_PARTIAL", "UNOBSERVABLE"}


def load_contract(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid contract JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("contract root must be an object")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _type_matches(value: object, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "null": value is None,
    }.get(expected, True)


def validate_against_schema(value: object, rule: object, root_schema: dict, path: str = "$") -> list[str]:
    """Validate the JSON-Schema vocabulary used by this closed contract."""
    if not isinstance(rule, dict):
        return []
    if "$ref" in rule:
        ref = rule["$ref"]
        if not isinstance(ref, str) or not ref.startswith("#/"):
            return [f"{path}: only local schema references are permitted"]
        target: object = root_schema
        for token in ref[2:].split("/"):
            if not isinstance(target, dict) or token not in target:
                return [f"{path}: unresolved schema reference {ref}"]
            target = target[token]
        return validate_against_schema(value, target, root_schema, path)
    errors: list[str] = []
    if "const" in rule and value != rule["const"]:
        errors.append(f"{path}: must equal {rule['const']!r}")
    if "enum" in rule and value not in rule["enum"]:
        errors.append(f"{path}: must be one of {rule['enum']!r}")
    expected_type = rule.get("type")
    if isinstance(expected_type, str) and not _type_matches(value, expected_type):
        return errors + [f"{path}: must have type {expected_type}"]
    if isinstance(value, str):
        if len(value) < rule.get("minLength", 0):
            errors.append(f"{path}: string is shorter than minLength")
        if "pattern" in rule and re.fullmatch(rule["pattern"], value) is None:
            errors.append(f"{path}: does not match required pattern")
        if rule.get("format") == "date" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
            errors.append(f"{path}: must use YYYY-MM-DD date format")
    if isinstance(value, dict):
        properties = rule.get("properties", {})
        for key in rule.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required property {key}")
        if rule.get("additionalProperties") is False:
            for key in value.keys() - properties.keys():
                errors.append(f"{path}: unexpected property {key}")
        for key, child in properties.items():
            if key in value:
                errors.extend(validate_against_schema(value[key], child, root_schema, f"{path}.{key}"))
    if isinstance(value, list):
        if len(value) < rule.get("minItems", 0):
            errors.append(f"{path}: has fewer than minItems")
        if "maxItems" in rule and len(value) > rule["maxItems"]:
            errors.append(f"{path}: has more than maxItems")
        if rule.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in value}) != len(value):
            errors.append(f"{path}: items must be unique")
        prefix = rule.get("prefixItems", [])
        for index, child in enumerate(prefix):
            if index < len(value):
                errors.extend(validate_against_schema(value[index], child, root_schema, f"{path}[{index}]"))
        items = rule.get("items")
        if items is False and len(value) > len(prefix):
            errors.append(f"{path}: additional array items are prohibited")
        elif isinstance(items, dict):
            start = len(prefix) if prefix else 0
            for index in range(start, len(value)):
                errors.extend(validate_against_schema(value[index], items, root_schema, f"{path}[{index}]"))
    return errors


def validate(data: dict) -> list[str]:
    errors: list[str] = []
    authority = data.get("authority", {})
    expected_authority = {
        "research_design_authorized": True,
        "runtime_execution_authorized": False,
        "implementation_authority": False,
        "production_authority": False,
        "gate_promotion_authority": False,
    }
    if authority != expected_authority:
        errors.append("authority must permit design only and deny runtime, implementation, production and promotion")

    gate = data.get("gate_state", {})
    expected_gate = {"gate": "G3", "status": "OPEN", "runtime_executed": False, "g3_pass": False, "decision": "DEFERRED"}
    for key, expected in expected_gate.items():
        if gate.get(key) != expected:
            errors.append(f"gate_state.{key} must equal {expected!r}")

    source = data.get("source_binding", {})
    if source.get("commit") != EXPECTED_PIN:
        errors.append("source binding must use the approved exact upstream pin")
    for key in ("license_sha256", "lock_sha256", "r1_contract_sha256"):
        if not re.fullmatch(r"[a-f0-9]{64}", str(source.get(key, ""))):
            errors.append(f"source_binding.{key} must be a SHA-256")

    safety = data.get("safety", {})
    for key in (
        "synthetic_data_only", "production_credentials_prohibited", "upstream_mutation_prohibited",
        "bopen_production_mutation_prohibited", "external_network_prohibited", "secret_scan_required",
        "redaction_required", "mutable_dependencies_prohibited",
    ):
        if safety.get(key) is not True:
            errors.append(f"safety.{key} must be true")

    substitutes = data.get("substitutes", [])
    substitute_ids = {item.get("id") for item in substitutes if isinstance(item, dict)}
    for item in substitutes:
        if not isinstance(item, dict):
            errors.append("every substitute must be an object")
            continue
        if item.get("local_only") is not True or item.get("network_access") != "deny-except-declared-local-substitutes":
            errors.append(f"substitute {item.get('id')} must be local-only with deny-by-default networking")
        if item.get("immutable_runtime_required") is not True or item.get("digest_status") not in {"pending-authority", "pinned"}:
            errors.append(f"substitute {item.get('id')} must require an immutable runtime identity")

    families = data.get("case_families", [])
    if len(families) != EXPECTED_FAMILIES:
        errors.append(f"case family census must equal {EXPECTED_FAMILIES}")
    family_ids: list[str] = []
    case_ids: list[str] = []
    reason_codes = {item.get("code"): item.get("decision") for item in data.get("reason_codes", []) if isinstance(item, dict)}
    for family in families:
        if not isinstance(family, dict):
            errors.append("every case family must be an object")
            continue
        family_id = str(family.get("family_id", "<missing>"))
        family_ids.append(family_id)
        if family.get("mandatory") is not True:
            errors.append(f"{family_id} must remain mandatory")
        stable = family.get("stable_case_ids", [])
        oracle = family.get("secure_oracles", [])
        oracle_ids = [item.get("case_id") for item in oracle if isinstance(item, dict)]
        if stable != oracle_ids:
            errors.append(f"{family_id} stable case IDs must exactly match secure oracle IDs and order")
        case_ids.extend(stable)
        observed = family.get("observed_upstream", {})
        if observed != {"executed": False, "decision": None, "reason_code": None, "http_status": None, "conformance": "NOT_EXECUTED", "receipt_sha256": None}:
            errors.append(f"{family_id} must preserve a distinct, unexecuted upstream observation")
        missing_substitutes = set(family.get("required_substitutes", [])) - substitute_ids
        if missing_substitutes:
            errors.append(f"{family_id} references unknown substitutes: {sorted(missing_substitutes)}")
        for item in oracle:
            if item.get("decision") not in ALLOWED_DECISIONS:
                errors.append(f"{family_id} has an invalid oracle decision")
            if item.get("reason_code") not in reason_codes:
                errors.append(f"{family_id} references an undeclared reason code")
            elif reason_codes[item.get("reason_code")] != item.get("decision"):
                errors.append(f"{family_id} oracle decision conflicts with its reason-code decision")
        assertions = family.get("assertions", {})
        for surface in ("database", "api", "session", "event", "audit"):
            if not assertions.get(surface):
                errors.append(f"{family_id} requires non-empty {surface} assertions")

    if len(family_ids) != len(set(family_ids)):
        errors.append("case family IDs must be unique")
    if len(case_ids) != EXPECTED_CASES:
        errors.append(f"stable case census must equal {EXPECTED_CASES}")
    if len(case_ids) != len(set(case_ids)):
        errors.append("stable case IDs must be globally unique")
    catalog = [
        {key: family.get(key) for key in ("family_id", "work_packages", "evidence_target", "source_evidence_ids", "stable_case_ids", "secure_oracles")}
        for family in families if isinstance(family, dict)
    ]
    if canonical_digest(catalog) != EXPECTED_CATALOG_DIGEST:
        errors.append("required family/case/oracle catalog differs from the independently reviewed exact catalog")

    reproduction = data.get("independent_reproduction", {})
    if reproduction.get("operator_count") != 2 or reproduction.get("distinct_operator_ids") is not True or reproduction.get("self_acceptance_prohibited") is not True:
        errors.append("independent reproduction must require two distinct operators and prohibit self-acceptance")
    prerequisites = data.get("execution_prerequisites", [])
    if not prerequisites or any(item.get("blocking") is not True or item.get("status") not in {"pending-authority", "pending-evidence"} for item in prerequisites):
        errors.append("every runtime prerequisite must remain blocking and pending authority or evidence")
    retention = data.get("retention", {})
    if retention.get("repository_storage") != "prohibited" or retention.get("sanitized_receipts_only") is not True:
        errors.append("retention must prohibit raw repository storage and allow sanitized receipts only")
    for reference in data.get("research_references", []):
        ref_path = ROOT / str(reference.get("path", ""))
        if not ref_path.is_file():
            errors.append(f"research reference does not exist: {reference.get('path')}")
            continue
        try:
            if ref_path.suffix.lower() == ".json":
                referenced = load_contract(ref_path)
                actual_version = str(referenced.get("version", ""))
                actual_status = str(referenced.get("status", ""))
            else:
                text = ref_path.read_text(encoding="utf-8")
                version_match = re.search(r"\*\*Version:\*\*\s*([^\r\n]+)", text)
                status_match = re.search(r"\*\*Status:\*\*\s*([^\r\n]+)", text)
                actual_version = version_match.group(1).strip() if version_match else ""
                actual_status = status_match.group(1).strip() if status_match else ""
            declared_version = str(reference.get("version", ""))
            normalized_actual_version = actual_version or "unversioned"
            if normalized_actual_version.casefold() != declared_version.casefold():
                errors.append(f"research reference version mismatch: {reference.get('path')}")
            if actual_status.casefold() != str(reference.get("status", "")).casefold():
                errors.append(f"research reference status mismatch: {reference.get('path')}")
        except (OSError, ValueError) as exc:
            errors.append(f"research reference cannot be verified: {reference.get('path')}: {exc}")
    r1_path = ROOT / str(source.get("r1_contract_path", ""))
    if not r1_path.is_file() or sha256(r1_path) != source.get("r1_contract_sha256"):
        errors.append("source_binding.r1_contract_sha256 must match the in-repository R1 contract")
    return errors


def validate_schema(schema: dict) -> list[str]:
    errors: list[str] = []
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("design schema must declare JSON Schema draft 2020-12")
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        errors.append("design schema root must be a closed object")
    if schema.get("properties", {}).get("contract_id", {}).get("const") != "BOX-R3-G3-DESIGN-001":
        errors.append("design schema must bind the canonical contract ID")
    if canonical_digest(schema) != EXPECTED_SCHEMA_DIGEST:
        errors.append("design schema differs from the independently reviewed exact schema")
    return errors


def validate_all(data: dict, schema: dict) -> list[str]:
    return validate_schema(schema) + validate_against_schema(data, schema, schema) + validate(data)


def render_report(data: dict) -> str:
    family_count = len(data["case_families"])
    case_count = sum(len(item["stable_case_ids"]) for item in data["case_families"])
    return f"""# G3 Research Design Readiness Report

**Status:** DESIGN_READY_FOR_AUTHORITY_REVIEW

**Artifact:** BOPEN-RES-001-G3-DESIGN

**Work packages:** RES-P0-05, RES-P0-06, RES-P0-07

**Source pin:** `{data['source_binding']['commit']}`

**Contract SHA-256:** `{sha256(DEFAULT_CONTRACT)}`

**Schema SHA-256:** `{sha256(DEFAULT_SCHEMA)}`

**Validator SHA-256:** `{sha256(Path(__file__).resolve())}`

## Census

- Mandatory case families: {family_count}
- Stable cases: {case_count}
- Required runtime operators: {data['independent_reproduction']['operator_count']}
- Blocking runtime prerequisites: {len(data['execution_prerequisites'])}

## Gate state

- Runtime executed: `false`
- G3 passed: `false`
- Production implementation authorized: `false`
- Gate decision: `DEFERRED`

This report validates a non-executing design only. DEC-0011 is proposed and not effective. It is not E3/E4 runtime evidence, a G3 gate decision, implementation authority, or production authority.
"""


def validate_report_integrity(data: dict) -> list[str]:
    if not DEFAULT_REPORT.is_file():
        return ["tracked readiness report is missing"]
    if DEFAULT_REPORT.read_text(encoding="utf-8") != render_report(data):
        return ["tracked readiness report does not match deterministic generator output"]
    return []


def build_research_inventory(data: dict) -> dict:
    files = []
    for path in sorted(RESEARCH_ROOT.rglob("*")):
        if not path.is_file() or path == ARTIFACT_INVENTORY:
            continue
        raw = path.read_bytes()
        if path.suffix.lower() in {".md", ".json", ".yaml", ".yml", ".ps1", ".sh", ".txt"}:
            raw = raw.replace(b"\r\n", b"\n")
        files.append({
            "path": path.relative_to(RESEARCH_ROOT).as_posix(),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        })
    return {"generated_on": data["issued_at"], "files": files}


def validate_inventory_integrity(data: dict) -> list[str]:
    try:
        actual = load_contract(ARTIFACT_INVENTORY)
    except ValueError as exc:
        return [f"research artifact inventory invalid: {exc}"]
    if actual != build_research_inventory(data):
        return ["research artifact inventory is stale or incomplete"]
    return []


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    path = Path(args[0]).resolve() if args else DEFAULT_CONTRACT
    try:
        data = load_contract(path)
        schema = load_contract(DEFAULT_SCHEMA)
        errors = validate_all(data, schema) + validate_report_integrity(data) + validate_inventory_integrity(data)
    except ValueError as exc:
        errors = [str(exc)]
        data = {}
    if errors:
        print("bOPEN G3 research design validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    case_count = sum(len(item["stable_case_ids"]) for item in data["case_families"])
    print("bOPEN G3 research design validation: PASS")
    print(f"Checked {len(data['case_families'])} mandatory families and {case_count} stable cases.")
    print("State: DESIGN_READY_FOR_AUTHORITY_REVIEW; runtime=false; G3=false; production=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
