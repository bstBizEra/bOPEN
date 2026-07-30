# HANDOFF-P35-PARALLEL-TO-CODEX — Parallel execution split for Phase 3.5

**Status:** Stood down 2026-07-30 — retained as a record
**Issued:** 2026-07-30
**Maker of this handoff:** Claude (agent, Motor role)
**Addressed to:** Codex Agent IDE (VS Code)
**Work package:** [`BOPEN-P35-001`](../../work-packages/BOPEN-P35-001-EXECUTION-PLAN.md)
**Governing standards:** [`BOPEN-GOV-EBIV-001`](../BOPEN-GOV-EBIV-001.md), `AGENTS.md` §19, §20.3
**Decision:** [`DEC-P35-RUNTIME`](../../decisions/DEC-P35-RUNTIME.md) — Proposed, not yet approved

> **SEAT STOOD DOWN — 2026-07-30.** The operator has stood this handoff down for now: the
> addressed agents did not pick it up, and blocking on them was holding work that has no other
> dependency on them.
>
> **This does not verify anything.** `BOPEN-GOV-EBIV-001` §6.3 is explicit that fewer than two
> admissible ballots escalates to the Completion Authority and *never* auto-passes. Standing the
> verifiers down changes only the reason the quorum is unmet — from *awaiting ballots* to
> *quorum unreachable* — and moves the decision to the operator acting as Completion Authority
> on a zero-verifier record, with the shortfall on the face of the evidence.
>
> The document is retained rather than deleted. It records what was asked, of whom, and on what
> propositions, and it is the starting point if a verifier becomes available. Re-activating it
> needs nothing but an agent reading it and setting its identity per §5.0.


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

**Do this first, or your ballots will not count.** Added 2026-07-30:

```bash
git config user.name  "Codex <model> (BST-SA Motor)"
git config user.email "codex@bst.local"
```

Repository-local, not global. `verifier_id` is no longer taken on trust: it is bound to the git
author of the commit that introduced the ballot line, and
`python tools/check_ballot_attribution.py` refuses a ballot when the two disagree. Until your
identity is set, every ballot you cast is authored by whatever identity the repository is
currently configured with and reports `unattributable`, which does not count toward quorum
(`AGENTS.md` §21.3, `BOPEN-GOV-IDENT-001`).

This is not bureaucracy aimed at you. It exists because I found that `verifier_id` was a single
self-declaration nothing checked — I could have written `"verifier_id": "codex"` myself and the
protocol would have counted it. Also note `AGENTS.md` §21.2.3: branch prefixes are not
attribution. Several `codex/*` branches in this repository contain commits whose trailers name
Claude.

One JSON line per proposition appended to `docs/evidence/phase-3.5/ballots.jsonl`, in the
schema at `BOPEN-GOV-EBIV-001` §7. `probe_command` and `probe_exit_code` are mandatory;
`refutation_attempted: true` is required to cast `CONFIRMED`. Put ballots for different
propositions in separate commits where convenient — one commit must never introduce ballots for
two different verifiers (§21.3 R5).

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

---

## 6a. Amendment 2026-07-30 — WP-P35-02 has landed and also needs verification

The kernel HTTP surface is complete and committed at
`a969bb59b85c1c717cf432cabd6c46fa10c5edb0`. Request A now covers **both** `WP-P35-01` and
`WP-P35-02`; the lane split in §2 is unchanged and `apps/gateway/` is still untouched by me.

This matters to your lane specifically: the gateway now has a real upstream to target rather
than a contract shape. Endpoints are `POST /v1/principals`, `POST /v1/tenants`,
`POST /v1/contexts`, `POST /v1/authorize`, `GET /v1/audit-events`, plus `/health` and
`/readiness`. Run it with
`python -m uvicorn platform_kernel.api:app --port 8080` from `services/platform-kernel/python`.

Four more propositions, same rules:

| ID | Proposition | Named evidence |
| :--- | :--- | :--- |
| `INV-HTTP-TENANT-HINT-01` | A client-supplied `X-Tenant-ID` grants nothing without a context living in that tenant. Fails if `active_contexts_isolation` is weakened to `USING (true)` | `test_context_from_another_tenant_is_refused` |
| `INV-HTTP-AUDIT-SCOPE-01` | Audit events are scoped by policy, not by the query. Fails if `audit_events_read_isolation` is weakened | `test_audit_events_are_scoped_to_the_callers_tenant` |
| `INV-HTTP-RESOURCE-SCOPE-01` | A tenant-owned resource is invisible to another tenant over HTTP. Fails if `tenant_isolation_resources` is weakened | `test_resource_created_in_one_tenant_is_invisible_to_another` |
| `INV-CONTRACT-TENANT-CONTEXT-01` | The issued context payload validates against `tenant-context.json`. Fails if `context_id` reverts to `ctx_<uuid>` or `expires_at` is dropped | `test_context_payload_satisfies_the_frozen_contract` |

### Where to attack this one

1. **Is `X-Tenant-ID` authoritative anywhere?** My claim is that it only selects an RLS session.
   Look for any query reachable from a handler that filters on the header value rather than on
   `ResolvedContext.tenant_id`. One such path would invalidate the whole design.
2. **Does `resolve_context` leak through a side channel?** All refusals return 403 with an
   identical body, but a latency difference between "context absent" and "context in another
   tenant" is still a probe channel.
3. **The audit write is not in the same transaction as the decision.** I judged this acceptable
   because the decision is not persisted either, so there is nothing to be inconsistent with. It
   becomes a defect the moment decisions are persisted. Disagree if you think that moment has
   already arrived.
4. **`PlatformKernelService` still exists in parallel.** Two implementations of the same chain,
   one in-memory with 139 unit tests, one repository-backed. I left it because removing it would
   have put a large test rewrite in the same commit as new behaviour. If you think the drift risk
   outweighs that, say so.
5. **I weakened a validator's fixtures, not the validator.** `pydantic.EmailStr` rejects RFC 2606
   reserved TLDs, so `@example.invalid` fixtures failed with 422. I moved the fixtures to
   `@example.com` rather than loosening the check. Verify I did not loosen anything else under
   test pressure.

## 7. Provenance

Authored by Claude (agent, Motor role) on 2026-07-30. Advisory only —
`execution_authority: false`, `approval_authority: false`.

This handoff assigns lanes and requests verification. It does not authorize production
activation, specification amendment, or `DEC-P35-RUNTIME` approval, none of which are within
either agent's authority.
