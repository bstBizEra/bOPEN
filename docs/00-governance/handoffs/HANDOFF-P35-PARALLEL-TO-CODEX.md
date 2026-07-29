# HANDOFF-P35-PARALLEL-TO-CODEX — Parallel execution split for Phase 3.5

**Status:** Open — action requested
**Issued:** 2026-07-30
**Maker of this handoff:** Claude (agent, Motor role)
**Addressed to:** Codex Agent IDE (VS Code)
**Work package:** [`BOPEN-P35-001`](../../work-packages/BOPEN-P35-001-EXECUTION-PLAN.md)
**Governing standards:** [`BOPEN-GOV-EBIV-001`](../BOPEN-GOV-EBIV-001.md), `AGENTS.md` §19, §20.3
**Decision:** [`DEC-P35-RUNTIME`](../../decisions/DEC-P35-RUNTIME.md) — Proposed, not yet approved

---

## 1. Two requests, kept separate on purpose

**Request A — verify `WP-P35-01`.** It is complete and committed. You did not author any part
of it, so you are eligible as an independent verifier under EBIV §3. This is read-only.

**Request B — build `WP-P35-04`, the API gateway.** Yours as Maker. I will not touch it, and
I am eligible to verify it because I will not have authored it.

They are separate because mixing them would disqualify you from both: an agent that edits an
artifact cannot vote on it. Please do not modify anything listed in §3 while verifying it.

---

## 2. Why this split avoids collision

`AGENTS.md` §19.1 requires all agents to work in the primary workspace on an explicit branch
and prohibits uncoordinated parallel worktrees. Parallel work therefore has to be separated by
**file ownership**, not by isolation.

| Lane | Owner | Directories | Language |
| :--- | :--- | :--- | :--- |
| `WP-P35-01` persistence | Claude — **complete** | `infrastructure/database/`, `services/platform-kernel/python/platform_kernel/db.py`, `tests/isolation/` | Python, SQL |
| `WP-P35-02` kernel HTTP surface | Claude — next | `services/platform-kernel/python/`, `packages/kernel-core/python/` | Python |
| `WP-P35-04` API gateway | **Codex** | `apps/gateway/`, `sdk/typescript/`, `package.json`, `pnpm-workspace.yaml` | TypeScript |

No file appears in two lanes. The gateway lane is entirely TypeScript and the kernel lane is
entirely Python, so the two can run simultaneously without a merge conflict and without either
agent waiting on the other.

Branch for your lane: `codex/BOPEN-P35-004-api-gateway`, cut from
`claude/BOPEN-P35-001-runtime-realization`.

---

## 3. Request A — independent verification of WP-P35-01

### 3.1 What to verify

Baseline: branch `claude/BOPEN-P35-001-runtime-realization`. Read the exact commit and tree
OIDs with `python tools/check_evidence_anchors.py --emit` rather than from this document, per
EBIV R3. If they do not match what
[`docs/evidence/phase-3.5/manifest.json`](../../evidence/phase-3.5/manifest.json) records,
that discrepancy is itself a finding and outranks everything below.

Four propositions, each stated so it can be refuted:

| ID | Proposition | Named evidence |
| :--- | :--- | :--- |
| `INV-TENANT-ISOLATION-01` | A tenant cannot read another tenant's rows. Fails if `tenant_isolation_resources` is dropped | `test_tenant_cannot_read_another_tenants_rows`, `test_the_other_direction_also_holds` |
| `INV-TENANT-DENY-DEFAULT-01` | An unset or unknown tenant context reads zero rows. Fails if the `NULLIF(...)` guard is removed from the policies | `test_unset_context_reads_nothing`, `test_unknown_tenant_reads_nothing` |
| `INV-TENANT-WRITE-01` | A cross-tenant write is refused by the database. Fails if `WITH CHECK` is removed from `active_contexts_isolation` | `test_cross_tenant_insert_is_refused`, `test_cross_tenant_update_cannot_reach_foreign_rows` |
| `INV-AUDIT-APPEND-ONLY-01` | Audit records cannot be updated or deleted. Fails if any UPDATE or DELETE policy is added to `audit_events` | `test_audit_events_cannot_be_modified_or_deleted` |

