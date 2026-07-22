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
    parser.add_argument("--output", type=Path, required=True,
                        help="Report path outside the immutable skill package tree")
    args = parser.parse_args()
    output = args.output.resolve()
    try:
        output.relative_to(ROOT)
    except ValueError:
        pass
    else:
        parser.error("Evaluation output must be outside the hashed skill package tree")

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
                "--output", str(artifact_output),
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
        "package": "io.bizera.bopen.architecture@0.1.0",
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
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "checksPassed", "checksTotal")}, indent=2))
    print(output)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
