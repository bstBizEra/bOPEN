# WP-P35-07 — Machine-readable disposition record and §6.5 quorum reporting

**Work package ID:** `WP-P35-07`
**Version:** `1.0.0`
**Status:** **BUILT AND UNVERIFIED — verification PAUSED 2026-08-08 by operator decision (see §14). Entry gate GO, operator authorization 2026-08-08** ([`DEC-P35-QUORUM-TOOL-GAP`](../decisions/DEC-P35-QUORUM-TOOL-GAP.md) §7, §8). Transcribed by Claude (Motor); not a maker approval.
**Issued:** 2026-08-08
**Owner:** Engineering Authority
**Governing:** [`BOPEN-GOV-EBIV-001`](../00-governance/BOPEN-GOV-EBIV-001.md) §3, §6.1, §6.2, §6.3, §6.5; [`DEC-P35-TWO-AGENT-QUORUM`](../decisions/DEC-P35-TWO-AGENT-QUORUM.md); `AGENTS.md` §21.2.1, §21.3, §23, §25.1

---

## 1. Why this exists

`tools/check_ballot_attribution.py` implements only `BOPEN-GOV-EBIV-001` §6.1 (two independent
verifiers). The ratified §6.5 two-agent profile — one admissible `CONFIRMED` ballot **plus** an
explicit Completion Authority disposition, labelled `CONFIRMED_UNDER_TWO_AGENT_PROFILE` — has no
expression in any automated check, because the disposition it requires has no machine-readable home.

Measured 2026-08-07: **26 of 27 candidates** sit below two verifiers, covering `AUTH-D1`, `AUTH-D3`,
gateway decoding, the placement seam, trial→paid migration, Party, Workflow, UOM, ContactPoint and
Location. The profile is this repository's normal operating mode, not an edge case.

## 2. Scope

**In scope**

1. `docs/evidence/phase-3.5/dispositions.jsonl` — append-only disposition record, schema per
   `DEC-P35-QUORUM-TOOL-GAP` §6.1.
2. `tools/check_ballot_attribution.py` — read dispositions; for a candidate holding exactly one
   admissible `CONFIRMED` ballot **and** a valid disposition, report
   `CONFIRMED_UNDER_TWO_AGENT_PROFILE` instead of a shortfall.
3. Negative tests in `tests/governance/` covering every row of §4.

**Out of scope** — and each would be a separate decision

- Writing any actual disposition (an operator act, §21.2.1 — see §5).
- Confirming or disposing any candidate, including Location.
- Any change to §6.1's two-verifier path, §3 maker exclusion, §6.2 refutation asymmetry, or §6.3
  escalation.
- The orphan anchor ([`DEC-P35-ORPHAN-CANDIDATE-ANCHOR`](../decisions/DEC-P35-ORPHAN-CANDIDATE-ANCHOR.md)).

## 3. Keystone invariant

> A disposition may only ever **add** the §6.5 path to a candidate that already holds one admissible,
> independent, non-refuted `CONFIRMED` ballot. It may never create a confirmation on its own, and it
> may never be authored by an agent.

## 4. Refusal Matrix

Each row is a negative test written **before** implementation, and each must be shown to fail when
its mechanism is removed.

| # | Input | Required behaviour |
| :--- | :--- | :--- |
| R-1 | One ballot, **no** disposition | Report shortfall exactly as today — no confirmation |
| R-2 | Disposition introduced by a commit **not** authored by the operator identity | **Refused.** Not a valid disposition; candidate still short. This is the §21.2.1 integrity condition and the most important row |
| R-3 | Disposition present, but the only ballot is **maker-cast** | Refused — §3 maker exclusion is untouched |
| R-4 | Disposition present, and a reproducible `REFUTED` ballot exists | Refused — §6.2 asymmetry holds; a disposition cannot discharge a refutation |
| R-5 | Disposition present, **zero** admissible ballots | Refused — §6.5.3: a candidate with no admissible ballot is not confirmed |
| R-6 | Disposition whose `candidate_commit_oid` matches no candidate | Refused, and reported — never silently ignored |
| R-7 | Disposition claiming bare `CONFIRMED` rather than `CONFIRMED_UNDER_TWO_AGENT_PROFILE` | Refused — §6.5.2 forbids conflating the two verdicts |
| R-8 | Malformed JSON line in `dispositions.jsonl` | A reported finding, not a skipped line |
| R-9 | Two verifiers **and** a disposition | Reports the §6.1 verdict; the profile adds nothing and must not downgrade it |

Positive case: one admissible independent `CONFIRMED` ballot + a valid operator-committed
disposition → `CONFIRMED_UNDER_TWO_AGENT_PROFILE`.

## 5. The recursion, stated so it is not discovered late

The first artifact this mechanism would confirm is **the mechanism itself**. `WP-P35-07` must
therefore be verified and disposed under the **existing** rules — Codex ballot plus an operator
disposition recorded in prose — and only afterwards may `dispositions.jsonl` carry entries. Using
the new path to confirm the change that created it would be circular.

## 6. Roles

