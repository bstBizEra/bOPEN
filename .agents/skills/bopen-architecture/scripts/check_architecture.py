#!/usr/bin/env python3
"""Run deterministic baseline checks against a bOPEN architecture document."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

GROUPS = {
    "principal-membership-context": [r"\bprincipal\b", r"\bmembership\b", r"active tenant context|tenant context"],
    "authorization-entitlement": [r"\bauthori[sz]ation\b", r"\bentitlement\b"],
    "tenant-isolation": [r"row[- ]level security|\bRLS\b", r"default[- ]deny|fail closed", r"cross[- ]tenant"],
    "platform-package-boundary": [r"\bplatform\b", r"\bmodule\b|\bpackage\b", r"\bcapabilit(?:y|ies)\b"],
    "events-audit": [r"\boutbox\b|transactional outbox", r"\baudit\b", r"\bevents?\b"],
    "verification-evidence": [r"\bverification\b|\btest(?:ing|s)?\b", r"\bevidence\b", r"exit gate|acceptance criteria"],
}

BLOCKING_PATTERNS = {
    "client-tenant-authority": r"(?:trust|accept|use).{0,40}(?:x-tenant-id|tenant header|client[- ]supplied tenant).{0,40}(?:authoritative|without validation)",
    "disable-rls": r"(?:disable|remove|avoid).{0,20}(?:row[- ]level security|\bRLS\b)",
    "skill-grants-permission": r"skill.{0,30}(?:grant|authori[sz]e).{0,30}(?:permission|production|tool access)",
    "entitlement-is-permission": r"entitlement.{0,20}(?:is|equals|automatically grants).{0,20}permission",
    "duplicate-tenant-users": r"tenant.{0,20}(?:owns|stores).{0,20}(?:duplicate|separate).{0,20}user",
    "fabricated-evidence": r"mark.{0,30}(?:test|control).{0,20}pass.{0,30}(?:without|no).{0,20}evidence",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("document", type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    text = args.document.read_text(encoding="utf-8")
    missing: dict[str, list[str]] = {}
    present: list[str] = []
    for group, patterns in GROUPS.items():
        absent = [p for p in patterns if not re.search(p, text, flags=re.IGNORECASE | re.DOTALL)]
        if absent:
            missing[group] = absent
        else:
            present.append(group)

    blocking = [name for name, pattern in BLOCKING_PATTERNS.items() if re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)]
    score = round(100 * len(present) / len(GROUPS))
    status = "fail" if blocking or (args.strict and missing) else "pass"
    result = {
        "status": status,
        "score": score,
        "presentControlGroups": present,
        "missingControlGroups": missing,
        "blockingPatterns": blocking,
    }

    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        print(f"Architecture baseline score: {score}%")
        for group in present:
            print(f"PASS: {group}")
        for group in missing:
            print(f"WARN: missing or incomplete control group: {group}")
        for finding in blocking:
            print(f"BLOCK: prohibited pattern detected: {finding}")
        print(f"Result: {status.upper()}")

    return 2 if status == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
