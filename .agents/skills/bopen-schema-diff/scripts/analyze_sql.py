#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from common import STATUS_FOR_VERDICT, dump_json, max_verdict, redact, sha256_file

RULES = [
    ("BOPEN-SCHEMA-001", "critical", "DESTRUCTIVE", re.compile(r"\bDROP\s+TABLE\b", re.I), "Dropping a table may destroy data."),
    ("BOPEN-SCHEMA-002", "critical", "DESTRUCTIVE", re.compile(r"\bDROP\s+COLUMN\b", re.I), "Dropping a column may destroy data."),
    ("BOPEN-SCHEMA-003", "critical", "DESTRUCTIVE", re.compile(r"\bTRUNCATE\b", re.I), "TRUNCATE destroys table data."),
    ("BOPEN-SCHEMA-004", "high", "REVIEW_REQUIRED", re.compile(r"\bALTER\s+COLUMN\b[\s\S]{0,160}\bTYPE\b", re.I), "Column type changes require compatibility and data validation."),
    ("BOPEN-SCHEMA-005", "medium", "CONDITIONAL", re.compile(r"\bSET\s+NOT\s+NULL\b", re.I), "SET NOT NULL requires existing-data verification."),
    ("BOPEN-SCHEMA-006", "medium", "CONDITIONAL", re.compile(r"\bADD\s+(?:CONSTRAINT\s+\S+\s+)?FOREIGN\s+KEY\b", re.I), "Adding a foreign key can scan or lock existing data."),
    ("BOPEN-SCHEMA-007", "medium", "CONDITIONAL", re.compile(r"\bCREATE\s+(?!UNIQUE\s+)?INDEX\b(?![\s\S]{0,80}\bCONCURRENTLY\b)", re.I), "Non-concurrent index creation may block writes."),
    ("BOPEN-SCHEMA-008", "high", "REVIEW_REQUIRED", re.compile(r"\bRENAME\s+(?:COLUMN|TO)\b", re.I), "Renames require consumer compatibility coordination."),
    ("BOPEN-TENANT-001", "critical", "BLOCKED", re.compile(r"\bDISABLE\s+ROW\s+LEVEL\s+SECURITY\b", re.I), "Disabling RLS violates the tenant-isolation boundary."),
    ("BOPEN-TENANT-002", "critical", "SECURITY_CRITICAL", re.compile(r"\bNO\s+FORCE\s+ROW\s+LEVEL\s+SECURITY\b", re.I), "Removing FORCE RLS may let table owners bypass policies."),
    ("BOPEN-TENANT-003", "critical", "BLOCKED", re.compile(r"\bBYPASSRLS\b", re.I), "BYPASSRLS is prohibited for application principals."),
    ("BOPEN-PRIV-001", "critical", "SECURITY_CRITICAL", re.compile(r"\bGRANT\b[\s\S]{0,240}\bTO\s+PUBLIC\b", re.I), "Granting privileges to PUBLIC requires security review."),
    ("BOPEN-PRIV-002", "high", "SECURITY_CRITICAL", re.compile(r"\bALTER\s+TABLE\b[\s\S]{0,160}\bOWNER\s+TO\b", re.I), "Ownership changes can alter RLS enforcement."),
    ("BOPEN-FUNC-001", "high", "SECURITY_CRITICAL", re.compile(r"\bSECURITY\s+DEFINER\b", re.I), "SECURITY DEFINER functions require search_path and privilege review."),
]

