# EVD-OPTION-A-DEDICATED-AUTH-CHAIN-DISPOSITION — usable dedicated tenant, §6.5 disposition surface

**Document ID:** `EVD-OPTION-A-DEDICATED-AUTH-CHAIN-DISPOSITION`
**Version:** `1.0.0`
**Status:** **DISPOSED 2026-08-04 — `CONFIRMED_UNDER_TWO_AGENT_PROFILE`.** Operator (`BizEra`, Completion Authority) disposed the verdict and acknowledged the disclosed-risk record. Transcribed by Claude (Motor); not a maker approval.
**Issued:** 2026-08-04
**Maker/Recorder:** Claude (agent, Motor role) — `claude@bst.local`, advisory only
**Governing:** [`BOPEN-GOV-EBIV-001`](../../00-governance/BOPEN-GOV-EBIV-001.md) §6.5; [`DEC-P35-TWO-AGENT-QUORUM`](../../decisions/DEC-P35-TWO-AGENT-QUORUM.md)
**Subject:** [`EVD-OPTION-A-DEDICATED-AUTH-CHAIN-MAKER`](option-a-dedicated-auth-chain-maker.md); [`DEC-P35-TENANCY-MODEL`](../../decisions/DEC-P35-TENANCY-MODEL.md) §11

---

## 1. The verifier verdict — confirmed from repository objects

Confirmed against `ballots.jsonl` and `git`:

| Field | Value |
| :--- | :--- |
| Candidate | `9ad31ca` |
| Ballot commit | `53532ff` (author `codex@bst.local`) |
| Verdicts | **3/3 `CONFIRMED`** (`INV-DEDI-AUTHCHAIN-01..03`), 0 `REFUTED` |
| Admissibility | R1–R5 true on every ballot; verifier `codex`, distinct from the maker |
| Suite | canonical 551/551 against PostgreSQL, with a second real database provisioned |

The verifier reproduced the fix adversarially: restoring the membership FK reproduced the original
`ForeignKeyViolation`; restoring only the context FK reproduced `active_contexts_principal_id_fkey`;
the pre-016 FK/RLS existence channel was reproduced and shown closed post-016; HTTP context issuance
returned 201 and a mismatched membership principal returned 403; the principal was observed once in
control and zero times in the dedicated database.

## 2. What the verdict closes

A dedicated tenant is now **usable end to end**. With migration 016 dropping the three cross-database
`principal_id` foreign keys (the migration-009 "survives its referent" pattern), a dedicated tenant
can be given a membership and a context — both landing in its own database — while its principal
stays a single global registry row in the control database (not routed, not replicated). The auth
chain principal → membership → context → authorize completes for a dedicated tenant.

## 3. The disclosed-risk record (acknowledged by the operator)

- **No orphan handling on principal deletion** — not reachable today (no DELETE policy on
  `principals` after migration 007, no code path deletes one); recorded, deferred to whenever
  principal deletion is built.
- **The FK drop weakens a same-database guarantee** (a membership's `principal_id` is no longer
  FK-guaranteed on the shared pool; the application validates it) **and closes a covert channel** (the
  FK check bypassed row security, letting principal existence be probed — now closed).
- **New/usable dedicated tenants**; the **trial→paid** cross-database data migration of an *existing*
  shared-pool tenant remains a separate deferred slice.
- **One verifier, not two** (two-agent profile).

## 4. Disposition — RESERVED TO THE OPERATOR (Completion Authority)

```yaml
disposition:
  verdict_basis: one_verifier_plus_operator            # EBIV §6.5 two-agent profile
  candidate_commit: 9ad31ca
  ballot_commit: 53532ff   # Codex, 3/3 CONFIRMED, verified from ballots.jsonl
  decision: CONFIRMED_UNDER_TWO_AGENT_PROFILE
  disclosed_risk_acknowledged: true                    # the items in §3 are read and accepted
  approver: "Operator: BizEra <ounkhamvilay@gmail.com>, Completion Authority"
  decision_timestamp: 2026-08-04
  recorded_by: Claude (Motor), transcribing — execution_authority:false approval_authority:false
```

**Recorded follow-through:** the profile verdict is noted in [`manifest.json`](manifest.json); Option A
is verified-and-disposed. A dedicated tenant is a usable end-to-end property. The only remaining
tenancy item is the trial→paid data migration, which enters on its own operator decision.

## 5. Authority

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
