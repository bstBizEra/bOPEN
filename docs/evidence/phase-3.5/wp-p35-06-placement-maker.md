# EVD-P35-06-MAKER — WP-P35-06 placement resolution seam

**Document ID:** `EVD-P35-06-MAKER`
**Version:** `1.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision
**Issued:** 2026-08-03
**Implements:** [`DEC-P35-TENANCY-MODEL`](../../decisions/DEC-P35-TENANCY-MODEL.md) Option D + §9 (Option C, strict A-09), operator-ratified 2026-08-03
**Candidate:** the commit carrying this submission (seam wired at `25960aa`; fixtures at `718fbd7`)
**Blob — `placement.py`:** `94668dfe2fad5ed01e15426de7d4183b9b987550`
**Blob — `db.py`:** `dadb041c86da97c43be22543d82e1063bdda7090`
**Blob — `011_tenant_placement.sql`:** `33f8a9f5c723b2d26e999d00e41220d2527ee981`
**Blob — `invariant-traceability.csv`:** `b241846b233198cfcfc0bb03f92a930fb9b5e513`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifier:** Codex
**Suites:** canonical **488/488** against PostgreSQL

---

## 1. What this is — and why it is the most safety-critical seam so far

Hybrid placement (`DEC-P35-TENANCY-MODEL` Option D) routes each tenant to the database holding its
data: a shared RLS pool by default, a dedicated database for paying tenants. **A mis-resolution is
the one tenant-isolation failure row-level security cannot catch** — inside the wrong database the
session is correctly scoped to a tenant with no rows there, so the caller reads "no data", never a
refusal (`DEC-P35-TENANCY-MODEL` §7.2). So the resolution must be structurally fail-closed.

This is also the seam whose A-09 interpretation an **independent immune review** corrected: defaulting
unregistered tenants to the shared pool (the tempting small change) is *fail-open-to-shared* and
re-opens exactly that silent path. The operator ratified the strict option (§9) for safety.

## 2. This is a defensive boundary — verify the refusals

Every proposition below asserts that the resolver **refuses** what it cannot vouch for and **routes**
only what it can. There is no offensive objective.

## 3. Propositions (traced in `invariant-traceability.csv`)

| ID | The seam must… | Test |
| :--- | :--- | :--- |
| `P35-06-01` | resolve a shared-pool tenant to the control database | `test_a_shared_pool_tenant_resolves_to_the_control_database` |
| `P35-06-02` | resolve a dedicated tenant to its configured database | `test_a_dedicated_tenant_resolves_to_its_configured_database` |
| `P35-06-03` | refuse an **unregistered** tenant — never default (A-09 strict) | `test_an_unknown_tenant_is_refused_not_defaulted` |
| `P35-06-04` | refuse a dedicated tenant whose connection is unconfigured — never fall back to shared | `test_a_dedicated_tenant_with_no_configured_connection_is_refused` |
| `P35-06-05` | refuse an empty tenant identifier | `test_an_empty_tenant_identifier_is_refused` |
| `P35-06-06` | **`tenant_session` refuses an unregistered tenant** rather than serving it against the shared pool | `test_tenant_session_refuses_an_unregistered_tenant` |
| `P35-06-07` | `tenant_session` resolves and RLS-scopes a registered shared-pool tenant | `test_tenant_session_serves_a_registered_shared_pool_tenant` |

**Attack angle for the verifier:** try to get a tenant with no `tenants` row served (P35-06-03/06);
try to make a dedicated tenant with a missing `BOPEN_DEDICATED_DB__*` fall back to the shared pool
(P35-06-04). Both must refuse.

## 4. Execution

```text
python tools/run_tests.py     488/488 OK   (live PostgreSQL)
```

Migration 011 adds `placement_kind`/`placement_ref` to the `tenants` row (default `shared_pool`,
backfilled). `resolve_placement` reads it via the control connection and is fail-closed;
`tenant_session` calls it when no connection is supplied and verifies a dedicated connection's
declared identity before use. Mutation intuition: making `resolve_placement` return a default on a
missing row (Option B) breaks P35-06-03 and P35-06-06.

## 5. What this does NOT establish (disclosed)

1. **Resolution is per-`tenant_session` call, not at the request boundary** (`DEC-P35-TENANCY-MODEL`
   §9.3). Same security property, one extra placement read per tenant-scoped call; boundary
   resolution is a tracked refinement.
2. **No dedicated database is provisioned** — the resolver routes to one when configured, but the
   provisioning path and trial→paid migration are deferred until a paying tenant exists.
3. **The entitlement→`tenants` foreign key is scheduled, not added** — it needs the deferred
   `VARCHAR(64)→UUID` type migration migration 004 raised. Until then the strict resolver enforces
   the registration invariant at the routing boundary (an orphan entitlement tenant is unreachable
   through the kernel), which is the property the FK would give at the storage layer.
4. **`verify_connection_serves` is exercised structurally**, not against a real dedicated database
   (none exists yet); its `placement_identity` check is proven by unit reasoning, not a live probe.

## 6. Authority

A maker's submission. `EBIV` §8: a passing suite carries no verdict weight.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
