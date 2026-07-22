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
    args = parser.parse_args()

    output = args.output.resolve()
    workspace = ROOT.parents[2].resolve()
    try:
        output.relative_to(workspace)
    except ValueError:
        parser.error(f"Output must remain inside the current workspace: {workspace}")
    if output.exists():
        parser.error(f"Refusing to overwrite existing output: {output}")

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

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
