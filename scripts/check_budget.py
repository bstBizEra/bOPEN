#!/usr/bin/env python3
"""Budget circuit breaker, minimal executable form.

`AGENTS.md` section 15 prefers small, work-package-aligned changes and
section 31 makes a declared diff budget a condition of any autonomous
merge. This script makes the budget mechanically trip: every pull
request must declare a diff budget, and CI fails the PR when the diff
exceeds it.

Contract:

    stdin        output of ``git diff --numstat <base>...<head>``
    BUDGET_TEXT  the PR body, containing exactly one budget line:

        BUDGET: max_files=<int> max_lines=<int>

Exit codes (fail-closed):

    0  diff is within the declared budget
    2  budget missing, malformed, declared twice, or exceeded

Counting rules: every changed path counts as one file. Lines are added
plus deleted. Binary files report no line counts in numstat ("-"); they
count as one file and zero lines, so a binary-heavy PR is bounded by
max_files rather than silently unbounded.

Budget overruns are renegotiated by comment on the work-package ticket,
never silently restated in the PR body alone.

Ported from the SecB Project Framework (`SECB-WP-FWK-006`) under
`BOPEN-WP-GOV-AUTONOMY-001`.
"""

from __future__ import annotations

import os
import re
import sys

BUDGET_PATTERN = re.compile(
    r"^\s*BUDGET:\s*max_files=(\d+)\s+max_lines=(\d+)\s*$", re.MULTILINE
)

FAIL = 2


def parse_budget(text: str) -> tuple[int, int]:
    """Return (max_files, max_lines) or raise ValueError, fail-closed."""
    matches = BUDGET_PATTERN.findall(text or "")
    if not matches:
        raise ValueError(
            "no budget declared -- every PR body must contain exactly one "
            "line: 'BUDGET: max_files=<n> max_lines=<n>' (AGENTS.md section 31)"
        )
    if len(matches) > 1:
        raise ValueError(
            f"{len(matches)} BUDGET lines found -- the budget authority is "
            "ambiguous; declare exactly one"
        )
    max_files, max_lines = matches[0]
    return int(max_files), int(max_lines)


def measure_diff(numstat: str) -> tuple[int, int]:
    """Return (files, lines) totals from git numstat output."""
    files = 0
    lines = 0
    for row in numstat.splitlines():
        row = row.strip()
        if not row:
            continue
        parts = row.split("\t")
        if len(parts) < 3:
            raise ValueError(f"unrecognized numstat row: {row!r}")
        added, deleted = parts[0], parts[1]
        files += 1
        if added != "-":  # "-" marks a binary file: counted, lines unknown
            lines += int(added) + int(deleted)
    return files, lines


def main() -> int:
    try:
        max_files, max_lines = parse_budget(os.environ.get("BUDGET_TEXT", ""))
        files, lines = measure_diff(sys.stdin.read())
    except ValueError as exc:
        print(f"BUDGET GATE FAIL (closed): {exc}", file=sys.stderr)
        return FAIL

    usage = (
        f"{files}/{max_files} files, {lines}/{max_lines} changed lines"
    )
    if files > max_files or lines > max_lines:
        print(
            f"BUDGET GATE FAIL: diff exceeds the declared budget -- {usage}. "
            "A reached cap is a stop condition; shrink the change or "
            "re-negotiate the budget on the work-package ticket.",
            file=sys.stderr,
        )
        return FAIL

    print(f"BUDGET GATE PASS: {usage}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
