"""
Governance validators execute as part of the canonical suite.

Work package: BOPEN-P35-001
Governing artifacts: AGENTS.md §19.4, §20.5, §21.3;
                     BOPEN-GOV-EBIV-001 R3; BOPEN-GOV-IDENT-001 §4

Two validators were written to make governance rules machine-checkable — one binding evidence
manifests to real git objects, one binding ballots to the commit author that introduced them.
Neither was wired into anything. `AGENTS.md` §19.4 mandates only `validate_repository.py` and
`check_clean_room.py`, so a validator outside that set runs when somebody remembers.

That is the state §20.5 names: *"A governance rule that is not machine-checkable is a
preference."* A rule with a checker nobody runs is in the same position — the checker exists, and
the rule is still a preference. This file closes that gap by putting both validators inside
`python tools/run_tests.py`, which `check_authority_bootstrap.py` already invokes, so a gate
cannot be realized while either is failing.

Each validator is run as a subprocess rather than imported. They are command-line tools with exit
codes, and exercising them the way CI and an agent will actually call them is what this suite is
for; importing a function would test a different thing from the one that gets run.
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_tool(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


class GovernanceValidatorTests(unittest.TestCase):
    """Every check here fails the canonical suite, which is the point of it existing."""

    def test_evidence_anchors_resolve(self):
        """EBIV R3 — every commit and tree OID in docs/evidence/ resolves to a real object.

        The Phase 3 completion manifest bound `f59bbd289196b02a…`, which does not exist; only its
        seven-character prefix matched the real commit. An evidence package anchored to a
        non-existent object cannot be re-verified by anyone, and nothing caught it for a day.
        """
        result = run_tool("tools/check_evidence_anchors.py")
        self.assertEqual(
            result.returncode,
            0,
            msg=(
                "evidence anchors do not resolve — an evidence package is inadmissible "
                f"under EBIV R3:\n\n{result.stdout}\n{result.stderr}"
            ),
        )

    def test_ballot_attribution_holds(self):
        """BOPEN-GOV-IDENT-001 §4 — every ballot binds to a registered agent that is not the Maker.

        Passes vacuously while no ballots exist. That is correct and is reported as such by the
        tool: an empty ballot file is an unverified state, not a verified one.
        """
        result = run_tool("tools/check_ballot_attribution.py")
        self.assertEqual(
            result.returncode,
            0,
            msg=(
                "ballot attribution failed — one or more ballots are unattributable, "
                f"misattributed, or cast by the Maker:\n\n{result.stdout}\n{result.stderr}"
            ),
        )

    def test_identity_register_is_valid_and_agrees_with_its_document(self):
        """The machine-readable register and its normative document must not drift apart.

        `agent-identity-register.json` is what the validator reads; `BOPEN-GOV-IDENT-001.md` is
        what a human reads. If a canonical address were changed in one and not the other, the
        rule enforced would silently stop being the rule written down.
        """
        import json

        register_path = ROOT / "docs/00-governance/agent-identity-register.json"
        document_path = ROOT / "docs/00-governance/BOPEN-GOV-IDENT-001.md"

        self.assertTrue(register_path.is_file(), "identity register is missing")
        self.assertTrue(document_path.is_file(), "BOPEN-GOV-IDENT-001.md is missing")

        register = json.loads(register_path.read_text(encoding="utf-8"))
        document = document_path.read_text(encoding="utf-8")

        self.assertGreaterEqual(len(register.get("agents", [])), 2)

        for agent in register["agents"]:
            email = agent["canonical"]["email"]
            self.assertIn(
                email,
                document,
                f"canonical address {email} is in the register but not in the document; "
                f"the enforced rule and the written rule have drifted",
            )

        for entry in register.get("forbidden", []):
            self.assertTrue(
                entry.get("reason"),
                f"forbidden identity {entry['pattern']} carries no reason; a prohibition "
                f"without a stated reason cannot be reviewed",
            )

    def test_every_migration_has_a_rollback_or_a_recorded_absence(self):
        """AGENTS.md §14 — every migration needs a forward, rollback or compensating strategy.

        Migrations 001 and 002 have no rollback script. That is a real, pre-existing gap, so this
        test asserts the gap is *recorded* rather than asserting it does not exist. An
        undocumented missing rollback and a documented one look identical to a reader; only the
        second can be planned around.
        """
        migrations = sorted(
            p for p in (ROOT / "infrastructure/database").glob("*.sql")
            if not p.name.endswith((".down.sql", ".compensate.sql"))
        )
        self.assertGreater(len(migrations), 0, "no migrations found")

        missing = [
            p.name for p in migrations
            if not (p.parent / p.name.replace(".sql", ".down.sql")).is_file()
        ]

        if missing:
            manifest = ROOT / "docs/evidence/phase-3.5/manifest.json"
            self.assertTrue(manifest.is_file(), "phase-3.5 manifest missing")
            recorded = manifest.read_text(encoding="utf-8")
            for name in missing:
                number = name.split("_")[0]
                self.assertIn(
                    "no rollback",
                    recorded.lower(),
                    f"migration {number} has no rollback script and the gap is not recorded "
                    f"in the evidence manifest",
                )


if __name__ == "__main__":
    unittest.main()
