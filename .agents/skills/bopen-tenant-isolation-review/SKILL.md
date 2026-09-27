---
name: bopen-tenant-isolation-review
description: Review tenant context, membership resolution, PostgreSQL RLS and cross-tenant negative-test coverage for a bOPEN change.
---

# Tenant Isolation Review

Trace tenant context from authentication to request, service, database, jobs, cache,
files, search, exports, events and audit.
Verify missing or forged context fails closed.
Require read, write and reference negative tests between at least two tenants.
Record findings without granting final conformance approval.
