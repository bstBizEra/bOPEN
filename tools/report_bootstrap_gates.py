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
SIGNED_B7_MARKERS = (
    "## Append-only accepted decision — 2026-07-23",
    "**Outcome:** APPROVED; option 1; BOOT-B7 approved",
    "**Approved by:** HUMAN-OPERATOR-001 (Architecture Authority, DIRECT)",
    "**Approved at:** 2026-07-23T00:45:00+07:00",
    "docs/00-governance/signing/SIGNING-PASS-2.md#append-only-batch-2-signing-record--2026-07-23",
)


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


def latest_table_records(records: list[dict[str, str]], key: str) -> list[dict[str, str]]:
    """Use the last append-only disposition for each governed record."""
    latest: dict[str, dict[str, str]] = {}
    order: list[str] = []
    for record in records:
        value = record.get(key, "")
        if value not in latest:
            order.append(value)
        latest[value] = record
    return [latest[value] for value in order if value]


def load_registers(root: Path = ROOT) -> dict[str, list[dict[str, str]]]:
    return {
        "gates": parse_markdown_table(root / "docs/work-packages/BOOTSTRAP-GATES.md"),
        "work_packages": parse_markdown_table(
            root / "docs/work-packages/WORK-PACKAGE-REGISTER.md"
        ),
        "evidence": parse_markdown_table(root / "docs/evidence/EVIDENCE-INDEX.md"),
        "documents": parse_markdown_table(root / "docs/DOCUMENT-STATUS.md"),
    }


def build_report(root: Path = ROOT) -> dict[str, object]:
    registers = load_registers(root)
    gates = latest_table_records(registers["gates"], "Gate")
    work_packages = latest_table_records(registers["work_packages"], "ID")
    evidence = latest_table_records(registers["evidence"], "Evidence ID")
    documents = registers["documents"]

    b7 = next((gate for gate in gates if gate.get("Gate", "").startswith("B7")), {})
    decision_path = root / "docs/decisions/DEC-0007.md"
    decision_text = decision_path.read_text(encoding="utf-8") if decision_path.is_file() else ""
    b7_signed = all(marker in decision_text for marker in SIGNED_B7_MARKERS)
    b7_status = "Approved" if b7_signed else b7.get("Status", "Missing")
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
    execution_pending_packages = [
        item
        for item in work_packages
        if item.get("ID", "").startswith("BOOT-P0-")
        and item.get("ID") != "BOOT-P0-12"
        and item.get("Status", "").lower() != "execution complete"
    ]
    b7_review_ready = not pending_evidence and not execution_pending_packages

    blockers: list[str] = []
    if execution_pending_packages:
        blockers.append("Some BOOT-P0 execution packages require external activation.")
    if b7_status != "Approved":
        blockers.append("B7 exit gate is not approved.")
    if pending_evidence:
        blockers.append("Some bootstrap evidence remains ungenerated.")
    return {
        "bootstrap_review_state": (
            "approved"
            if b7_status == "Approved" and b7_review_ready
            else "ready_for_authority_review"
            if b7_review_ready
            else "incomplete"
        ),
        "b7_review_ready": b7_review_ready,
        "production_implementation_authorized": False,
        "gate_count": len(gates),
        "b7_status": b7_status,
        "b7_signed_decision_verified": b7_signed,
        "pending_evidence": pending_evidence,
        "execution_pending_packages": execution_pending_packages,
        "implementation_blocking_docs": implementation_blocking_docs,
        "blockers": blockers,
    }


def format_report(report: dict[str, object]) -> str:
    lines = [
        "# Bootstrap Gate Readiness Report",
        "",
        f"**Bootstrap review state:** `{report['bootstrap_review_state']}`",
        f"**B7 review ready:** `{str(report['b7_review_ready']).lower()}`",
        f"**Production implementation authorized:** `{str(report['production_implementation_authorized']).lower()}`",
        f"**Gate count:** {report['gate_count']}",
        f"**B7 status:** {report['b7_status']}",
        f"**B7 signed decision verified:** `{str(report['b7_signed_decision_verified']).lower()}`",
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

    lines.extend(["", "## Execution Packages Pending", ""])
    packages = report["execution_pending_packages"]
    if packages:
        for item in packages:  # type: ignore[union-attr]
            lines.append(f"- {item['ID']}: {item['Status']}")
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
            "This report verifies the signed DEC-0007/BOOT-B7 outcome; it does not create or alter that approval and does not authorize production platform kernel implementation.",
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
