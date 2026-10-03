# Architecture Baseline

The skill enforces the bOPEN P0 architecture position:

```text
Global principal
  → tenant membership
  → validated active tenant context
  → authorization
  → entitlement
  → product/module/capability
  → resource/action
  → domain event
  → audit/usage/evidence
```

Database controls are part of the trust boundary. PostgreSQL RLS, tenant-aware constraints, audit integrity, transactional outbox integrity, and migration evidence must therefore be evaluated as architecture controls rather than ordinary implementation details.

The skill remains analysis-only. Mutation belongs to a separately authorized migration deployment workflow with independent review and post-deployment verification.
