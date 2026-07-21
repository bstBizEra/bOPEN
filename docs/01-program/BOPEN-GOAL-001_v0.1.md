# GOALS.md — bOPEN Program Goals v0.1

## North Star

By the P4 conformance exit, bOPEN shall demonstrate a production-credible reusable
multi-tenant platform kernel in which a global principal can operate through governed
memberships across multiple tenants, modules can be registered and activated without
modifying the kernel, and the bPro reference product passes independent tenant-isolation,
authorization, audit, recovery and evidence gates.

## Strategic goals

### G-01 — Governed delivery

100% of implementation work is registered, authorized, traceable to requirements,
executed in an isolated worktree, independently checked and supported by evidence.

### G-02 — Verified multi-tenancy

100% of tenant-aware resources pass read, write, reference, background-job, cache, file,
search, export and event cross-tenant negative tests.

### G-03 — Reusable platform kernel

Identity, tenancy, membership, authorization, entitlement, audit, events, files,
notifications and module operations are implemented once and reused by product modules.

### G-04 — Module factory

A new module can move from registration to pilot through a repeatable contract,
scaffolding, test, evidence and release workflow without modifying unrelated modules.

### G-05 — Reference product

bPro validates the platform through at least one complete flow:

```text
Authenticate
→ select tenant
→ verify membership
→ verify entitlement
→ open bPro module
→ create tenant-owned resource
→ emit event
→ write audit record
→ process background work
→ verify isolation
```

### G-06 — Operational readiness

Backups, restoration, audit continuity, event replay, monitoring, incident response and
rollback are tested before general availability.

### G-07 — Harness interoperability

Codex, Claude Code, Antigravity and approved additional harnesses operate through a
shared governance contract, common skill format, bounded worktrees and structured
handoffs.

### G-08 — Evidence-to-learning conversion

Verified findings can become documentation, tests, ADRs, runbooks or SkillsHub
candidates through a controlled promotion process; raw agent memory never becomes
governing truth automatically.

## Program KPIs

| KPI | Target |
|---|---:|
| Requirements linked to work items | 100% |
| Authorized work items with evidence envelopes | 100% |
| Tenant-aware tables with verified RLS | 100% |
| Cross-tenant negative-test pass rate | 100% |
| Modules with complete manifests | 100% |
| Material changes independently checked | 100% |
| Open critical/high isolation findings at release | 0 |
| Releases with rollback evidence | 100% |
| Unexpired approved exceptions | 100% |
| Unauthorized production mutations | 0 |
