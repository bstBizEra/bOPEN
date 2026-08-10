#!/usr/bin/env python3
"""Authority Gate, minimal executable form: No Ticket, No Work.

`AGENTS.md` section 5 requires every change to identify its accepted
work-package ID before anything else happens. This script enforces the
smallest verifiable slice of that rule: a pull request must cite a
work-package ID in its title or body before any downstream gate runs.

Accepted ID shapes:

    BOPEN-WP-<SEGMENT>[-<SEGMENT>...]   canonical, minted for governed-autonomy work
    BOPEN-P<n>-<SEGMENT>...             legacy execution-plan IDs (e.g. BOPEN-P35-001)
    WP-P<n>-<SEGMENT>...                legacy work-package IDs (e.g. WP-P35-07)
    BOOT-P<n>-<SEGMENT>...              bootstrap-pack IDs (e.g. BOOT-P0-05)

Fail-closed by design: missing input is a failure, not a pass. Exit codes:

    0  a work-package reference was found
    2  no reference found, or nothing to check (fail closed)

Input is read from the ``WP_TEXT`` environment variable when set, else
from the command line. CI passes the PR title and body through the
environment so that attacker-controlled text is never interpolated into
a shell command.

Ported from the SecB Project Framework (`SECB-WP-FWK-005`) under
`BOPEN-WP-GOV-AUTONOMY-001`; identifier prefixes renamed per the
`AGENTS.md` section 30.4 collision rulings.
"""

from __future__ import annotations

import os
import re
import sys

WP_PATTERN = re.compile(
    r"\b(?:BOPEN-WP|BOPEN-P\d+|WP-P\d+|BOOT-P\d+)-[A-Z0-9]+(?:-[A-Z0-9]+)*\b"
)


def find_reference(text: str) -> str | None:
    """Return the first work-package ID in *text*, or None."""
    match = WP_PATTERN.search(text or "")
    return match.group(0) if match else None


def main(argv: list[str]) -> int:
    text = os.environ.get("WP_TEXT")
    if text is None:
        text = " ".join(argv[1:])
    text = text.strip()

    if not text:
        print(
            "AUTHORITY GATE FAIL (closed): no input text -- "
            "a work-package reference cannot be verified",
            file=sys.stderr,
        )
        return 2

    ref = find_reference(text)
    if ref is None:
        print(
            "AUTHORITY GATE FAIL: no BOPEN-WP-* work-package reference found. "
            "AGENTS.md section 5: identify the accepted work-package ID. "
            "No Ticket, No Work.",
            file=sys.stderr,
        )
        return 2

    print(f"AUTHORITY GATE PASS: work-package reference {ref}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
