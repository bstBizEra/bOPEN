# EVD-P35-01-MAKER — WP-P35-01 Maker Submission

**Document ID:** `EVD-P35-01-MAKER`
**Version:** `1.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — this is not a completion decision
**Issued:** 2026-07-30
**Work package:** [`BOPEN-P35-001`](../../work-packages/BOPEN-P35-001-EXECUTION-PLAN.md) — `WP-P35-01`
**Commit:** `6ce069e3c3e09b4d33323d4d8d185b6c796213c0`
**Tree:** `434bc7302711efd5ed01b4a133a35a48cb994986`
**Maker:** Claude (agent, Motor role)
**Admissibility standard:** [`BOPEN-GOV-EBIV-001`](../../00-governance/BOPEN-GOV-EBIV-001.md)

> This document deliberately does **not** claim completion. Under EBIV §3 the Maker does not
> vote on its own work, and under §6.1 two independent verifiers are required to realize a
> confirmation. Zero ballots have been cast. The correct current status is
> `IMPLEMENTED_UNVERIFIED`, and it stays that way until verifiers say otherwise.

---

## 1. What changed materially

Before this work package the repository contained no database driver, no connection, and no
migration runner. Row-Level Security had never been executed by any automated check across
three phases recorded as complete. Tenant isolation — the property the entire product exists to
provide — was asserted in SQL files that had never been run.

It is now executed. The specific difference:

| | Before | After |
| :--- | :--- | :--- |
| PostgreSQL policies executed by CI | 0 | 12 invariants, executed |
| Isolation test fixture | a Python list | PostgreSQL 17.10 with migrations 001–003 |
| Behaviour with no database configured | suite green | suite **fails** |
| Quota ceiling enforcement | application `if` statement | `CHECK (used_quantity <= quota_limit)` |
| Audit immutability | convention | absence of UPDATE/DELETE policy, probed |
| Evidence anchors | agent-transcribed | tool-emitted, machine-validated |

## 2. Why the pass count is not the claim

`python tools/run_tests.py` reports 182/182. That number is not the evidence, and the Phase 3
record is the reason to say so plainly: it reported 169/169 while `RateLimitDecision` violated
its own frozen schema, because the suite loaded the schema and never applied it to an instance.
A pass count measures what a suite asserted, not what it declined to assert.

What makes these assertions evidence is that they can fail. Three schema mutations
([`mutation-probes.json`](mutation-probes.json)) removed one mechanism each and turned the suite
red every time; restoring each mechanism turned it green again.

Two supplementary probes license reading the green suite at all:

- **`bopen_app` cannot bypass RLS.** `rolsuper=false`, `rolbypassrls=false`, owns none of the 11
  tables. Had any of those been otherwise, every passing result would be worthless — a
  superuser sees all rows regardless of policy.
- **Tenant context does not leak across transactions on a reused connection.** The claim in
  `platform_kernel/db.py` that `set_config(..., is_local => true)` confines the tenant to one
  transaction was a code comment until it was executed against a shared connection. It holds.

## 3. What is not met, stated as such

**A-06 (migration reversibility) is unmet.** Migration `003` was applied forward against a
database already carrying `001` and `002`. The rollback script was authored but never executed,
so I cannot claim it works. Running `python tools/db_bootstrap.py --rollback 003` with
`BOPEN_DB_NON_PRODUCTION=1` and re-applying would close it.

**Mutation A is detected but not legible.** Dropping `tenant_isolation_resources` turns the
suite red, but as 13 `setUp` errors rather than one assertion naming the breach, because with
RLS enabled and no policy present the seed INSERT is itself refused. I judged this acceptable.
A verifier may reasonably judge it insufficient under R5, and the handoff invites exactly that
disagreement rather than presenting the result as clean.

**Findings F-4 through F-7 remain open.** The frozen-schema divergence, the unwired
transactional outbox, the tenant-blind feature toggles, and the never-resetting rate-limit
counters are entitlement-module defects. They are outside this work package and are not fixed
here. Migration `003` closed the *database-enforceable* half of F-2 (quota ceiling, positive
quantity, expiry ordering); the application code that ignores those rules still needs the
repository layer of `D-06`.

**Migrations `001` and `002` have no rollback scripts**, contrary to `AGENTS.md` §14.
Pre-existing, not introduced here, not corrected here.

## 4. Two defects I introduced and found by executing my own work

Both were invisible on reading and appeared within minutes of running the tool:

1. `forward_migrations()` classified `003_phase1_context_audit.down.sql` as a **forward**
   migration. The negative lookahead tested whether the remainder ended in `.down`, but it ends
   in `.sql`. Every rollback script would have been applied as a migration.
2. `app_url()` hardcoded port 5432 while the verification instance runs on 5433, so the tool
   printed a URL that could not connect.

Both existed because I wrote the tool and the test for it — which is the precise failure mode
EBIV §3 exists to interrupt. A verifier should assume there is a third.

## 5. Verification status

| Field | Value |
| :--- | :--- |
| Ballots cast | 0 |
| Quorum required | 2 (EBIV §6.1) |
| Eligible verifiers | Codex Agent IDE; Gemini / Antigravity |
| Disqualified | Claude — authored the implementation and its tests (§3) |
| Handoff | [`HANDOFF-P35-PARALLEL-TO-CODEX`](../../00-governance/handoffs/HANDOFF-P35-PARALLEL-TO-CODEX.md) |

Ballots belong in [`ballots.jsonl`](ballots.jsonl), one JSON line per proposition, schema at
EBIV §7. A single `REFUTED` ballot carrying a reproducible probe blocks, and I cannot discharge
it by re-asserting that the work is correct — only a failed reproduction discharges it.

## 6. Reproduction

```bash
python -m pip install -r requirements.txt
set -a; . ./.env.local; set +a
python tools/db_bootstrap.py --apply     # idempotent
python tools/run_tests.py                # 182/182
python tools/check_evidence_anchors.py   # PASS
```

Credentials are registered in
[`BOPEN-SEC-VAULT-001`](../../07-security/secrets/BOPEN-SEC-VAULT-001.md). The verification
cluster is at `C:\laragon\data\bopen-verify`, loopback only, port 5433.

## 7. Provenance

Authored by Claude (agent, Motor role) on 2026-07-30. Advisory only —
`execution_authority: false`, `approval_authority: false`.

Anchors in §front-matter and in [`manifest.json`](manifest.json) were emitted by
`python tools/check_evidence_anchors.py --emit`. No OID in this package was transcribed by an
agent, which is the specific defect that made the Phase 3 manifest unverifiable.
