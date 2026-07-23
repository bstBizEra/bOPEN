#!/usr/bin/env python3
"""Fail-closed skeleton validator for SKEL-P0-01 (bOPEN PG-P0 preparation scope).

Dependency-free. All text is LF-normalized before inspection and no raw-byte
hashing is performed, so results are reproducible across platforms (a CRLF vs
LF checkout cannot change a verdict).

Checks (fail closed): scoped AGENTS.md per populated zone; no runtime/business
logic in kernel zones; every draft contract shell carries draft status and the
required control/stability/traceability fields; typed package roots stay
type-only; skeleton test tiers keep their fail-closed guard and manifest.
"""
from __future__ import annotations

import argparse
from pathlib import Path

try:
    import json
except Exception as exc:  # pragma: no cover - json is stdlib
    raise SystemExit(f"json unavailable: {exc}")

ZONES = ["apps", "services", "packages", "contracts", "sdk", "infrastructure", "tools", "tests"]
KERNEL_ZONES = ["apps", "services", "packages", "sdk"]
RUNTIME_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
TEST_TIERS = ["unit", "contract", "integration", "tenant_isolation", "authorization"]


def normalized_text(path: Path) -> str:
    """Read text and normalize line endings so hashing/compare is platform-independent."""
    data = path.read_text(encoding="utf-8", errors="replace")
    return data.replace("\r\n", "\n").replace("\r", "\n")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.groups: list[tuple[str, bool]] = []

    def group(self, name: str, errors: list[str]) -> None:
        self.groups.append((name, not errors))
        self.errors.extend(errors)


def is_runtime_source(path: Path) -> bool:
    name = path.name
    if name.endswith(".d.ts"):
        return False
    if path.suffix in RUNTIME_SUFFIXES:
        return True
    if path.suffix == ".py" and name != "__init__.py":
        return normalized_text(path).strip() != ""
    return False


def check_zone_agents(root: Path, report: Report) -> None:
    errors: list[str] = []
    for zone in ZONES:
        directory = root / zone
        if directory.is_dir() and not (directory / "AGENTS.md").is_file():
            errors.append(f"scoped AGENTS.md missing in populated zone: {zone}")
    report.group("zone-structure-and-instructions", errors)


def check_no_business_logic(root: Path, report: Report) -> None:
    errors: list[str] = []
    for zone in KERNEL_ZONES:
        directory = root / zone
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*"), key=lambda p: p.as_posix()):
            if path.is_file() and is_runtime_source(path):
                errors.append(
                    f"runtime/business-logic source prohibited in kernel zone: "
                    f"{path.relative_to(root).as_posix()}"
                )
    report.group("no-production-business-logic", errors)


def check_contract_shells(root: Path, report: Report) -> None:
    errors: list[str] = []
    contracts = root / "contracts"
    shells = sorted(contracts.rglob("*.draft.schema.json"), key=lambda p: p.as_posix()) if contracts.is_dir() else []
    if not shells:
        errors.append("no draft contract shells found under contracts/")
    for path in shells:
        rel = path.relative_to(root).as_posix()
        try:
            data = json.loads(normalized_text(path))
        except Exception as exc:  # noqa: BLE001 - report and continue
            errors.append(f"{rel}: invalid JSON ({exc})")
            continue
        if not isinstance(data, dict):
            errors.append(f"{rel}: contract shell must be a JSON object")
            continue
        if data.get("status") != "draft":
            errors.append(f"{rel}: status must be draft")
        schema_id = data.get("$id", "")
        if not (isinstance(schema_id, str) and schema_id.startswith("bopen://") and "draft" in schema_id):
            errors.append(f"{rel}: $id must be a bopen:// draft URI")
        control = data.get("x-bopen-control", {})
        if not isinstance(control, dict):
            errors.append(f"{rel}: x-bopen-control must be an object")
            control = {}
        for key in ("artifactId", "version", "status", "owner"):
            if key not in control:
                errors.append(f"{rel}: x-bopen-control.{key} missing")
        if control.get("status") != "draft":
            errors.append(f"{rel}: x-bopen-control.status must be draft")
        stability = data.get("x-bopen-stability", {})
        if not isinstance(stability, dict) or stability.get("stableDependency") is not False:
            errors.append(f"{rel}: x-bopen-stability.stableDependency must be false")
        trace = data.get("x-bopen-traceability", {})
        if not isinstance(trace, dict) or not trace.get("normativeArtifact"):
            errors.append(f"{rel}: x-bopen-traceability.normativeArtifact missing")
        elif not isinstance(trace.get("requirementIds"), list):
            errors.append(f"{rel}: x-bopen-traceability.requirementIds must be a list")
    report.group("draft-contract-shells", errors)


def check_typed_packages(root: Path, report: Report) -> None:
    errors: list[str] = []
    packages = root / "packages"
    if packages.is_dir():
        for package in sorted(packages.iterdir(), key=lambda p: p.as_posix()):
            if not package.is_dir():
                continue
            for path in sorted(package.rglob("*"), key=lambda p: p.as_posix()):
                if path.is_file() and is_runtime_source(path):
                    errors.append(
                        f"typed package root must be type-only: {path.relative_to(root).as_posix()}"
                    )
    report.group("typed-package-skeletons", errors)


def check_test_guards(root: Path, report: Report) -> None:
    errors: list[str] = []
    for tier in TEST_TIERS:
        directory = root / "tests" / tier
        if directory.is_dir():
            if not (directory / "test_guard.py").is_file():
                errors.append(f"tests/{tier}: fail-closed guard test missing")
            if not (directory / "negative-tests.manifest.json").is_file():
                errors.append(f"tests/{tier}: negative-tests manifest missing")
    report.group("fail-closed-test-harness", errors)


def validate_skeleton(root: Path) -> Report:
    report = Report()
    check_zone_agents(root, report)
    check_no_business_logic(root, report)
    check_contract_shells(root, report)
    check_typed_packages(root, report)
    check_test_guards(root, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed SKEL-P0-01 skeleton validator.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", default="all", help="Reserved; only 'all' is currently defined.")
    args = parser.parse_args()
    root = args.root.resolve()
    report = validate_skeleton(root)
    for name, ok in report.groups:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    for error in report.errors:
        print(f"[FAIL] {error}")
    passed = sum(1 for _, ok in report.groups if ok)
    if report.errors:
        print(f"SKELETON VALIDATION FAILED: {len(report.errors)} failure(s), {passed} passed group(s)")
        return 1
    print(f"SKELETON VALIDATION PASSED: {len(report.groups)} check group(s), 0 failures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
