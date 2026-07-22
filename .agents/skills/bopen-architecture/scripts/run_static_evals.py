#!/usr/bin/env python3
"""Run deterministic package and utility evaluations."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[2].resolve()


def run(command: list[str]) -> dict[str, object]:
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    return {
        "command": command,
        "returnCode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "pass": proc.returncode == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Existing, separately authorized output directory inside the workspace",
    )
    parser.add_argument("--output", type=Path, required=True, help="Relative report path beneath --output-dir")
    args = parser.parse_args()
    if args.output.is_absolute():
        parser.error("--output must be relative to --output-dir")
    if not args.output_dir.exists() or not args.output_dir.is_dir() or args.output_dir.is_symlink():
        parser.error("--output-dir must be an existing, non-symlink directory")
    output_dir = args.output_dir.resolve(strict=True)
    try:
        output_dir.relative_to(WORKSPACE)
    except ValueError:
        parser.error(f"--output-dir must remain inside the current workspace: {WORKSPACE}")
    try:
        output_dir.relative_to(ROOT)
    except ValueError:
        pass
    else:
        parser.error("--output-dir must be outside the immutable skill package tree")
    output = (output_dir / args.output).resolve()
    try:
        output.relative_to(output_dir)
    except ValueError:
        parser.error("--output escapes --output-dir")
    if output.exists() or output.is_symlink():
        parser.error(f"Refusing to overwrite existing output: {output}")

    checks: list[dict[str, object]] = []
    checks.append(run([sys.executable, "scripts/validate_package.py"]))

    with tempfile.TemporaryDirectory(prefix="bopen-skill-eval-", dir=ROOT.parents[1]) as tmp:
        tmp_path = Path(tmp)
        for artifact_type in ("research-report", "architecture-design", "adr", "conformance-review", "implementation-control"):
            artifact_output = tmp_path / f"{artifact_type}.md"
            result = run([
                sys.executable,
                "scripts/new_artifact.py",
                "--type", artifact_type,
                "--id", "TEST-001",
                "--title", "Static Evaluation Artifact",
                "--output-dir", str(tmp_path),
                "--output", artifact_output.name,
            ])
            if result["pass"] and (not artifact_output.exists() or "TEST-001" not in artifact_output.read_text(encoding="utf-8")):
                result["pass"] = False
                result["stderr"] = str(result["stderr"]) + "\nGenerated artifact missing expected content."
            checks.append(result)

    sample = ROOT / "evals/example-output.json"
    sample_doc = ROOT / "references/architecture-baseline.md"
    checks.append(run([sys.executable, "scripts/check_architecture.py", str(sample_doc), "--strict"]))

    positive = yaml.safe_load((ROOT / "evals/trigger-positive.yaml").read_text(encoding="utf-8"))
    negative = yaml.safe_load((ROOT / "evals/trigger-negative.yaml").read_text(encoding="utf-8"))
    trigger_check = {
        "command": ["deterministic-trigger-fixture-check"],
        "returnCode": 0,
        "stdout": f"positive={len(positive)} negative={len(negative)}",
        "stderr": "",
        "pass": bool(positive and negative and len(positive) == len(set(positive)) and len(negative) == len(set(negative))),
    }
    if not trigger_check["pass"]:
        trigger_check["returnCode"] = 1
    checks.append(trigger_check)

    passed = sum(1 for c in checks if c["pass"])
    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "package": "io.bizera.bopen.architecture@0.1.1",
        "evaluationType": "deterministic-static",
        "checksPassed": passed,
        "checksTotal": len(checks),
        "status": "pass" if passed == len(checks) else "fail",
        "limitations": [
            "Does not measure model activation precision or recall.",
            "Does not evaluate model reasoning quality across runtimes.",
            "Does not constitute independent security or architecture approval."
        ],
        "checks": checks,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("status", "checksPassed", "checksTotal")}, indent=2))
    print(output)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
