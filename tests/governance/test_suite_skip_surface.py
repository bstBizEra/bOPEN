"""The suite's conditional-skip surface, pinned so it cannot grow silently.

Work package: BOPEN-WP-SKIP-SURFACE-001
Governing artifacts: docs/01-product/KERNEL-AUTONOMY-OBJECTIVE.md section 1 (criteria 3 and 6)

WHY THIS EXISTS

`tools/run_tests.py` prints a category inventory and returns 0 or 1 on `result.wasSuccessful()`.
It never prints the skip count, and `wasSuccessful()` is True when tests are skipped. So a canonical
run can report

    Ran 685 tests in 625.203s
    OK

while an unknown share of those 685 executed nothing at all, and the report does not say which.

Measured on 2026-08-19 with no database reachable:

    inventory   unit 171, integration 253, contracts 108, isolation 146, governance 63 = 741
    ran 738     skipped 279     failures 49     errors 25
    executed    459 of 738 = 62%

**279 of 738 skipped.** That run also failed, so nothing was hidden that day — but a run where the
database is merely slow rather than absent can skip and still be judged only by its failures.

WHAT IS PINNED, AND WHY THIS SHAPE

Every conditional skip in the suite is database-gated. There are twenty-six of them and no others:
the whole skip surface of this repository is one external dependency. That is worth knowing and
worth keeping visible.

The counts below are pinned so that

  * adding a database-gated test is a deliberate, recorded act rather than a silent one, and
  * making a test hermetic — the direction the stability backlog wants — also fails this test, so the
    improvement gets recorded in a commit message instead of quietly changing what a green run means.

Either direction requires updating a number here and saying why. That is the point; a skip surface
that changes without anyone stating the new size is how "OK" stops meaning anything.

WHAT THIS DOES NOT DO

It does not make `run_tests.py` report skips. That is the real repair and it belongs in
`tools/run_tests.py`, which is a governance-implementation path under the delegation envelope and
classifies `AGENT_BALLOT_REQUIRED`. Recorded here, not worked around.
"""

from __future__ import annotations

import collections
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
TESTS = ROOT / "tests"

# Measured 2026-08-19, updated the same day by BOPEN-WP-SKIP-GUARD-001.
#
# 26 -> 28. The two added guards cover TestRegistryTableIsolation (10 tests) and
# TestAuditableInputBoundary (5), which previously FAILED rather than skipped when the
# database was absent — reporting names like test_a_tenant_cannot_read_another_tenants_people,
# which read as a tenant-isolation breach rather than a missing environment variable.
#
# The surface grew and the suite got MORE honest, which is why this number is pinned in both
# directions rather than capped.
EXPECTED_DATABASE_GATED = {"integration": 14, "isolation": 14}
EXPECTED_DATABASE_GATED_TOTAL = 28
EXPECTED_OTHER_CONDITIONAL_SKIPS = 0

_SKIP_IF = re.compile(r"@unittest\.skipIf\(\s*([^\n]{0,120})")


def scan() -> tuple:
    database_gated: collections.Counter = collections.Counter()
    other: collections.Counter = collections.Counter()
    for path in sorted(TESTS.rglob("test_*.py")):
        category = path.relative_to(TESTS).parts[0]
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in _SKIP_IF.finditer(text):
            condition = match.group(1)
            if "_unavailable_reason" in condition:
                database_gated[category] += 1
            else:
                other[category] += 1
    return database_gated, other


class SuiteSkipSurface(unittest.TestCase):
    def setUp(self) -> None:
        self.database_gated, self.other = scan()

    def test_the_scan_is_not_vacuous(self) -> None:
        """A scanner that matches nothing passes every count assertion below."""
        files = list(TESTS.rglob("test_*.py"))
        self.assertGreater(len(files), 40, "test files not found; the scanner is broken")
        self.assertGreater(
            sum(self.database_gated.values()),
            0,
            "no conditional skips found at all, which contradicts the recorded measurement",
        )

    def test_database_gated_skips_have_not_grown(self) -> None:
        self.assertEqual(
            dict(self.database_gated),
            EXPECTED_DATABASE_GATED,
            "\nThe database-gated skip surface changed.\n"
            "Growing it means more of the suite can report OK without executing. Shrinking it is\n"
            "the direction the stability backlog wants. Either way, update the numbers here and\n"
            "say which direction and why in the commit message.\n"
            "measured: " + str(dict(self.database_gated)) + "\n"
            "expected: " + str(EXPECTED_DATABASE_GATED),
        )
        self.assertEqual(sum(self.database_gated.values()), EXPECTED_DATABASE_GATED_TOTAL)

    def test_no_conditional_skip_is_gated_on_anything_else(self) -> None:
        """Today the entire skip surface is one external dependency. That is worth keeping true.

        A skip gated on something other than database availability is not forbidden, but it is a
        second reason a green run might mean nothing, and it should be introduced deliberately.
        """
        self.assertEqual(
            sum(self.other.values()),
            EXPECTED_OTHER_CONDITIONAL_SKIPS,
            "a conditional skip appeared that is not gated on database availability: "
            + str(dict(self.other)),
        )


if __name__ == "__main__":
    unittest.main()
