# WP-P35-07 — Machine-readable disposition record and §6.5 quorum reporting

**Work package ID:** `WP-P35-07`
**Version:** `1.0.0`
**Status:** **ACCEPTED — entry gate GO, operator authorization 2026-08-08** ([`DEC-P35-QUORUM-TOOL-GAP`](../decisions/DEC-P35-QUORUM-TOOL-GAP.md) §7, §8). Transcribed by Claude (Motor); not a maker approval.
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
