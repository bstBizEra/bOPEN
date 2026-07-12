#!/usr/bin/env python3
"""Validate the Phase 0 dependency and supply-chain control baseline."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def check_baseline(root: Path = ROOT) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    required = (
        "LICENSE",
        "NOTICE",
        "pnpm-lock.yaml",
        ".github/CODEOWNERS",
        ".github/dependabot.yml",
        ".github/workflows/bootstrap-governance.yml",
        "docs/07-security/supply-chain/dependency-policy.md",
        "docs/08-engineering/dependency-policy.md",
    )
    for relative in required:
        if not (root / relative).is_file():
            errors.append(f"missing required supply-chain control: {relative}")

    package_path = root / "package.json"
    if package_path.is_file():
        package = json.loads(package_path.read_text(encoding="utf-8"))
        if package.get("private") is not True:
            errors.append("package.json must remain private during bootstrap")
    else:
        errors.append("missing package.json")

    dependabot_path = root / ".github/dependabot.yml"
    if dependabot_path.is_file():
        dependabot = dependabot_path.read_text(encoding="utf-8")
        for ecosystem in ("github-actions", "npm"):
            if f"package-ecosystem: {ecosystem}" not in dependabot:
                errors.append(f"dependabot does not cover {ecosystem}")

    workflow_path = root / ".github/workflows/bootstrap-governance.yml"
    if workflow_path.is_file():
        workflow = workflow_path.read_text(encoding="utf-8")
        if "permissions:\n  contents: read" not in workflow:
            errors.append("bootstrap workflow must use read-only contents permission")
        if "write-all" in workflow:
            errors.append("bootstrap workflow must not request write-all permission")

    codeowners_path = root / ".github/CODEOWNERS"
    if codeowners_path.is_file() and "@bopen/" in codeowners_path.read_text(encoding="utf-8"):
        warnings.append("CODEOWNERS identities remain pending external repository activation")

    return errors, warnings


def main() -> int:
    errors, warnings = check_baseline()
    for warning in warnings:
        print(f"Supply-chain warning: {warning}")
    if errors:
        print("Supply-chain baseline: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Supply-chain baseline: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
