#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def normalize(sql: str, engine: str) -> list[dict]:
    changes = []
    patterns = [
        ("table", "create", re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w\".]+)", re.I)),
        ("table", "drop", re.compile(r"DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?([\w\".]+)", re.I)),
        ("table", "alter", re.compile(r"ALTER\s+TABLE\s+([\w\".]+)", re.I)),
        ("index", "create", re.compile(r"CREATE\s+(?:UNIQUE\s+)?INDEX(?:\s+CONCURRENTLY)?\s+([\w\"]+)", re.I)),
        ("policy", "create", re.compile(r"CREATE\s+POLICY\s+([\w\"]+)", re.I)),
        ("policy", "drop", re.compile(r"DROP\s+POLICY\s+(?:IF\s+EXISTS\s+)?([\w\"]+)", re.I)),
    ]
    for object_type, operation, pattern in patterns:
        for m in pattern.finditer(sql):
            full = m.group(1).replace('"','')
            schema, name = (full.rsplit('.',1) if '.' in full else (None, full))
            risky = operation == "drop"
            changes.append({
                "change_id": f"{engine.upper()}-{len(changes)+1:04d}",
                "object_type": object_type,
                "operation": operation,
                "object": {"schema": schema, "table": None, "name": name},
                "before": None,
                "after": None,
                "classification": {
                    "compatibility": "breaking" if risky else "potentially_breaking",
                    "data_risk": "high" if risky else "unknown",
                    "lock_risk": "high" if object_type == "table" else "unknown",
                    "tenancy_risk": "unknown",
                    "security_risk": "unknown",
                },
                "dependencies": [],
                "engine_findings": {engine: "detected"},
                "confidence": 0.65,
                "required_actions": ["Review the preserved raw engine output."],
            })
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize SQL plan output into bOPEN canonical changes")
    parser.add_argument("input", type=Path)
    parser.add_argument("--engine", choices=["atlas", "pg-schema-diff", "prisma", "unknown"], required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = normalize(args.input.read_text(encoding="utf-8"), args.engine)
    text = json.dumps(data, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
