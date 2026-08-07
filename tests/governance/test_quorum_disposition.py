"""
Refusal Matrix for the §6.5 two-agent disposition path.

Work package: WP-P35-07
Governing artifacts: BOPEN-GOV-EBIV-001 §3, §6.1, §6.2, §6.3, §6.5;
                     DEC-P35-QUORUM-TOOL-GAP §6, §7, §8;
                     AGENTS.md §21.2.1, §21.3, §23

These tests are written BEFORE the implementation and are expected to fail. They define the
contract for `tools/check_ballot_attribution.py` once it can express EBIV §6.5: one admissible
`CONFIRMED` ballot from an independent verifier, PLUS an explicit Completion Authority
disposition, reported as `CONFIRMED_UNDER_TWO_AGENT_PROFILE` and never as bare `CONFIRMED`.

Keystone invariant (WP-P35-07 §3):

    A disposition may only ADD the §6.5 path to a candidate that already holds one admissible,
    independent, non-refuted CONFIRMED ballot. It may never create a confirmation on its own,
    and it may never be authored by an agent.

Every test below builds a disposable git repository rather than asserting against this one. A
negative case needs a disposition committed by the wrong identity, a REFUTED ballot, a
maker-cast ballot — none of which can be staged here without writing false evidence into the
real record. That is also why the tool needs a `--root` seam: a control that can only ever
inspect one repository cannot be shown to refuse anything.

`--root` does not weaken the control. The canonical invocation in `AGENTS.md` §19.4 and
`check_authority_bootstrap.py` passes no arguments and still resolves the real repository; a
fixture root only ever produces a verdict about the fixture.

TWO SCOPE NOTES recorded when these tests were written, both surfaced to the operator:

1. The checker currently reads neither `verdict` nor `admissibility`. It counts *distinct
   attributable verifiers*, so today a `REFUTED` ballot counts toward quorum exactly as a
   `CONFIRMED` one does. R-4 and R-5 therefore cannot pass without the tool learning to read
   both fields. This is implied by §6.5's wording ("one admissible CONFIRMED ballot") rather
   than being new scope, but it is more than "add disposition support".
2. The positive path deliberately asserts the candidate is ABSENT from the shortfall list as
   well as present as CONFIRMED_UNDER_TWO_AGENT_PROFILE. Reporting both would be worse than
   reporting neither.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "check_ballot_attribution.py"

CLAUDE = ("Claude (BST-SA Motor)", "claude@bst.local")
CODEX = ("Codex (BST-SA Motor)", "codex@bst.local")
GEMINI = ("Gemini (BST-SA Cortex)", "gemini@bst.local")
OPERATOR = ("BizEra", "ounkhamvilay@gmail.com")

CANDIDATE = "1cde9942096b29795ddd937a2130e170c970b2e7"
TREE = "dfc5d2202a2bafae92f939c8bde6ba41f4aa3c33"

REGISTER = {
    "register_id": "BOPEN-GOV-IDENT-001",
    "agents": [
        {"agent_id": "claude", "canonical": {"name_prefix": "Claude", "email": "claude@bst.local"}},
        {"agent_id": "codex", "canonical": {"name_prefix": "Codex", "email": "codex@bst.local"}},
        {"agent_id": "gemini", "canonical": {"name_prefix": "Gemini", "email": "gemini@bst.local"}},
        {
            "agent_id": "operator",
            "canonical": {"name_prefix": "BizEra", "email": "ounkhamvilay@gmail.com"},
            "is_human": True,
        },
    ],
    "forbidden": [],
}


def ballot(verifier: str, *, verdict: str = "CONFIRMED", independent: bool = True,
           candidate: str = CANDIDATE, proposition: str = "LOC-INV-ISOLATION-01",
           admissible: bool = True) -> dict:
    return {
        "ballot_id": f"blt_{verifier}_{proposition}",
        "proposition_id": proposition,
        "commit_oid": candidate,
        "tree_oid": TREE,
        "verifier_id": verifier,
        "independent_of_maker": independent,
        "verdict": verdict,
        "probe_command": "python tools/run_tests.py",
        "probe_exit_code": 0,
        "refutation_attempted": True,
        "admissibility": {k: admissible for k in ("R1", "R2", "R3", "R4", "R5")},
    }


def disposition(*, candidate: str = CANDIDATE,
                verdict: str = "CONFIRMED_UNDER_TWO_AGENT_PROFILE",
                authority: str = "BizEra <ounkhamvilay@gmail.com>") -> dict:
    return {
        "disposition_id": "dsp_0001",
        "candidate_commit_oid": candidate,
        "artifact": "BOPEN-LOC-001",
        "profile": "two_agent",
        "verdict": verdict,
        "disposing_authority": authority,
        "authority_role": "Completion Authority",
        "disclosed_risk_ack": "docs/evidence/phase-3.5/disclosed-risk.md",
        "issued_at": "2026-08-08T00:00:00+07:00",
        "recorded_by": "claude",
    }


class Fixture:
    """A disposable repository holding exactly the evidence a single test needs."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.phase = root / "docs" / "evidence" / "phase-3.5"
        self.phase.mkdir(parents=True)
        (root / "docs" / "00-governance").mkdir(parents=True)
        self._git("init", "-q")
        self._git("config", "user.name", "seed")
        self._git("config", "user.email", "seed@fixture.invalid")
        self.write(
            "docs/00-governance/agent-identity-register.json",
            json.dumps(REGISTER, indent=2),
        )
        self.set_maker("Claude (agent, Motor role)")
        self._commit_all("seed", CLAUDE)

    def _git(self, *args: str) -> str:
        done = subprocess.run(
            ["git", *args], cwd=str(self.root), capture_output=True, text=True,
            encoding="utf-8", errors="replace", check=False,
        )
        return done.stdout

    def write(self, rel: str, text: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def set_maker(self, maker: str) -> None:
        self.write(
            "docs/evidence/phase-3.5/manifest.json",
            json.dumps({"roles": {"maker": maker}}, indent=2),
        )

    def _commit_all(self, message: str, author: tuple[str, str]) -> None:
        name, email = author
        self._git("add", "-A")
        self._git(
            "-c", f"user.name={name}", "-c", f"user.email={email}",
            "commit", "-q", "--no-gpg-sign", "-m", message,
        )

    def append(self, filename: str, rows: list[dict], author: tuple[str, str]) -> None:
        """Append rows to an evidence file and commit them under `author`.

        Committing per author is the whole point: the tool binds a line to the git author of
        the commit that introduced it, so the author is the fact under test.
        """
        path = self.phase / filename
        existing = path.read_text(encoding="utf-8") if path.is_file() else ""
        payload = existing + "".join(json.dumps(r) + "\n" for r in rows)
        self.write(f"docs/evidence/phase-3.5/{filename}", payload)
        self._commit_all(f"evidence: {filename} +{len(rows)}", author)

    def check(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(TOOL), "--root", str(self.root)],
            cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8",
            errors="replace", check=False,
        )


