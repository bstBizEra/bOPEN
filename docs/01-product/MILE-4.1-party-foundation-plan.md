# MILE-4.1 — Party & Relationship Foundation, first-slice plan (`BOPEN-PARTY-001`)

**Document ID:** `PLAN-MILE-4.1`
**Version:** `1.0.0`
**Status:** **Plan — buildable on Phase 4 authorization** ([`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md))
**Issued:** 2026-08-03
**Raised by:** Claude (agent, Motor role) — advisory only

---

## 1. What a "party" is, and why it is not a "principal"

The kernel already has **principals** — authentication identities that hold tenant memberships and
mint tokens. A **party** is a *business* entity: a person, an organization, a vendor, a supplier, a
customer. The two are deliberately separate:

- A principal is *who is calling* (auth). A party is *who the business is dealing with* (data).
- One tenant's customer list is business data owned by that tenant; it must be tenant-isolated the
  same way resources are — a party is never global.
- A person-party may or may not ever become a principal (most customers never log in).

Conflating them would put business records in the authentication namespace and leak one tenant's
customer graph into another's. They stay distinct.

## 2. The narrow first slice (only this)

| In scope | Out of scope (later slices) |
| :--- | :--- |
| **Party** core: `party_type` (person \| organization), display name, tenant scope, status, timestamps | Vendor/supplier/customer *roles* on a party |
| **Relationship** edge: a typed, directed link between two parties in the same tenant (e.g. `employs`, `supplies`) | Cross-tenant relationships (there are none by design) |
| Tenant isolation by **RLS** from migration one | The 4.2 foundations (documents, money, UOM, …) |
| HTTP surface: create/read party and relationship, tenant-scoped | Any satellite product (4.3) |

## 3. Invariants to verify (the R4 negative probes, drafted early)

Each will carry an executed test and a row in `invariant-traceability.csv` before any ballot:

- `INV-PARTY-TENANT-ISOLATION-01` — a party created in tenant A is invisible to tenant B (RLS,
  executed SQL, not application filtering).
- `INV-PARTY-TENANT-WRITE-01` — a cross-tenant party INSERT is refused by the database.
- `INV-PARTY-TYPE-01` — a party with an unknown `party_type` is refused (CHECK constraint).
- `INV-RELATIONSHIP-SAME-TENANT-01` — a relationship cannot link parties across tenants; the
  foreign keys and RLS make the foreign party unreadable, so the edge cannot be formed.
- `INV-RELATIONSHIP-NO-SELF-01` — a party cannot have a relationship to itself (CHECK).
- `INV-PARTY-AUTHZ-01` — creating or reading a party requires a validated context (bearer path),
  reusing the Phase 3.5 `resolve_context` dependency — a party endpoint is not a new auth hole.

## 4. How it plugs into the proven kernel (reuse, not reinvent)

- **Persistence**: a new migration adds `parties` and `party_relationships`, both with
  `FORCE ROW LEVEL SECURITY` and tenant-isolation policies mirroring the existing tenant-scoped
  tables — the same mechanism the Phase 3.5 isolation suite already verifies.
- **HTTP**: new endpoints on the existing FastAPI app, behind the same `resolve_context` bearer
  dependency; the gateway forwards them unchanged (no gateway change needed).
- **Audit**: party lifecycle events go through the existing durable audit envelope.
- **Contracts**: a frozen JSON schema for the party payload, conformance-checked like the others.

## 5. The maker cycle (same governance)

Tests-first → migration + code → execute against live PostgreSQL → trace invariants (R2) → maker
submission → **Codex** independent ballot (defensive framing) → operator disposition under EBIV §6.5.
Party data is tenant-scoped from the first migration; the first probe run is the cross-tenant
isolation test, red before the RLS policy exists.

## 6. Why this is the right first build

It is the smallest Phase 4 unit that (a) every later foundation and product needs, (b) commits to no
satellite product, and (c) re-exercises the Phase 3.5 isolation boundary on real business data — so
if tenant isolation has any gap for non-kernel tables, MILE-4.1 finds it before any product is built
on top.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
