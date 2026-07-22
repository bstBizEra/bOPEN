#!/usr/bin/env python3
"""Run every installed skill package test and validator without bytecode residue."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents" / "skills"


def run(command: list[str], cwd: Path) -> bool:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(command, cwd=cwd, env=env)
    return result.returncode == 0


def main() -> int:
    failures: list[str] = []
    suites = 0
    validators = 0
    for skill in sorted(path for path in SKILLS.iterdir() if path.is_dir()):
        tests = skill / "tests"
        if tests.is_dir():
            suites += 1
            if not run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], skill):
                failures.append(f"{skill.name}: tests")
        validator = skill / "scripts" / "validate_package.py"
        if validator.is_file():
            validators += 1
            if not run([sys.executable, str(validator)], skill):
                failures.append(f"{skill.name}: package validation")

    # The architecture evaluator must emit outside the immutable package tree.
    architecture_eval = SKILLS / "bopen-architecture" / "scripts" / "run_static_evals.py"
    with tempfile.TemporaryDirectory(prefix="bopen-skill-eval-") as temporary:
        output = Path(temporary) / "static-eval-report.json"
        if not run([sys.executable, str(architecture_eval), "--output", str(output)], architecture_eval.parents[1]):
            failures.append("bopen-architecture: static evaluation")

    if failures:
        print("bOPEN skill package checks: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"bOPEN skill package checks: PASS ({suites} suites, {validators} validators, 1 static evaluation)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
