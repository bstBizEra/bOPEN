#!/usr/bin/env python3
"""Report bootstrap exit-gate readiness from governed markdown registers."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_IMPLEMENTATION_ARTIFACTS = {
    "BOPEN-REQ-001",
    "BOPEN-ARCH-001",
    "BOPEN-TENANT-001",
    "BOPEN-AUTHZ-001",
    "BOPEN-SEC-001",
}


def parse_markdown_table(path: Path) -> list[dict[str, str]]:
    rows: list[list[str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]
        if all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append(cells)

    if not rows:
        return []

    headers = rows[0]
    records: list[dict[str, str]] = []
    for row in rows[1:]:
        if len(row) != len(headers):
            continue
        records.append(dict(zip(headers, row)))
    return records


def load_registers(root: Path = ROOT) -> dict[str, list[dict[str, str]]]:
    return {
        "gates": parse_markdown_table(root / "docs/work-packages/BOOTSTRAP-GATES.md"),
        "evidence": parse_markdown_table(root / "docs/evidence/EVIDENCE-INDEX.md"),
        "documents": parse_markdown_table(root / "docs/DOCUMENT-STATUS.md"),
    }


def build_report(root: Path = ROOT) -> dict[str, object]:
    registers = load_registers(root)
    gates = registers["gates"]
    evidence = registers["evidence"]
    documents = registers["documents"]

    b7 = next((gate for gate in gates if gate.get("Gate", "").startswith("B7")), {})
    pending_evidence = [
        item
        for item in evidence
        if item.get("Status", "").lower() in {"to generate", "pending", "blocked"}
    ]
    implementation_blocking_docs = [
        item
        for item in documents
        if item.get("Artifact") in REQUIRED_IMPLEMENTATION_ARTIFACTS
        and item.get("Implementation authority", "").lower() != "yes"
    ]

    blockers: list[str] = []
    if b7.get("Status") != "Approved":
        blockers.append("B7 exit gate is not approved.")
    if pending_evidence:
        blockers.append("Some bootstrap evidence remains ungenerated.")
    if implementation_blocking_docs:
        blockers.append("Required implementation artifacts do not grant implementation authority.")

    return {
        "bootstrap_review_state": "review_required" if blockers else "ready",
        "production_implementation_authorized": False,
        "gate_count": len(gates),
        "b7_status": b7.get("Status", "Missing"),
        "pending_evidence": pending_evidence,
        "implementation_blocking_docs": implementation_blocking_docs,
        "blockers": blockers,
    }


def format_report(report: dict[str, object]) -> str:
    lines = [
        "# Bootstrap Gate Readiness Report",
        "",
        f"**Bootstrap review state:** `{report['bootstrap_review_state']}`",
        f"**Production implementation authorized:** `{str(report['production_implementation_authorized']).lower()}`",
        f"**Gate count:** {report['gate_count']}",
        f"**B7 status:** {report['b7_status']}",
        "",
        "## Blockers",
        "",
    ]

    blockers = report["blockers"]
    if blockers:
        lines.extend(f"- {blocker}" for blocker in blockers)  # type: ignore[union-attr]
    else:
        lines.append("- None")

    lines.extend(["", "## Pending Evidence", ""])
    pending_evidence = report["pending_evidence"]
    if pending_evidence:
        for item in pending_evidence:  # type: ignore[union-attr]
            lines.append(f"- {item['Evidence ID']} ({item['Work package']}): {item['Status']}")
    else:
        lines.append("- None")

    lines.extend(["", "## Implementation Authority Gaps", ""])
    docs = report["implementation_blocking_docs"]
    if docs:
        for item in docs:  # type: ignore[union-attr]
            lines.append(
                f"- {item['Artifact']}: {item['Status']} "
                f"(implementation authority: {item['Implementation authority']})"
            )
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "This report is readiness evidence only. It does not approve B7 and does not authorize production platform kernel implementation.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", type=Path, help="Write the markdown report to this path.")
    args = parser.parse_args(argv)

    report_text = format_report(build_report())
    if args.write:
        output = args.write
        if not output.is_absolute():
            output = ROOT / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report_text, encoding="utf-8")
        print(f"Wrote {output.relative_to(ROOT)}")
    else:
        print(report_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
