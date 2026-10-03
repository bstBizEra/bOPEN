#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def render(data: dict) -> str:
    lines = [
        "# bOPEN Schema Difference Assessment",
        "",
        f"**Status:** {data.get('status','UNKNOWN')}  ",
        f"**Verdict:** {data.get('verdict','UNKNOWN')}  ",
        f"**Generated:** {data.get('generated_at','')}  ",
        "",
        "## Summary",
        "",
        data.get("summary", ""),
        "",
        "## Findings",
        "",
        "| Rule | Severity | Verdict | Object | Finding |",
        "|---|---|---|---|---|",
    ]
    for item in data.get("findings", []):
        lines.append(f"| {item.get('rule_id','')} | {item.get('severity','')} | {item.get('verdict','')} | {item.get('object') or ''} | {item.get('message','').replace('|','\\|')} |")
    if not data.get("findings"):
        lines.append("| — | — | SAFE | — | No findings |")
    lines.extend(["", "## Required actions", ""])
    lines.extend([f"- {a}" for a in data.get("required_actions", [])] or ["- None recorded."])
    lines.extend(["", "## Limitations", ""])
    lines.extend([f"- {a}" for a in data.get("limitations", [])] or ["- None recorded."])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    args.output.write_text(render(data), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
