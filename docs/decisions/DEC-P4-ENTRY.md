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

---

## 11. Amendment 2026-08-05 — Location foundation authorized

> **Change note (extend-only).** Recorded **before** any build, per the §7/§8 sequencing lesson. The
> operator authorized the Location foundation after the advisory review
> ([`REVIEW-MILE-4.2-LOCATION`](../01-product/MILE-4.2-location-foundation-review.md)) closed with no
> blocking boundary defect. Scope follows [`RESEARCH-MILE-4.2-LOCATION`](../01-product/MILE-4.2-location-foundation-research.md)
> §11 with the LOC-D resolutions below.

### 11.1 Decision

**The Location foundation is AUTHORIZED** — a tenant-scoped Location Registry (`BOPEN-LOC-001`): stable
immutable place identity, versioned addresses, point geometry observations with explicit acceptance,
external identifiers, and a bounded `contains` relationship. Keystone (`LOC-INV-04` + `LOC-INV-06`):
**coordinate validity** (a NaN/∞, out-of-range, reversed-axis, or non-Point/unsupported-CRS coordinate
is refused) and **provider distrust** (an observation is a *candidate* requiring an explicit authorized
acceptance — "HTTP 200 does not mean accepted"; identity is never derived from a formatted address,
coordinate, or provider ID).

**LOC-D resolutions (operator, transcribed):**

| Decision | Resolution |
| :--- | :--- |
| `LOC-D-01` | Validation fixtures exercise **PropTech operating-address** and **bFleet depot** (schema is consumer-neutral; both exercise identity/address/point/containment/privacy) |
| `LOC-D-02` | Small governed `location_type` vocabulary via CHECK (`site`,`building`,`depot`,`office`,`warehouse`,`other`), versioned — not arbitrary strings |
| `LOC-D-03` | Owned structured address components informed by ISO 19160-1 / UPU S42; **Laos/Thailand profile prioritized**; original input preserved separately from normalized + rendered forms |
| `LOC-D-04` | Point storage **`NUMERIC(9,6)` exact decimal** longitude/latitude (never float), round-trip proven; **accuracy radius carried as a UOM `length` `Quantity`** (m/km, exact `Decimal`), recorded separately from numeric precision |
| `LOC-D-05` | First-slice relationship **`contains` only**; one active parent per hierarchy; **containment cycles refused by a real `WITH RECURSIVE` check**, not a row CHECK |
| `LOC-D-06` | Precise geometry is higher-sensitivity: **redacted from logs/events/default exports**; `location.geometry.read_precise` a separate capability; coarsening is presentation, not an accuracy claim |
| `LOC-D-07` | **Production provider selection DEFERRED** (needs its own ADR); the first slice ships the owned registry + acceptance discipline; a deterministic fake adapter serves contract tests only; the live `geocode.request` HTTP flow ships with the provider ADR |
| `LOC-D-08` | Acceptance requires an **explicit authorized action**; no observation auto-accepts on HTTP success; confidence/provenance gate acceptance (`LOC-INV-05`) |
| `LOC-D-09` | Nearby/spatial/autocomplete **search DEFERRED** (avoids a cross-tenant existence oracle, `LOC-INV-01`) |
| `LOC-D-10` | PostGIS / geofence / polygon / alternate CRS **DEFERRED** to a later ADR; Point + `OGC:CRS84` only |
| `LOC-D-11` | Jurisdiction refs treated as external versioned references via `ExternalLocationIdentifier`, not bOPEN legal truth |
| `LOC-D-12` | Deletion = **retire/tombstone** once referenced; append-only history; `ON DELETE RESTRICT` on durable referents |

The API names coordinate fields **`longitude`/`latitude`** explicitly (not a bare `[a,b]`) to make a
silent axis transposition unrepresentable. The six tables (`locations`, `location_address_versions`,
`location_geometry_observations`, `location_external_identifiers`, `location_relationships`, and
append-only `location_history`) enter `TENANT_SCOPED_TABLES` and the trial→paid `COPY_ORDER`
(parents before children).

| Field | Value |
| :--- | :--- |
| **Decision** | **AUTHORIZE the Location foundation** per the scope and LOC-D resolutions above |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — Architecture Authority |
| **Decision timestamp** | 2026-08-05 |
| **Recorded by** | Claude (agent, Motor role), transcribing an operator decision. `execution_authority: false`, `approval_authority: false` |

The build proceeds tests-first under the governed cycle; an independent **Codex** ballot follows under
`EBIV` §6.5, then operator disposition.

---

## 12. Amendment 2026-08-06 — Notification foundation build authorized

> **Change note (extend-only).** Recorded on the operator's explicit authorization, per the §7/§8
> authorize-before-build discipline. The build proceeds on a **frozen artifact set** and discharges the
> independent re-review's build-time obligations with executed tests; it does not defer them further.

### 12.1 Decision

**The Notification foundation build is AUTHORIZED** — the kernel's first asynchronous runtime surface: a
Postgres-only transactional-outbox worker with a durable fenced lease, idempotency-first duplicate-send
safety, a mutable-current + append-only-evidence model, in-database tenant fairness, and an
AUTH-D1-verified inbound callback plane, resolving a business recipient through the disposed ContactPoint
resolver (never `principals.email`).

**Governing frozen artifacts:**
- `ADR-NOTIFY-WQ` v2.1 (worker/queue) and `ADR-NOTIFY-PROVIDER` v2.1 (provider/channel) — **frozen at
  commit `96f21d3`** (the 9 re-review corrections applied; design decisions independently assessed sound).
- `BOPEN-NOTIFY-001` (spec), the Notification test/refusal matrix, and the migration/rollback plan —
  being finalized now; **the build's first migration does not land until these are committed (frozen).**
- Foundation research + review; the privacy/threat model; the two independent Codex review records.

**Scope of the first slice:** channels **email and phone** only (aligned to the built ContactPoint
endpoint types); a deterministic **fake adapter** only — **no production provider is selected**
(`NOTIFY-D-07` deferred); the worker/queue + outbox + append-only attempt/receipt evidence + the callback
plane + the fake send path. Outbound webhooks/egress, production providers, and provider failover are
deferred to their own decisions.

**Build-time obligations (acknowledged, not deferred).** The independent re-review returned the design
decisions sound with residual *concurrency/completeness* items. These are **discharged during the
governed tests-first build on live PostgreSQL**, with executed tests (EBIV R2): lease-steal / fence-CAS
rejection; crash-mid-send → `unknown` recovery that reuses the same attempt's stored idempotency key
(no duplicate external send); no blind resend of an expired-`sending` reclaim; concurrent-claimer
per-tenant inflight cap not exceeded; callback-role RLS/grant/revocation parity; deterministic replay
dedup; and append-only attempt/receipt resisting UPDATE/DELETE and parent cascade. The exit gate stays
closed until they pass.

| Field | Value |
| :--- | :--- |
| **Decision** | **AUTHORIZE the Notification foundation build** per the frozen artifact set and scope above |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — Architecture Authority |
| **Decision timestamp** | 2026-08-06 |
| **Recorded by** | Claude (agent, Motor role), transcribing an operator decision. `execution_authority: false`, `approval_authority: false` |

The build follows the governed cycle (tests-first → migrations + forced RLS → repositories →
bearer-gated endpoints + the worker/callback planes → invariant traceability → maker submission anchored
to a candidate → independent **Codex** ballot → operator disposition). It authorizes no deployment,
provider activation, or production; those remain distinct later acts.
