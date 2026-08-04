# bOPEN — the next visible success target

**Status:** **Advisory plan — target realized 2026-08-04.** The described success (multi-tenant business data, end to end, isolated and placement-routed over the gateway) is demonstrated by `scripts/demo_business_scenario.py` (two tenants, private party graphs) and `scripts/demo_approval_flow.py` (Party + Money + Workflow composed into an invoice-approval flow). Retained as the record of the target and how it was met.
**Issued:** 2026-08-03
**Raised by:** Claude (agent, Motor role) — advisory plan, no approval authority
**Purpose:** name a concrete, demonstrable success the next working round drives straight to, and the ordered path to it.

---

## 1. What "success" will look like — something you can watch

A single script run that shows **bOPEN handling real multi-tenant business data, end to end, isolated and placement-routed** — not kernel plumbing, but the thing a business actually uses:

> Two tenants are provisioned. Each creates its own **parties** — customers, vendors, an
> organization — and **relationships** between them (a vendor *supplies* a customer). Everything
> flows **through the gateway** to the kernel to PostgreSQL. Then the proof: **tenant B cannot see
> or touch a single one of tenant A's parties or relationships** — the database refuses it — and
> every tenant's request is **routed to its correct placement** (shared pool today, ready for a
> dedicated database the moment one is configured), with a mis-route **refused, never silently
> served**.

That is bOPEN doing its one job — being a safe multi-tenant foundation — on business data, visibly.

## 2. The ordered path to it (each step verified before the next)

Every step is the same governed loop: tests-first → execute on live PostgreSQL → trace invariants
(R2) → **Codex** independent ballot (defensive framing) → operator disposition (§6.5).

1. **Finish the placement seam (`WP-P35-06`).** Wire `db.tenant_session` through `resolve_placement`
   + the identity check. This changes the connection path every request uses, so it is done
   carefully, full-suite-green, and **Codex-verified** before anything is trusted. *(core already
   landed and green — `53adc14`, 488/488.)*
2. **Finish MILE-4.1 (party foundation HTTP layer).** `PartyRepository` + bearer-gated endpoints to
   create/read parties and relationships, integration tests, then Codex verification. *(DB layer
   already landed and green — `eec7957`, 7 isolation probes.)*
3. **The success demo + milestone.** A `demo_business_scenario.py` that runs §1 end to end through
   the live gateway, prints each step and each refusal, and a milestone tag. This is the artifact
   you run to *see* the success.

## 3. Why this is the right "success" to aim at

- It is **achievable in one focused round** — both underlying layers already have their verified
  foundations; only the wiring, the HTTP surface, and the demo remain.
- It is **visible** — a business scenario (customers, vendors, relationships), not a test summary.
- It **proves the promise** — cross-tenant refusal on real data plus correct placement routing is
  exactly what "one tenant, one database" and "tenant privacy is structural" mean, shown rather
  than asserted.
- It **commits to no product yet** — parties are the foundation every satellite product (bPro,
  bFleet, bERP, …) will build on, so this success is reusable, not a bet on one product.

## 4. What is deliberately NOT in this target

Dedicated-database provisioning and trial→paid data migration remain deferred until a paying tenant
exists (no infrastructure ahead of measured need). The seam is built so they slot in later without
touching call sites. No satellite product (MILE-4.3) is started; that entry is a separate operator
decision.

```text
execution_authority: false
approval_authority: false
completion_claimed: false
```
