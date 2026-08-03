# EVD-MILE-4.1-DISPOSITION — Party foundation, §6.5 disposition surface

**Document ID:** `EVD-MILE-4.1-DISPOSITION`
**Version:** `1.0.0`
**Status:** **DISPOSED 2026-08-03 — `CONFIRMED_UNDER_TWO_AGENT_PROFILE`.** Operator (`BizEra`, Completion Authority) disposed the verdict and acknowledged the disclosed-risk record. Transcribed by Claude (Motor); not a maker approval.
**Issued:** 2026-08-03
**Maker/Recorder:** Claude (agent, Motor role) — `claude@bst.local`, advisory only
**Governing:** [`BOPEN-GOV-EBIV-001`](../../00-governance/BOPEN-GOV-EBIV-001.md) §6.5; [`DEC-P35-TWO-AGENT-QUORUM`](../../decisions/DEC-P35-TWO-AGENT-QUORUM.md) (Option B)
**Subject:** [`EVD-MILE-4.1-MAKER`](mile-4.1-party-maker.md); [`DEC-P4-ENTRY`](../../decisions/DEC-P4-ENTRY.md) MILE-4.1

---

## 1. The verifier verdict — confirmed from repository objects

Confirmed against `ballots.jsonl` and `git`, not the run's self-report:

| Field | Value |
| :--- | :--- |
| Candidate | `0eb2b21044ce13e55012c21d54c9471c9d266250` |
| Ballot commit | `1e9ced7` (parent `0eb2b21`; author `codex@bst.local`; `ballots.jsonl` only, +13) |
| Verdicts | **13/13 `CONFIRMED`** (`P4-PARTY-01..06`, `P4-PARTY-HTTP-01..07`), 0 `REFUTED` |
| Admissibility | R1–R5 true on every ballot; verifier `codex`, distinct from the maker |
| Suite | canonical 498/498 |

No proposition was refuted, so the disposition proceeds.

## 2. What the verdict closes

MILE-4.1 (`BOPEN-PARTY-001`), the Phase 4 first slice: a tenant-scoped party graph (person /
organization + typed relationships), created and read over HTTP behind a signed bearer, with the
Phase 3.5 isolation boundary proven to hold **on real business data** — a party is invisible to
another tenant over the wire, a relationship cannot cross tenants, and the party endpoints are
bearer-only. Demonstrated end to end through the gateway by `scripts/demo_business_scenario.py`.

## 3. The disclosed-risk record — weaker than a quorum, and the carried items

`DEC-P35-TWO-AGENT-QUORUM` §5 — the weaker basis stated rather than let `CONFIRMED` imply parity:

- **One verifier, not two.** A single independent verdict; the maker's suite carries no verdict weight.
- **Party is distinct from principal and MILE-4.1 does not link them** — that mapping is a later slice.
- **No vendor/supplier/customer role vocabulary** on a party yet; **no update or delete** — create and
  read only.
- **Dedicated-placement identity verification is inherited from WP-P35-06**, exercised structurally,
  not against a live dedicated database.

## 4. Disposition — RESERVED TO THE OPERATOR (Completion Authority)

Under §6.5 / Option B, confirmation requires the admissible ballot in §1 **plus** an explicit
operator disposition on this disclosed-risk record. The maker records; the maker does not dispose.

```yaml
disposition:
  verdict_basis: one_verifier_plus_operator            # EBIV §6.5 two-agent profile
  candidate_commit: 0eb2b21044ce13e55012c21d54c9471c9d266250
  ballot_commit: 1e9ced7   # Codex, 13/13 CONFIRMED, verified from ballots.jsonl
  decision: CONFIRMED_UNDER_TWO_AGENT_PROFILE
  disclosed_risk_acknowledged: true                    # the items in §3 are read and accepted
  approver: "Operator: BizEra <ounkhamvilay@gmail.com>, Completion Authority"
  decision_timestamp: 2026-08-03
  recorded_by: Claude (Motor), transcribing — execution_authority:false approval_authority:false
```

**Recorded follow-through:** the profile verdict is noted in [`manifest.json`](manifest.json) and
MILE-4.1 is marked verified-and-disposed. Phase 4's first slice — the party foundation — is a
ratified base for the foundations and products that build on it.

**On a `CONFIRMED_UNDER_TWO_AGENT_PROFILE` disposition:** record the profile verdict in
[`manifest.json`](manifest.json); mark MILE-4.1 verified-and-disposed. Phase 4's first slice is then
verified, and the party foundation is a ratified base for the next foundations and products.

## 5. Authority

This surface decides nothing and changes no code.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
