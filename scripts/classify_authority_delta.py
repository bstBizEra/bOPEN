#!/usr/bin/env python3
"""Authority-delta classifier (`BOPEN-WP-GOV-AUTONOMY-001`).

The question is not "which files does this PR touch" but **"how does this
PR change authority or risk relative to the ratified delegation envelope"**
(`AGENTS.md` section 30.2, adopted from the SecB Project Framework's
`SECB-WP-FWK-012` classifier; change-class identifiers renamed `G*` -> `AD*`
per the section 30.4 collision rulings).

Change classes and the verdict each produces (the *authority verdict*
vocabulary — distinct from EBIV ballot verdicts and operator dispositions):

    AD0  non-governance work inside the envelope        AUTO_APPROVED
    AD1  governance implementation, authority unchanged AGENT_BALLOT_REQUIRED
    AD2  adjustment inside the delegated envelope       AGENT_BALLOT_REQUIRED
    AD3  pre-authorized ladder advance, conditions met  AUTO_APPROVED_WITH_CONDITIONS
    AD4  root authority expansion                       CONSTITUTIONAL_REQUIRED
    AD5  prohibited: bypass, audit removal, evidence    REJECTED

Contract:

    stdin        output of ``git diff --numstat <base>...<head>``
    ENVELOPE     path to the delegation envelope (default config/delegation_envelope.json)
    DIFF_TEXT    optional unified diff body, used to detect AD5 signatures

Exit codes:

    0  AUTO_APPROVED or AUTO_APPROVED_WITH_CONDITIONS — the envelope covers it
    2  escalation required (AGENT_BALLOT_REQUIRED or CONSTITUTIONAL_REQUIRED)
    3  REJECTED — prohibited change

Fail-closed: a missing, unreadable, malformed, or expired envelope, an
unparseable diff, or an empty diff all escalate. `HUMAN_REQUIRED` is
deliberately absent from the vocabulary: the constitutional authority may in
future be a committee, a threshold-signature council, or an external body,
so the verdict names the *authority level* required, not the species of the
approver.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date

AUTO_APPROVED = "AUTO_APPROVED"
AUTO_APPROVED_WITH_CONDITIONS = "AUTO_APPROVED_WITH_CONDITIONS"
AGENT_BALLOT_REQUIRED = "AGENT_BALLOT_REQUIRED"
CONSTITUTIONAL_REQUIRED = "CONSTITUTIONAL_REQUIRED"
REJECTED = "REJECTED"

EXIT_OK = 0
EXIT_ESCALATE = 2
EXIT_REJECTED = 3

EXIT_FOR = {
    AUTO_APPROVED: EXIT_OK,
    AUTO_APPROVED_WITH_CONDITIONS: EXIT_OK,
    AGENT_BALLOT_REQUIRED: EXIT_ESCALATE,
    CONSTITUTIONAL_REQUIRED: EXIT_ESCALATE,
    REJECTED: EXIT_REJECTED,
}

# Removing an audit trail, deleting evidence, or skipping a verifier is not a
# governance decision to be weighed — it is prohibited outright (AD5). Detected
# as whole-file deletions of a control, plus one diff-body signature for the
# removal of an enforcement step from CI.
AD5_PATH_DELETIONS = (
    "scripts/check_work_package_ref.py",
    "scripts/check_budget.py",
    "scripts/classify_authority_delta.py",
    "scripts/check_dual_policy.py",
    "docs/evidence/",
    "evidence/",
)

# Enforcement steps whose *removal* from CI is prohibited. Matched only on
# removed lines, never on a substring of the whole diff: an added line that
# merely quotes one of these strings — a test fixture, or documentation of
# this very rule — is not a removal.
AD5_REMOVED_STEPS = (
    "run: python scripts/check_work_package_ref.py",
    "run: python scripts/check_budget.py",
    "run: python scripts/classify_authority_delta.py",
)


def removed_enforcement_steps(diff_text: str) -> list[str]:
    """Enforcement steps that appear on removed lines of *diff_text*."""
    found = []
    for line in (diff_text or "").splitlines():
        if not line.startswith("-") or line.startswith("---"):
            continue
        body = line[1:].strip()
        for step in AD5_REMOVED_STEPS:
            if body.endswith(step):
                found.append(step)
    return found


def load_envelope(path: str) -> dict:
    with open(path, encoding="utf-8") as handle:
        envelope = json.load(handle)
    for key in ("scope", "absolute_ceilings", "current_tier", "expires_at"):
        if key not in envelope:
            raise ValueError(f"envelope missing required key: {key}")
    return envelope


def parse_numstat(numstat: str) -> tuple[list[tuple[str, int, bool]], int]:
    """Return ([(path, lines, is_deletion)], total_lines)."""
    rows: list[tuple[str, int, bool]] = []
    total = 0
    for raw in numstat.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        parts = raw.split("\t")
        if len(parts) < 3:
            raise ValueError(f"unrecognized numstat row: {raw!r}")
        added, deleted, path = parts[0], parts[1], parts[-1]
        if added == "-":  # binary
            rows.append((path, 0, False))
            continue
        lines = int(added) + int(deleted)
        # A pure deletion has additions == 0 and deletions > 0.
        rows.append((path, lines, int(added) == 0 and int(deleted) > 0))
        total += lines
    return rows, total


def classify(
    rows: list[tuple[str, int, bool]], total_lines: int, envelope: dict, diff_text: str
) -> tuple[str, str]:
    """Return (verdict, reason)."""
    if not rows:
        return CONSTITUTIONAL_REQUIRED, "no diff parsed — authority delta cannot be established"

    scope = envelope["scope"]
    ceilings = envelope["absolute_ceilings"]
    paths = [path for path, _, _ in rows]

    # AD5 first: prohibited changes are never weighed against anything.
    deleted_controls = [
        path for path, _, is_del in rows
        if is_del and path.startswith(AD5_PATH_DELETIONS)
    ]
    if deleted_controls:
        return REJECTED, (
            "prohibited: deletes a control or evidence artifact — "
            + ", ".join(sorted(deleted_controls)[:3])
        )
    removed_steps = removed_enforcement_steps(diff_text)
    if removed_steps:
        return REJECTED, (
            "prohibited: removes an enforcement step from CI — "
            + ", ".join(sorted(set(removed_steps)))
        )

    # Absolute ceiling: never waivable by any tier or ballot.
    if total_lines > ceilings["max_changed_lines_ever"]:
        return CONSTITUTIONAL_REQUIRED, (
            f"{total_lines} lines exceeds the absolute ceiling "
            f"{ceilings['max_changed_lines_ever']} — no tier may waive it"
        )

    # AD4: anything that can alter the constitution, the envelope itself, the
    # classifier, the verifier, or the CI that runs them.
    constitutional = [p for p in paths if p.startswith(tuple(scope["constitutional_paths"]))]
    if constitutional:
        return CONSTITUTIONAL_REQUIRED, (
            "root authority surface touched: " + ", ".join(sorted(constitutional)[:4])
        )

    # AD1/AD2: governance implementation or in-envelope adjustment. Both need
    # the ballot layer, which is inert; they therefore escalate rather than pass.
    governance = [p for p in paths if p.startswith(tuple(scope["governance_implementation_paths"]))]
    if governance:
        state = envelope.get("ballot_layer", {}).get("state", "NOT_ACTIVE")
        detail = "" if state == "ACTIVE" else " (ballot layer NOT_ACTIVE — cannot be satisfied here)"
        return AGENT_BALLOT_REQUIRED, (
            "governance implementation: " + ", ".join(sorted(governance)[:4]) + detail
        )

    # AD0 must lie wholly inside the delegated scope.
    outside = [p for p in paths if not p.startswith(tuple(scope["auto_paths"]))]
    if outside:
        return CONSTITUTIONAL_REQUIRED, (
            "path(s) outside the delegated envelope: " + ", ".join(sorted(outside)[:4])
        )

    if total_lines > scope["max_changed_lines"]:
        return AGENT_BALLOT_REQUIRED, (
            f"{total_lines} lines exceeds the envelope cap {scope['max_changed_lines']} "
            f"but is within the absolute ceiling"
        )

    return AUTO_APPROVED, (
        f"AD0, {len(paths)} path(s), {total_lines}/{scope['max_changed_lines']} lines, "
        f"tier {envelope['current_tier']}"
    )


def main() -> int:
    envelope_path = os.environ.get("ENVELOPE", "config/delegation_envelope.json")
    try:
        envelope = load_envelope(envelope_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(
            f"VERDICT: {CONSTITUTIONAL_REQUIRED} — envelope unusable ({exc})",
            file=sys.stderr,
        )
        return EXIT_ESCALATE

    if str(envelope["expires_at"]) < date.today().isoformat():
        print(
            f"VERDICT: {CONSTITUTIONAL_REQUIRED} — envelope expired "
            f"{envelope['expires_at']}; renewal is a constitutional act",
            file=sys.stderr,
        )
        return EXIT_ESCALATE

    try:
        rows, total = parse_numstat(sys.stdin.read())
    except ValueError as exc:
        print(f"VERDICT: {CONSTITUTIONAL_REQUIRED} — {exc}", file=sys.stderr)
        return EXIT_ESCALATE

    verdict, reason = classify(rows, total, envelope, os.environ.get("DIFF_TEXT", ""))
    line = f"VERDICT: {verdict} — {reason}"
    if EXIT_FOR[verdict] == EXIT_OK:
        print(line)
    else:
        print(line, file=sys.stderr)
    return EXIT_FOR[verdict]


if __name__ == "__main__":
    sys.exit(main())
