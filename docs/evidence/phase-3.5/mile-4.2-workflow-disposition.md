# EVD-MILE-4.2-WORKFLOW-DISPOSITION — Workflow State Engine, §6.5 disposition surface

**Document ID:** `EVD-MILE-4.2-WORKFLOW-DISPOSITION`
**Version:** `1.0.0`
**Status:** **DISPOSED 2026-08-03 — `CONFIRMED_UNDER_TWO_AGENT_PROFILE`.** Operator (`BizEra`, Completion Authority) disposed the verdict and acknowledged the disclosed-risk record. Transcribed by Claude (Motor); not a maker approval.
**Issued:** 2026-08-03
**Maker/Recorder:** Claude (agent, Motor role) — `claude@bst.local`, advisory only
**Governing:** [`BOPEN-GOV-EBIV-001`](../../00-governance/BOPEN-GOV-EBIV-001.md) §6.5; [`DEC-P35-TWO-AGENT-QUORUM`](../../decisions/DEC-P35-TWO-AGENT-QUORUM.md)
**Subject:** [`EVD-MILE-4.2-WORKFLOW-MAKER`](mile-4.2-workflow-maker.md); [`DEC-P4-ENTRY`](../../decisions/DEC-P4-ENTRY.md) §8 (Workflow State Engine authorized)

---

## 1. The verifier verdict — confirmed from repository objects

Confirmed against `ballots.jsonl` and `git`:

| Field | Value |
| :--- | :--- |
| Candidate | `2ee4612342fbd30f1f122ac4abfd909c62d746c4` (the append-only fix; supersedes `a09022d`) |
| Ballot commit | `c1847b4` (author `codex@bst.local`; `ballots.jsonl` + verifier probe) |
| Verdicts | **16/16 `CONFIRMED`** (`INV-WF-*`, including both append-only invariants), 0 `REFUTED` at this candidate |
| Admissibility | R1–R5 true on every ballot; verifier `codex`, distinct from the maker |
| Suite | canonical 539/539 against PostgreSQL |

## 2. What the verdict closes

MILE-4.2 Workflow State Engine: a generic, tenant-scoped **state machine** — definitions (states +
allowed transitions), instances, transitions gated by the definition (a move it does not list is
refused, the instance does not move), an **append-only** history, and a lifecycle audit event on each
transition. The process substrate every satellite product composes on (`CAPABILITY-MATRIX`).

## 3. The refutation cycle — recorded, not hidden

The first candidate `a09022d` was **REFUTED** by Codex on the append-only invariant
(`INV-WF-HISTORY-APPEND-ONLY-01`, ballot `blt_a4367591a838`): `workflow_history` had no direct DELETE
policy, but its instance foreign key was `ON DELETE CASCADE`, so deleting the parent instance erased
the history through the referential path — which PostgreSQL performs past row security. Reproduced
live. Fixed at root cause by **migration 014** (`ON DELETE RESTRICT`, the migration-009 precedent for
durable referents); the reproduction is now `INV-WF-HISTORY-APPEND-ONLY-02`. This disposition is at
the fixed candidate. The independent verifier catching a plausible-but-wrong append-only claim, and
the object trail (not the prose summary) settling it, is the two-agent governance working as designed.

## 4. The disclosed-risk record

- **One verifier, not two.** A single independent verdict.
- **No per-transition role authorization yet** — a transition is gated by a valid bearer and the
  definition's allowed edges; restricting *which role* may take an edge is a later slice.
- **No timers, parallel/branching states, or sub-workflows** — a single state machine per instance,
  not BPMN.
- **The lifecycle event is the audit record** (`workflow_instance:transition`), not a separate bus.
- **No definition versioning** or migration of running instances across a definition change.

## 5. Disposition — RESERVED TO THE OPERATOR (Completion Authority)

```yaml
disposition:
  verdict_basis: one_verifier_plus_operator            # EBIV §6.5 two-agent profile
  candidate_commit: 2ee4612342fbd30f1f122ac4abfd909c62d746c4
  ballot_commit: c1847b4   # Codex, 16/16 CONFIRMED, verified from ballots.jsonl
  superseded_candidate: a09022d  # refuted on append-only; fixed by migration 014
  decision: CONFIRMED_UNDER_TWO_AGENT_PROFILE
  disclosed_risk_acknowledged: true                    # the items in §4 are read and accepted
  approver: "Operator: BizEra <ounkhamvilay@gmail.com>, Completion Authority"
  decision_timestamp: 2026-08-03
  recorded_by: Claude (Motor), transcribing — execution_authority:false approval_authority:false
```

**Recorded follow-through:** the profile verdict is noted in [`manifest.json`](manifest.json) and
MILE-4.2 Workflow is marked verified-and-disposed. The Workflow State Engine is a ratified base for
the satellite products that compose business processes on it.

## 6. Authority

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