| Role | Assigned |
| :--- | :--- |
| Maker | Claude (agent, Motor role) — excluded from voting on this package for its lifetime (EBIV §3) |
| Independent verifier | Codex — authored none of this package |
| Completion Authority | Operator, `BizEra <ounkhamvilay@gmail.com>` — not an agent role |

## 7. Sequence

1. **Baseline** (§23) — tag before the change lands, never after.
2. Write the §4 negative tests; observe them fail.
3. Implement the smallest change that turns them green.
4. Mutate each mechanism; confirm the corresponding test goes red.
5. Trace each proposition into `invariant-traceability.csv` (EBIV R2) **before** dispatching Codex —
   an unregistered proposition yields `R2:false` and wastes the run.
6. Maker submission anchored to an exact candidate commit and tree.
7. Codex ballot, defensively framed.
8. Operator disposition, in prose, per §5 above.

## 8. Acceptance criteria

- Every §4 row has a named executed test, and each test fails when its mechanism is removed.
- `check_ballot_attribution.py` output is unchanged for every candidate that has no disposition —
  the 26 shortfalls stay reported until dispositions exist.
- Full canonical suite green, run **serialized** (concurrent runs against the shared PostgreSQL
  produce contention artifacts: 22552s versus a 712s baseline, with three spurious errors).
- No change to `ballots.jsonl`.

## 9. Authority

Work package document. Confers no implementation, approval, merge, release or production authority.
Acceptance of this package authorizes the build described here and nothing beyond it.

---

## 10. Disclosed finding 2026-08-08 — the shortfall moved from 26 to 27, and why that is correct

§8 required that output be unchanged for candidates without dispositions, and the 26 shortfalls
stay reported. **The count moved to 27.** Recorded rather than reconciled, because the movement is
the change working.

### 10.1 What happened

Before `WP-P35-07`, quorum was counted from *distinct attributable verifiers* — `verdict` and
`admissibility` were never read. Exactly one candidate in the repository had two verifiers and was
therefore the only one not in shortfall:

`88e6ed2` — *"fix(gateway): the caller could choose the upstream host — unauthenticated SSRF"*.

It carries confirmations from `codex` **and** `gemini`, and **two `REFUTED` ballots from `gemini`**
with reproducible probes:

- `P35-04R-15` — *"Client request target /v1/../admin and /v1/%2E%2E/admin reached kernel as /admin
  due to Hono decoding and URL dot-segment normalisation."*
- `P35-04R-16` — *"buildUpstreamUrl with configured base path /base and path /../../admin produced
  pathname /admin, escaping the configured base path prefix."*

Under EBIV §6.2 one reproducible `REFUTED` blocks, discharged only by a failed reproduction. The old
count could not see this, so **the repository's single "quorum met" candidate was in fact blocked by
two unresolved refutations of an authorization-boundary bypass**, and had been since 2026-07-31.

The defect itself was remediated at a later candidate — `1b39a30`, *"fix(gateway): stop decoding the
request target, and refuse…"*. That is the correct shape: the refuted candidate stays refuted, and
the fix carries its own candidate and its own ballots. Nothing here says the gateway is unfixed; it
says the old candidate was never confirmable.

### 10.2 Two further exclusions the new reading surfaces

- **Seven candidates** hold both `CONFIRMED` and `REFUTED` ballots from `codex` — a verifier
  confirming some propositions and refuting others on the same candidate. All were already in
  shortfall; they are now reported as *blocked by refutation* rather than merely *short*, which is
  a materially different state.
- **`ce97561`** holds a ballot inadmissible on **R2** — the proposition was not registered in
  `invariant-traceability.csv`. Correct behaviour observed, inadmissible verdict (EBIV §6.5.3).

### 10.3 Judgment recorded for review

A refutation is cast against a *proposition*, while quorum here is counted per *candidate*. This
implementation blocks the **whole candidate** when any proposition on it is refuted. That is the
fail-closed reading and matches §6.2's wording, but it is a judgment rather than a quotation, and a
reviewer should test it rather than inherit it.

**Consequence to be explicit about:** zero candidates in this repository are currently confirmable
under §6.1. Every one of the 27 is either short, refuted, or both. That was true before this change;
only its visibility is new.

## 11. Amendment 2026-08-08 — a second scoped §19.1 worktree, for the candidate-bound suite run

> **Change note (extend-only).** Recorded **before** the worktree is created.

§10 withdrew the canonical-suite result from the submission: it was measured in the primary
workspace while that workspace carried 21 uncommitted items from an unrelated change-set, and
`run_tests.py` discovers tests by walking the working tree. §8's "green canonical suite for the
candidate" is therefore unmet, and cannot be met in the primary workspace while it is dirty.

`git archive` was considered and rejected: it exports the tree without touching anything, but the
result has no `.git`, so `check_evidence_anchors.py`, `check_ballot_attribution.py` and the
governance validators cannot run there at all.

