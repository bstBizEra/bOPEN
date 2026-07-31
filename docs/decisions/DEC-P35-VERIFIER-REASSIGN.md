# DEC-P35-VERIFIER-REASSIGN — Codex cannot both remediate and verify `WP-P35-01`..`03`

**Decision ID:** `DEC-P35-VERIFIER-REASSIGN`
**Version:** `1.0.0`
**Status:** **Proposed — awaiting operator ratification**
**Issued:** 2026-08-01
**Owner:** Engineering Authority
**Raised by:** Claude (agent, Motor role) — advisory only
**Amends:** [`DEC-P35-DOCKET`](DEC-P35-DOCKET.md) §5.2 role assignment
**Governing artifacts:** `BOPEN-GOV-EBIV-001` §3, §3.1, §6.1, §6.3; `AGENTS.md` §20.3, §22.3

---

## 1. Question

`DEC-P35-DOCKET` §5.2 assigns **Codex as maker** for `WP-P35-01`..`03` remediation. Codex is also
now the **only remaining eligible second verifier** for those same packages. EBIV §3 makes roles
mutually exclusive within a work package. It cannot hold both.

## 2. Findings of fact, 2026-08-01

| Fact | Basis |
| :--- | :--- |
| `WP-P35-01`..`03` have **one verifier** (gemini) | `check_ballot_attribution.py` after `fbd8a99`; manifest `quorum_per_candidate` |
| **Codex has authored nothing** in those packages | `git log --format='%an'` over `db.py`, `tokens.py`, `db_bootstrap.py` and their tests returns only `BizEra` and `Claude Opus 5`. Codex appears nowhere |
| Codex is therefore **eligible** under §3 | The exclusion is on having *authored* an artifact. Its maker assignment is prospective; it has made nothing |
| Claude is **disqualified** | Authored all three, including their tests |
| Gemini **cannot close the gap** | Already the sole verifier there. §3.1: sequential verifiers who can read prior verdicts count as one |
| Kimi is **unavailable** | Operator, 2026-08-01. Seat recorded stood down in the phase manifest |

So the seat is fillable by exactly one agent, and only by changing its role.

## 3. Why this matters most for `WP-P35-01`

`WP-P35-01` carries the tenant isolation invariants. Its single existing verifier used
`python -m unittest tests/isolation/test_rls_database_behavior.py` as the `probe_command` for 13
separate ballots — the maker's own test file. That establishes the named test passes at that
commit. It does not establish that an independent agent tried to break isolation and failed,
which is what EBIV §8 means when it says a maker's passing suite carries no verdict weight.

Disposing that package on one verifier whose probe was a rerun of the maker's tests would leave
the platform's primary security property resting on the thinnest evidence in the repository.

## 4. Options

| | Disposition | Consequence |
| :--- | :--- | :--- |
| **A** | **Codex verifies `WP-P35-01`..`03` now; remediation maker seat returns to Claude** *(recommended)* | Quorum reachable on all three. Codex becomes permanently excluded from *making* those packages |
| B | Codex stays maker; accept §6.3 escalation on one verifier | `WP-P35-01`'s isolation claim disposed on a single verifier using maker-authored probes |
| C | Introduce a fifth engine | No candidate exists today; adds an identity, a registration and a dispatch path |

## 5. Recommendation — Option A

**Verification precedes remediation in the natural order.** You remediate what verification
finds. Codex's maker assignment was made on 2026-07-31, when nobody had verified anything and the
remediation scope was therefore guesswork. Two verifier passes would give it an actual defect list
to work from — which is a better remediation than the one currently planned.

**The role chain stays clean afterwards:**

```text
Codex verifies WP-P35-01..03  ─┐
Gemini has verified them       ─┴─► quorum reachable, remediation scope established
                                     │
Claude remediates (already the author, so no new exclusion is created)
                                     │
Codex + Gemini verify the remediated candidate — neither authored the remediation
```

Codex loses nothing durable: it is excluded from *making* these three, and remains eligible to
verify every future candidate of them, including the remediation it would otherwise have written.

## 6. What this does not change

`WP-P35-04` quorum, `WP-P35-05a`'s `HOLD_FOR_DECISION`, `AUTH-D1`/`AUTH-D3`, the control-plane
docket, and Codex's maker role on `WP-P35-06` are all untouched. This decision concerns three
work packages and one role.

## 7. Decision and approver

| Field | Value |
| :--- | :--- |
| **Decision** | *Pending* |
| **Approver** | *Not assigned — Engineering Authority* |
| **Agent authority** | Advisory only. `execution_authority: false`, `approval_authority: false` |

Nothing in this record changes a contract, migration, specification or production source. If
rejected, `WP-P35-01`..`03` remain at one verifier and escalate to the Completion Authority under
§6.3, which never auto-passes.
