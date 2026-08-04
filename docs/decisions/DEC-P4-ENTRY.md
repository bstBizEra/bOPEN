# DEC-P4-ENTRY — Phase 4 entry gate: the Phase 3.5 precondition is met

**Decision ID:** `DEC-P4-ENTRY`
**Version:** `1.0.0`
**Status:** **AUTHORIZED — MILE-4.1 (2026-08-03) and MILE-4.2 (2026-08-03, §7).** MILE-4.3 remains gated. Operator (`BizEra`, Architecture & Engineering Authority) authorizations transcribed by Claude (Motor); not a maker approval.
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

---

## 7. Amendment 2026-08-03 — MILE-4.2 (Money & Currency) authorized

> **Change note (extend-only).** §3 set MILE-4.1 as the only in-scope slice and recorded that
> MILE-4.2/4.3 "enter on their own operator dispositions". This records that disposition for MILE-4.2.

**Sequencing note, disclosed:** the maker built the MILE-4.2 Money slice on the operator's verbal
"start the Money foundation" instruction **before** this gate authorization was recorded. Codex,
verifying, correctly refused to ballot it fail-closed — the record still gated MILE-4.2 — and cast no
verdict. The engineering is complete and green (canonical 521/521), but authorization is an authority
act the maker may not infer from an execution instruction, so it is recorded here explicitly rather
than interpreted. The maker should have obtained this before building, as it did for MILE-4.1.

### 7.1 Decision

**MILE-4.2 (Money & Currency) is AUTHORIZED.** In scope: the money value type (integer minor units)
and tenant-scoped exchange rates with conversion, as submitted in
[`EVD-MILE-4.2-MONEY-MAKER`](../evidence/phase-3.5/mile-4.2-money-maker.md), candidate `30f3ca2`.
MILE-4.3 (satellite products) and the other MILE-4.2 foundations (Document, Location, UOM, Calendar,
Asset, Workflow, Notification) remain gated and enter on their own operator dispositions.

| Field | Value |
| :--- | :--- |
| **Decision** | **AUTHORIZE MILE-4.2 (Money & Currency)** — the money value type and tenant exchange rates/conversion. Other 4.2 foundations and all of 4.3 stay gated |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — Architecture Authority |
| **Decision timestamp** | 2026-08-03 |
| **Recorded by** | Claude (agent, Motor role), transcribing an operator decision. `execution_authority: false`, `approval_authority: false` |

On this authorization the MILE-4.2 candidate `30f3ca2` becomes verifiable; its Codex ballot follows
under `EBIV` §6.5.

---

## 8. Amendment 2026-08-03 — Workflow State Engine (MILE-4.2) authorized

> **Change note (extend-only).** Recorded **before** any build this time, per the sequencing lesson
> in §7. The operator directed the next foundation with authorization first.

### 8.1 Decision

**The Workflow State Engine foundation (part of MILE-4.2) is AUTHORIZED.** In scope: a generic,
tenant-scoped state machine for business processes — workflow definitions (states + allowed
transitions), instances, and transitions gated by the definition and by authorization, with an
append-only history and a lifecycle event on each transition. Consumers: all satellite products
(`CAPABILITY-MATRIX`). The other MILE-4.2 foundations (Document, Location, UOM, Calendar, Asset,
Notification) and all of MILE-4.3 remain gated and enter on their own operator dispositions.

| Field | Value |
| :--- | :--- |
| **Decision** | **AUTHORIZE the Workflow State Engine foundation (MILE-4.2)** — definitions, instances, transitions (definition- and authz-gated), append-only history, lifecycle events. Other foundations and all of 4.3 stay gated |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — Architecture Authority |
| **Decision timestamp** | 2026-08-03 |
| **Recorded by** | Claude (agent, Motor role), transcribing an operator decision. `execution_authority: false`, `approval_authority: false` |

The build proceeds tests-first under the governed cycle; a Codex ballot follows under `EBIV` §6.5.

---

## 9. Amendment 2026-08-05 — Unit-of-Measure (UOM) foundation authorized

> **Change note (extend-only).** Recorded **before** any build, per the §7/§8 sequencing lesson. The
> operator directed UOM as the next foundation, with scope, after reviewing the research
> [`RESEARCH-MILE-4.2-UOM`](../01-product/MILE-4.2-uom-foundation-research.md).

### 9.1 Decision

