#!/usr/bin/env python3
"""Validate immutable root-control genesis and its required signed activation event."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "82ed6b38b118aab14a9961c5d75a33e515cb136a"
BASE_TREE = "cad6b595fb74a70cc706a78d45778e15524aebd9"
ROOT_SURFACES = {
    "Roadmap.md": "GOV-P0-03-ROOT-ROADMAP",
    "Master_Standards.md": "GOV-P0-03-ROOT-STANDARDS",
    "Progress_Log.md": "GOV-P0-03-ROOT-PROGRESS",
    "Backlog.md": "GOV-P0-03-ROOT-BACKLOG",
    "Recap_Today.md": "GOV-P0-03-ROOT-RECAP",
}
PACKAGE_PATHS = (
    *ROOT_SURFACES,
    "contracts/governance/root-control-surface.schema.json",
    "docs/decisions/DEC-0012.md",
    "docs/evidence/EVD-GOV-003-root-control-surfaces.md",
    "docs/work-packages/GOV-P0-03.md",
    "tests/governance/test_root_control_surfaces.py",
    "tools/validate_root_control_surfaces.py",
)
MANIFEST_PATH = "docs/manifests/GOV-P0-03-PACKAGE-MANIFEST.json"
CONFIG_PATHS = (
    "/opt/bizera-smartthink/config/agents.yaml",
    "/opt/bizera-smartthink/config/routing.yaml",
    "/opt/bizera-smartthink/config/system.yaml",
)
REQUIRED_FIELDS = {
    "Version": "0.1",
    "Status": "Draft",
    "Lifecycle": "Inactive",
    "Decision reference": "DEC-0012 option 1 user-level drafting authorization",
    "Evidence reference": "EVD-GOV-003",
    "Agent ID": "/root/gov_p0_03_preflight",
    "Base commit": BASE_COMMIT,
    "Base tree": BASE_TREE,
    "Append-only": "true",
    "PG-G0 passed": "false",
    "Production implementation authorized": "false",
    "Merge authorized": "false",
    "Release authorized": "false",
}
FIELD_PATTERN = re.compile(r"^\*\*([^*]+):\*\*\s*(.*?)\s*$", re.MULTILINE)
CHECKBOX_PATTERN = re.compile(r"^\s*[-*]\s+\[[ xX]\]", re.MULTILINE)
ACTIVATION_HEADING = "## Root control activation event"
ACTIVATION_FIELDS = {
    "Activation status": "Active",
    "Activation lifecycle": "Active",
    "Activated by": "HUMAN-OPERATOR-001",
    "Activation decision ref": "docs/00-governance/signing/SIGNING-PASS-2.md#B6",
    "Activation evidence ref": "docs/00-governance/signing/SIGNING-PASS-2.md",
    "Activation substrate commit": "26bea090c0aca14f1337c4be1a146fd48bb1f626",
}
SIGNED_ACTIVATION_AT = "2026-07-23T00:45:00+07:00"
SIGNED_RECORD_MARKER = "## Append-only Batch 2 signing record — 2026-07-23"


def exact_file_bytes(path: Path) -> bytes:
    """Return exact on-disk bytes; integrity bindings must not normalize content."""
    return path.read_bytes()


def manifest_record(path: Path, root: Path) -> dict[str, object]:
    data = exact_file_bytes(path)
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }


def build_package_manifest(root: Path = ROOT) -> dict[str, object]:
    records = [manifest_record(root / rel, root) for rel in sorted(PACKAGE_PATHS)]
    return {
        "package_id": "GOV-P0-03",
        "version": "0.3",
        "status": "active",
        "lifecycle": "active",
        "generated": "2026-07-23",
        "base_commit": BASE_COMMIT,
        "base_tree": BASE_TREE,
        "activation": {
            "activated_by": "HUMAN-OPERATOR-001",
            "activated_at": SIGNED_ACTIVATION_AT,
            "decision_ref": "docs/00-governance/signing/SIGNING-PASS-2.md#B6",
            "evidence_ref": "docs/00-governance/signing/SIGNING-PASS-2.md",
            "substrate_commit": "26bea090c0aca14f1337c4be1a146fd48bb1f626",
        },
        "authority": {
            "pg_g0_passed": False,
            "production_implementation_authorized": False,
            "merge_authorized": False,
            "release_authorized": False,
        },
        "count": len(records),
        "files": records,
    }


def parse_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for key, value in FIELD_PATTERN.findall(text):
        fields.setdefault(key.strip(), value.strip())
    return fields


def parse_activation_event(text: str) -> tuple[dict[str, str] | None, list[str]]:
    count = text.count(ACTIVATION_HEADING)
    if count == 0:
        return None, []
    if count != 1:
        return None, ["ROOT CONTROL ACTIVATION EVENT COUNT INVALID"]
    event = parse_fields(text.split(ACTIVATION_HEADING, 1)[1])
    errors: list[str] = []
    for key, expected in ACTIVATION_FIELDS.items():
        if event.get(key) != expected:
            errors.append(f"ROOT CONTROL ACTIVATION FIELD INVALID: {key}")
    activated_at = event.get("Activated at")
    try:
        parsed = datetime.fromisoformat(str(activated_at).replace("Z", "+00:00"))
    except ValueError:
        parsed = None
    if parsed is None or parsed.tzinfo is None:
        errors.append("ROOT CONTROL ACTIVATION FIELD INVALID: Activated at")
    return event, errors


def validate_exact_root_names(names: list[str]) -> list[str]:
    errors: list[str] = []
    lower_to_actual: dict[str, list[str]] = {}
    for name in names:
        lower_to_actual.setdefault(name.lower(), []).append(name)
    for expected in ROOT_SURFACES:
        actual = lower_to_actual.get(expected.lower(), [])
        if actual != [expected]:
            errors.append(f"ROOT CONTROL EXACT NAME INVALID: {expected} -> {actual}")
    return errors


def validate_append_only_bytes(previous: bytes | None, candidate: bytes) -> list[str]:
    if previous is None:
        return []
    errors: list[str] = []
    if len(candidate) < len(previous):
        errors.append("ROOT CONTROL TRUNCATED")
    if not candidate.startswith(previous):
        errors.append("ROOT CONTROL PREFIX REWRITTEN")
    return errors


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def read_git_blob(root: Path, object_spec: str) -> bytes | None:
    """Read a Git blob without text decoding or universal-newline translation."""
    result = subprocess.run(
        ["git", "cat-file", "blob", object_spec],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def validate_git_history(root: Path) -> list[str]:
    errors: list[str] = []
    if run_git(root, "rev-parse", "--is-inside-work-tree").returncode != 0:
        return ["GIT WORKTREE REQUIRED FOR APPEND-ONLY VALIDATION"]
    base_tree = run_git(root, "show", "-s", "--format=%T", BASE_COMMIT)
    if base_tree.returncode != 0 or base_tree.stdout.strip() != BASE_TREE:
        errors.append("ROOT CONTROL BASE TREE MISMATCH")
        return errors
    if run_git(root, "merge-base", "--is-ancestor", BASE_COMMIT, "HEAD").returncode != 0:
        errors.append("ROOT CONTROL BASE IS NOT HEAD ANCESTOR")

    tracked: list[str] = []
    untracked: list[str] = []
    for rel in ROOT_SURFACES:
        if run_git(root, "cat-file", "-e", f"{BASE_COMMIT}:{rel}").returncode == 0:
            errors.append(f"ROOT CONTROL unexpectedly exists at authorized base: {rel}")
        if run_git(root, "ls-files", "--error-unmatch", "--", rel).returncode == 0:
            tracked.append(rel)
        else:
            untracked.append(rel)
    if tracked and untracked:
        errors.append("ROOT CONTROL GENESIS PARTIALLY TRACKED")
        return errors
    if untracked:
        return errors

    additions: dict[str, str] = {}
    for rel in ROOT_SURFACES:
        result = run_git(root, "log", "--diff-filter=A", "--format=%H", "--", rel)
        commits = [line for line in result.stdout.splitlines() if line]
        if len(commits) != 1:
            errors.append(f"ROOT CONTROL GENESIS COMMIT INVALID: {rel}")
            continue
        additions[rel] = commits[0]
    if additions and len(set(additions.values())) != 1:
        errors.append("ROOT CONTROLS NOT CREATED IN ONE ATOMIC COMMIT")
        return errors

    for rel, addition in additions.items():
        history = run_git(root, "rev-list", "--reverse", f"{addition}..HEAD", "--", rel)
        for commit in [line for line in history.stdout.splitlines() if line]:
            parents = run_git(root, "show", "-s", "--format=%P", commit).stdout.split()
            if not parents:
                errors.append(f"ROOT CONTROL HISTORY PARENT MISSING: {rel} {commit}")
                continue
            before = read_git_blob(root, f"{parents[0]}:{rel}")
            after = read_git_blob(root, f"{commit}:{rel}")
            if before is None or after is None:
                errors.append(f"ROOT CONTROL HISTORY BLOB MISSING: {rel} {commit}")
                continue
            for issue in validate_append_only_bytes(before, after):
                errors.append(f"{issue}: {rel} {commit}")
    return errors


def validate_root_control_surfaces(
    root: Path = ROOT, *, check_git: bool = True
) -> list[str]:
    errors: list[str] = []
    root_names = [item.name for item in root.iterdir() if item.is_file() or item.is_symlink()]
    errors.extend(validate_exact_root_names(root_names))

    expected_links = tuple(ROOT_SURFACES) + ("README.md",)
    seen_ids: set[str] = set()
    activation_events: dict[str, dict[str, str]] = {}
    for rel, expected_id in ROOT_SURFACES.items():
        path = root / rel
        if not path.exists():
            errors.append(f"ROOT CONTROL MISSING: {rel}")
            continue
        if path.is_symlink() or not path.is_file():
            errors.append(f"ROOT CONTROL MUST BE REGULAR FILE: {rel}")
            continue
        data = path.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"ROOT CONTROL MUST BE UTF-8: {rel}")
            continue
        if data.startswith(b"\xef\xbb\xbf") or "\r" in text:
            errors.append(f"ROOT CONTROL MUST USE UTF-8 WITHOUT BOM AND LF: {rel}")
        fields = parse_fields(text)
        if fields.get("Document ID") != expected_id:
            errors.append(f"ROOT CONTROL DOCUMENT ID INVALID: {rel}")
        elif expected_id in seen_ids:
            errors.append(f"ROOT CONTROL DOCUMENT ID DUPLICATE: {expected_id}")
        else:
            seen_ids.add(expected_id)
        for key, value in REQUIRED_FIELDS.items():
            if fields.get(key) != value:
                errors.append(f"ROOT CONTROL FIELD INVALID {rel}: {key}")
        if not fields.get("Owner") or not fields.get("Issued") or not fields.get("Source"):
            errors.append(f"ROOT CONTROL PROVENANCE INCOMPLETE: {rel}")
        if not fields.get("Governing artifacts") or not fields.get("Dependent artifacts"):
            errors.append(f"ROOT CONTROL TRACEABILITY INCOMPLETE: {rel}")
        for linked in expected_links:
            if f"]({linked})" not in text:
                errors.append(f"ROOT CONTROL LINK MISSING {rel}: {linked}")
        for config_path in CONFIG_PATHS:
            if config_path not in text:
                errors.append(f"ROOT CONTROL CONFIG REFERENCE MISSING {rel}: {config_path}")
        if "UNRESOLVED_EXTERNAL_DEPENDENCY" not in text:
            errors.append(f"ROOT CONTROL CONFIG STATE MISSING: {rel}")
        if "Reason:" not in text or "Benefit of old phase:" not in text or "Expected outcome:" not in text:
            errors.append(f"ROOT CONTROL EXTEND-ONLY NOTE INCOMPLETE: {rel}")
        activation, activation_errors = parse_activation_event(text)
        errors.extend(f"{item}: {rel}" for item in activation_errors)
        if activation is not None:
            activation_events[rel] = activation

    if set(activation_events) != set(ROOT_SURFACES):
        missing = sorted(set(ROOT_SURFACES) - set(activation_events))
        errors.append(f"ROOT CONTROL ACTIVATION MUST BE ATOMIC: missing {missing}")
    if len(activation_events) == len(ROOT_SURFACES):
        activated_at = {item.get("Activated at") for item in activation_events.values()}
        if len(activated_at) != 1:
            errors.append("ROOT CONTROL ACTIVATION TIMESTAMPS MUST MATCH")
        elif activated_at != {SIGNED_ACTIVATION_AT}:
            errors.append("ROOT CONTROL ACTIVATION TIMESTAMP MUST MATCH SIGNED B6")
        signing_path = root / "docs/00-governance/signing/SIGNING-PASS-2.md"
        if not signing_path.is_file():
            errors.append("ROOT CONTROL ACTIVATION SIGNING EVIDENCE MISSING")
        else:
            signing_text = signing_path.read_text(encoding="utf-8")
            for marker in (
                SIGNED_RECORD_MARKER,
                "**Signed by:** HUMAN-OPERATOR-001",
                f"**Signed at:** {SIGNED_ACTIVATION_AT}",
                "PG-G0-PREP-013 | GOV-P0-03 root-control package — ACTIVE",
            ):
                if marker not in signing_text:
                    errors.append(f"ROOT CONTROL ACTIVATION SIGNED RECORD INVALID: {marker}")

    roadmap = (root / "Roadmap.md").read_text(encoding="utf-8") if (root / "Roadmap.md").is_file() else ""
    for token in ("PROGRAM / PG-G0", "NOT_READY", "BOOT / B7", "PENDING", "PRODUCTION", "UNAUTHORIZED"):
        if token not in roadmap:
            errors.append(f"ROOT ROADMAP BOUNDED STATE MISSING: {token}")
    standards = (root / "Master_Standards.md").read_text(encoding="utf-8") if (root / "Master_Standards.md").is_file() else ""
    if "locator and precedence map" not in standards:
        errors.append("ROOT STANDARDS LOCATOR DECLARATION MISSING")
    for rel in ("Progress_Log.md", "Backlog.md", "Recap_Today.md"):
        path = root / rel
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        if "## Event GOV-P0-03-" not in text:
            errors.append(f"ROOT LEDGER GENESIS EVENT MISSING: {rel}")
        if CHECKBOX_PATTERN.search(text):
            errors.append(f"ROOT LEDGER MUTABLE CHECKBOX PROHIBITED: {rel}")

    schema_path = root / "contracts/governance/root-control-surface.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"ROOT CONTROL SCHEMA INVALID: {exc}")
    else:
        if schema.get("status") != "draft" or schema.get("additionalProperties") is not False:
            errors.append("ROOT CONTROL SCHEMA MUST BE DRAFT AND FAIL CLOSED")
        if schema.get("$id") != "bopen://schemas/governance/root-control-surface/0.3.0-draft":
            errors.append("ROOT CONTROL SCHEMA VERSION INVALID")
        enum = schema.get("properties", {}).get("document_id", {}).get("enum", [])
        if set(enum) != set(ROOT_SURFACES.values()):
            errors.append("ROOT CONTROL SCHEMA DOCUMENT IDS INVALID")

    manifest_path = root / MANIFEST_PATH
    try:
        actual_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"ROOT CONTROL PACKAGE MANIFEST INVALID: {exc}")
    else:
        missing_manifest_sources = [rel for rel in PACKAGE_PATHS if not (root / rel).is_file()]
        if missing_manifest_sources:
            for rel in missing_manifest_sources:
                errors.append(f"ROOT CONTROL PACKAGE MANIFEST SOURCE MISSING: {rel}")
        else:
            expected_manifest = build_package_manifest(root)
            if actual_manifest != expected_manifest:
                errors.append("ROOT CONTROL PACKAGE MANIFEST STALE")

    if check_git:
        errors.extend(validate_git_history(root))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate without modifying files.")
    parser.add_argument(
        "--write-manifest",
        action="store_true",
        help="Regenerate the exact package manifest before validation.",
    )
    args = parser.parse_args()
    if args.write_manifest:
        manifest_path = ROOT / MANIFEST_PATH
        manifest_path.write_text(
            json.dumps(build_package_manifest(ROOT), indent=2) + "\n",
            encoding="utf-8",
        )
    errors = validate_root_control_surfaces()
    if errors:
        print("bOPEN root control surface validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("bOPEN root control surface validation: PASS")
    print(f"Checked {len(ROOT_SURFACES)} root controls and {len(PACKAGE_PATHS)} manifest-bound package files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

