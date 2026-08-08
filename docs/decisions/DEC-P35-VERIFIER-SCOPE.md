# DEC-P35-VERIFIER-SCOPE — does EBIV §3 disqualify a verifier who authored the code the change extends?

**Decision ID:** `DEC-P35-VERIFIER-SCOPE`
**Version:** `1.0.0`
**Status:** **Proposed — decision request raised under `AGENTS.md` §16 (authorization precedence is undefined)**
**Issued:** 2026-08-08
**Owner:** Engineering Authority
**Raised by:** Claude (agent, Motor role) — advisory only, and the maker of the package that surfaced it
**Governing:** [`BOPEN-GOV-EBIV-001`](../00-governance/BOPEN-GOV-EBIV-001.md) §3, §6.5; [`DEC-P35-TWO-AGENT-QUORUM`](DEC-P35-TWO-AGENT-QUORUM.md); [`WP-P35-07`](../work-packages/WP-P35-07-QUORUM-DISPOSITION-RECORD.md) §6

---

## 1. What happened

`WP-P35-07` was dispatched to Codex for independent verification on 2026-08-08. Codex **declined to
ballot and disqualified itself**, reporting that it had previously authored part of the artifact
under review.

It was told to verify its own standing rather than accept the assignment, and it did. The
disqualification is the instruction working, not a failure of the dispatch.

## 2. The claim, verified independently

Codex's reasoning was checked against the repository rather than accepted:

| Check | Result |
| :--- | :--- |
| `git blame` of `tools/check_ballot_attribution.py` at candidate `bdc07e5` | Claude **467** lines, **Codex 38** |
| Is `fbd8a99` real? | Yes — *"fix(governance): count quorum per work package, not per phase"*, `Codex (BST-SA Motor)`, 2026-08-01 |
| Where do the Codex lines sit? | On `by_candidate`, `unmet` and the per-candidate verifier reporting — **the exact mechanism `WP-P35-07` extends** |

Codex reported "40 lines"; a whitespace-insensitive blame gives 38. The discrepancy is immaterial to
the question.

**`WP-P35-07` §6 recorded "Codex — authored none of this package". That was wrong** and is corrected
in that document. It is true of the package's *changes*; it is false of the *code those changes
extend*.

## 3. The question

`BOPEN-GOV-EBIV-001` §3 excludes an agent that authored "any part of the artifact, including its
tests". Two readings, and the repository has never had to choose:

| Reading | Consequence here |
| :--- | :--- |
| **A — the artifact is the change under review.** Codex authored none of `WP-P35-07`'s diff, so it is eligible | Codex verifies; the two-agent profile keeps working |
| **B — the artifact is the code as it now stands.** Codex authored 38 lines of the file, including the mechanism being extended, so it is disqualified | Codex is ineligible; `WP-P35-07` has no assigned verifier |

Codex chose **B**, the fail-closed reading. That is the safer default and is defensible: judging
whether the extension is sound requires judging the base it sits on, and Codex wrote that base.

Reading B has a cost that must be stated plainly. In a small team, every governance tool eventually
carries lines from more than one agent. Under B, **the more a file is collaboratively maintained,
the fewer agents may ever verify it** — and the tools most central to governance are exactly the
ones most likely to have been touched by everyone. Applied consistently, B tends toward no eligible
verifier for the most important artifacts.

Reading A has the opposite cost: an agent could author a mechanism, and later confirm a change that
depends on that mechanism being correct, without that dependency ever being independently examined.

## 4. Who is actually available

| Agent | Lines authored in `check_ballot_attribution.py` @ `bdc07e5` | Status |
| :--- | :--- | :--- |
| Claude | 467 | **Maker.** Excluded under either reading |
| Codex | 38 | Eligible under A, disqualified under B |
| Gemini | **0** | Eligible under both readings |
| Kimi | **0** | Eligible under both; `agent-identity-register.json` records "no commit identity yet. Seated as verifier V3" |

So reading B does not leave the package unverifiable — it moves the seat to Gemini or Kimi. Note
that `DEC-P35-TWO-AGENT-QUORUM` §6.5 states the two-agent profile **"expires when a third
independent engine returns"**; seating a third engine here would interact with that clause and
should be decided deliberately, not as a side effect.

## 5. Options

| # | Option | Assessment |
| :--- | :--- | :--- |
| 1 | **Adopt reading B and seat Gemini or Kimi** for `WP-P35-07` | **Recommended.** Keeps the fail-closed reading Codex applied, and a verifier who wrote none of the file is unambiguously independent. Costs a dispatch to an engine with no commit history here |
| 2 | **Adopt reading A** and re-dispatch Codex | Cheapest, and defensible on the text — but it decides a governance question in order to unblock a package, which is the wrong order. If A is right, it should be recorded because it is right |
| 3 | **Record the scope in `BOPEN-GOV-EBIV-001` §3** and apply it going forward | The durable fix. §3's wording is the actual defect; whichever reading is chosen belongs in the specification, not in each dispatch |

