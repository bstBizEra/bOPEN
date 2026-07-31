# WP-P35-06 — Tenant shard routing

**Status:** **Accepted, not started** — authorized by [`DEC-P35-TENANCY-MODEL`](../decisions/DEC-P35-TENANCY-MODEL.md) §7.1
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
