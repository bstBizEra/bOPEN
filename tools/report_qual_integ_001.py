#!/usr/bin/env python3
"""Write or verify the deterministic QUAL-INTEG-001 maker-readiness record."""

from __future__ import annotations

import argparse
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path("artifacts/validation/qual-integ-001-readiness.json")


def count_integration_tests() -> int:
    suite = unittest.defaultTestLoader.discover(
        str(ROOT / "tests/governance"), pattern="test_qual_integ_001.py"
    )
    return suite.countTestCases()


def build_report(root: Path = ROOT) -> dict:
    baseline = {"contracts": 41, "governance": 136, "qualification": 45, "full": 222}
    added = count_integration_tests()
    return {
        "report_id": "QUAL-INTEG-001-READINESS",
        "version": "0.1",
        "status": "READY_FOR_INDEPENDENT_TECHNICAL_REVIEW",
        "lifecycle": "inactive",
        "generated": "2026-07-22",
        "work_package_id": "QUAL-INTEG-001",
        "base_commit": "82ed6b38b118aab14a9961c5d75a33e515cb136a",
        "composition_head": "43f0b8b84c5bcd3ad8f6a713a44aadd722bb9c78",
        "pre_integration_test_floor": baseline,
        "integration_tests_added": added,
        "expected_full_test_floor": baseline["full"] + added,
        "required_outcomes": {
            "source_replay_equivalent": True,
            "package_bytes_preserved": True,
            "historical_manifests_immutable": True,
            "validation_dag_union_present": True,
            "conflict_markers_absent": True,
        },
        "authority": {
            "technology_approved": False,
            "identity_provider_approved": False,
            "qualification_executed": False,
            "gate_passed": False,
            "merge_authorized": False,
            "release_authorized": False,
            "runtime_authorized": False,
            "production_implementation_authorized": False,
        },
        "limitation": "Maker readiness is technical evidence only; independent exact-SHA review and every human authority decision remain pending.",
    }


def rendered_report(root: Path = ROOT) -> str:
    return json.dumps(build_report(root), indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true")
    action.add_argument("--write", action="store_true")
    args = parser.parse_args()
    output = ROOT / OUTPUT
    expected = rendered_report(ROOT)
    if args.write:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(expected, encoding="utf-8", newline="\n")
        print(f"Wrote deterministic QUAL-INTEG-001 readiness report: {OUTPUT}")
        return 0
    try:
        actual = output.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"QUAL-INTEG-001 readiness report: FAIL ({exc})")
        return 1
    if actual != expected:
        print("QUAL-INTEG-001 readiness report: FAIL (stale or non-deterministic)")
        return 1
    report = build_report(ROOT)
    print(f"QUAL-INTEG-001 readiness report: PASS ({report['expected_full_test_floor']} minimum checks/tests)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
