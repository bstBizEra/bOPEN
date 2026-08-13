# The disposition queue is two items, not six — correction, 2026-08-11

**Status:** **CORRECTION RECORD — advisory.** Disposes nothing and changes no verdict.
**Work package:** `BOPEN-WP-GOV-QUEUE-001`
**Raised at:** `ed992ff` (`main`)
**Raised by:** Claude (agent, Motor role), before writing disposition drafts that would have been wrong.

---

## 1. What happened

`tools/governance_state.py` reports **`AWAITING OPERATOR DISPOSITION — 6`**. Four of the six are
already settled. The queue the operator has been shown is **three times larger than the real one.**

The intended next action was to write disposition drafts for the four that lacked them. Checking what
each candidate *was* — rather than trusting the count — stopped that.

## 2. The true state of all six

| Candidate | What it is | Actual state |
| :--- | :--- | :--- |
| `6ce069e3c3e0` | **WP-P35-01**, 16 ballots, gemini | **DISPOSED** — `CONFIRMED_UNDER_TWO_AGENT_PROFILE`, operator disposition **2026-08-02** |
| `a969bb59b85c` | **WP-P35-02**, 8 ballots, gemini | **DISPOSED** — same verdict and date |
| `767cb8143fa2` | **WP-P35-03**, 11 ballots, gemini | **DISPOSED** — same verdict and date |
| `f12e5fc0fc91` | **WP-P35-05a**, earlier candidate (R2) | **SUPERSEDED** — WP-P35-05a was disposed at `2c31379ad7ed`, 27 propositions, 2026-08-02 |
| `d3a5be25ce6e` | **Notification Stage 1**, 20 propositions | **GENUINELY AWAITING** — draft prepared: `notification-stage1-disposition-DRAFT.md` |
| `0412b85f02f3` | **WP-P35-08** tenant cascade, 16 propositions | **GENUINELY AWAITING** — draft prepared: `wp-p35-08-disposition-DRAFT.md` |

**Both genuinely pending items already have a prepared draft.** There is no draft-writing work
outstanding; there are two signatures outstanding.

## 3. Why the tool could not see it — a second record format

The four settled dispositions are recorded in
[`manifest.json`](manifest.json) under `roles.candidate_disposition`:

```json
"WP-P35-01": { "commit": "6ce069e3…", "ballots": 16, "verifiers": ["gemini"],
               "verdict": "CONFIRMED_UNDER_TWO_AGENT_PROFILE",
               "note": "operator disposition 2026-08-02; …" }
```

`governance_state.py` discovers dispositions by globbing `*disposition*.md` and matching SHAs found
in the prose. **It never reads `manifest.json`.** A disposition recorded in the manifest and not in a
markdown file is invisible to it, and the candidate stays in the queue forever.

`AGENT-ALIGNMENT.md` line 24 states the same outcome independently:
*"WP-P35-01..03 `CONFIRMED_UNDER_TWO_AGENT_PROFILE` (one verifier + operator disposition)"*.

**Three independent records agree; the tool reads none of them.**

## 4. Fourth occurrence of one failure

This is the fourth time the same tool has reported settled work as open, each time because the
follow-up record exists in a shape it does not read:

| | Cause | Fixed at |
| ---: | :--- | :--- |
| 1 | Aggregated by candidate, not proposition | `c15fbde` |
| 2 | Matched proposition IDs, which are renumbered between revisions | `92ccbb1` |
| 3 | Could not see a withdrawn proposition | `561333a` |
| 4 | **Reads `*disposition*.md` but not `manifest.json`** | *this record* |

Every one made the situation look **worse** than it was, which is the opposite direction from the
fifteen maker defects the tool was built to catch — and no less wrong. A queue inflated threefold
costs the operator the same attention a hidden defect costs, spent on nothing.

## 5. What is not fixed here, and why

The repair is in `tools/governance_state.py`: read `manifest.json`'s
`roles.candidate_disposition` alongside the markdown files, and treat a candidate as disposed when
**either** record covers it. `tools/` is a `governance_implementation_path` in
`config/delegation_envelope.json`, so that change classifies **`AGENT_BALLOT_REQUIRED`** and the
ballot layer is `NOT_ACTIVE`.

It is therefore recorded rather than applied. **Until it is applied, read this file alongside the
tool's output** — the tool's `AWAITING OPERATOR DISPOSITION` count is an upper bound, not a queue.

## 6. What the operator actually has waiting

```text
Notification Stage 1   d3a5be25   20 propositions, 1 INADMISSIBLE   draft prepared
WP-P35-08 cascade      0412b85f   16 propositions, 0 refutations    draft prepared
```

Both are on the `EBIV` §6.5 route — one independent verifier plus a Completion Authority disposition
standing in for the second verifier — so both must be recorded
`CONFIRMED_UNDER_TWO_AGENT_PROFILE`, never bare `CONFIRMED`.

The `WP-P35-08` draft asks whether Notification Stage 1 should be accepted **after** it, since the
cascade defect Notification carried is what `WP-P35-08` repairs. That sequencing question is the only
open dependency between them.

Recorded advisory-only. Confers no verdict, disposition, merge, release or production authority.
