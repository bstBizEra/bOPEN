#!/usr/bin/env python3
"""
bOPEN governance state — derived from repository objects, not from an agent's narration.

Work package: WP-P35-09
Governing artifacts: AGENTS.md §16, §20.3, §25.1; BOPEN-GOV-EBIV-001 §6.2, §6.5

Why this exists
---------------
The operator's only view of what is ready to dispose has been an agent's summary. On 2026-08-08/09
a single agent produced fifteen defects in one session and caught none of them itself — including
five inside the very document written to support a merge decision, where it counted disposition
files and reported them as artifacts, surveyed commit authors and drew conclusions about identity,
and wrote "no candidate meets the two-verifier quorum" while fourteen propositions did.

The errors were not careless. They were direction-biased: each one made the work look better or a
finding look smaller. A maker cannot see that from inside, so the fix is not a more careful summary.
It is to remove the maker from the path between the repository and the operator.

Everything below is read from `ballots.jsonl`, the evidence manifest, the disposition files and the
decision register. Nothing is read from prose written to persuade. Where a fact cannot be derived,
this tool says so rather than inferring it.

What it does NOT do
-------------------
It does not dispose, confirm, merge, or recommend. `AGENTS.md` §20.3 keeps merge, release and
production outside agent authority, and §25.1 step 8 reserves disposition to the Completion
Authority. This prints a queue; the reading of it is the operator's.

Usage:
    python tools/governance_state.py
    python tools/governance_state.py --phase phase-3.5
    python tools/governance_state.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "evidence"
REGISTER = ROOT / "docs" / "decisions" / "DECISION-REGISTER.md"

PROFILE_VERDICT = "CONFIRMED_UNDER_TWO_AGENT_PROFILE"


def load_ballots(phase_dir: Path) -> list[dict]:
    path = phase_dir / "ballots.jsonl"
    if not path.is_file():
        return []
    out = []
    for index, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            out.append(json.loads(raw))
        except json.JSONDecodeError:
            out.append({"_malformed": True, "_line": index})
    return out


def candidate_state(ballots: list[dict]) -> dict[str, dict]:
    """Per candidate: who confirmed, who refuted, what was inadmissible.

    A refutation is tracked separately from a confirmation because EBIV §6.2 makes one reproducible
    REFUTED block regardless of how many confirmations oppose it. Collapsing them into a count is
    how a blocked candidate comes to look like a met quorum.
    """
    state: dict[str, dict] = defaultdict(
        lambda: {"confirm": set(), "refuted": set(), "inadmissible": set(),
                 "other": set(), "propositions": set(), "refuted_props": set(),
                 "no_same_id_followup": set(), "malformed": 0}
    )
    confirmed_elsewhere: dict[str, set[str]] = defaultdict(set)

    for b in ballots:
        if b.get("_malformed"):
            state["<malformed>"]["malformed"] += 1
            continue
        c = b.get("commit_oid", "<none>")
        s = state[c]
        prop = b.get("proposition_id", "?")
        s["propositions"].add(prop)
        verdict = str(b.get("verdict", "")).strip().upper()
        who = b.get("verifier_id", "?")
        if verdict == "CONFIRMED":
            adm = b.get("admissibility") or {}
            if not any(v is False for v in adm.values()):
                s["confirm"].add(who)
                confirmed_elsewhere[prop].add(c)
            else:
                s["inadmissible"].add(who)
        elif verdict == "REFUTED":
            s["refuted"].add(who)
            s["refuted_props"].add(prop)
        elif verdict == "INADMISSIBLE":
            s["inadmissible"].add(who)
        else:
            s["other"].add(f"{who}:{verdict or '<none>'}")

    # Follow-up resolved per PROPOSITION ID, not per candidate — and that is still not per CLAIM.
    #
    # Two corrections, an hour apart on 2026-08-10, in the same direction:
    #
    #   1. Aggregating by CANDIDATE listed `aa2a74b2` as blocked while both of its refuted
    #      propositions were CONFIRMED at a disposed successor. Fixed by resolving per proposition.
    #   2. That fix was still wrong, because PROPOSITION IDS ARE RENUMBERED BETWEEN REVISIONS. The
    #      base-path escape refuted as `P35-04R-16` is carried by `P35-04R3-16` ("a path escaping the
    #      configured base prefix is refused, not resolved", CONFIRMED at `1b39a30`), and the
    #      fractional-lifetime defect refuted as `P35-05aR3-02` is carried by `P35-05aR4-01/02`
    #      (CONFIRMED at `2c31379`, which is disposed). Neither shares an ID with the refutation it
    #      answers, so both still read here as never carried.
    #
    # Matching a renumbered successor requires reading proposition TEXT, which this tool does not do
    # and should not guess at. So the field below is named for exactly what it computes — no later
    # ballot under the SAME identifier — and the rendered output says the rest. An entry here means
    # "look for a renumbered successor", not "unaddressed".
    #
    # And none of it is a §6.2 discharge in any case: a discharge is a FAILED REPRODUCTION. Of the
    # five refutations reproduced at `ebb4dcc` on 2026-08-10, two no longer reproduce and three do,
    # one of which awaits an operator decision and cannot be closed by any agent.
    for oid, s in state.items():
        if oid == "<malformed>":
            continue
        s["no_same_id_followup"] = {
            p for p in s["refuted_props"] if not (confirmed_elsewhere.get(p, set()) - {oid})
        }
    return dict(state)


def dispositions(phase_dir: Path) -> tuple[dict[str, Path], list[Path]]:
    """Signed dispositions and unsigned drafts, kept apart.

    A draft that reads like a disposition is the failure this separation prevents: the queue must
    never show prepared-for-signature as signed.
    """
    signed: dict[str, Path] = {}
    drafts: list[Path] = []
    for p in sorted(phase_dir.glob("*disposition*.md")):
        text = p.read_text(encoding="utf-8", errors="replace")
        if "DRAFT, UNSIGNED" in text or "THIS IS NOT A DISPOSITION" in text or p.name.endswith("-DRAFT.md"):
            drafts.append(p)
            continue
        for oid in set(re.findall(r"\b([0-9a-f]{7,40})\b", text)):
            signed.setdefault(oid, p)
    return signed, drafts


def open_decisions() -> list[tuple[str, str]]:
    if not REGISTER.is_file():
        return []
    out = []
    for line in REGISTER.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("| DEC-"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 3 and "**Proposed" in cells[2]:
            out.append((cells[0], cells[2][:80]))
    return out


def short(oid: str) -> str:
    return oid[:12] if oid and oid != "<none>" else oid


def build(phase_dir: Path) -> dict:
    ballots = load_ballots(phase_dir)
    state = candidate_state(ballots)
    signed, drafts = dispositions(phase_dir)

    ready, blocked, short_of_quorum, disposed, disposed_refuted = [], [], [], [], []
    carried_elsewhere = []
    for oid, s in sorted(state.items()):
        if oid == "<malformed>":
            continue
        is_disposed = any(oid.startswith(k) or k.startswith(oid[:7]) for k in signed)
        row = {
            "candidate": short(oid),
            "propositions": len(s["propositions"]),
            "confirming_verifiers": sorted(s["confirm"]),
            "refuted_by": sorted(s["refuted"]),
            "inadmissible_from": sorted(s["inadmissible"]),
            "refuted_propositions": sorted(s["refuted_props"]),
            "refuted_propositions_with_no_later_ballot_under_the_same_id": sorted(s["no_same_id_followup"]),
            "disposition_file": signed.get(next((k for k in signed if oid.startswith(k)), ""), None),
        }
        row["disposition_file"] = str(row["disposition_file"].name) if row["disposition_file"] else None

        if s["refuted"] and is_disposed:
            # A triage pointer, deliberately named for what it measures rather than for what it
            # might mean. An earlier name — "disposed while carrying a refutation" — was semantically
            # stronger than the fact and was corrected after independent re-check found all four
            # entries to be the normal shape: the disposition binds a successor candidate and names
            # the refuted one only as superseded.
            #
            # The tool aggregates by CANDIDATE and does not bind disposition scope to proposition
            # scope, so it cannot distinguish that normal shape from a genuine acceptance of refuted
            # state. It reports the pointer; the reading is the operator's.
            disposed_refuted.append(row)
        elif s["refuted"] and not s["no_same_id_followup"]:
            carried_elsewhere.append(row)
        elif s["refuted"]:
            blocked.append(row)
        elif is_disposed:
            disposed.append(row)
        elif len(s["confirm"]) >= 2:
            ready.append({**row, "route": "EBIV §6.1 — two independent verifiers"})
        elif len(s["confirm"]) == 1:
            ready.append({**row, "route": f"EBIV §6.5 — one verifier, needs {PROFILE_VERDICT}"})
        else:
            short_of_quorum.append(row)

    return {
        "phase": phase_dir.name,
        "ballots": len([b for b in ballots if not b.get("_malformed")]),
        "malformed_ballot_lines": sum(1 for b in ballots if b.get("_malformed")),
        "awaiting_disposition": ready,
        "blocked_by_refutation": blocked,
        "refuted_proposition_carried_under_the_same_id_elsewhere": carried_elsewhere,
        "refuted_candidate_referenced_by_a_disposition": disposed_refuted,
        "no_admissible_confirmation": short_of_quorum,
        "disposed": disposed,
        "unsigned_drafts": [p.name for p in drafts],
        "open_decision_requests": open_decisions(),
    }


def render(data: dict) -> None:
    print(f"bOPEN governance state — {data['phase']}")
    print(f"derived from repository objects; nothing here is an agent's assessment\n")

    if data["malformed_ballot_lines"]:
        print(f"!! {data['malformed_ballot_lines']} malformed ballot line(s) — not counted anywhere\n")

    print(f"AWAITING OPERATOR DISPOSITION — {len(data['awaiting_disposition'])}")
    if not data["awaiting_disposition"]:
        print("    none")
    for r in data["awaiting_disposition"]:
        extra = f", {len(r['inadmissible_from'])} inadmissible" if r["inadmissible_from"] else ""
        print(f"    {r['candidate']}  {r['propositions']} propositions{extra}")
        print(f"        verifier(s): {', '.join(r['confirming_verifiers'])}")
        print(f"        route: {r['route']}")

    print(f"\nBLOCKED BY REFUTATION — {len(data['blocked_by_refutation'])}")
    print("    EBIV §6.2: discharged only by a failed reproduction, never by re-assertion.")
    print("    Each proposition below has NO LATER BALLOT UNDER THE SAME IDENTIFIER. That is not the")
    print("    same as unaddressed: proposition IDs are renumbered between revisions, and two")
    print("    refutations verified on 2026-08-10 were in fact carried by renumbered successors")
    print("    (P35-04R-16 -> P35-04R3-16; P35-05aR3-02 -> P35-05aR4-01/02). Matching those needs")
    print("    the proposition TEXT, which this tool does not read. An entry here means LOOK FOR A")
    print("    RENUMBERED SUCCESSOR.")
    if not data["blocked_by_refutation"]:
        print("    none")
    for r in data["blocked_by_refutation"]:
        print(f"    {r['candidate']}  refuted by {', '.join(r['refuted_by'])}"
              f"  (also {len(r['confirming_verifiers'])} confirming)")
        print(f"        open: {', '.join(r['refuted_propositions_with_no_later_ballot_under_the_same_id'])}")

    print(f"\nREFUTED PROPOSITION CARRIED UNDER THE SAME ID ELSEWHERE — "
          f"{len(data['refuted_proposition_carried_under_the_same_id_elsewhere'])}")
    print("    Every proposition refuted here later took an admissible CONFIRMED ballot under the")
    print("    SAME identifier at another candidate. That is NOT a §6.2 discharge — a discharge is a")
    print("    FAILED REPRODUCTION, and a later confirmation is not one. Split out on 2026-08-10")
    print("    after candidate-level aggregation reported one such candidate blocked for a third time.")
    if not data["refuted_proposition_carried_under_the_same_id_elsewhere"]:
        print("    none")
    for r in data["refuted_proposition_carried_under_the_same_id_elsewhere"]:
        print(f"    {r['candidate']}  refuted by {', '.join(r['refuted_by'])}"
              f"  ->  {', '.join(r['refuted_propositions'])} carried elsewhere")

    print(f"\nREFUTED CANDIDATE REFERENCED BY A SIGNED DISPOSITION — "
          f"{len(data['refuted_candidate_referenced_by_a_disposition'])}")
    print("    A candidate carrying a REFUTED ballot whose SHA appears somewhere in a signed")
    print("    disposition. This is a TRIAGE POINTER, not a finding.")
    print("    The normal and expected shape is that the disposition binds a SUCCESSOR candidate and")
    print("    names this one only as superseded — independently verified to be the case for all four")
    print("    entries on 2026-08-10. This tool aggregates by candidate and does not bind disposition")
    print("    scope to proposition scope, so it cannot tell that shape from a real one. Read each.")
    if not data["refuted_candidate_referenced_by_a_disposition"]:
        print("    none")
    for r in data["refuted_candidate_referenced_by_a_disposition"]:
        print(f"    {r['candidate']}  refuted by {', '.join(r['refuted_by'])}"
              f"  ->  {r['disposition_file']}")

    print(f"\nNO ADMISSIBLE CONFIRMATION — {len(data['no_admissible_confirmation'])}")
    if not data["no_admissible_confirmation"]:
        print("    none")
    for r in data["no_admissible_confirmation"]:
        print(f"    {r['candidate']}  {r['propositions']} propositions, 0 confirming verifiers")

    print(f"\nDISPOSED — {len(data['disposed'])}")
    for r in data["disposed"]:
        print(f"    {r['candidate']}  {r['disposition_file']}")

    if data["unsigned_drafts"]:
        print(f"\nUNSIGNED DRAFTS — {len(data['unsigned_drafts'])}  (prepared, NOT dispositions)")
        for n in data["unsigned_drafts"]:
            print(f"    {n}")

    print(f"\nOPEN DECISION REQUESTS — {len(data['open_decision_requests'])}")
    for did, _ in data["open_decision_requests"]:
        print(f"    {did}")

    print("\nThis tool disposes nothing, confirms nothing and recommends nothing.")
    print("Merge, release and production remain outside agent authority (AGENTS.md §20.3);")
    print("disposition is reserved to the Completion Authority (§25.1 step 8).")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phase", default="phase-3.5")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    phase_dir = EVIDENCE / args.phase
    if not phase_dir.is_dir():
        print(f"ERROR: no evidence directory at {phase_dir}", file=sys.stderr)
        return 2

    data = build(phase_dir)
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        render(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
