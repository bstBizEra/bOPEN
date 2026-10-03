#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from analyze_sql import analyze_text

TENANT_RULE_PREFIXES = ("BOPEN-TENANT-", "BOPEN-PRIV-", "BOPEN-FUNC-")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check bOPEN tenant-isolation and database security invariants")
    parser.add_argument("sql_file", type=Path)
    args = parser.parse_args()
    report = analyze_text(args.sql_file.read_text(encoding="utf-8"), "invariant-check")
    findings = [f for f in report["findings"] if f["rule_id"].startswith(TENANT_RULE_PREFIXES)]
    result = {"status": "BLOCK" if any(f["verdict"] in {"BLOCKED", "SECURITY_CRITICAL"} for f in findings) else "PASS", "findings": findings}
    print(json.dumps(result, indent=2))
    return 2 if result["status"] == "BLOCK" else 0


if __name__ == "__main__":
    sys.exit(main())
