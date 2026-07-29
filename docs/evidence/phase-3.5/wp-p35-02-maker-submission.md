# EVD-P35-02-MAKER — WP-P35-02 Maker Submission (Kernel HTTP Surface)

**Document ID:** `EVD-P35-02-MAKER`
**Version:** `1.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision
**Issued:** 2026-07-30
**Work package:** [`BOPEN-P35-001`](../../work-packages/BOPEN-P35-001-EXECUTION-PLAN.md) — `WP-P35-02`, deliverables D-06 and D-07
**Commit OID:** `a969bb59b85c1c717cf432cabd6c46fa10c5edb0`
**Tree OID:** `93daf415759363a0a891a2e7abda652a2fb01b82`
**Maker:** Claude (agent, Motor role)
**Admissibility standard:** [`BOPEN-GOV-EBIV-001`](../../00-governance/BOPEN-GOV-EBIV-001.md)

> Zero ballots cast. Under EBIV §3 the Maker does not vote on its own work; under §6.1 two
> independent verifiers are required. The status above is the honest one.

---

## 1. What this changes about what bOPEN is

Before this deliverable, a satellite product could only consume the kernel by
`import kernel_core` and running it inside its own process. Each of bPro, bFleet, PropTech,
bERP and LDM would then hold its own copy of tenant, membership and context state, and the
kernel would be a shared library rather than an isolation boundary — which forfeits the reason
bOPEN exists and contradicts `BOPEN-TENANT-001` invariant 2.

There is now one kernel, reachable over HTTP, with one tenant boundary. That is the premise
Phase 4 depends on, and it did not exist until this commit.

## 2. Scope discipline

Only the chain `AGENTS.md` §3 authorizes is exposed:

```
POST /v1/principals → POST /v1/tenants → POST /v1/contexts
→ POST /v1/authorize → audit row readable under the tenant's own policy
```

Plus `/health`, `/readiness`, `/v1/audit-events`, and a minimal tenant-owned resource used as
the authorization target.

No Phase 2 endpoint (SSO, SCIM, invitation, delegation) and no Phase 3 endpoint (capability,
entitlement, metering) is exposed. Those belong to work packages `DEC-P35-RUNTIME` has not
authorized, and shipping them would resolve reserved architecture decisions by code default —
the exact thing `AGENTS.md` §3.1 prohibited before it was superseded.

## 3. How the tenant is established without trusting the client

`AGENTS.md` §8: *never trust tenant IDs supplied by clients without server-side context
validation.*

| Header | Trust level | Role |
| :--- | :--- | :--- |
| `X-Tenant-ID` | none | Routing hint. Selects which RLS session to open, nothing more |
| `X-Context-ID` | authority | Must resolve to a live, unrevoked context row **inside that tenant**, read under the tenant's own policy |
| `X-Correlation-ID` | n/a | Mandatory. Rejected when absent rather than generated server-side |

A caller who lies about `X-Tenant-ID` gains nothing: the lookup runs in the claimed tenant, the
context is not there, refused. To pass, the caller must hold a context that genuinely lives in
the tenant it names.

Every refusal returns the same body, `"context is not valid"`. Distinguishing *no such context*
from *belongs to another tenant* would confirm another tenant's context to someone who cannot
read it.

`X-Correlation-ID` is not generated when missing, deliberately. A server-generated correlation
ID produces an audit trail that cannot be joined to the caller's own logs while appearing as
though it can be.

## 4. Two frozen-contract violations fixed

`contracts/schemas/tenant-context.json` requires `context_id` with `format: uuid` and requires
`expires_at`. The in-memory `ContextPayload` satisfies neither: it emits `ctx_<uuid>`, and it has
no `expires_at` field at all.

This is the same class of defect as the Phase 3 `RateLimitDecision` divergence — a frozen schema
that nothing ever validated an instance against. `test_context_payload_satisfies_the_frozen_contract`
now runs `jsonschema.validate()` against an actual response, so the HTTP surface cannot inherit
the divergence.

## 5. What makes the green suite evidence

Canonical suite: **198/198** (`unit 139, integration 30, contracts 8, isolation 16, governance 5`).
The count is an input, not the claim.

Six mutation probes establish that these assertions can fail. Three were surgical — the policy
was weakened to `USING (true)` rather than dropped, simulating a **wrongly written** policy
instead of a missing one, which is the realistic failure mode and the one a "policy exists"
check would miss:

| Probe | Mutation | Result |
| :--- | :--- | :--- |
| `MUT-G` | `ALTER POLICY active_contexts_isolation ... USING (true)` | 1 failure — `200 != 403`, tenant A's context accepted under tenant B's header and a full `ALLOW` decision returned |
| `MUT-H` | `ALTER POLICY audit_events_read_isolation ... USING (true)` | 1 failure — tenant A read tenant B's audit event |
| `MUT-I` | `ALTER POLICY tenant_isolation_resources ... USING (true)` | 1 failure — `200 != 404 : tenant B read a resource owned by tenant A` |

Each produced exactly one legible failure naming the breach. Full records including the
coarser drop-the-policy probes (`MUT-D`, `MUT-E`, `MUT-F`) are in
[`mutation-probes.json`](mutation-probes.json).

The endpoint that demonstrates the design most directly is `GET /v1/audit-events`: there is no
tenant filter in the query behind it. The row-level security policy is what scopes the result,
so a bug in that handler cannot leak another tenant's audit trail. `MUT-H` is what proves the
claim rather than asserting it.

## 6. Known gaps, stated as gaps

**`Authorization: Bearer` is not enforced.** `HTTP_HEADER_SPEC.md` makes it mandatory. No issuer
exists — `WP-P35-03` builds it. This surface does not enforce it and **deliberately does not
accept an unverified bearer token either**: a path that accepts any bearer value without
checking a signature is a hole that reads as a feature. Absent is honest; unverified-but-accepted
would be worse than absent.

**`HTTP_HEADER_SPEC.md` contradicts itself.** It calls `X-Tenant-ID` an "Explicit UUID" while its
own example is `tnt_88a11b22-…`, which is not a UUID. Migration 001 declares those columns
`UUID`. Both forms are accepted and normalised so a satellite product following the published
spec is not silently broken, but the contradiction needs a decision rather than a quiet choice.

**`PlatformKernelService` still exists as a parallel in-memory path.** Its 139 unit tests pass
against it. It is superseded by the repository-backed path and should be removed so there is one
implementation, but doing that in this increment would have exceeded `AGENTS.md` §15
("smallest coherent change") and put a large test rewrite in the same commit as new behaviour.
Recorded as debt, not as design.

**`A-06` (migration reversibility) is still unmet.** Carried over from
[`maker-submission.md`](maker-submission.md) §3. Migration 003's rollback has still never been
executed.

**Findings F-4 through F-7 remain open.** Entitlement-module defects, out of scope here.

## 7. A defect this work introduced and caught

`pydantic.EmailStr` rejects RFC 2606 reserved TLDs, so the first test fixtures using
`@example.invalid` failed at registration with 422. The strict validation is correct behaviour
for a production kernel — real services do reject those domains — so the fixtures moved to
`@example.com` rather than the validation being loosened. Recorded because the tempting fix was
the wrong one: weakening a correct validator to make a test pass is how contract drift starts.

## 8. Verification status

| Field | Value |
| :--- | :--- |
| Ballots cast | 0 |
| Quorum required | 2 (EBIV §6.1) |
| Eligible verifiers | Codex Agent IDE; Gemini / Antigravity |
| Disqualified | Claude — authored the implementation and its tests |
| Handoff | [`HANDOFF-P35-PARALLEL-TO-CODEX`](../../00-governance/handoffs/HANDOFF-P35-PARALLEL-TO-CODEX.md) |

Propositions a verifier should attack, beyond those in the handoff:

1. **Can `X-Tenant-ID` be made authoritative by any path?** The claim is that it only selects an
   RLS session. Look for any query reachable from a handler that filters by the header value
   instead of by `ResolvedContext.tenant_id`.
2. **Does `resolve_context` leak through timing or status codes?** All refusals return 403 with
   an identical body, but a difference in latency between "context absent" and "context in
   another tenant" would still be a probe channel.
3. **Is the audit write in the same transaction as the decision?** It currently is not — the
   decision is evaluated, then `audit.record` opens its own `tenant_session`. If the audit insert
   fails, the caller still receives a decision that was never recorded. I judged this acceptable
   for Phase 1 because the decision is not persisted either, so there is nothing to be
   inconsistent with; a verifier may reasonably call it a defect once decisions are persisted.
4. **Context revocation on re-establish.** `ContextRepository.establish` revokes prior live
   contexts for the principal. Confirm no window exists where two live contexts satisfy the
   partial unique index.

## 9. Reproduction

```bash
python -m pip install -r requirements.txt
set -a; . ./.env.local; set +a
python tools/db_bootstrap.py --apply
python tools/run_tests.py                # 198/198
python -m uvicorn platform_kernel.api:app --port 8080   # from services/platform-kernel/python
```

Credentials registered in
[`BOPEN-SEC-VAULT-001`](../../07-security/secrets/BOPEN-SEC-VAULT-001.md).

## 10. Provenance

Authored by Claude (agent, Motor role) on 2026-07-30. Advisory only —
`execution_authority: false`, `approval_authority: false`.

Anchors emitted by `python tools/check_evidence_anchors.py --emit`. No OID in this package was
transcribed by an agent.
