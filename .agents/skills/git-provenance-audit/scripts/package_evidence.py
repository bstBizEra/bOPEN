#!/usr/bin/env python3
"""Create a deterministic checksum manifest for a provenance audit directory."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    audit_dir = args.audit_dir.expanduser().resolve()
    schema_path = args.schema.expanduser().resolve()
    output = (args.output or (audit_dir / "audit-manifest.json")).expanduser().resolve()
    if not audit_dir.is_dir():
        parser.error("--audit-dir must be a directory")
    if not schema_path.is_file():
        parser.error("--schema must be a file")

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    required = {"schema_version", "generated_at_utc", "files", "checksum_root_sha256"}
    if set(schema.get("required", [])) != required:
        parser.error("manifest schema has unexpected required fields")

    audit_path = audit_dir / "audit.json"
    findings_path = audit_dir / "findings.json"
    if not audit_path.is_file() or not findings_path.is_file():
        parser.error("audit.json and findings.json are required")
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    findings = json.loads(findings_path.read_text(encoding="utf-8"))
    if not isinstance(findings, list):
        parser.error("findings.json must contain an array")

    files = []
    for path in sorted(item for item in audit_dir.rglob("*") if item.is_file() and item.resolve() != output):
        relative = path.relative_to(audit_dir).as_posix()
        files.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)})
    root_material = "".join(f"{item['path']}\0{item['sha256']}\n" for item in files).encode("utf-8")
    manifest = {
        "schema_version": "1.0.0",
        "generated_at_utc": audit["observed_at_utc"],
        "files": files,
        "checksum_root_sha256": hashlib.sha256(root_material).hexdigest(),
    }
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"manifest": str(output), "checksum_root_sha256": manifest["checksum_root_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