Options 1 and 3 compose: seat an unambiguous verifier now, and fix §3's wording so the next package
does not rediscover this.

## 6. What this decision request does not do

It does not re-seat any verifier, alter any ballot, or change `BOPEN-GOV-EBIV-001`. `WP-P35-07`
remains unverified and its §8 criterion remains unmet for the separate reason recorded in the maker
submission.

The maker of `WP-P35-07` raised this. That is a conflict of interest worth naming: the maker
benefits from reading A, which unblocks its own package. The recommendation above is for reading B,
which does not.

Raised advisory-only. Confers no implementation, approval, merge, release or production authority.

---

## 7. Correction 2026-08-08 — §3's text is less ambiguous than §3 of this document claimed

§3 above framed this as two readings the repository "has never had to choose" between. **Reading
`BOPEN-GOV-EBIV-001` §3 in full weakens that framing considerably**, and the correction is recorded
because a decision taken on the wrong frame is worse than a decision deferred.

Its operative sentence is not the summary phrase quoted earlier. It reads:

> An agent that contributed **any line of the artifact under review** — implementation, test,
> fixture, schema, or migration — is **disqualified as a Verifier for that artifact**. This is a
> structural rule, not a preference. It is what the word *independent* means here.

Three things follow:

1. **"Any line" is not a threshold.** 38 lines is not a small contribution under a rule that says
   *any*. Codex did not take a cautious reading; it applied the plain one.
2. **The enumeration points at artifacts, not diffs.** "Implementation, test, fixture, schema, or
   migration" are kinds of *artifact*, not kinds of *change*. That favours reading B.
3. **§3 pre-empts the argument for A.** "This is a structural rule, not a preference" is written
   precisely to refuse case-by-case relaxation — which is what adopting A to unblock a package
   would be.

**Option 2 in §5 should therefore be read as a proposal to weaken a control against its plain text,
not as a neutral choice between two equal readings.** It is retained in the table for the record,
with that recharacterisation.

The residual question is narrower than §3 of this document suggested: whether "the artifact under
review" denotes the file or the change. The enumeration favours the file. The maker's original
framing overstated the room available, and the maker is the party that benefits from that overstatement.

## 8. A consequence of seating a third engine that must not happen as a side effect

`BOPEN-GOV-EBIV-001` §6.5.4 states:

> The profile expires when a third independent engine returns. It names the team it was written
> for. From that point §6.1's two-verifier quorum is reachable again and is required; verdicts
> already recorded under the profile keep their label and are not retroactively upgraded.

Seating Gemini or Kimi as verifier for `WP-P35-07` may therefore **expire the two-agent profile**,
with effects far beyond this package:

| Effect | Consequence |
| :--- | :--- |
| §6.1 two-verifier quorum becomes required again | `WP-P35-07` would itself need **two** verifiers, not one |
| The 26 shortfall candidates | Would need two verifiers each, rather than one ballot plus an operator disposition |
| `WP-P35-07`'s own premise | It implements §6.5. If the profile is expired, the mechanism applies only to verdicts recorded while it was in force |

This does not make the package pointless — the profile's existing verdicts still need expressing,
and the profile could re-enter if an engine becomes unavailable again — but it changes what the
package is *for*, and that should be decided deliberately.

**A prior question, unresolved:** does dispatching an engine once constitute a third engine
"returning" in the sense §6.5.4 means, or does returning describe sustained availability as a team
member? The clause does not say. Both engines are invocable here (`gemini` and `kimi` are both on
PATH; Gemini has 4 commits and 51 ballots in this repository, Kimi has none of either), so
availability is not the discriminator.

**Recommendation: decide the §6.5.4 question before seating anyone.** Seating first and discovering
the profile expired afterwards would change the quorum rule for 27 candidates as a side effect of
staffing one package.

## 9. Analysis of the §6.5.4 question — advisory, the decision is the operator's

§8 asked whether dispatching an engine once constitutes a third engine "returning". The answer turns
on a sentence in `DEC-P35-TWO-AGENT-QUORUM` §4 that settles what made the team two agents:

> | D | Re-admit a third engine | Restores quorum, and **the operator has excluded it for now** |

**The two-agent team is the product of an operator exclusion recorded 2026-08-02 — not of an engine
being unavailable.** `gemini` and `kimi` are on PATH today and were almost certainly invocable then;
availability was never the criterion. The exclusion was.

