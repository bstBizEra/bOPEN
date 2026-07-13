#!/usr/bin/env python3
"""Pure validation helpers for Research Sprint R0 receipts and paths."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PIN_PATH = ROOT / "research/sources/boxyhq-upstream-pin.json"


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def validate_paths(
    target: Path, evidence_root: Path, approved_root: Path, repository_root: Path = ROOT
) -> list[str]:
    errors: list[str] = []
    for label, path in (("target", target), ("evidence", evidence_root)):
        if not is_within(path, approved_root):
            errors.append(f"{label} escapes approved research root")
        if is_within(path, repository_root):
            errors.append(f"{label} enters bOPEN worktree")
    if target.resolve() == evidence_root.resolve():
        errors.append("target and evidence roots must be separate")
    return errors


def validate_provenance(record: dict, pin: dict) -> list[str]:
    expected = {
        "source_id": pin["source_id"],
        "repository": pin["repository_url"],
        "pinned_commit": pin["commit"],
        "actual_commit": pin["commit"],
        "license_sha256": pin["license_sha256"],
        "lockfile": pin["lockfile"],
        "lock_sha256": pin["lock_sha256"],
        "credential_prompting": "disabled",
    }
    return [f"provenance mismatch: {key}" for key, value in expected.items() if record.get(key) != value]


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    paths = subparsers.add_parser("paths")
    paths.add_argument("--target", type=Path, required=True)
    paths.add_argument("--evidence-root", type=Path, required=True)
    paths.add_argument("--approved-root", type=Path, required=True)
    metadata = subparsers.add_parser("metadata")
    metadata.add_argument("--record", type=Path, required=True)
    lock_hosts = subparsers.add_parser("lock-hosts")
    lock_hosts.add_argument("--lock", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "paths":
        errors = validate_paths(args.target, args.evidence_root, args.approved_root)
    elif args.command == "metadata":
        record = json.loads(args.record.read_text(encoding="utf-8-sig"))
        pin = json.loads(PIN_PATH.read_text(encoding="utf-8"))
        errors = validate_provenance(record, pin)
    else:
        lock = json.loads(args.lock.read_text(encoding="utf-8"))
        hosts = sorted(
            {
                urlparse(item["resolved"]).hostname
                for item in lock.get("packages", {}).values()
                if isinstance(item, dict)
                and isinstance(item.get("resolved"), str)
                and "://" in item["resolved"]
            }
        )
        if hosts != ["registry.npmjs.org"]:
            print("Research R0 validation: FAIL")
            print("lockfile contains non-allowlisted dependency hosts")
            return 1
        print("registry.npmjs.org")
        return 0
    if errors:
        print("Research R0 validation: FAIL")
        print("\n".join(errors))
        return 1
    print("Research R0 validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