CREATE_TABLE_RE = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>[\w\".]+)\s*\((?P<body>[\s\S]*?)\)\s*;", re.I)
CREATE_POLICY_RE = re.compile(r"CREATE\s+POLICY\s+(?P<policy>[\w\"]+)\s+ON\s+(?P<table>[\w\".]+)(?P<body>[\s\S]*?);", re.I)
ENABLE_RLS_RE = re.compile(r"ALTER\s+TABLE\s+(?P<table>[\w\".]+)\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY", re.I)
FORCE_RLS_RE = re.compile(r"ALTER\s+TABLE\s+(?P<table>[\w\".]+)\s+FORCE\s+ROW\s+LEVEL\s+SECURITY", re.I)
GLOBAL_TABLE_HINTS = {"tenants", "platforms", "schema_migrations", "countries", "currencies"}
TENANT_TABLE_HINT = re.compile(r"tenant|membership|workspace|project|resource|audit|outbox|entitlement|module|skill|agent|document", re.I)


def finding(rule_id: str, severity: str, verdict: str, message: str, evidence: str, object_name=None, line=None, actions=None):
    return {
        "id": f"F-{uuid.uuid4().hex[:12]}",
        "rule_id": rule_id,
        "severity": severity,
        "verdict": verdict,
        "message": message,
        "object": object_name,
        "line": line,
        "evidence": redact(evidence.strip())[:500],
        "required_actions": actions or [],
    }


