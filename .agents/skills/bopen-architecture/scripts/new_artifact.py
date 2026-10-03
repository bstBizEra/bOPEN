#!/usr/bin/env python3
"""Create a bOPEN architecture artifact from a bundled template."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = {
    "research-report": "assets/architecture-research-template.md",
    "architecture-design": "assets/architecture-design-template.md",
    "adr": "assets/adr-template.md",
    "conformance-review": "assets/conformance-review-template.md",
    "implementation-control": "assets/implementation-control-template.md",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=sorted(TEMPLATES), required=True)
    parser.add_argument("--id", required=True, dest="artifact_id")
    parser.add_argument("--title", required=True)
    parser.add_argument("--owner", default="bOPEN Architecture Authority")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.output.exists() and not args.force:
        parser.error(f"Output exists: {args.output}. Use --force to replace it.")

    template_path = ROOT / TEMPLATES[args.type]
    text = template_path.read_text(encoding="utf-8")
    replacements = {
        "{{ARTIFACT_ID}}": args.artifact_id,
        "{{TITLE}}": args.title,
        "{{OWNER}}": args.owner,
        "{{DATE}}": args.date,
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8", newline="\n")
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
