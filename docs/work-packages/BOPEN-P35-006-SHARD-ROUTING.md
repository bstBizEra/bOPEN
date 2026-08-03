# WP-P35-06 — Tenant placement routing

**Status:** **In progress — resolution seam CORE landed 2026-08-03 (`53adc14`), maker work awaiting wiring + Codex verification.**
> **Resume point (2026-08-03).** The correctness-critical resolution core is built and green:
> migration 011 records placement on the tenant registry row (`placement_kind` shared_pool|dedicated
> + `placement_ref`, backfilled shared_pool); `platform_kernel/placement.py` resolves fail-closed
> (unknown tenant, unknown kind, unconfigured dedicated, empty → refused, never defaulted);
> `verify_connection_serves` is the identity check for dedicated databases. 6 probes executed,
> canonical suite 488/488. **Next, as a deliberate separate step:** (1) wire `db.tenant_session` to
> resolve the connection through `resolve_placement` when none is passed, and call
> `verify_connection_serves` on dedicated — this changes the connection path every request uses, so
> it is done carefully and full-suite-green before it is trusted; (2) trace the seam invariants
> (R2), maker submission, **Codex** ballot (defensive framing), operator disposition under §6.5.
> Dedicated-DB provisioning and trial→paid migration remain deferred until a paying tenant exists.
**Original status:** Accepted, not started — authorized by [`DEC-P35-TENANCY-MODEL`](../decisions/DEC-P35-TENANCY-MODEL.md) §7.1, **generalized by §8.4**

> **Generalized 2026-07-31.** This package was written as *shard routing* under Option C. Option D
> (hybrid placement) supersedes that, and the package widens rather than dies: the resolver now
> returns a **connection target**, which may be a tenant's dedicated database or a shared
> row-level-security pool. Every acceptance criterion below survives unchanged, and `A-09` becomes
> more important — under hybrid placement a wrong default could route a private tenant into the
> shared pool. Read "shard" below as "placement target".
**Version:** `1.0.0`
**Issued:** 2026-07-31
**Owner:** Engineering Authority
**Parent plan:** [`BOPEN-P35-001`](BOPEN-P35-001-EXECUTION-PLAN.md)
**Governing artifacts:** `BOPEN-TENANT-001`, `BOPEN-ARCH-001`, `ADR-0005`, `AGENTS.md` §7 invariants 2 and 10, §8, §14
**Maker:** *unassigned*
**Eligible verifier:** any engine that does not author it

---

## Objective

Distribute tenants across multiple PostgreSQL instances so that database load scales by adding
instances, while row-level security continues to enforce isolation *within* each instance.

The measure of completion is not that routing works. It is that **a tenant cannot be served from
the wrong shard**, and that a test would fail if that protection were removed.

## Why this shape

`DEC-P35-TENANCY-MODEL` §3.2 established that load distribution and the isolation mechanism are
independent axes. This work package changes only the first. Every RLS policy, every migration and
all 38 isolation tests survive unchanged — and now run per shard.

## In scope

- **D-11 Shard map.** A resolver from tenant identifier to shard, and from shard to DSN.
  Configuration-driven, no new table — a control-plane table would need `D-P35-004`..`D-P35-010`,
  which are unratified. A single-shard configuration must be the default so that an unconfigured
  deployment behaves exactly as today.
- **D-12 Routing in `db.py`.** `tenant_session(tenant_id)` resolves the tenant's shard and
  connects there. `system_session` gains an explicit shard argument rather than a default,
  because "the system shard" is not a meaningful idea once there is more than one.
- **D-13 Provisioning placement.** `POST /v1/tenants` records which shard a tenant was placed on,
  at placement time, and that placement is immutable without a governed migration.
- **D-14 Per-shard migration orchestration.** `db_bootstrap.py --apply` applies to every
  configured shard, and reports per-shard migration state. A shard behind on migrations must be
  refused, not silently used.
