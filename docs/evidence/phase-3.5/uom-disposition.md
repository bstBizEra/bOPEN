# EVD-UOM-DISPOSITION — Unit-of-Measure foundation, §6.5 disposition surface

**Document ID:** `EVD-UOM-DISPOSITION`
**Version:** `1.0.0`
**Status:** **DISPOSED 2026-08-05 — `CONFIRMED_UNDER_TWO_AGENT_PROFILE`.** Operator (`BizEra`, Completion Authority) disposed the verdict and acknowledged the disclosed-risk record. Transcribed by Claude (Motor); not a maker approval.
**Issued:** 2026-08-05
**Maker/Recorder:** Claude (agent, Motor role) — `claude@bst.local`, advisory only
**Governing:** [`BOPEN-GOV-EBIV-001`](../../00-governance/BOPEN-GOV-EBIV-001.md) §6.5; [`DEC-P35-TWO-AGENT-QUORUM`](../../decisions/DEC-P35-TWO-AGENT-QUORUM.md)
**Subject:** [`EVD-UOM-MAKER`](uom-maker.md); [`DEC-P4-ENTRY`](../../decisions/DEC-P4-ENTRY.md) §9

---

## 1. The verifier verdict — confirmed from repository objects

Confirmed against `ballots.jsonl` and `git`:

| Field | Value |
| :--- | :--- |
| Candidate | `9ea765c` |
| Ballot commit | `c5dd559` (author `codex@bst.local`) |
| Verdicts | **15/15 `CONFIRMED`** (`INV-UOM-*`), 0 `REFUTED` — a clean first pass, no refutation |
| Admissibility | R1–R5 true on every ballot; verifier `codex`, distinct from the maker |
| Suite | canonical 589/589 against PostgreSQL |

The verifier's independent probe confirmed exact `Decimal` conversions (`1 rai → 1600 m²`,
`2 in → 0.0508 m`, `2.5 kg → 2500 g`, `1 pallet → 4 dozen`) and the refusals (float magnitude,
`kg → m`, `kg + m`, `100 degC → degF`), plus HTTP CRUD, the 409 standard-unit shadow refusal, the
cross-tenant 404/422, and the 401 without a bearer. It also confirmed `INV-MIGRATE-COVERAGE-01` still
passes with `uom_custom_units` in both the RLS classification and the migrate tool's `COPY_ORDER`.

## 2. What the verdict closes

The UOM foundation — Money's dimension-safe sibling. A `Quantity(magnitude: Decimal, unit)` with exact
arithmetic and banker's rounding, never a float; dimension safety (`kg + m` refused) is the keystone.
Standard units are a code constant (SI + imperial + Thai `rai`/`ngan`/`wah²`); tenant custom units are
tenant-scoped by RLS with full CRUD. Product-agnostic — ready to support bERP, bFleet, PropTech,
shipping and any product that measures something.

## 3. The disclosed-risk record (acknowledged by the operator)

- **Multiplicative units only.** Temperature and any affine unit are refused, not converted — deferred.
- **No compound/derived units** (`km/h`, price-per-unit where UOM meets Money) — a later slice.
- **A custom-unit factor with more than 18 decimal places is rounded to 18** by the `NUMERIC(38,18)`
  column (18 dp is far beyond any real unit factor; the most precise standard factor is 5 dp).
  Rejecting an over-precise factor rather than rounding it is a small tracked refinement.
- **A custom unit's dimension is not editable** (delete-and-recreate), deliberately.
- **One verifier, not two** (two-agent profile).

## 4. Disposition — RESERVED TO THE OPERATOR (Completion Authority)

```yaml
disposition:
  verdict_basis: one_verifier_plus_operator            # EBIV §6.5 two-agent profile
  candidate_commit: 9ea765c
  ballot_commit: c5dd559   # Codex, 15/15 CONFIRMED, verified from ballots.jsonl
  decision: CONFIRMED_UNDER_TWO_AGENT_PROFILE
  disclosed_risk_acknowledged: true                    # the items in §3 are read and accepted
  approver: "Operator: BizEra <ounkhamvilay@gmail.com>, Completion Authority"
  decision_timestamp: 2026-08-05
  recorded_by: Claude (Motor), transcribing — execution_authority:false approval_authority:false
```

**Recorded follow-through:** the profile verdict is noted in [`manifest.json`](manifest.json); UOM is
verified-and-disposed. It joins Party, Money and Workflow as a ratified MILE-4.2 foundation. The other
MILE-4.2 foundations (Document, Location, Calendar, Asset, Notification) and all of MILE-4.3 remain
gated and enter on their own operator dispositions.

## 5. Authority

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
