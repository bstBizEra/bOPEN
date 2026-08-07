# DEC-P35-ORPHAN-CANDIDATE-ANCHOR — 23 ballots are anchored to a commit no ref reaches

**Decision ID:** `DEC-P35-ORPHAN-CANDIDATE-ANCHOR`
**Version:** `1.0.0`
**Status:** **Proposed — decision request raised under `AGENTS.md` §16**
**Issued:** 2026-08-08
**Owner:** Engineering Authority
**Raised by:** Claude (agent, Motor role) — advisory only
**Governing:** `AGENTS.md` §21.4 (history is not rewritten), §23 (baselines); [`BOPEN-GOV-EBIV-001`](../00-governance/BOPEN-GOV-EBIV-001.md)

---

## 1. The finding

Candidate `119f2d8cf678624c055c8d1be48c770b3936de11` — *"fix(kernel): stop truncating the assertion
lifetime before comparing it"*, Claude, 2026-08-01 — carries **23 ballots** in
`docs/evidence/phase-3.5/ballots.jsonl` and is reachable from **zero refs**. The object survives only
because git has not yet pruned it.

A successor commit `98f5dd9` exists with the identical subject and date, and **is** reachable from
`HEAD`. The commit was recreated — consistent with the 2026-08-01 identity remediation recorded in
`AGENTS.md` §23.0 — and the ballots were left pointing at the pre-rewrite object.

## 2. The good news, established rather than assumed

| Object | Tree |
| :--- | :--- |
| orphan `119f2d8` | `210c6f4be07837f01c6e866b490aca730afc529f` |
| successor `98f5dd9` (reachable from `HEAD`) | `210c6f4be07837f01c6e866b490aca730afc529f` |
| `tree_oid` claimed by all 23 ballots | `210c6f4be078…` |

**The trees are identical.** The content those 23 ballots verified is intact and still reachable
through `98f5dd9`. The verification claim is substantively sound; only its `commit_oid` anchor points
at an object outside the reachable history.

## 3. Why it still needs a decision

`tools/check_evidence_anchors.py` currently reports `PASS — every recorded anchor resolves to a real
object of the expected type`, because the orphan is still in the object database. **That PASS has a
shelf life.** A `git gc` past the reflog expiry window prunes an unreachable object, and on that day
23 ballots become permanently unresolvable and the check flips to failing — with no change to the
repository and no event to explain it.

This is a silent, dated failure. It is cheaper to defuse now than to diagnose later, and the
repository has already paid once for an unresolvable anchor (`BOPEN-ENG-LOOP-001` §2.6 records that
the check exists because of a Phase 3 incident).

## 4. Options

| # | Option | Assessment |
| :--- | :--- | :--- |
| 1 | **Pin the orphan with a ref** — e.g. `git tag evidence-anchor/119f2d8 119f2d8` — and record the tree-equivalence with `98f5dd9` here | **Recommended.** Non-destructive, defuses the gc time-bomb, changes no evidence, and preserves the anchor exactly as balloted. One command |
| 2 | **Re-anchor the 23 ballots to `98f5dd9`** | Mutates recorded evidence to fix a bookkeeping problem. The trees match, so the claim would remain true — but rewriting a verifier's ballot after the fact is precisely what `DEC-P4-LOCATION-BALLOT-ATTRIBUTION` established should not be done by a non-verifier |
| 3 | **Do nothing** | Accepts a dated, silent failure of `check_evidence_anchors.py` |

Option 1 plus this record is the smallest change that makes the situation legible and stable.

## 5. What this decision request does not do

It does not alter any ballot, verdict, or quorum state, and does not rewrite history. Candidate
`119f2d8` has one verifier and is among the 26 in
[`DEC-P35-QUORUM-TOOL-GAP`](DEC-P35-QUORUM-TOOL-GAP.md); nothing here confirms it.

Raised advisory-only. Confers no implementation, approval, merge, release or production authority.
