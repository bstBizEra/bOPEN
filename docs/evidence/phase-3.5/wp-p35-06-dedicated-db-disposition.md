# EVD-P35-06-DEDICATED-DB-DISPOSITION — Dedicated-database provisioning, §6.5 disposition surface

**Document ID:** `EVD-P35-06-DEDICATED-DB-DISPOSITION`
**Version:** `1.0.0`
**Status:** **DISPOSED 2026-08-04 — `CONFIRMED_UNDER_TWO_AGENT_PROFILE`.** Operator (`BizEra`, Completion Authority) disposed the verdict and acknowledged the disclosed-risk record. Transcribed by Claude (Motor); not a maker approval.
**Issued:** 2026-08-04
**Maker/Recorder:** Claude (agent, Motor role) — `claude@bst.local`, advisory only
**Governing:** [`BOPEN-GOV-EBIV-001`](../../00-governance/BOPEN-GOV-EBIV-001.md) §6.5; [`DEC-P35-TWO-AGENT-QUORUM`](../../decisions/DEC-P35-TWO-AGENT-QUORUM.md)
**Subject:** [`EVD-P35-06-DEDICATED-DB-MAKER`](wp-p35-06-dedicated-db-maker.md); [`DEC-P35-TENANCY-MODEL`](../../decisions/DEC-P35-TENANCY-MODEL.md) §10 (authorized)

---

## 1. The verifier verdict — confirmed from repository objects

Confirmed against `ballots.jsonl` and `git`:

| Field | Value |
| :--- | :--- |
| Candidate | `d8dd023` (the RLS-tightened fix; supersedes `ec14c53`) |
| Ballot commit | `763e728` (author `codex@bst.local`; `ballots.jsonl` + preserved probe `0dde546`) |
| Verdicts | **7/7 `CONFIRMED`** (`INV-DEDI-*`, including the tightening probe `INV-DEDI-IDENTITY-SCOPED-01`), 0 `REFUTED` |
| Admissibility | R1–R5 true on every ballot; verifier `codex`, distinct from the maker |
| Suite | canonical 547/547 against PostgreSQL, with a second real database provisioned |

## 2. What the verdict closes

The provisioning that makes "one tenant, one database" real. A dedicated tenant's **domain data**
physically lives in its own PostgreSQL database and is absent from the shared pool; a mis-configured
route is refused loudly (`verify_connection_serves` vs `placement_identity`) rather than read as
empty. Migration 015 (`placement_identity`, tenant-matching RLS, single-row) and
`provision_dedicated_db.py` (same-ledger provisioning) are the mechanism; the shared-pool bootstrap
is unchanged (`apply_ledger_to` shared by both, re-verified).

## 3. The refutation cycle — recorded, not hidden

Candidate `ec14c53` had **6/6 CONFIRMED**, but the verifier's keystone ballot recorded that its
permissive `placement_identity` policy (`USING (true)`) was broader than necessary and the maker's
rationale false — a tenant-matching policy, proven by execution, still admits the served tenant,
still refuses a mis-route, **and** hides the served-tenant id from other scopes. The maker narrowed
the policy to tenant-matching (migration 015), added `INV-DEDI-IDENTITY-SCOPED-01`, and re-balloted:
`d8dd023` is **7/7 CONFIRMED** with no caveat. The verifier improving a control it confirmed, and the
maker's own self-review finding the auth-chain gap in §4, are the two-agent governance working.

## 4. The disclosed-risk record (acknowledged by the operator)

- **The auth chain is not yet usable for a dedicated tenant.** Three routed tables
  (`memberships`, `active_contexts`, `audit_events`) foreign-key `principal_id` to the global
  `principals` (control database); a dedicated tenant's routed rows cannot satisfy that FK across
  databases (reproduced `ForeignKeyViolation`). So a **new dedicated tenant cannot yet be given a
  membership/context** — this slice proves domain-data placement and mis-route refusal, not a usable
  dedicated tenant end to end. **Resolution authorized as the next slice — Option A** (drop the three
  cross-database FKs, the migration-009 "survives its referent" pattern; principals stay global).
- **"One tenant, one database" here means the tenant's *domain* data.** Principals and the tenant's
  registry row stay global by design (a principal is multi-tenant).
- **New dedicated tenants only** — the trial→paid cross-database data migration is deferred.
- **One verifier, not two** (two-agent profile).

## 5. Disposition — RESERVED TO THE OPERATOR (Completion Authority)

```yaml
disposition:
  verdict_basis: one_verifier_plus_operator            # EBIV §6.5 two-agent profile
  candidate_commit: d8dd023
  ballot_commit: 763e728   # Codex, 7/7 CONFIRMED, verified from ballots.jsonl
  superseded_candidate: ec14c53  # permissive RLS narrowed after the verifier's finding
  decision: CONFIRMED_UNDER_TWO_AGENT_PROFILE
  disclosed_risk_acknowledged: true                    # the items in §4 are read and accepted
  next_slice_authorized_in_principle: option_A_drop_cross_db_principal_fks
  approver: "Operator: BizEra <ounkhamvilay@gmail.com>, Completion Authority"
  decision_timestamp: 2026-08-04
  recorded_by: Claude (Motor), transcribing — execution_authority:false approval_authority:false
```

**Recorded follow-through:** the profile verdict is noted in [`manifest.json`](manifest.json);
WP-P35-06 dedicated-database provisioning is verified-and-disposed. "One tenant, one database" for
domain data is a ratified property. The auth-chain gap (§4) proceeds as the Option A slice under its
own operator authorization.

## 6. Authority

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
