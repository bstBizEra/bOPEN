#!/usr/bin/env python3
"""Fail-closed skeleton validator for SKEL-P0-01 (bOPEN PG-P0 preparation scope).

Dependency-free (standard library only). All text is line-ending normalized before
inspection and no raw-byte hashing is performed, so a verdict is identical on a CRLF
or an LF checkout.

Checks (each fails closed): a scoped ``AGENTS.md`` in every populated zone; no runtime
or business-logic source in the kernel zones (Python judged by AST, TS/JS by an
import/declaration heuristic); every draft contract shell carries draft status and the
required control/stability/traceability fields; typed package roots stay type-only; and
each skeleton test tier keeps its guard and, recursively, admits no implementation file
unless its negative-test manifest is armed.

Sole maker: Claude (BST-SA Motor worker agent). This module is authored in full by the
maker; it inherits no third-party bytes.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

ZONES = ("apps", "services", "packages", "contracts", "sdk", "infrastructure", "tools", "tests")
KERNEL_ZONES = ("apps", "services", "packages", "sdk")
SCRIPT_SUFFIXES = frozenset({".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"})
TEST_TIERS = ("unit", "contract", "integration", "tenant_isolation", "authorization")
TIER_ALLOWED = frozenset({"__init__.py", "test_guard.py", "README.md", "AGENTS.md", "negative-tests.manifest.json"})
TIER_IGNORED_DIRS = frozenset({"__pycache__"})


def normalized_text(path: Path) -> str:
    """Read UTF-8 text and normalize line endings so results are platform-independent."""
    return path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.groups: list[tuple[str, bool]] = []

    def add_group(self, name: str, errors: list[str]) -> None:
        self.groups.append((name, not errors))
        self.errors.extend(errors)


def _python_has_runtime_substance(text: str) -> bool:
    """True if a Python module contains executable substance beyond a pure skeleton.

    Allowed (returns False): docstrings, ``from __future__`` imports, plain imports,
    ``__all__`` and simple constant string/number assignments. Anything else -- a
    function/class definition, a call, a loop, a conditional -- is runtime substance.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        # Unparseable Python in a kernel zone is not a clean skeleton stub.
        return True
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue  # module or bare-string docstring
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Assign):
            targets_ok = all(isinstance(t, ast.Name) for t in node.targets)
            value_ok = isinstance(node.value, ast.Constant)
            if targets_ok and value_ok:
                continue
        # FunctionDef, ClassDef, calls, loops, conditionals, complex assignments, etc.
        return True
    return False


def _is_runtime_source(path: Path) -> bool:
    name = path.name
    if name.endswith(".d.ts"):
        return False  # type-only declarations are permitted
    if path.suffix == ".py":
        if name == "__init__.py":
            return normalized_text(path).strip() != ""  # only an empty __init__ is a clean stub
        return _python_has_runtime_substance(normalized_text(path))
    if path.suffix in SCRIPT_SUFFIXES:
        # Fail-closed: the skeleton is type-only. TypeScript/JavaScript type declarations
        # must live in a `.d.ts` file (handled above). Any other script file in a kernel
        # zone is treated as runtime regardless of its contents, so no runtime construct
        # (function, class, arrow with or without parentheses, expression, one-liner, or
        # obfuscated form) can slip past a content heuristic.
        return True
    return False


def check_zone_agents(root: Path, report: Report) -> None:
    errors = [
        f"scoped AGENTS.md missing in populated zone: {zone}"
        for zone in ZONES
        if (root / zone).is_dir() and not (root / zone / "AGENTS.md").is_file()
    ]
    report.add_group("zone-structure-and-instructions", errors)


def check_no_business_logic(root: Path, report: Report) -> None:
    errors: list[str] = []
    for zone in KERNEL_ZONES:
        directory = root / zone
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*"), key=lambda p: p.as_posix()):
            if path.is_file() and _is_runtime_source(path):
                errors.append(f"runtime/business-logic source prohibited in kernel zone: {path.relative_to(root).as_posix()}")
    report.add_group("no-production-business-logic", errors)


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
        except json.JSONDecodeError as exc:
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
        control = data.get("x-bopen-control")
        if not isinstance(control, dict):
            errors.append(f"{rel}: x-bopen-control must be an object")
        else:
            for key in ("artifactId", "version", "status", "owner"):
                if key not in control:
                    errors.append(f"{rel}: x-bopen-control.{key} missing")
            if control.get("status") != "draft":
                errors.append(f"{rel}: x-bopen-control.status must be draft")
        stability = data.get("x-bopen-stability")
        if not isinstance(stability, dict) or stability.get("stableDependency") is not False:
            errors.append(f"{rel}: x-bopen-stability.stableDependency must be false")
        trace = data.get("x-bopen-traceability")
        if not isinstance(trace, dict) or not trace.get("normativeArtifact"):
            errors.append(f"{rel}: x-bopen-traceability.normativeArtifact missing")
        elif not isinstance(trace.get("requirementIds"), list):
            errors.append(f"{rel}: x-bopen-traceability.requirementIds must be a list")
    report.add_group("draft-contract-shells", errors)


def check_typed_packages(root: Path, report: Report) -> None:
    errors: list[str] = []
    packages = root / "packages"
    if packages.is_dir():
        for package in sorted(packages.iterdir(), key=lambda p: p.as_posix()):
            if not package.is_dir():
                continue
            for path in sorted(package.rglob("*"), key=lambda p: p.as_posix()):
                if path.is_file() and _is_runtime_source(path):
                    errors.append(f"typed package root must be type-only: {path.relative_to(root).as_posix()}")
    report.add_group("typed-package-skeletons", errors)


def tier_implementation_files(directory: Path, root: Path) -> list[str]:
    """Recursively list a tier's non-scaffolding files. Recursion is required: a
    top-level-only scan would let a nested implementation bypass the fail-closed guard."""
    found: list[str] = []
    for path in sorted(directory.rglob("*"), key=lambda p: p.as_posix()):
        if not path.is_file():
            continue
        parts = path.relative_to(directory).parts
        if any(part in TIER_IGNORED_DIRS for part in parts):
            continue
        if path.parent == directory and path.name in TIER_ALLOWED:
            continue
        found.append(path.relative_to(root).as_posix())
    return found


def check_test_guards(root: Path, report: Report) -> None:
    errors: list[str] = []
    for tier in TEST_TIERS:
        directory = root / "tests" / tier
        if not directory.is_dir():
            continue
        if not (directory / "test_guard.py").is_file():
            errors.append(f"tests/{tier}: fail-closed guard test missing")
        manifest_path = directory / "negative-tests.manifest.json"
        if not manifest_path.is_file():
            errors.append(f"tests/{tier}: negative-tests manifest missing")
            continue
        try:
            manifest = json.loads(normalized_text(manifest_path))
        except json.JSONDecodeError:
            errors.append(f"tests/{tier}: negative-tests manifest is not valid JSON")
            continue
        implementation_files = tier_implementation_files(directory, root)
        if implementation_files and manifest.get("status") != "armed":
            errors.append(
                f"tests/{tier}: implementation file(s) present while manifest status is not 'armed' "
                f"(fail-closed): {implementation_files}"
            )
    report.add_group("fail-closed-test-harness", errors)


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
    report = validate_skeleton(args.root.resolve())
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
