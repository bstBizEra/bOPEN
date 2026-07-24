#!/usr/bin/env python3
"""Generate a deterministic document manifest or an immutable candidate snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path("docs/DOCUMENT-MANIFEST.json")
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml"}


def canonical_document_bytes(path: Path) -> tuple[bytes, str]:
    """Return platform-independent bytes for governed UTF-8 text documents."""
    data = path.read_bytes()
    if path.suffix not in TEXT_SUFFIXES:
        return data, ""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data, ""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.encode("utf-8"), normalized


def build_manifest(output: Path, root: Path = ROOT) -> dict:
    records = []
    resolved_output = output if output.is_absolute() else root / output
    document_paths = sorted(
        (root / "docs").rglob("*"),
        key=lambda candidate: candidate.relative_to(root).as_posix(),
    )
    for path in document_paths:
        if not path.is_file() or path.name == "DOCUMENT-MANIFEST.json" or path.resolve() == resolved_output.resolve():
            continue
        data, text = canonical_document_bytes(path)
        title = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), "")
        match = re.search(r"\*\*Status:\*\*\s*([^\n]+)", text)
        records.append(
            {
                "path": str(path.relative_to(root)).replace("\\", "/"),
                "title": title,
                "status": match.group(1).strip() if match else "",
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
        )
    return {
        "generated": datetime.now(timezone.utc).date().isoformat(),
        "count": len(records),
        "documents": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="Verify output without rewriting it.")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    manifest = build_manifest(args.output)
    rendered = json.dumps(manifest, indent=2) + "\n"
    if args.check:
        try:
            actual = output.read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"ERROR: manifest snapshot missing: {output}")
            return 1
        # Reproducibility: `generated` is a human-facing date stamp, not content.
        # Adopt the committed value before comparing so a byte-frozen candidate
        # does not go stale at UTC-midnight rollover. Genuine content drift
        # (paths, titles, statuses, sha256, bytes, count) still fails the check.
        try:
            committed_generated = json.loads(actual).get("generated")
        except json.JSONDecodeError:
            committed_generated = None
        if committed_generated is not None:
            manifest["generated"] = committed_generated
            rendered = json.dumps(manifest, indent=2) + "\n"
        if actual != rendered:
            print(f"ERROR: manifest snapshot stale: {output}")
            return 1
        print(f"Manifest snapshot current: {output} ({manifest['count']} records)")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"Wrote {manifest['count']} records to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
