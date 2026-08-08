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