### 3.2 Reproduce the baseline

```bash
python -m pip install -r requirements.txt
set -a; . ./.env.local; set +a          # values registered in BOPEN-SEC-VAULT-001
python tools/db_bootstrap.py --status
python tools/run_tests.py               # expect 182/182
python tools/check_evidence_anchors.py  # expect PASS
```

If `.env.local` is absent, `python tools/db_bootstrap.py --apply` provisions the instance and
prints the URL to export. The verification cluster is at `C:\laragon\data\bopen-verify` on
port 5433 and is separate from anything on 5432.

### 3.3 Please attack it specifically here

I am the Maker, so my confidence is not evidence. These are the places I would look first, and
disclosing them is part of the handoff rather than a reason to skip them:

1. **Does the suite actually detect policy removal?** I ran three mutations and recorded them
   in the evidence package. Mutations B (`NO FORCE ROW LEVEL SECURITY`) and C (adding a DELETE
   policy) produce clean, legible assertion failures. **Mutation A (dropping
   `tenant_isolation_resources`) errors all 13 tests in `setUp` rather than failing one
   assertion**, because with RLS enabled and no policy present the seed INSERT is itself
   refused. That is detection, but the message does not name the defect. I judged it
   acceptable and recorded the nuance; a checker may reasonably disagree, and if you do, say
   so — I would rather that be a recorded finding than a shared assumption. Try mutations I
   did not: drop `WITH CHECK` alone, drop only the SELECT policy on `audit_events`, revoke
   `FORCE` on `memberships`.

2. **Is `bopen_app` genuinely unprivileged?** The whole design rests on the test role not
   being a superuser and not owning the tables, because both bypass RLS. Check
   `pg_roles.rolsuper`, `rolbypassrls`, and table ownership. If `bopen_app` turns out to own
   anything, every green result in §3.2 is worthless and this is a `REFUTED` ballot.

3. **Does `set_config(..., is_local => true)` really scope to the transaction?** My claim is
   that a pooled connection cannot carry tenant A's context into tenant B's next transaction.
   Try to break it: open one connection, run a `tenant_session` for A, then query outside any
   `tenant_session` on that same connection and see whether A's rows are still visible.

4. **Migration 003 rollback.** I applied `003` forward against a database already carrying
   `001` and `002`. I did **not** execute the rollback, so acceptance criterion `A-06` in
   `BOPEN-P35-001` is unmet and I have recorded it as such. Running
   `python tools/db_bootstrap.py --rollback 003` (requires `BOPEN_DB_NON_PRODUCTION=1`) and
   then re-applying would close it.

5. **The two tool bugs I already found in my own work.** `forward_migrations()` classified
   `003_..._audit.down.sql` as a forward migration, and `app_url()` hardcoded port 5432. Both
   are fixed. Both existed because I wrote the tool and the test for it. Assume there is a
   third.

### 3.4 How to record your verdict

One JSON line per proposition appended to `docs/evidence/phase-3.5/ballots.jsonl`, in the
schema at `BOPEN-GOV-EBIV-001` §7. `probe_command` and `probe_exit_code` are mandatory;
`refutation_attempted: true` is required to cast `CONFIRMED`.

Under §6.1 a single `REFUTED` ballot carrying a reproducible probe blocks the proposition
regardless of how many confirmations oppose it. You do not need to persuade me, and I cannot
discharge your refutation by re-asserting that the work is correct — only a failed
reproduction discharges it.

---

## 4. Request B — WP-P35-04, the API gateway

### 4.1 Scope

Bound by `BOPEN-ARCH-PLAN-001` §2 layer 1 and §3: Node.js with Hono, validation via Zod.

Deliverables:

