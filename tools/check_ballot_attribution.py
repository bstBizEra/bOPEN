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


def check_phase(phase_dir: Path, register: dict) -> tuple[list[Finding], int, set[str]]:
    ballots_path = phase_dir / "ballots.jsonl"
    findings: list[Finding] = []
    countable: set[str] = set()

    if not ballots_path.is_file():
        return findings, 0, countable

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

    return findings, total, countable


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", help="limit to one phase directory, e.g. phase-3.5")
    args = parser.parse_args()

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

    for phase_dir in phase_dirs:
        findings, total, countable = check_phase(phase_dir, register)
        if total == 0 and not findings:
            continue
        grand_total += total
        all_findings.extend(findings)
        quorum = len(countable)
        print(
            f"- {phase_dir.name}: {total} ballot(s), "
            f"{quorum} attributable verifier(s) toward a quorum of 2"
        )
        if quorum < 2:
            print(
                f"    quorum NOT MET — EBIV §6.1 requires two independent verifiers. "
                f"A confirmation cannot be realized."
            )

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
