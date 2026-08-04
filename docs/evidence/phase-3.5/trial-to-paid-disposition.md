# EVD-TRIAL-TO-PAID-DISPOSITION — trial→paid tenant migration, §6.5 disposition surface

**Document ID:** `EVD-TRIAL-TO-PAID-DISPOSITION`
**Version:** `1.0.0`
**Status:** **DISPOSED 2026-08-05 — `CONFIRMED_UNDER_TWO_AGENT_PROFILE`.** Operator (`BizEra`, Completion Authority) disposed the verdict and acknowledged the disclosed-risk record. Transcribed by Claude (Motor); not a maker approval.
**Issued:** 2026-08-05
**Maker/Recorder:** Claude (agent, Motor role) — `claude@bst.local`, advisory only
**Governing:** [`BOPEN-GOV-EBIV-001`](../../00-governance/BOPEN-GOV-EBIV-001.md) §6.5; [`DEC-P35-TWO-AGENT-QUORUM`](../../decisions/DEC-P35-TWO-AGENT-QUORUM.md)
**Subject:** [`EVD-TRIAL-TO-PAID-MAKER`](trial-to-paid-maker.md); [`DEC-P35-TENANCY-MODEL`](../../decisions/DEC-P35-TENANCY-MODEL.md) §12

---

## 1. The verifier verdict — confirmed from repository objects

Confirmed against `ballots.jsonl` and `git`:

| Field | Value |
| :--- | :--- |
| Candidate | `1adf673` (the freeze at the `tenant_session` entry point; supersedes `2a253a5` and `6fdb8e9`) |
| Ballot commit | `5cfac11` (author `codex@bst.local`) |
| Verdicts | **8/8 `CONFIRMED`** (`INV-MIGRATE-*`), 0 `REFUTED` |
| Admissibility | R1–R5 true on every ballot; verifier `codex`, distinct from the maker |
| Suite | canonical 560/560 against PostgreSQL, with a second real database provisioned |

## 2. What the verdict closes

An existing shared-pool tenant can be moved into its own dedicated database with **no data lost and
no split-brain read** — the last piece of the hybrid tenancy model (`DEC-P35-TENANCY-MODEL` §8). The
guarantee is by sequencing (freeze → prepare → copy → verify → cutover → cleanup), not a distributed
transaction: the freeze stops writes at the `db.tenant_session` entry point every write path shares,
the cutover is one atomic control-row flip, and a failure before cutover leaves the tenant safely on
the shared pool. With this, the model is complete end to end — trial tenants share the pool, a new
paying tenant gets its own database, and an existing tenant migrates between them.

## 3. The refutation cycle — recorded, not hidden (two rounds)

The freeze was placed too narrowly twice, and the verifier reproduced the same data-loss shape (a
write reaching the shared pool after the copy, then deleted by cleanup — zero copies in either
database) through a different path each time:

1. **`2a253a5`** — freeze at the HTTP layer only; a `db.tenant_session` write bypassed it.
   `INV-MIGRATE-COMPLETE-01` REFUTED.
2. **`6fdb8e9`** — freeze in `_connect_for_tenant`, reached only by the resolved-connection branch;
   `tenant_session(..., connection=X)` (used by `entitlement_repositories`) bypassed it.
   `INV-MIGRATE-COMPLETE-01` and `INV-MIGRATE-FREEZE-DATA-PATH-01` REFUTED.

Fixed by moving the freeze to the top of `db.tenant_session`, before the connection branch, covering
both paths; `1adf673` is 8/8 CONFIRMED. The verifier refusing to pass a data-loss window until every
write path was closed — on the most data-irreversible operation in the system — is the two-agent
governance working exactly where it matters most.

## 4. The disclosed-risk record (acknowledged by the operator)

- **Not zero-downtime.** The freeze refuses the tenant's requests for the copy+cutover window — a
  brief unavailability, acceptable for an operator-run upgrade.
- **A cutover-step failure is not auto-repaired.** A failure exactly at/after the cutover UPDATE can
  leave the tenant `migrating` (frozen) needing a manual clear; the data is safe. Recorded, not built.
- **The freeze adds one control read per `tenant_session`** (canonical ~365→417s); folding it into
  `resolve_placement`'s existing read for the `connection is None` path is a tracked optimization.
- **No reverse (dedicated→shared) or bulk/scheduled migration.**
- **One verifier, not two** (two-agent profile).

## 5. Disposition — RESERVED TO THE OPERATOR (Completion Authority)

```yaml
disposition:
  verdict_basis: one_verifier_plus_operator            # EBIV §6.5 two-agent profile
  candidate_commit: 1adf673
  ballot_commit: 5cfac11   # Codex, 8/8 CONFIRMED, verified from ballots.jsonl
  superseded_candidates: [2a253a5, 6fdb8e9]  # each refuted on a freeze gap, both closed
  decision: CONFIRMED_UNDER_TWO_AGENT_PROFILE
  disclosed_risk_acknowledged: true                    # the items in §4 are read and accepted
  closes: hybrid_tenancy_model_end_to_end
  approver: "Operator: BizEra <ounkhamvilay@gmail.com>, Completion Authority"
  decision_timestamp: 2026-08-05
  recorded_by: Claude (Motor), transcribing — execution_authority:false approval_authority:false
```

**Recorded follow-through:** the profile verdict is noted in [`manifest.json`](manifest.json); the
trial→paid migration is verified-and-disposed. The hybrid tenancy model of `DEC-P35-TENANCY-MODEL` §8
(Option D) is now complete: shared pool for trial/free, dedicated database for paying, and a verified
migration between them. Remaining items are tracked refinements (§4), not model gaps.

## 6. Authority

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
