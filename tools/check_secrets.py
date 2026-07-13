#!/usr/bin/env python3
"""Fail when repository text contains common credential material."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {".git", "node_modules", "__pycache__"}
TEXT_SUFFIXES = {
    "",
    ".env",
    ".json",
    ".log",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

PATTERNS = (
    (
        "private key",
        re.compile("-----BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
    ("AWS access key", re.compile("AKIA" + r"[0-9A-Z]{16}")),
    (
        "assigned credential",
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)"
            r"\s*[:=]\s*['\"]?[A-Za-z0-9_+/.=-]{16,}"
        ),
    ),
)


def scan_text(text: str) -> list[str]:
    return [name for name, pattern in PATTERNS if pattern.search(text)]


def candidate_files(root: Path) -> list[Path]:
    return [
        path
        for path in root.rglob("*")
        if path.is_file()
        and not any(part in IGNORED_PARTS for part in path.parts)
        and (path.suffix.lower() in TEXT_SUFFIXES or path.name == ".env.example")
    ]


def scan_repository(root: Path = ROOT) -> list[str]:
    violations: list[str] = []
    for path in candidate_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for finding in scan_text(text):
            violations.append(f"{path.relative_to(root)}: {finding}")
    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    scan_root = args.root.resolve()
    files = candidate_files(scan_root)
    violations = scan_repository(scan_root)
    if args.receipt:
        receipt = {
            "schema_version": "1.0",
            "scanner": "tools/check_secrets.py",
            "scanner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "scope": str(scan_root),
            "files_scanned": len(files),
            "finding_count": len(violations),
            "status": "PASS" if not violations else "FAIL",
        }
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    if violations:
        print("Secret scan: FAIL")
        for violation in violations:
            print(f"- {violation}")
        return 1
    print("Secret scan: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
