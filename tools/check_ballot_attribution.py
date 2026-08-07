#!/usr/bin/env python3
"""
bOPEN ballot attribution validator.

Enforces BOPEN-GOV-IDENT-001 §4 and, through it, BOPEN-GOV-EBIV-001 §3 and §6.1.

A ballot records who cast it in a `verifier_id` field. On its own that is a single
self-declaration in a single place — any agent, including the disqualified Maker, could write
`"verifier_id": "Codex"` and nothing would object. This tool binds that field to a second,
independently written record: the git author of the commit that introduced the ballot line.

    ballot.verifier_id  ->  git author of the introducing commit  ->  identity register

Two places must agree. That does not stop deliberate forgery — local git identity is
self-declared — but it catches every accidental collapse, and defeating it requires deliberate
effort rather than inattention.

Usage:
    python tools/check_ballot_attribution.py
    python tools/check_ballot_attribution.py --phase phase-3.5

Exit codes:
    0  every ballot is attributable and admissible, or there are no ballots yet
    1  one or more ballots are unattributable, misattributed, or violate a register rule
    2  the check could not run
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = ROOT / "docs" / "evidence"
REGISTER = ROOT / "docs" / "00-governance" / "agent-identity-register.json"

# The verdict labels EBIV §6.5.2 insists are different verdicts. Kept apart deliberately: a
# disposition claiming bare CONFIRMED is refused, because conflating the two is the specific
# thing §6.5.2 forbids.
PROFILE_VERDICT = "CONFIRMED_UNDER_TWO_AGENT_PROFILE"


def configure_root(root: Path) -> None:
    """Point the check at a different repository.

    Exists so the Refusal Matrix (WP-P35-07 §4) can be tested at all. A control that can only
    ever inspect one repository cannot be shown to refuse anything, because every negative case
    would have to be staged as false evidence in the real record.

    This does not weaken the control. The canonical invocation (AGENTS.md §19.4, and
    check_authority_bootstrap.py) passes no arguments and still resolves the real repository;
    a fixture root only ever yields a verdict about the fixture.
    """
    global ROOT, EVIDENCE_ROOT, REGISTER
    ROOT = root.resolve()
    EVIDENCE_ROOT = ROOT / "docs" / "evidence"
    REGISTER = ROOT / "docs" / "00-governance" / "agent-identity-register.json"


class Finding:
    def __init__(self, rule: str, locator: str, detail: str) -> None:
        self.rule = rule
        self.locator = locator
        self.detail = detail

    def render(self) -> str:
        return f"  [{self.rule}] {self.locator}\n      {self.detail}"


def git(*args: str) -> tuple[int, str]:
    try:
        done = subprocess.run(
            ["git", *args], cwd=str(ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace", check=False,
        )
    except FileNotFoundError:
        print("ERROR: git executable not found on PATH", file=sys.stderr)
        raise SystemExit(2)
    return done.returncode, done.stdout


def load_register() -> dict:
    if not REGISTER.is_file():
        print(
            f"ERROR: identity register not found at {REGISTER.relative_to(ROOT).as_posix()}\n"
            f"       BOPEN-GOV-IDENT-001 must exist before ballots can be attributed.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return json.loads(REGISTER.read_text(encoding="utf-8"))


def resolve_agent(register: dict, name: str, email: str) -> tuple[str | None, str]:
    """Map a git ident to a registered agent_id.

    Returns (agent_id, how) where `how` is 'canonical', 'legacy', 'forbidden', 'operator' or
    'unknown'. The distinction matters: a legacy ident is attributable but should not be used
    for new work, while a forbidden one is a finding regardless of who it names.
    """
    ident = f"{name} <{email}>"

    for entry in register.get("forbidden", []):
        if ident == entry["pattern"]:
            return None, "forbidden"

    for agent in register["agents"]:
        canonical = agent["canonical"]
        if email == canonical["email"] and name.startswith(canonical["name_prefix"]):
            return agent["agent_id"], "operator" if agent.get("is_human") else "canonical"
        if ident in agent.get("legacy_recognised", []):
            return agent["agent_id"], "legacy"

    return None, "unknown"


def introducing_commit(path: Path, line_no: int) -> tuple[str, str, str] | None:
    """Return (sha, author_name, author_email) for the commit that introduced a line.

    `git blame -L` is used rather than `git log -S` because a ballot line is not guaranteed to
    contain a unique string, and blame answers the question actually being asked: which commit
    put *this* line here.
    """
    code, out = git(
        "blame", "-L", f"{line_no},{line_no}", "--line-porcelain", "--",
        path.relative_to(ROOT).as_posix(),
    )
    if code != 0 or not out.strip():
        return None

    sha = out.splitlines()[0].split()[0]
    author = author_mail = ""
    for line in out.splitlines():
        if line.startswith("author "):
            author = line[len("author "):].strip()
        elif line.startswith("author-mail "):
            author_mail = line[len("author-mail "):].strip().strip("<>")
    return sha, author, author_mail


def manifest_maker(phase_dir: Path) -> str | None:
    manifest = phase_dir / "manifest.json"
    if not manifest.is_file():
        return None
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    maker = data.get("roles", {}).get("maker", "")
    return maker.split()[0].lower() if maker else None


def check_phase(
    phase_dir: Path, register: dict
) -> tuple[list[Finding], int, set[str], dict[str, set[str]]]:
    ballots_path = phase_dir / "ballots.jsonl"
    findings: list[Finding] = []
    countable: set[str] = set()
    by_candidate: dict[str, set[str]] = {}

    if not ballots_path.is_file():
        return findings, 0, countable, by_candidate

    lines = ballots_path.read_text(encoding="utf-8").splitlines()
    maker = manifest_maker(phase_dir)
    seen_commits: dict[str, str] = {}   # sha -> verifier_id, for R5
    total = 0

    for index, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        total += 1
        locator = f"{ballots_path.relative_to(ROOT).as_posix()}:{index}"

        try:
            ballot = json.loads(raw)
        except json.JSONDecodeError as exc:
            findings.append(Finding("R4", locator, f"ballot is not valid JSON: {exc}"))
            continue

        claimed = str(ballot.get("verifier_id", "")).strip().lower()
        if not claimed:
            findings.append(Finding("R4", locator, "ballot has no verifier_id"))
            continue

        blame = introducing_commit(ballots_path, index)
        if blame is None:
            findings.append(
                Finding("R4", locator,
                        "the introducing commit could not be resolved; is the ballot committed?")
            )
            continue

        sha, author_name, author_email = blame
        agent_id, how = resolve_agent(register, author_name, author_email)

        if how == "forbidden":
            findings.append(
                Finding("R2", locator,
                        f"introduced by a forbidden identity {author_name} <{author_email}> "
                        f"in {sha[:12]}. A commit designed to be untraceable cannot carry a "
                        f"verification verdict.")
            )
            continue

        if how == "unknown":
            findings.append(
                Finding("R4", locator,
                        f"introducing commit {sha[:12]} carries an unregistered identity "
                        f"{author_name} <{author_email}>. Ballot is UNATTRIBUTABLE and does not "
                        f"count toward quorum.")
            )
            continue

        if how == "operator":
            findings.append(
                Finding("R1", locator,
                        f"introducing commit {sha[:12]} carries the operator identity. An agent "
                        f"must not commit as the operator, and a ballot cast under it cannot be "
                        f"attributed to any agent.")
            )
            continue

        if agent_id != claimed:
            findings.append(
                Finding("R4", locator,
                        f"verifier_id claims '{claimed}' but commit {sha[:12]} was authored by "
                        f"'{agent_id}' ({author_name} <{author_email}>). The two records disagree.")
            )
            continue

        if maker and agent_id == maker:
            findings.append(
                Finding("R3", locator,
                        f"'{agent_id}' is the Maker recorded in manifest.json and is disqualified "
                        f"as a verifier of its own work (EBIV §3).")
            )
            continue

        if ballot.get("independent_of_maker") is False:
            findings.append(
                Finding("R3", locator, "ballot declares independent_of_maker: false; it is void.")
            )
            continue

        if sha in seen_commits and seen_commits[sha] != agent_id:
            findings.append(
                Finding("R5", locator,
                        f"commit {sha[:12]} introduced ballots for both "
                        f"'{seen_commits[sha]}' and '{agent_id}'. One actor wrote both, whatever "
                        f"the verifier_id fields say.")
            )
            continue

        seen_commits[sha] = agent_id
        if how == "legacy":
            print(
                f"  note: {locator} attributed via a legacy identity "
                f"({author_name} <{author_email}>); acceptable for history, not for new work."
            )
        countable.add(agent_id)

        # Quorum is a property of a candidate, not of a phase. See the note in main().
        #
        # It is also a property of ADMISSIBLE CONFIRMED ballots, not of attributable ones.
        # Until WP-P35-07 this counted every attributable ballot alike, so a REFUTED ballot
        # advanced a candidate toward "two verifiers" exactly as a CONFIRMED one did — the
        # opposite of EBIV §6.2, where one reproducible refutation blocks. An inadmissible
        # ballot was likewise counted despite EBIV §6.5.3.
        state = by_candidate.setdefault(
            ballot.get("commit_oid", "<none>"), {"confirm": set(), "refuted": set()}
        )
        verdict = str(ballot.get("verdict", "")).strip().upper()
        inadmissible = [
            rule for rule, held in (ballot.get("admissibility") or {}).items() if held is False
        ]

        if verdict == "REFUTED":
            state["refuted"].add(agent_id)
        elif inadmissible:
            print(
                f"  note: {locator} is INADMISSIBLE ({', '.join(sorted(inadmissible))}) and does "
                f"not count toward quorum (EBIV §6.5.3). It is attributable; that is a different "
                f"property."
            )
        elif verdict == "CONFIRMED":
            state["confirm"].add(agent_id)
        else:
            print(
                f"  note: {locator} carries verdict {verdict or '<none>'!r}, which is neither "
                f"CONFIRMED nor REFUTED; it does not count toward quorum."
            )

    return findings, total, countable, by_candidate


def load_dispositions(phase_dir: Path, register: dict, candidates: set[str]) -> tuple[list[Finding], dict[str, dict]]:
    """Read Completion Authority dispositions for the EBIV §6.5 two-agent profile.

    A disposition never confirms anything by itself. It only supplies the operator act that
    §6.5.1 requires alongside one admissible independent CONFIRMED ballot, and every way it can
    be wrong is a finding rather than a silent skip — a disposition that does nothing quietly is
    indistinguishable from one that was never written.
    """
    findings: list[Finding] = []
    valid: dict[str, dict] = {}
    path = phase_dir / "dispositions.jsonl"
    if not path.is_file():
        return findings, valid

    for index, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        locator = f"{path.relative_to(ROOT).as_posix()}:{index}"

        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            findings.append(Finding("D1", locator, f"disposition is not valid JSON: {exc}"))
            continue

        blame = introducing_commit(path, index)
        if blame is None:
            findings.append(
                Finding("D2", locator,
                        "the introducing commit could not be resolved; is the disposition "
                        "committed?")
            )
            continue

        sha, author_name, author_email = blame
        _, how = resolve_agent(register, author_name, author_email)

        # The integrity condition (DEC-P35-QUORUM-TOOL-GAP §6.4). Without it an agent could write
        # a disposition confirming its own work, reintroducing on the authority side the defect
        # DEC-P4-LOCATION-BALLOT-ATTRIBUTION repaired on the verifier side. This is the one place
        # where AGENTS.md §21.2.1 is load-bearing rather than hygienic.
        if how != "operator":
            findings.append(
                Finding("D3", locator,
                        f"introduced by {author_name} <{author_email}> in {sha[:12]}, which is "
                        f"not the operator identity. A Completion Authority disposition may be "
                        f"DRAFTED by an agent but only COMMITTED by the operator (§21.2.1).")
            )
            continue

        verdict = str(record.get("verdict", "")).strip()
        if verdict != PROFILE_VERDICT:
            findings.append(
                Finding("D4", locator,
                        f"verdict is {verdict!r}; a two-agent disposition must be labelled "
                        f"{PROFILE_VERDICT}. EBIV §6.5.2: §6.1's CONFIRMED and this are different "
                        f"verdicts and must not be conflated.")
            )
            continue

        candidate = str(record.get("candidate_commit_oid", "")).strip()
        if candidate not in candidates:
            findings.append(
                Finding("D5", locator,
                        f"names candidate {candidate[:12] or '<none>'}, which has no ballots in "
                        f"this phase. A disposition for a candidate nobody verified is reported, "
                        f"never ignored.")
            )
            continue

        valid[candidate] = record

    return findings, valid


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", help="limit to one phase directory, e.g. phase-3.5")
    parser.add_argument(
        "--root",
        type=Path,
        help="repository to inspect (default: this tool's own repository). See configure_root.",
    )
    args = parser.parse_args()

    if args.root is not None:
        configure_root(args.root)

    code, _ = git("rev-parse", "--git-dir")
    if code != 0:
        print("ERROR: not a git repository", file=sys.stderr)
        return 2

    register = load_register()

    if not EVIDENCE_ROOT.is_dir():
        print(f"ERROR: no evidence directory at {EVIDENCE_ROOT}", file=sys.stderr)
        return 2

    phase_dirs = sorted(
        d for d in EVIDENCE_ROOT.iterdir()
        if d.is_dir() and (args.phase is None or d.name == args.phase)
    )

    print("bOPEN ballot attribution check (BOPEN-GOV-IDENT-001 §4)")

    all_findings: list[Finding] = []
    grand_total = 0
    unmet: list[str] = []

    for phase_dir in phase_dirs:
        findings, total, countable, by_candidate = check_phase(phase_dir, register)
        if total == 0 and not findings:
            continue
        grand_total += total
        all_findings.extend(findings)
        print(f"- {phase_dir.name}: {total} ballot(s), {len(countable)} distinct verifier(s)")

        # Quorum is counted PER CANDIDATE COMMIT, not per phase.
        #
        # EBIV §3 assigns roles per work package and §6.1 requires two verifiers to confirm a
        # proposition. A phase-level count says "2 of 2" when one package has two verifiers and
        # three have one each — which is exactly what this file reported on 2026-08-01, and the
        # false reading propagated into two agent reports before anyone checked by hand.
        # A check that reports a weaker property than the rule it enforces is worse than no
        # check, because its PASS is quoted as if it were the rule.
        disposition_findings, dispositions = load_dispositions(
            phase_dir, register, set(by_candidate)
        )
        all_findings.extend(disposition_findings)

        for candidate in sorted(by_candidate):
            state = by_candidate[candidate]
            verifiers, refuted = state["confirm"], state["refuted"]
            short = candidate[:12] if candidate != "<none>" else candidate
            print(
                f"    candidate {short}: {len(verifiers)} confirming verifier(s) "
                f"[{', '.join(sorted(verifiers)) or '—'}] toward a quorum of 2"
            )

            if refuted:
                # EBIV §6.2. Discharged only by a failed reproduction — never by a second
                # opinion, and never by a disposition.
                print(
                    f"      REFUTED by [{', '.join(sorted(refuted))}] — blocks regardless of "
                    f"confirmations or disposition (EBIV §6.2)."
                )
                unmet.append(f"{phase_dir.name}/{short}")
                continue

            if len(verifiers) >= 2:
                continue

            # EBIV §6.5: one admissible CONFIRMED ballot PLUS an operator disposition. The
            # disposition stands in for the second verifier; it does not pretend to be one, and
            # it cannot manufacture the ballot it stands beside.
            if len(verifiers) == 1 and candidate in dispositions:
                print(
                    f"      {PROFILE_VERDICT} — one independent verifier plus a Completion "
                    f"Authority disposition (EBIV §6.5, {dispositions[candidate].get('disposition_id', '?')}). "
                    f"This is not §6.1's CONFIRMED and must not be quoted as it."
                )
                continue

            print(
                f"      quorum NOT MET — EBIV §6.1 requires two independent verifiers, and no "
                f"§6.5 disposition applies. A confirmation cannot be realized for this candidate."
            )
            unmet.append(f"{phase_dir.name}/{short}")

    if grand_total == 0:
        print("- no ballots recorded yet")
        print("\nPASS — nothing to attribute. This is not a verified state; it is an empty one.")
        return 0

    if all_findings:
        print(f"\nFAIL — {len(all_findings)} attribution finding(s):\n")
        for finding in all_findings:
            print(finding.render())
        print(
            "\nAn unattributable ballot does not count toward quorum (AGENTS.md §21.3). "
            "Register: docs/00-governance/agent-identity-register.json"
        )
        return 1

    print("\nPASS — every ballot binds to a registered agent distinct from the Maker.")

    # PASS here means *attributable*, and nothing more. A quorum shortfall is not an attribution
    # failure — EBIV §6.3 makes it an escalation to the Completion Authority, which is a state
    # rather than an error — so it must not change the exit code. But it must not be silent
    # either: this line exists because the previous phase-level summary was twice quoted as
    # "quorum met" when three of four candidates had a single verifier.
    if unmet:
        print(
            f"\nQUORUM SHORTFALL — {len(unmet)} candidate(s) below two verifiers: "
            f"{', '.join(unmet)}"
        )
        print(
            "This PASS attests attribution only. It does not attest quorum, and must not be "
            "quoted as though it did. EBIV §6.3: fewer than two admissible ballots escalates to "
            "the Completion Authority and never auto-passes."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
