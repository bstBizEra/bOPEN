# DEC-P35-TWO-AGENT-QUORUM — A two-agent team cannot reach a quorum of two

**Decision ID:** `DEC-P35-TWO-AGENT-QUORUM`
**Version:** `1.0.0`
**Status:** **Proposed — awaiting operator ratification**
**Issued:** 2026-08-01
**Owner:** Architecture Authority & Engineering Authority
**Raised by:** Claude (agent, Motor role) — advisory only
**Governing artifacts:** `BOPEN-GOV-EBIV-001` §3, §6.1, §6.3; `AGENTS.md` §20.3
**Trigger:** operator instruction, 2026-08-01 — the team is Claude and Codex

---

## 1. The constraint, stated plainly

EBIV §3 makes maker and verifier mutually exclusive within a work package. EBIV §6.1 requires
**two** independent verifiers to confirm.

With a two-agent team, one agent is always the maker. **The maximum achievable is one verifier per
package.** Two is not difficult here; it is impossible by construction.

This is not a scheduling problem that more dispatches would solve.

## 2. Consequence if nothing changes

Every package escalates under §6.3 — *"fewer than two admissible ballots escalates to the
Completion Authority. It never auto-passes"* — **permanently, for every artifact, forever.**

`CONFIRMED` becomes a verdict that can never be realized. The standard would remain formally
intact while describing an outcome the team cannot produce, which is the condition
`AGENTS.md` §20.5 warns about: *"A governance rule that is not machine-checkable is a
preference."* A rule that is checkable but unreachable is worse — it reads as satisfiable.

## 3. What the ballots have actually delivered

Measured across all 101 ballots cast:

| | Count |
| :--- | :--- |
| `CONFIRMED` | 97 |
| `REFUTED` | **4** |
| Candidates ever reaching two verifiers | **1**, and it is withdrawn |

**Every defect found in this repository came from a refutation, a preflight, or an adversarial
sweep. None came from counting confirmations.**

- the unauthenticated SSRF — adversarial subagent sweep, no ballot involved;
- the auth privilege escalation — subagent sweep, independently reproduced by a Codex preflight;
- the stale and superseded anchors — Codex preflight, before any ballot;
- five overclaiming propositions — two Gemini refutations, two Codex refutations, one found by
  the maker;
- eight misattributed commits — Codex, incidentally, while balloting something else.

The 97 confirmations recorded that claims held. They did not discover anything. **The mechanism
carrying the value is §6.1's asymmetry — one reproducible refutation blocks — not the count
required to confirm.**

## 4. Options

| | Disposition | Consequence |
| :--- | :--- | :--- |
| A | Change nothing; accept permanent §6.3 escalation | Honest, and every package is disposed by the operator on a one-verifier record forever. `CONFIRMED` is dead letter but the standard is untouched |
| B | **Amend for a two-agent team profile** *(recommended)* | Confirmation requires **one** independent verifier plus operator disposition. Refutation rules unchanged |
| C | Rotate makers between Claude and Codex | **Does not help.** Alternating who makes what still yields one verifier per package |
| D | Re-admit a third engine | Restores quorum, and the operator has excluded it for now |

## 5. Recommendation — Option B, with the asymmetry preserved

Amend `BOPEN-GOV-EBIV-001` with a **team-size profile**:

1. **Confirmation** requires one admissible ballot from an independent verifier **plus** an
   explicit Completion Authority disposition on the disclosed-risk record. Not a silent downgrade
   — the operator's act replaces the second verifier, and is recorded as such.
2. **Refutation is unchanged.** One `REFUTED` ballot with a reproducible probe still blocks, and
   is discharged only by a failed reproduction. This is the half that has found every defect.
3. **The maker still cannot vote.** §3 is untouched.
4. **The profile is recorded in the evidence manifest**, so a later reader knows a verdict was
   reached under a two-agent rule rather than a two-verifier quorum.
5. **It expires when a third engine returns.** The profile names the team it was written for; it
   is not a permanent relaxation.

### What this gives up, stated rather than glossed

Two blind verifiers catch what one verifier's blind spot misses. That property is real and is
being surrendered. The mitigation is partial and should not be oversold: adversarial subagent
sweeps and mutation probes both found defects this session without being ballots, and they remain
available — but neither is an independent verdict, and neither is a substitute for a second pair
of eyes that owes nothing to the first.

**A one-verifier confirmation is weaker evidence than a two-verifier one.** The recommendation is
to say so in the record rather than to let the word `CONFIRMED` imply parity.

## 6. Decision and approver

| Field | Value |
| :--- | :--- |
| **Decision** | **ACCEPT — Option B.** A two-agent team profile is added to `BOPEN-GOV-EBIV-001`: confirmation requires **one** admissible ballot from an independent verifier **plus an explicit Completion Authority disposition** on the disclosed-risk record. Refutation rules unchanged — one reproducible `REFUTED` still blocks. The maker still may not vote. The profile is recorded per verdict and **expires when a third engine returns.** |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — acting as Architecture and Engineering Authority |
| **Decision timestamp** | 2026-08-02 |
| **What was weighed** | The measured record (§3): 97 confirmations found nothing, 4 refutations and the adversarial sweeps found everything. The profile keeps the half that works and does not pretend a one-verifier confirmation equals a two-verifier one — §5 requires the weaker basis to be stated on each verdict |
| **Recorded by** | Claude (agent, Motor role), transcribing an operator decision. `execution_authority: false`, `approval_authority: false` |

### 6.1 What this does not do

It does not discharge a refutation. `WP-P35-04` R3 carries two standing refutations that Option B
leaves exactly where they are — §6.2 of the standard governs them, not this profile. It does not
confirm a candidate with **zero** ballots: `WP-P35-05a` R4 still needs one verifier before the
profile can apply. And it does not lower the maker exclusion — the agent that built an artifact
still cannot be the one verifier.

The amendment is recorded in `BOPEN-GOV-EBIV-001` §6.5.
