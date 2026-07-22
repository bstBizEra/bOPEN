# bOPEN Architecture Invariants

- **INV-001** — Global Principal identity is independent of every Tenant.
- **INV-002** — Membership is the governed relationship between Principal and Tenant.
- **INV-003** — Every tenant-sensitive operation uses a validated Active Tenant Context.
- **INV-004** — No tenant-local duplicate identity store such as tenant_users.
- **INV-005** — Principal Party Tenant Organization Legal Entity Membership Role Permission and Entitlement remain distinct.
- **INV-006** — Membership is not Role; Role is not Job Title; Permission is not Entitlement.
- **INV-007** — Available Entitled Enabled and Authorized remain separate.
- **INV-008** — Tenant-owned PostgreSQL data uses default-deny RLS and cross-Tenant negative tests.
- **INV-009** — P0 remains a modular monolith unless an approved ADR changes it.
- **INV-010** — Business changes and integration events use a transactional outbox.
- **INV-011** — Security-relevant actions create correlated audit and evidence records.
- **INV-012** — bOPEN owns platform concerns; product and industry packages own domain behavior.
- **INV-013** — A Skill is a procedure and never an authorization grant.
- **INV-014** — Published Skill versions are immutable and digest-bound.
- **INV-015** — Every tool call is independently authorized in current context.
- **INV-016** — Skill packages contain no credentials or unrestricted secrets.
- **INV-017** — Tenant-facing autonomous production execution is outside P0 unless separately authorized.
- **INV-018** — No uncontrolled external Skill marketplace or remote installation in P0.
