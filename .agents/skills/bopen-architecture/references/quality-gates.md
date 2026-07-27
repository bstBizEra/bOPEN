# Quality Gates

## Architecture completeness

- Scope, assumptions, exclusions, and authority are explicit.
- Principal, tenant, membership, organization, legal entity, role, permission, entitlement, capability, tool, skill, and workflow are not conflated.
- Component and data ownership are defined.
- State machines and invalid transitions are defined for lifecycle-sensitive entities.
- APIs and events have versioning, idempotency, and error semantics.
- Provider-specific choices are behind owned contracts unless an ADR accepts lock-in.

## Tenancy and authorization

- Context is server validated and propagated through API, job, event, cache, and database layers.
- Pooled tenant data has RLS/default deny and no bypass path for application roles.
- Service and agent principals use explicit grants.
- Entitlement, module enablement, authorization, and policy checks are separate.
- Cross-tenant negative tests cover direct access, search, exports, analytics, caches, logs, events, background jobs, and support access.

## Data and operations

- Data classification, encryption, retention, deletion, backup, and restore are defined.
- Transactions, concurrency, retries, compensation, and partial failure are defined.
- Outbox, deduplication, ordering assumptions, replay, and dead-letter handling are defined.
- Audit events are complete, correlated, protected, and queryable.
- Observability includes tenant-safe logs, metrics, traces, and alerts.

## Delivery and supply chain

- Dependencies are pinned or governed.
- CI runs schema validation, tests, secret scanning, dependency scanning, and package checks.
- Build provenance and SBOM are produced for publication candidates.
- Published versions are immutable, signed, and revocable.
- Rollback and emergency suspension procedures are tested.

## Mandatory test catalogue

At minimum:

```text
happy path
invalid input
unauthenticated principal
unauthorized principal
wrong tenant
missing tenant context
inactive tenant
inactive/expired membership
missing entitlement
disabled module
expired grant
concurrent update
idempotent retry
partial failure
rollback/compensation
outbox replay
dead-letter recovery
audit integrity
backup and restore
cache isolation
search/export isolation
agent/tool denial
```

## Exit rule

A package or system cannot pass when a non-waivable control is untested, evidence is missing, or cross-tenant behavior is uncertain. Unknown is not pass.
