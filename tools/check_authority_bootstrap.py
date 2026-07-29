#!/usr/bin/env python3
"""
bOPEN Authority & Bootstrap Verification Script (bopen-authority-bootstrap-check)
Validates repository governance, evidence-driven gate realization, document manifest,
clean-room status, document status harmony, and canonical test suite results.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors = []

def check_agents_md():
    agents_file = ROOT / "AGENTS.md"
    if not agents_file.exists():
        errors.append("AGENTS.md is missing")
        return
    txt = agents_file.read_text(encoding="utf-8")
    required_sections = [
        "Clean-room controls",
        "Architectural invariants",
        "Stop conditions",
        "Tenant data safety",
        "Evidence-Driven Gate Realization"
    ]
    for section in required_sections:
        if section not in txt:
            errors.append(f"AGENTS.md missing required section: '{section}'")

def check_normative_specs():
    specs = [
        "docs/02-requirements/BOPEN-REQ-001.md",
        "docs/03-architecture/BOPEN-ARCH-001.md",
        "docs/04-platform/BOPEN-TENANT-001.md",
        "docs/04-platform/BOPEN-AUTHZ-001.md",
        "docs/04-platform/BOPEN-IDP-001.md",
        "docs/04-platform/BOPEN-MOD-001.md",
        "docs/04-platform/BOPEN-ENT-001.md",
    ]
    for rel in specs:
        if not (ROOT / rel).exists():
            errors.append(f"Approved normative spec missing: {rel}")

def check_governance_harmony():
    """Verify zero contradiction across status registers and execution artifacts."""
    alignment = (ROOT / "docs/00-governance/AGENT-ALIGNMENT.md").read_text(encoding="utf-8")
    if "Phase 3" not in alignment:
        errors.append("AGENT-ALIGNMENT.md is not updated to Phase 3")

    p3_wp = (ROOT / "docs/work-packages/BOPEN-P3-001-EXECUTION-PLAN.md").read_text(encoding="utf-8")
    if "DRAFT — IMPLEMENTATION HOLD" in p3_wp:
        errors.append("BOPEN-P3-001-EXECUTION-PLAN.md still contains stale IMPLEMENTATION HOLD status")

    mod_spec = (ROOT / "docs/04-platform/BOPEN-MOD-001.md").read_text(encoding="utf-8")
    if "APPROVED FOR PHASE 3 IMPLEMENTATION" not in mod_spec:
        errors.append("BOPEN-MOD-001.md status header not updated to APPROVED FOR PHASE 3 IMPLEMENTATION")

    ent_spec = (ROOT / "docs/04-platform/BOPEN-ENT-001.md").read_text(encoding="utf-8")
    if "APPROVED FOR PHASE 3 IMPLEMENTATION" not in ent_spec:
        errors.append("BOPEN-ENT-001.md status header not updated to APPROVED FOR PHASE 3 IMPLEMENTATION")

    dec_entry = (ROOT / "docs/decisions/DEC-P3-ENTRY.md").read_text(encoding="utf-8")
    if "GO ON EVIDENCE" not in dec_entry:
        errors.append("DEC-P3-ENTRY.md status is not GO ON EVIDENCE")

    receipt = ROOT / "docs/evidence/phase-3/entry-gate-receipt.json"
    if not receipt.exists():
        errors.append("docs/evidence/phase-3/entry-gate-receipt.json is missing")
    else:
        receipt_data = json.loads(receipt.read_text(encoding="utf-8"))
        if receipt_data.get("disposition") != "GO_ON_EVIDENCE":
            errors.append("entry-gate-receipt.json disposition is not GO_ON_EVIDENCE")

def check_manifest():
    manifest_file = ROOT / "docs" / "DOCUMENT-MANIFEST.json"
    if not manifest_file.exists():
        errors.append("docs/DOCUMENT-MANIFEST.json is missing")
        return
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    doc_count = data.get("count", len(data.get("documents", [])))
    if doc_count < 200:
        errors.append(f"DOCUMENT-MANIFEST.json record count suspicious: {doc_count} records")

def run_script(cmd, name):
    res = subprocess.run([sys.executable] + cmd, cwd=str(ROOT), capture_output=True, text=True)
    if res.returncode != 0:
        errors.append(f"{name} failed:\n{res.stderr or res.stdout}")

def main():
    print("Executing bOPEN Authority Bootstrap & Evidence Realization Check...")
    check_agents_md()
    check_normative_specs()
    check_governance_harmony()
    
    run_script(["tools/generate_document_manifest.py"], "generate_document_manifest.py")
    check_manifest()
    run_script(["tools/validate_repository.py"], "validate_repository.py")
    run_script(["tools/check_clean_room.py"], "check_clean_room.py")
    run_script(["tools/run_tests.py"], "run_tests.py")

    if errors:
        print("bOPEN Authority Bootstrap Check: FAIL")
        for err in errors:
            print(f"- {err}")
        sys.exit(1)

    print("bOPEN Authority Bootstrap Check: PASS")
    print("Evidence-Driven Gate Realization baseline & governance harmony verified.")

if __name__ == "__main__":
    main()
