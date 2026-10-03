#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from analyze_sql import analyze_text

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    cases_doc = yaml.safe_load((ROOT / "evals/cases.yaml").read_text(encoding="utf-8"))
    security_doc = yaml.safe_load((ROOT / "evals/security-cases.yaml").read_text(encoding="utf-8"))
    cases = cases_doc["cases"] + security_doc["cases"]
    case_schema = json.loads((ROOT / "schemas/evaluation-case.schema.json").read_text(encoding="utf-8"))
    output_schema = json.loads((ROOT / "schemas/output.schema.json").read_text(encoding="utf-8"))
    change_schema = json.loads((ROOT / "schemas/canonical-change.schema.json").read_text(encoding="utf-8"))
    finding_schema = json.loads((ROOT / "schemas/risk-finding.schema.json").read_text(encoding="utf-8"))
    results = []
    for case in cases:
        schema_errors = list(Draft202012Validator(case_schema).iter_errors(case))
        if schema_errors:
            results.append({"id": case.get("id", "unknown"), "passed": False, "errors": [e.message for e in schema_errors]})
            continue
        fixture = ROOT / case["fixture"]
        report = analyze_text(fixture.read_text(encoding="utf-8"), case["id"])
        output_errors = list(Draft202012Validator(output_schema).iter_errors(report))
        for item in report.get("changes", []):
            output_errors.extend(Draft202012Validator(change_schema).iter_errors(item))
        for item in report.get("findings", []):
            output_errors.extend(Draft202012Validator(finding_schema).iter_errors(item))
        rules = {f["rule_id"] for f in report["findings"]}
        errors = []
        if report["status"] != case["expected_status"]:
            errors.append(f"status {report['status']} != {case['expected_status']}")
        if report["verdict"] != case["expected_verdict"]:
            errors.append(f"verdict {report['verdict']} != {case['expected_verdict']}")
        missing = sorted(set(case["required_rules"]) - rules)
        forbidden = sorted(set(case.get("forbidden_rules", [])) & rules)
        if missing:
            errors.append(f"missing rules: {missing}")
        if forbidden:
            errors.append(f"forbidden rules present: {forbidden}")
        if output_errors:
            errors.append("output schema errors: " + "; ".join(e.message for e in output_errors))
        results.append({"id": case["id"], "passed": not errors, "status": report["status"], "verdict": report["verdict"], "rules": sorted(rules), "errors": errors})
    passed = sum(1 for r in results if r["passed"])
    payload = {"package": "bopen-schema-diff", "version": "0.1.0", "total": len(results), "passed": passed, "failed": len(results)-passed, "results": results}
    out = ROOT.parent / "bopen-schema-diff-static-eval-report.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 1 if passed != len(results) else 0


if __name__ == "__main__":
    sys.exit(main())