- **D-15 Per-shard isolation conformance.** The existing 38 isolation tests execute against every
  configured shard, plus the cross-shard tests in A-11.

## Out of scope

- Cross-shard queries, joins or reporting. If a requirement needs them, stop and raise a decision.
- Rebalancing or moving a tenant between shards. Explicitly deferred — see "Deferred" below.
- Any change to an RLS policy, a migration's contents, or `ADR-0005`.
- Option B (database-per-tenant) in any form.

## Acceptance criteria

**A-08 — A tenant resolves to exactly one shard, always.**
Resolution is deterministic and total. The same tenant identifier resolves to the same shard on
every call, in every process, across restarts.

**A-09 — An unresolvable tenant is refused, never defaulted.**
A tenant with no placement must raise. Falling back to a default shard would write a tenant's
data somewhere it does not belong, and RLS would not catch it because the session would be
correctly scoped to a tenant with no rows there — a silent wrong answer rather than a refusal.

**A-10 — A misconfigured shard map is refused at startup, not at first use.**
A DSN that does not resolve, a shard named in a placement but absent from the map, or a duplicate
placement must prevent the kernel starting. Discovering this on a tenant's first request means
discovering it in production.

**A-11 — Cross-shard leakage is impossible and adversarially tested.**
With two shards configured and a tenant on each, a negative probe must show that a session scoped
to tenant A on shard 1 cannot read tenant B's rows on shard 2 — and, critically, that a request
for tenant B routed to shard 1 **fails** rather than returning an empty result.

**A-12 — Every shard passes the full isolation suite.**
The 38 existing isolation tests run per shard. A shard is not usable until it does.

**A-13 — Migration state is uniform before service.**
The kernel refuses to serve from a shard whose applied-migration set differs from the others.

**A-14 — Single-shard default is behaviour-identical.**
With one shard configured, or none, behaviour matches the pre-`WP-P35-06` kernel exactly. This is
what makes the change additive and rollback trivial.

**A-15 — Placement kind is explicit, and a dedicated tenant never lands in the shared pool.**
*(added by `DEC-P35-TENANCY-MODEL` §8.4)*
Every placement records whether it is `dedicated` or `shared`. A tenant placed as `dedicated`
must be unroutable to the shared pool by construction, not by convention — a negative probe must
show the attempt failing rather than succeeding quietly. Under Option D this is the isolation
guarantee itself: a private tenant reaching the shared pool is the failure the model exists to
prevent, and it would look like ordinary operation.

**A-16 — Shared-pool tenants remain covered by row-level security.**
The 38 isolation tests run against the shared pool exactly as today. Option D keeps RLS as a live
mechanism rather than a retired one, and it must keep being tested as one.

## Deferred, and named so it is not forgotten

**Rebalancing.** Moving a tenant between shards needs a migration path, a cutover with no split
brain, and a way to prove no rows were left behind. It is not in this package. The consequence is
that placement is effectively permanent until a further work package addresses it — which should
be decided **before** the first deployment has enough tenants for rebalancing to matter, not
after.

## Risks

| Risk | Mitigation |
| :--- | :--- |
| Wrong-shard routing returns empty results that read as "no data" | A-09 and A-11 require refusal, not empty results |
| Connection-pool multiplication across shards exhausts client resources | Measure per-shard pool sizing before increasing shard count |
| Per-shard migration drift | A-13 refuses service rather than tolerating drift |
| Shard map and actual placements diverge | A-10 validates at startup |

## Required checks

Every check in `BOPEN-P35-001`, plus the isolation suite executed once per configured shard.

## Rollback

Configure a single shard. D-11 through D-13 are additive and inert under a single-shard map
(A-14), so rollback is configuration, not code removal.

## Authority

Authorized for implementation by `DEC-P35-TENANCY-MODEL` §7.1. Production activation remains
unauthorized. Completion requires an independent verifier under `BOPEN-GOV-EBIV-001`.