class QuorumDispositionRefusalMatrix(unittest.TestCase):
    """WP-P35-07 §4. Each test is one row; each must fail if its mechanism is removed."""

    def assertEvaluated(self, res):
        """The tool ran and reached a verdict.

        Exit 2 is "could not run" and empty output is "did not run". Either would satisfy any
        assertion phrased purely as an absence, so every negative test anchors on this first.
        """
        self.assertNotEqual(res.returncode, 2, f"tool could not run: {res.stderr}")
        self.assertTrue(res.stdout.strip(), "tool produced no output; nothing was evaluated")

    def shortfall(self, stdout: str) -> str:
        """Just the shortfall listing, so 'candidate is absent from it' is a real assertion."""
        marker = "QUORUM SHORTFALL"
        return stdout.split(marker, 1)[1] if marker in stdout else ""

    def profile_applied(self, stdout: str) -> bool:
        """Was the profile verdict actually APPLIED to a candidate?

        Searching stdout for the bare string is not the same question, and answering the wrong
        one made a correct refusal look like a failure: the D4 finding text necessarily quotes
        the label it is demanding ("must be labelled CONFIRMED_UNDER_TWO_AGENT_PROFILE"). Only
        the per-candidate verdict line announces that the profile was applied, so that is what
        this matches.
        """
        return any(
            line.strip().startswith("CONFIRMED_UNDER_TWO_AGENT_PROFILE")
            for line in stdout.splitlines()
        )

    def assertProfileNotApplied(self, res):
        self.assertFalse(self.profile_applied(res.stdout),
                         f"profile must not be applied:\n{res.stdout}")

    def assertProfileApplied(self, res):
        self.assertTrue(self.profile_applied(res.stdout),
                        f"profile should have been applied:\n{res.stdout}")

    def scenario(self, *, ballots, dispositions=None, maker=None):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        fx = Fixture(Path(self._tmp.name))
        if maker:
            fx.set_maker(maker)
            fx._commit_all("maker", CLAUDE)
        for author, rows in ballots:
            fx.append("ballots.jsonl", rows, author)
        for author, rows in dispositions or []:
            fx.append("dispositions.jsonl", rows, author)
        return fx.check()

    # ---- positive path -------------------------------------------------------------

    def test_one_ballot_plus_operator_disposition_confirms_under_the_profile(self):
        """The only route to CONFIRMED_UNDER_TWO_AGENT_PROFILE."""
        res = self.scenario(
            ballots=[(CODEX, [ballot("codex")])],
            dispositions=[(OPERATOR, [disposition()])],
        )
        self.assertEvaluated(res)
        self.assertProfileApplied(res)
        self.assertNotIn(CANDIDATE[:12], self.shortfall(res.stdout),
                         "a confirmed candidate must not also be listed as short")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    # ---- R-1 .. R-9 ----------------------------------------------------------------

    def test_R1_one_ballot_without_a_disposition_stays_short(self):
        res = self.scenario(ballots=[(CODEX, [ballot("codex")])])
        self.assertIn("QUORUM SHORTFALL", res.stdout)
        self.assertProfileNotApplied(res)

    def test_R2_disposition_not_committed_by_the_operator_is_refused(self):
        """The integrity condition. Without it an agent confirms its own work."""
        res = self.scenario(
            ballots=[(CODEX, [ballot("codex")])],
            dispositions=[(CLAUDE, [disposition()])],
        )
        self.assertProfileNotApplied(res)
        self.assertEqual(res.returncode, 1, "an agent-authored disposition must be a finding")

    def test_R3_disposition_cannot_rescue_a_maker_cast_ballot(self):
        res = self.scenario(
            ballots=[(CLAUDE, [ballot("claude")])],
            dispositions=[(OPERATOR, [disposition()])],
            maker="Claude (agent, Motor role)",
        )
        self.assertProfileNotApplied(res)
        self.assertEqual(res.returncode, 1)

    def test_R4_disposition_cannot_discharge_a_refutation(self):
        """EBIV §6.2 — one reproducible REFUTED blocks, and a disposition is not a reproduction.

        Asserting only the ABSENCE of the profile string would pass against empty output, i.e.
        against a tool that never ran. The positive half — that the candidate was evaluated and
        left short — is what makes this test capable of failing.
        """
        res = self.scenario(
            ballots=[(CODEX, [ballot("codex", verdict="REFUTED")])],
            dispositions=[(OPERATOR, [disposition()])],
        )
        self.assertEvaluated(res)
        self.assertIn("QUORUM SHORTFALL", res.stdout)
        self.assertProfileNotApplied(res)

    def test_R4b_a_refutation_blocks_even_alongside_a_confirmation(self):
        """The case R-4 does not actually exercise.

        With a REFUTED ballot alone the candidate has zero confirmations, so it is short for a
        reason that has nothing to do with §6.2 — R-4 therefore still passes if the refutation
        guard is deleted. This is the scenario §6.2 is really about: a genuine confirmation and
        a genuine refutation on the same candidate, where a disposition must not tip it.
        """
        res = self.scenario(
            ballots=[
                (CODEX, [ballot("codex", verdict="CONFIRMED")]),
                (GEMINI, [ballot("gemini", verdict="REFUTED",
                                 proposition="LOC-INV-COORD-LAT-01")]),
            ],
            dispositions=[(OPERATOR, [disposition()])],
        )
        self.assertEvaluated(res)
        self.assertProfileNotApplied(res)
        self.assertIn("QUORUM SHORTFALL", res.stdout)

    def test_R5_disposition_with_no_admissible_ballot_confirms_nothing(self):
        """EBIV §6.5.3 — zero admissible ballots escalates under §6.3 as before."""
        res = self.scenario(
            ballots=[(CODEX, [ballot("codex", admissible=False)])],
            dispositions=[(OPERATOR, [disposition()])],
        )
        self.assertEvaluated(res)
        self.assertIn("QUORUM SHORTFALL", res.stdout)
        self.assertProfileNotApplied(res)

    def test_R6_disposition_for_an_unknown_candidate_is_reported_not_ignored(self):
        res = self.scenario(
            ballots=[(CODEX, [ballot("codex")])],
            dispositions=[(OPERATOR, [disposition(candidate="0" * 40)])],
        )
        self.assertEqual(res.returncode, 1, "a dangling disposition must never be silent")

    def test_R7_disposition_claiming_bare_CONFIRMED_is_refused(self):
        """EBIV §6.5.2 — the two verdicts must not be conflated."""
        res = self.scenario(
            ballots=[(CODEX, [ballot("codex")])],
            dispositions=[(OPERATOR, [disposition(verdict="CONFIRMED")])],
        )
        self.assertEqual(res.returncode, 1)
        self.assertProfileNotApplied(res)

    def test_R8_malformed_disposition_line_is_a_finding(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        fx = Fixture(Path(self._tmp.name))
        fx.append("ballots.jsonl", [ballot("codex")], CODEX)
        fx.write("docs/evidence/phase-3.5/dispositions.jsonl", "{not json\n")
        fx._commit_all("malformed disposition", OPERATOR)
        res = fx.check()
        self.assertEqual(res.returncode, 1, "a malformed line must not be skipped")

    def test_R9_two_verifiers_are_unaffected_by_a_disposition(self):
        """§6.1 already confirms; the profile must not downgrade or duplicate that."""
        res = self.scenario(
            ballots=[
                (CODEX, [ballot("codex")]),
                (GEMINI, [ballot("gemini", proposition="LOC-INV-COORD-LAT-01")]),
            ],
            dispositions=[(OPERATOR, [disposition()])],
        )
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertNotIn("QUORUM SHORTFALL", res.stdout)


if __name__ == "__main__":
    unittest.main()