1. A Hono service under `apps/gateway/` validating `X-Tenant-ID`, `X-Context-ID` and
   `X-Correlation-ID` against [`HTTP_HEADER_SPEC.md`](../../../sdk/headers/HTTP_HEADER_SPEC.md).
2. Zod schemas derived from `contracts/schemas/` — generated or checked against them, not
   hand-transcribed. A hand-copied schema drifts from its contract and the drift is invisible;
   Phase 3 already produced one of those, where `RateLimitDecision` diverged from
   `rate-limit-decision.schema.json` on five fields while the contract suite reported green.
3. Request-scoped context propagation via `AsyncLocalStorage`.
4. Contract tests asserting that a request missing or malforming any required header is
   **rejected**, and that a header-supplied tenant identifier is never forwarded as
   authoritative — `AGENTS.md` §8: *"Never trust tenant IDs supplied by clients without
   server-side context validation."*

### 4.2 Out of scope for your lane

Do not implement the kernel HTTP endpoints the gateway will call. That is `WP-P35-02`, mine.
Until it exists, target the contract shape and keep the upstream call behind one seam so it
can be pointed at the real kernel without reshaping the gateway.

Do not add the Go worker tier. `DEC-P35-RUNTIME` §5 defers it deliberately: a third language
runtime before layers 1–4 exist adds operational cost against no measured load.

### 4.3 Constraint worth stating plainly

`package.json` currently declares **no dependencies at all** and there is no lockfile content
for the workspace. Your lane is the first real Node dependency set in this repository. Record
each addition under `AGENTS.md` §13 (dependency and license changes) and keep it minimal —
this repository is intended for open-source release, so every transitive dependency becomes
part of what BST publishes.

---

## 5. The quorum shortfall, disclosed rather than worked around

`BOPEN-GOV-EBIV-001` §6.1 requires **a minimum of two verifiers** to realize a confirmation.

For `WP-P35-01` there is currently one eligible verifier: you. I authored it, so I am
disqualified. A single `CONFIRMED` ballot therefore **cannot** realize a verified status, and
the correct recorded outcome would be `IMPLEMENTED_UNVERIFIED` with the shortfall stated —
not a verified pass with a footnote.

Two ways to close it, both for the operator to choose:

1. **Add a third agent.** Gemini / Antigravity is eligible for `WP-P35-01`: it was Maker on
   Phase 3 but authored nothing in this work package. Two independent verifiers with distinct
   lenses — you on reproducibility and privilege, Gemini on contract conformance — meets
   §3.2 diversity and §6.1 quorum.
2. **Operator acts as Completion Authority** on a single-verifier record, with the shortfall
   disclosed on the face of the evidence.

I am not choosing between these. Recording the gap is the part that is mine to do; deciding
how to fill it is not.

---

## 6. What is already true, so you do not re-derive it

- Phases 1–3 are `IMPLEMENTED_UNVERIFIED` per `AGENTS.md` §20.2. Not a retraction — the code
  exists and is specification-shaped; what was withdrawn is the claim that it was verified.
- Phase 3 evidence bound commit `f59bbd2891...`, which does not exist. Corrected to the
  tool-read value; `tools/check_evidence_anchors.py` now makes that class of defect fail CI.
- Findings F-2, F-3 and F-8 from the 2026-07-30 review were structural, not local bugs. Quota
  could not reserve because no balance store existed; the outbox was a list because no
  transaction existed; RLS was unproven because no database connection existed anywhere in the
  repository. `WP-P35-01` removes the substrate that caused them. **F-4 through F-7 remain
  open and are not in my lane or yours** — they belong to a later work package against the
  entitlement module.
- `169/169` was never evidence of isolation. It measured what the suite asserted, not what it
  declined to assert.

---

## 7. Provenance

Authored by Claude (agent, Motor role) on 2026-07-30. Advisory only —
`execution_authority: false`, `approval_authority: false`.

This handoff assigns lanes and requests verification. It does not authorize production
activation, specification amendment, or `DEC-P35-RUNTIME` approval, none of which are within
either agent's authority.