| Field | Value |
| :--- | :--- |
| **Scope** | One detached worktree at `bdc07e5`, **suite execution only** |
| **Prohibited in it** | Any commit, branch, push, or edit of tracked files |
| **Purpose** | Produce a canonical-suite result bound to tree `e0121de` |
| **Lifetime** | Removed after the run |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — Architecture & Engineering Authority |
| **Recorded by** | Claude (agent, Motor role), transcribing an operator decision. `execution_authority: false`, `approval_authority: false` |

This is the second such exception. The first (`DEC-P4-LOCATION-BALLOT-ATTRIBUTION` §6) stated it did
not generalize, and it did not — this one was authorized separately, for a different candidate and a
different purpose, and carries the same non-generalizing limit.

**Known limitation, recorded in advance rather than discovered.** A worktree isolates the file tree
but **not the database**. The shared PostgreSQL already has migration `021_notification_foundation`
applied from the in-flight change-set, so a candidate-bound run may report a registry-classification
failure caused by tables that do not belong to this candidate. Codex disclosed exactly this while
verifying Location at `1cde994`. Such a failure is an artifact of shared database state, not a
property of `e0121de`, and must be reported as such rather than treated as a product defect — or
silently discounted.

## 12. Correction 2026-08-08 — §6's verifier assignment was wrong

§6 records *"Independent verifier — Codex, authored none of this package"*. **That is false as
written.** Codex authored none of this package's *changes*, but `git blame` at candidate `bdc07e5`
shows **38 lines** of `tools/check_ballot_attribution.py` authored by Codex in `fbd8a99`
(*"fix(governance): count quorum per work package, not per phase"*, 2026-08-01) — including
`by_candidate`, `unmet` and the per-candidate verifier reporting, which is **the exact mechanism this
package extends**.

Codex was dispatched on 2026-08-08, verified its own standing as instructed, and **disqualified
itself under EBIV §3 without balloting**. It changed no file, set no identity, made no commit, and
ran no suite. The eleven propositions, the `--root` question and the PostgreSQL failure attribution
are all **unevaluated**.

The maker did not catch this when assigning roles. The verifier did, because it was told to check
rather than accept — which is the only reason the error surfaced before a ballot was cast rather than
after.

Whether EBIV §3 disqualifies an agent who authored the code a change *extends* — as opposed to the
change itself — is now raised as
[`DEC-P35-VERIFIER-SCOPE`](../decisions/DEC-P35-VERIFIER-SCOPE.md). **This package has no eligible
assigned verifier until that is decided.**

## 13. Verifier re-seated 2026-08-08 — Gemini, scoped

Superseding the §6 assignment corrected in §12: the independent verifier for `WP-P35-07` is
**Gemini**, seated under [`DEC-P35-VERIFIER-SCOPE`](../decisions/DEC-P35-VERIFIER-SCOPE.md) §10.

| Role | Assigned |
| :--- | :--- |
| Maker | Claude — excluded from voting on this package for its lifetime (EBIV §3) |
| Independent verifier | **Gemini** — `git blame` at `bdc07e5` shows **0 lines** of `tools/check_ballot_attribution.py` |
| Disqualified | **Codex** — 38 lines in `fbd8a99`, the per-candidate quorum mechanism this package extends |
| Completion Authority | Operator — not an agent role |

**The seating is scoped to this package.** It is not a team change: the two-agent profile remains in
effect, `BOPEN-GOV-EBIV-001` §6.5.4 is not triggered, and Option D of `DEC-P35-TWO-AGENT-QUORUM`
remains excluded. Confirmation still requires one admissible ballot **plus** an operator disposition,
labelled `CONFIRMED_UNDER_TWO_AGENT_PROFILE`.

## 14. Verification paused 2026-08-08 — read this before running the checker

The operator paused verification of this package to prioritise other work. **No verifier was
dispatched.** Gemini was seated in §13 but never invoked; Codex disqualified itself in §12 without
balloting. `ballots.jsonl` holds **no** `WP07-INV-*` ballots.

**The implementation is committed and live on this branch.** Anyone running
`tools/check_ballot_attribution.py` from `claude/BOPEN-P35-001-runtime-realization` is running an
**unverified change to the control that guards the evidence base**. Its two most visible effects:

1. The quorum shortfall reports **27 of 27** candidates rather than 26, because the checker now reads
   `verdict` and `admissibility` and no candidate holds two admissible non-refuted confirmations
   (§10).
2. `dispositions.jsonl` is read if present. None exists, so nothing is confirmed by it today.

**Nothing here has been verified or disposed.** State on pause:

| Item | State |
| :--- | :--- |
| 11 `WP07-INV-*` propositions | Unevaluated by any verifier |
| The §10.3 judgment — refutation blocks the whole candidate, not one proposition | Untested by anyone but the maker |
| `--root` behaviour and provenance ambiguity | Unassessed |
| The maker's attribution of the single suite failure to shared database state | Unchecked by an independent party |
| §8 green canonical suite for the candidate | **Not met**, and currently unsatisfiable (§10) |

Resuming needs only a dispatch to Gemini against candidate `bdc07e5` / tree `e0121de`; the seat,
the propositions, the traceability and the baseline are all already in place.