**The Unit-of-Measure foundation (part of MILE-4.2) is AUTHORIZED.** In scope: a dimension-safe
`Quantity` value type (exact `decimal.Decimal` magnitude, never a float; `ROUND_HALF_EVEN`),
**multiplicative units only**, with a **standard unit registry as a code constant** (SI + common
business/imperial units + Thai land units `rai`/`ngan`/`wah²`) and **tenant custom units with full
CRUD** (create, read, update, delete), tenant-scoped by RLS — reusing the `exchange_rates` tenancy
machinery. The keystone invariant is **dimension safety** (`kg + m` refused, cross-dimension
conversion refused). **Affine/temperature units are REFUSED loudly** (not silently mis-converted), and
**compound/derived units** (`km/h`, price-per-unit) are **deferred** to their own slices. The
foundation is product-agnostic — ready to support multiple satellite products. Other MILE-4.2
foundations (Document, Location, Calendar, Asset, Notification) and all of MILE-4.3 remain gated.

| Field | Value |
| :--- | :--- |
| **Decision** | **AUTHORIZE the UOM foundation (MILE-4.2)** — Quantity value type (Decimal, dimension-safe, exact multiplicative conversion), standard unit constant, tenant custom units with full CRUD (RLS). Temperature/affine refused; compound units deferred. Other foundations and all of 4.3 stay gated |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — Architecture Authority |
| **Decision timestamp** | 2026-08-05 |
| **Recorded by** | Claude (agent, Motor role), transcribing an operator decision. `execution_authority: false`, `approval_authority: false` |

The build proceeds tests-first under the governed cycle; a Codex ballot follows under `EBIV` §6.5.

---

## 10. Amendment 2026-08-05 — Party ContactPoint extension authorized (unblocks Notification)

> **Change note (extend-only).** Recorded **before** any build, per the §7/§8 sequencing lesson. The
> operator directed the ContactPoint extension after reviewing
> [`RESEARCH-MILE-4.2-PARTY-CONTACTPOINT`](../01-product/MILE-4.2-party-contactpoint-extension-research.md)
> (authored by a Claude subagent; its build will be independently verified by Codex under EBIV §6.5).
> This extends the built Party foundation (`BOPEN-PARTY-001`) with the contact-endpoint entity the
> Notification `NotificationRecipientResolver` needs; it never uses `principals.email` as a destination.

### 10.1 Decision

**The Party ContactPoint extension is AUTHORIZED**, scoped to `RESEARCH-MILE-4.2-PARTY-CONTACTPOINT`
§13 with the operator's CP-D resolutions below. Keystone (`CP-INV-03`): the resolver yields a usable
destination **only** for a *verified* contact point of the *authorized purpose* belonging to a *Party
of the caller's tenant* — never `principals.email`, never a cross-tenant/unverified/wrong-purpose
endpoint.

**CP-D resolutions (operator, transcribed):**

| Decision | Resolution |
| :--- | :--- |
| `CP-D-01`/`CP-D-02` | First slice endpoint types **`email` and `phone` only**; **`postal` deferred** (Location is unbuilt — no dependency now); social/push/webhook deferred |
| `CP-D-03` | **`ON DELETE RESTRICT` + retire-not-delete**; append-only `party_contact_point_verification_events` survives direct mutation and parent cascade (migration-014 lesson) |
| `CP-D-04` | Primary flag scope **per `(party, type)`**; one live primary enforced |
| `CP-D-05`/`CP-D-08` | Self-service verification ceremony (OTP/magic-link) **deferred**; the first slice ships a **governed, audited administrative-assertion** verify capability that records `verification_method='administrative_assertion'` in the append-only history — so a real verified destination exists and Notification is functionally unblocked, while the asserted-vs-challenged distinction stays auditable |
| `CP-D-06` | Channel→type: `email→email`, `sms`/`voice→phone`; purpose vocabulary small & governed, aligned with Notification |
| `CP-D-07` | Endpoint value stored, **redacted in logs/events/status**; at-rest encryption a tracked refinement (disclosed) |
| `CP-D-09` | `resolve` is a distinct, higher-trust capability from reading a raw endpoint value |

Both new tables (`party_contact_points`, `party_contact_point_verification_events`) enter
`TENANT_SCOPED_TABLES` and the trial→paid `COPY_ORDER` (parents before children, after `parties`).

| Field | Value |
| :--- | :--- |
| **Decision** | **AUTHORIZE the Party ContactPoint extension** per the scope and CP-D resolutions above |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — Architecture Authority |
| **Decision timestamp** | 2026-08-05 |
| **Recorded by** | Claude (agent, Motor role), transcribing an operator decision. `execution_authority: false`, `approval_authority: false` |

The build proceeds tests-first under the governed cycle; an independent **Codex** ballot follows under
`EBIV` §6.5, then operator disposition.
