#!/usr/bin/env python3
"""
bOPEN Evidence Anchor Validator

Enforces BOPEN-GOV-EBIV-001 rule R3 (machine-anchored evidence).

Every commit or tree OID recorded in an evidence package must resolve to a real object of
the expected type in this repository. Agents transcribe OIDs unreliably: a seven-character
prefix that matches a real commit says nothing about the remaining thirty-three characters,
and a manifest bound to an object that does not exist cannot be re-verified by anyone.

This check runs before test results are read, because a manifest that cannot be anchored
carries no information about what was tested.

Usage:
    python tools/check_evidence_anchors.py            # validate all evidence packages
    python tools/check_evidence_anchors.py --emit     # print tool-read anchors for HEAD

Exit codes:
    0  all anchors resolve
    1  one or more anchors are unresolvable, mistyped, or abbreviated
    2  the check could not run (not a git repository, git unavailable)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = ROOT / "docs" / "evidence"

FULL_OID = re.compile(r"\b[0-9a-f]{40}\b")
ABBREVIATED_OID = re.compile(r"\b[0-9a-f]{7,39}\b")

# JSON keys whose values are expected to be object identifiers, mapped to the git object
# type they must resolve to.
JSON_OID_KEYS = {
    "commit_oid": "commit",
    "candidate_commit_oid": "commit",
    "baseline_commit_oid": "commit",
    "reviewed_commit_oid": "commit",
    "head_commit_oid": "commit",
    "tree_oid": "tree",
    "candidate_tree_oid": "tree",
    "baseline_tree_oid": "tree",
}

# Markdown labels that introduce an OID value, mapped to expected git object type.
MARKDOWN_OID_LABELS = {
    "commit oid": "commit",
    "candidate commit oid": "commit",
    "baseline commit oid": "commit",
    "reviewed commit oid": "commit",
    "tree oid": "tree",
    "candidate tree oid": "tree",
}


class Finding:
    def __init__(self, path: Path, locator: str, oid: str, problem: str) -> None:
        self.path = path
        self.locator = locator
        self.oid = oid
        self.problem = problem

    def render(self) -> str:
        rel = self.path.relative_to(ROOT).as_posix()
        return f"  {rel}\n    {self.locator}: {self.oid}\n    -> {self.problem}"


def git(*args: str) -> tuple[int, str]:
    """Run a git command in the repository root. Returns (exit_code, stdout)."""
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print("ERROR: git executable not found on PATH", file=sys.stderr)
        raise SystemExit(2)
    return completed.returncode, completed.stdout.strip()


def object_type(oid: str) -> str | None:
    """Return the git object type for oid, or None when it does not resolve."""
    code, out = git("cat-file", "-t", oid)
    return out if code == 0 else None


def check_oid(oid: str, expected_type: str, path: Path, locator: str) -> Finding | None:
    if len(oid) != 40:
        return Finding(
            path,
            locator,
            oid,
            f"abbreviated identifier ({len(oid)} chars). R3 requires a full 40-character "
            f"OID emitted by a tool, not a prefix",
        )

    actual = object_type(oid)
    if actual is None:
        finding = Finding(
            path, locator, oid, "object does not exist in this repository"
        )
        # A prefix collision is the common failure mode when an agent knows the short SHA
        # and invents the tail. Surfacing the real object makes the defect unambiguous.
        code, resolved = git("rev-parse", oid[:7])
        if code == 0 and resolved and resolved != oid:
            finding.problem += (
                f"; prefix {oid[:7]} resolves to {resolved}, which differs from the "
                f"recorded value at character {_first_difference(oid, resolved)}"
            )
        return finding

    if actual != expected_type:
        return Finding(
            path, locator, oid, f"resolves to a {actual}, expected a {expected_type}"
        )

    return None


def _first_difference(a: str, b: str) -> int:
    for index, (left, right) in enumerate(zip(a, b)):
        if left != right:
            return index + 1
    return min(len(a), len(b)) + 1


def walk_json(node: object, path: Path, trail: str = "") -> list[Finding]:
    findings: list[Finding] = []
    if isinstance(node, dict):
        for key, value in node.items():
            locator = f"{trail}.{key}" if trail else key
            expected = JSON_OID_KEYS.get(key)
            if expected and isinstance(value, str):
                finding = check_oid(value.strip(), expected, path, locator)
                if finding:
                    findings.append(finding)
            else:
                findings.extend(walk_json(value, path, locator))
    elif isinstance(node, list):
        for index, item in enumerate(node):
            findings.extend(walk_json(item, path, f"{trail}[{index}]"))
    return findings


def check_json_file(path: Path) -> list[Finding]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [Finding(path, "<file>", "-", f"unreadable evidence manifest: {exc}")]
    return walk_json(data, path)


def check_markdown_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [Finding(path, "<file>", "-", f"unreadable evidence document: {exc}")]

    for number, line in enumerate(lines, start=1):
        lowered = line.lower()
        for label, expected in MARKDOWN_OID_LABELS.items():
            if label not in lowered:
                continue
            candidates = FULL_OID.findall(line) or [
                match
                for match in ABBREVIATED_OID.findall(line)
                # Ignore short hex runs that are plainly not identifiers.
                if len(match) >= 7
            ]
            for oid in candidates:
                finding = check_oid(oid, expected, path, f"line {number} ({label})")
                if finding:
                    findings.append(finding)
            break

    return findings


def collect_evidence_files() -> list[Path]:
    if not EVIDENCE_ROOT.is_dir():
        return []
    return sorted(
        path
        for path in EVIDENCE_ROOT.rglob("*")
        if path.is_file() and path.suffix in {".json", ".md"}
    )


def emit_anchors() -> int:
    """Print anchors read from git so no agent needs to transcribe them."""
    code, commit = git("rev-parse", "HEAD")
    if code != 0:
        print("ERROR: unable to resolve HEAD", file=sys.stderr)
        return 2
    _, tree = git("rev-parse", "HEAD^{tree}")
    _, branch = git("rev-parse", "--abbrev-ref", "HEAD")
    _, status = git("status", "--porcelain")

    print(
        json.dumps(
            {
                "commit_oid": commit,
                "tree_oid": tree,
                "branch": branch,
                "working_tree_clean": status == "",
            },
            indent=2,
        )
    )
    if status != "":
        print(
            "WARNING: working tree is dirty; anchors describe HEAD, not the files on disk",
            file=sys.stderr,
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--emit",
        action="store_true",
        help="print tool-read anchors for HEAD instead of validating evidence",
    )
    args = parser.parse_args()

    code, _ = git("rev-parse", "--git-dir")
    if code != 0:
        print("ERROR: not a git repository", file=sys.stderr)
        return 2

    if args.emit:
        return emit_anchors()

    files = collect_evidence_files()
    if not files:
        print(f"ERROR: no evidence files found under {EVIDENCE_ROOT}", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    for path in files:
        if path.suffix == ".json":
            findings.extend(check_json_file(path))
        else:
            findings.extend(check_markdown_file(path))

    print(f"bOPEN evidence anchor check (EBIV R3)")
    print(f"- evidence files scanned: {len(files)}")

    if findings:
        print(f"- unresolvable anchors: {len(findings)}\n")
        print("FAIL — evidence packages contain anchors that cannot be verified:\n")
        for finding in findings:
            print(finding.render())
        print(
            "\nAn evidence package whose anchors do not resolve is inadmissible under "
            "BOPEN-GOV-EBIV-001 R3 and shall be rejected before its test results are read.\n"
            "Regenerate anchors with: python tools/check_evidence_anchors.py --emit"
        )
        return 1

    print("- unresolvable anchors: 0\n")
    print("PASS — every recorded anchor resolves to a real object of the expected type.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