That fixes the meaning of "returns". `BOPEN-GOV-EBIV-001` §6.5.4 keys expiry to a property, not an
event: *"From that point §6.1's two-verifier quorum is **reachable** again and is required."*
Reachability is general — it is about whether two independent verifiers can be seated for packages —
and one scoped dispatch does not make two-verifier quorum reachable for the other 26 candidates. It
produces one verifier for one package.

**Advisory reading: a single scoped dispatch does not expire the profile. Lifting the exclusion
does.** The trigger is a decision, not a CLI invocation.

Two conditions on that reading, both of which matter more than the reading itself:

1. **The scoping must be recorded, not inferred.** If Gemini verifies `WP-P35-07` and nothing says
   the exclusion still stands, a later reader sees a Gemini ballot dated August and concludes the
   third engine returned — and with it that every verdict after that date needed two verifiers. The
   record must say plainly that this was a scoped seating and that Option D remains excluded.
2. **If the exclusion no longer reflects reality, say so instead of preserving the profile on a
   stale premise.** The profile's whole justification is that two-verifier quorum is unreachable by
   construction. If a third engine is in fact available and the operator no longer wishes to exclude
   it, the honest move is to revisit `DEC-P35-TWO-AGENT-QUORUM` on its merits — not to keep the
   accommodation alive by describing each use of a third engine as an exception. An accommodation
   that outlives its premise is a relaxation.

**On the second half of the question — whether to accept the consequence for 27 candidates if the
profile does expire — the advisory answer is no, not as a side effect.** Changing the quorum rule
for every candidate in the repository is a decision with its own merits and its own costs, and it
should be taken deliberately, on a surface raised for that purpose, not absorbed as the by-product of
staffing one work package.

This section interprets a ratified normative specification. That interpretation is not the maker's
to make: it is recorded here as advice, and binds nothing until the operator records a decision
(EBIV §2).

## 10. Decision 2026-08-08 — reading B adopted; a scoped verifier seat; the profile stands

| Field | Value |
| :--- | :--- |
| **Reading adopted** | **B** — "the artifact under review" is the code as it stands. An agent that contributed any line of it is disqualified as its Verifier. Codex's self-disqualification from `WP-P35-07` was correct |
| **Two-agent profile** | **Remains in effect.** `BOPEN-GOV-EBIV-001` §6.5 continues to govern; §6.5.4 is **not** triggered |
| **Option D** | **Remains excluded.** No third engine is re-admitted to the team |
| **Verifier seat** | One **scoped** seating for `WP-P35-07` only. It is not a team change and confers no standing on any other package |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — Architecture & Engineering Authority |
| **Decision timestamp** | 2026-08-08 |
| **Recorded by** | Claude (agent, Motor role), transcribing an operator decision. `execution_authority: false`, `approval_authority: false` |

### 10.1 This is explicitly not a third engine returning

Recorded plainly, because §9.1 warned this is exactly what a later reader will otherwise infer:

> A ballot cast by a third engine on `WP-P35-07` in August 2026 is a **scoped seating under an
> exclusion that remains in force**. It does not expire the two-agent profile, does not restore
> §6.1's two-verifier quorum, and does not imply that verdicts recorded after that date required two
> verifiers. Option D of `DEC-P35-TWO-AGENT-QUORUM` stays excluded.

Confirmation of `WP-P35-07` therefore still requires one admissible independent ballot **plus** an
explicit Completion Authority disposition, labelled `CONFIRMED_UNDER_TWO_AGENT_PROFILE`.

### 10.2 Which engine, and a reconsideration

Both are eligible: `git blame` at `bdc07e5` shows **Gemini 0 lines** and **Kimi 0 lines** of
`tools/check_ballot_attribution.py`.

The maker's first suggestion was Kimi, on the grounds that it has no history in this repository at
all. **That reasoning does not survive examination.** §3 eligibility is already fully satisfied by
both — zero lines is zero lines — so Kimi's additional distance is cosmetic, and cosmetic
independence is not a property the standard asks for.

Once eligibility is equal, the discriminator that remains is demonstrated capability to produce an
admissible ballot:

| | Gemini | Kimi |
| :--- | :--- | :--- |
| Lines in the artifact | 0 | 0 |
| Ballots cast in this repository | **51** | 0 |
| Commits | 4 | 0 |
| Demonstrated refutation | **Yes** — the two `REFUTED` ballots on `88e6ed2` that `WP-P35-07` §10 surfaced | None |

**Gemini is seated.** It has proven it will refute rather than agree — the `88e6ed2` refutations are
the only reason that candidate's blocked state was discoverable at all — and that is the property
this seat needs most, given the maker has asked the verifier to attack two of its own claims.

Swapping to Kimi is a one-line change if the operator prefers it; both remain eligible.
