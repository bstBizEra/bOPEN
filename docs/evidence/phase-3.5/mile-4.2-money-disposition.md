# EVD-MILE-4.2-MONEY-DISPOSITION — Money foundation, §6.5 disposition surface

**Document ID:** `EVD-MILE-4.2-MONEY-DISPOSITION`
**Version:** `1.0.0`
**Status:** **AWAITING_OPERATOR_DISPOSITION** — the Codex ballot is confirmed from repository objects (§1: 13/13 `CONFIRMED`, no refutations). The §4 disposition is reserved to the operator.
**Issued:** 2026-08-03
**Maker/Recorder:** Claude (agent, Motor role) — `claude@bst.local`, advisory only
**Governing:** [`BOPEN-GOV-EBIV-001`](../../00-governance/BOPEN-GOV-EBIV-001.md) §6.5; [`DEC-P35-TWO-AGENT-QUORUM`](../../decisions/DEC-P35-TWO-AGENT-QUORUM.md)
**Subject:** [`EVD-MILE-4.2-MONEY-MAKER`](mile-4.2-money-maker.md); [`DEC-P4-ENTRY`](../../decisions/DEC-P4-ENTRY.md) §7 (MILE-4.2 authorized)

---

## 1. The verifier verdict — confirmed from repository objects

Confirmed against `ballots.jsonl` and `git`:

| Field | Value |
| :--- | :--- |
| Candidate | `e54d48cd40d095bda40b623a5e56c60824c92b6c` (money code identical to the submission; adds the recorded MILE-4.2 authorization) |
| Ballot commit | `e9a999d` (parent `e54d48c`; author `codex@bst.local`; `ballots.jsonl` only, +13) |
| Verdicts | **13/13 `CONFIRMED`** (`P4-MONEY-01..07`, `P4-MONEY-HTTP-01..06`), 0 `REFUTED` |
| Admissibility | R1–R5 true on every ballot; verifier `codex`, distinct from the maker |
| Suite | canonical 521/521 |

**Governance note:** Codex first refused to ballot this slice fail-closed because MILE-4.2 was not
yet authorized in the record (`DEC-P4-ENTRY` had gated it). The operator then authorized MILE-4.2
(`DEC-P4-ENTRY` §7); this ballot is at the authorized candidate. The independent verifier enforcing
the phase gate is the two-agent governance working as designed.

## 2. What the verdict closes

MILE-4.2 (Money & Currency): a money value type that is **integer minor units, never a float**, with
exact-decimal conversion and banker's rounding, plus tenant-scoped exchange rates over HTTP. The
correctness foundation every financial feature (and bERP) will build on.

## 3. The disclosed-risk record

- **One verifier, not two.** A single independent verdict.
- **No ledger, accounting or payment** — the money type and per-tenant rates only.
- **Rates are a single current value per pair**, not a time series.
- **The currency table is a code constant** (ISO-4217 subset), extended as products require.
- **No cross-currency allocation/splitting** yet.

## 4. Disposition — RESERVED TO THE OPERATOR (Completion Authority)

```yaml
disposition:
  verdict_basis: one_verifier_plus_operator            # EBIV §6.5 two-agent profile
  candidate_commit: e54d48cd40d095bda40b623a5e56c60824c92b6c
  ballot_commit: e9a999d   # Codex, 13/13 CONFIRMED, verified from ballots.jsonl
  decision: <PENDING — CONFIRMED_UNDER_TWO_AGENT_PROFILE | REJECTED | DEFERRED>
  disclosed_risk_acknowledged: <PENDING — true/false; the items in §3 are read and accepted>
  approver: <PENDING — Operator: BizEra <ounkhamvilay@gmail.com>, Completion Authority>
  decision_timestamp: <PENDING>
  recorded_by: Claude (Motor), transcribing — execution_authority:false approval_authority:false
```

**On a `CONFIRMED_UNDER_TWO_AGENT_PROFILE` disposition:** record the profile verdict in
[`manifest.json`](manifest.json); mark MILE-4.2 verified-and-disposed. The Money foundation is then a
ratified base for the financial features and products that need it.

## 5. Authority

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
