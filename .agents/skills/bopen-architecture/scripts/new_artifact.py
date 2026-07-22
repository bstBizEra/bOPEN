#!/usr/bin/env python3
"""Create a bOPEN architecture artifact from a bundled template."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[2].resolve()
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
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Existing, separately authorized output directory inside the workspace",
    )
    parser.add_argument("--output", type=Path, required=True, help="Relative path beneath --output-dir")
    args = parser.parse_args()

    if args.output.is_absolute():
        parser.error("--output must be relative to --output-dir")
    if not args.output_dir.exists() or not args.output_dir.is_dir() or args.output_dir.is_symlink():
        parser.error("--output-dir must be an existing, non-symlink directory")

    output_dir = args.output_dir.resolve(strict=True)
    try:
        output_dir.relative_to(WORKSPACE)
    except ValueError:
        parser.error(f"--output-dir must remain inside the current workspace: {WORKSPACE}")
    try:
        output_dir.relative_to(ROOT)
    except ValueError:
        pass
    else:
        parser.error("--output-dir must be outside the immutable skill package tree")

    output = (output_dir / args.output).resolve()
    try:
        output.relative_to(output_dir)
    except ValueError:
        parser.error("--output escapes --output-dir")
    if output.exists() or output.is_symlink():
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
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
