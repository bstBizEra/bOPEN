# DEC-P4-ENTRY — Phase 4 entry gate: the Phase 3.5 precondition is met

**Decision ID:** `DEC-P4-ENTRY`
**Version:** `1.0.0`
**Status:** **Proposed — awaiting operator authorization** (phase entry is an authority act; `AGENTS.md` §20.2)
**Issued:** 2026-08-03
**Owner:** Architecture & Engineering Authority
**Raised by:** Claude (agent, Motor role) — advisory only
**Governing:** [`PHASE-OUTLINE-SPEC`](../01-product/PHASE-OUTLINE-SPEC.md) (Phase 4); `AGENTS.md` §20.2 (phase gates)

---

## 1. Why this exists

Phase 4 is recorded as **"NOT AUTHORIZED — blocked pending Phase 3.5"**. That block now has a
resolved precondition: **Phase 3.5 is closed** — all five work packages disposed, the authentication
boundary and AUTH-D3 hardening verified and operator-disposed under the two-agent profile
([`milestone/auth-hardening-complete-2026-08-02`](../BOPEN-MILESTONE-AUTH-COMPLETE-2026-08-02.md)),
and the kernel demonstrated end to end over real sockets (`scripts/demo_live_stack.py`).

This surface proposes opening the Phase 4 gate. **It decides nothing and builds nothing** — it names
what Phase 4 delivers, the narrow first slice, and the criteria, so the operator can authorize entry
from one place.

## 2. What Phase 4 is (from the roadmap, not invented)

**Common Business Foundations & Satellite Products.** Three milestones:

- **MILE-4.1 — Party & Relationship Foundation (`BOPEN-PARTY-001`)**: person, organization, vendor,
  supplier, customer graph — the identity of *business* entities (distinct from the kernel's
  *principals*, which are auth identities).
- **MILE-4.2 — Reusable Business Foundations**: document management, location/geography, money/
  currency, measurement/UOM, calendar, assets, workflow state engine, notifications.
- **MILE-4.3 — Satellite Products**: bPro, bFleet, PropTech, bERP, LDM (composition specs already
  exist under `docs/10-products/`).

## 3. The narrow first slice — MILE-4.1 only

Entering Phase 4 does **not** mean building all of it. The recommended first slice is **MILE-4.1
alone**, for three reasons:

1. **It is the dependency root.** Every foundation in 4.2 and every product in 4.3 references parties
   (a customer, a vendor, an organization). Nothing else in Phase 4 is buildable without it.
2. **It is not a strategic product bet.** Recommending the party foundation does not pick bPro over
   bFleet, or commit to any satellite product. That choice stays open and is the operator's when
   MILE-4.3 is reached.
3. **It plugs into the proven kernel.** A party is *owned by a tenant* — MILE-4.1 is the first test
   that the Phase 3.5 tenant-isolation boundary holds for real business data, not just kernel
   entities. It reuses RLS, the audit trail, and the context/authorize path already verified.

MILE-4.2 and MILE-4.3 are **out of this slice** and enter on their own dispositions.

## 4. Entry criteria (met / to confirm)

| Criterion | State |
| :--- | :--- |
| Phase 3.5 closed and disposed | **met** — milestone tag + disposition records |
| Kernel runnable and demonstrated end to end | **met** — `demo_end_to_end.py`, `demo_live_stack.py` green |
| Network boundary for cross-service calls exists | **met** — gateway (WP-P35-04) forwards to the kernel |
| EBIV verification available for Phase 4 work | **met** — two-agent profile in force (§6.5) |
| A first-slice scope that is buildable and narrow | **this doc — MILE-4.1** |

## 5. How MILE-4.1 work will run (governed, same loop)

- A PRD/plan for the party graph (see the companion first-slice plan), then a maker cycle:
  tests-first, PostgreSQL with RLS, invariants traced in `invariant-traceability.csv` (R2), maker
  submission, **Codex** verification, operator disposition under §6.5.
- Party data is tenant-scoped from the first migration — RLS, not application filtering.
- No satellite product is started until MILE-4.3, and that entry is a separate operator decision.

## 6. What this is not

Not an authorization, not an implementation, not a product commitment. Phase entry is reserved to
the operator (`AGENTS.md` §20.2). On authorization, MILE-4.1 becomes buildable; MILE-4.2 and 4.3
remain gated.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
```