def line_for(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def analyze_text(sql: str, request_id: str = "local-analysis") -> dict:
    findings = []
    changes = []

    for rule_id, severity, verdict, pattern, message in RULES:
        for match in pattern.finditer(sql):
            findings.append(finding(rule_id, severity, verdict, message, match.group(0), line=line_for(sql, match.start())))

    created_tables = {}
    for match in CREATE_TABLE_RE.finditer(sql):
        raw_name = match.group("name")
        name = raw_name.replace('"', '').split('.')[-1]
        body = match.group("body")
        created_tables[name] = body
        changes.append({
            "change_id": f"CH-{len(changes)+1:04d}",
            "object_type": "table",
            "operation": "create",
            "object": {"schema": raw_name.split('.')[0].replace('"','') if '.' in raw_name else "public", "table": None, "name": name},
            "before": None,
            "after": {"definition_excerpt": redact(body.strip())[:1000]},
            "classification": {"compatibility": "compatible", "data_risk": "low", "lock_risk": "low", "tenancy_risk": "unknown", "security_risk": "unknown"},
            "dependencies": [],
            "engine_findings": {"static": "detected"},
            "confidence": 0.75,
            "required_actions": [],
        })

        likely_tenant = bool(TENANT_TABLE_HINT.search(name)) and name.lower() not in GLOBAL_TABLE_HINTS
        has_tenant = re.search(r"\btenant_id\b", body, re.I)
        tenant_not_null = re.search(r"\btenant_id\b[^,\n]*\bNOT\s+NULL\b", body, re.I)
        has_tenant_fk = re.search(r"(?:FOREIGN\s+KEY\s*\(\s*tenant_id\s*\)|tenant_id[^,\n]*REFERENCES\s+[\w\".]*tenants)", body, re.I)
        if likely_tenant and not has_tenant:
            findings.append(finding("BOPEN-TENANT-010", "critical", "BLOCKED", "Likely tenant-owned table is missing tenant_id.", match.group(0), name, line_for(sql, match.start()), ["Classify the table explicitly or add a non-null tenant_id with an approved foreign key."]))
        elif likely_tenant and not tenant_not_null:
            findings.append(finding("BOPEN-TENANT-011", "critical", "SECURITY_CRITICAL", "tenant_id is absent or nullable on a likely tenant-owned table.", match.group(0), name, line_for(sql, match.start()), ["Make tenant_id NOT NULL after verified backfill."]))
        if likely_tenant and has_tenant and not has_tenant_fk:
            findings.append(finding("BOPEN-TENANT-012", "high", "SECURITY_CRITICAL", "tenant_id lacks an explicit foreign key to tenants.", match.group(0), name, line_for(sql, match.start()), ["Add and validate a tenant foreign key or document an approved exception."]))
        for unique in re.finditer(r"UNIQUE\s*\((?P<cols>[^)]*)\)", body, re.I):
            cols = unique.group("cols").lower()
            if likely_tenant and "tenant_id" not in cols:
                findings.append(finding("BOPEN-TENANT-013", "high", "SECURITY_CRITICAL", "Tenant-owned table has a unique constraint that is not tenant-scoped.", unique.group(0), name, line_for(sql, match.start()+unique.start()), ["Confirm global uniqueness or include tenant_id in the unique key."]))

    enabled = {m.group("table").replace('"','').split('.')[-1] for m in ENABLE_RLS_RE.finditer(sql)}
    forced = {m.group("table").replace('"','').split('.')[-1] for m in FORCE_RLS_RE.finditer(sql)}
    policies = {}
    for m in CREATE_POLICY_RE.finditer(sql):
        table = m.group("table").replace('"','').split('.')[-1]
        policies.setdefault(table, []).append(m.group("body"))

    for table in created_tables:
        likely_tenant = bool(TENANT_TABLE_HINT.search(table)) and table.lower() not in GLOBAL_TABLE_HINTS
        if likely_tenant:
            if table not in enabled:
                findings.append(finding("BOPEN-TENANT-014", "critical", "BLOCKED", "Likely tenant-owned table is created without enabling RLS in the reviewed SQL.", f"CREATE TABLE {table}", table, actions=["Enable RLS in the same controlled migration or provide linked evidence that it is already enforced."]))
            if table not in forced:
                findings.append(finding("BOPEN-TENANT-015", "high", "SECURITY_CRITICAL", "Likely tenant-owned table is created without FORCE ROW LEVEL SECURITY.", f"CREATE TABLE {table}", table, actions=["Evaluate and normally enable FORCE ROW LEVEL SECURITY."]))
            table_policies = policies.get(table, [])
            if not table_policies:
                findings.append(finding("BOPEN-TENANT-016", "critical", "BLOCKED", "Likely tenant-owned table has no RLS policy in the reviewed SQL.", f"CREATE TABLE {table}", table, actions=["Create explicit read and write policies with server-resolved tenant context."]))
            else:
                body = "\n".join(table_policies)
                if not re.search(r"\bUSING\s*\([^)]*tenant", body, re.I):
                    findings.append(finding("BOPEN-TENANT-017", "critical", "BLOCKED", "RLS policy lacks an explicit tenant USING predicate.", body, table))
                if not re.search(r"\bWITH\s+CHECK\s*\([^)]*tenant", body, re.I):
                    findings.append(finding("BOPEN-TENANT-018", "critical", "BLOCKED", "RLS policy lacks an explicit tenant WITH CHECK predicate.", body, table))

    # Detect ALTER TABLE ADD COLUMN with volatile-looking defaults.
    volatile_default = re.compile(r"ADD\s+COLUMN[\s\S]{0,240}\bDEFAULT\s+(?:clock_timestamp\s*\(|now\s*\(|random\s*\(|gen_random_uuid\s*\()", re.I)
    for m in volatile_default.finditer(sql):
        findings.append(finding("BOPEN-SCHEMA-009", "high", "REVIEW_REQUIRED", "Adding a column with a volatile default may rewrite or touch every row.", m.group(0), line=line_for(sql, m.start())))

    # Add canonical changes for obvious drop/alter operations.
    op_patterns = [
        ("table", "drop", re.compile(r"DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?([\w\".]+)", re.I)),
        ("column", "drop", re.compile(r"ALTER\s+TABLE\s+([\w\".]+)[\s\S]{0,100}?DROP\s+COLUMN\s+(?:IF\s+EXISTS\s+)?([\w\"]+)", re.I)),
        ("table", "alter", re.compile(r"ALTER\s+TABLE\s+([\w\".]+)", re.I)),
        ("policy", "create", re.compile(r"CREATE\s+POLICY\s+([\w\"]+)", re.I)),
    ]
    seen = set()
    for object_type, operation, pattern in op_patterns:
        for m in pattern.finditer(sql):
            name = m.group(m.lastindex or 1).replace('"','')
            key = (object_type, operation, name, m.start())
            if key in seen:
                continue
            seen.add(key)
            risky = operation == "drop"
            changes.append({
                "change_id": f"CH-{len(changes)+1:04d}",
                "object_type": object_type,
                "operation": operation,
                "object": {"schema": None, "table": None, "name": name},
                "before": None,
                "after": None,
                "classification": {
                    "compatibility": "breaking" if risky else "potentially_breaking",
                    "data_risk": "critical" if risky else "medium",
                    "lock_risk": "high" if object_type == "table" else "medium",
                    "tenancy_risk": "unknown",
                    "security_risk": "unknown",
                },
                "dependencies": [],
                "engine_findings": {"static": "detected"},
                "confidence": 0.7,
                "required_actions": [],
            })

    verdict = max_verdict([f["verdict"] for f in findings])
    status = STATUS_FOR_VERDICT[verdict]
    actions = []
    for f in findings:
        for action in f["required_actions"]:
            if action not in actions:
                actions.append(action)
    summary = f"Detected {len(changes)} canonical change(s) and {len(findings)} policy finding(s)."
    return {
        "request_id": request_id,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "verdict": verdict,
        "summary": summary,
        "comparison": {"mode": "migration_review", "direction": "source_to_target", "analyzer": "static-sql"},
        "changes": changes,
        "findings": findings,
        "required_actions": actions,
        "tool_versions": {"bopen-static-analyzer": "0.1.0"},
        "evidence": None,
        "limitations": [
            "Static analysis is conservative and does not validate runtime data or full PostgreSQL dependency semantics.",
            "Use a deterministic schema engine and independent review for deployment decisions.",
        ],
    }


def to_markdown(report: dict, source: Path) -> str:
    lines = [
        "# bOPEN Schema Difference Assessment",
        "",
        f"- Source: `{source}`",
        f"- Source SHA-256: `{sha256_file(source)}`",
        f"- Status: **{report['status']}**",
        f"- Verdict: **{report['verdict']}**",
        f"- Generated: {report['generated_at']}",
        "",
        "## Summary",
        "",
        report["summary"],
        "",
        "## Findings",
        "",
        "| Rule | Severity | Verdict | Object | Line | Finding |",
        "|---|---|---|---|---:|---|",
    ]
    for f in report["findings"]:
        msg = f["message"].replace("|", "\\|")
        lines.append(f"| {f['rule_id']} | {f['severity']} | {f['verdict']} | {f.get('object') or ''} | {f.get('line') or ''} | {msg} |")
    if not report["findings"]:
        lines.append("| — | — | SAFE | — | — | No static policy finding |")
    lines += ["", "## Required actions", ""]
    if report["required_actions"]:
        lines.extend([f"- {a}" for a in report["required_actions"]])
    else:
        lines.append("- None from static analysis.")
    lines += ["", "## Limitations", ""] + [f"- {x}" for x in report["limitations"]]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Conservative static analyzer for bOPEN PostgreSQL migration SQL")
    parser.add_argument("sql_file", type=Path)
    parser.add_argument("--request-id", default="local-analysis")
    parser.add_argument("--json", dest="json_out", type=Path)
    parser.add_argument("--markdown", dest="md_out", type=Path)
    args = parser.parse_args()
    if not args.sql_file.is_file():
        parser.error(f"SQL file not found: {args.sql_file}")
    sql = args.sql_file.read_text(encoding="utf-8")
    report = analyze_text(sql, args.request_id)
    if args.json_out:
        dump_json(args.json_out, report)
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(to_markdown(report, args.sql_file), encoding="utf-8")
    if not args.json_out and not args.md_out:
        print(json.dumps(report, indent=2))
    return 2 if report["status"] == "BLOCK" else 1 if report["status"] == "REVIEW" else 0


if __name__ == "__main__":
    sys.exit(main())
