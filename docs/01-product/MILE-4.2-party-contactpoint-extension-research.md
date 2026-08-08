# MILE-4.2 — Party ContactPoint extension, research & design

**Document ID:** `RESEARCH-MILE-4.2-PARTY-CONTACTPOINT`  
**Version:** `1.0.0`  
**Status:** **Research — advisory. Extension of the built Party foundation to unblock Notification recipient resolution; buildable only on separate operator authorization.** The extension remains gated by [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §9; a build needs its own bounded authorization recorded in `DEC-P4-ENTRY`.  
**Issued:** 2026-08-05  
**Owner:** Architecture & Engineering Authority  
**Raised by:** Claude (agent, Cortex role) — research and planning only; no approval authority  
**Entry evidence:** [`REVIEW-MILE-4.2-NOTIFICATION`](MILE-4.2-notification-foundation-review.md) §3.1 named the Party ContactPoint dependency (`NOTIFY-D-01`) as the critical path and offered path (a) "a Party ContactPoint extension slice first". This document is path (a): the design of the Party-owned thing the `NotificationRecipientResolver` resolves against.  
**Governing:** `AGENTS.md` §§2, 6–15; [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md); [`CAPABILITY-MATRIX`](CAPABILITY-MATRIX.md)  
**Extends:** `BOPEN-PARTY-001` — the built and disposed Party foundation (migration `010_party_foundation.sql`, `party_repositories.py`), which has `parties` and `party_relationships` and **no contact-point entity today**.  
**Dependent artifacts:** Future `BOPEN-PARTY-002`, the `NotificationRecipientResolver` contract, accepted work package, privacy/threat model, API/event contracts, migration/rollback plan, test matrix, and EBIV evidence  
**Clean-room (AGENTS.md §6):** schema.org, vCard, E.164, and RFC 5322 are **requirements sources only**. No external schema, vocabulary file, implementation, migration, or test is copied into bOPEN.

---

## 1. Executive summary

The recommended extension is a **tenant-scoped, Party-owned `party_contact_points` registry**: a small
set of typed, purpose-classified, verifiable communication endpoints attached to an existing `Party`.
It is the missing entity that lets a future `NotificationRecipientResolver` resolve a *business
recipient* to a *consented, verified destination* without ever falling back to `principals.email`.

ContactPoint is **Party-owned, not Notification-owned.** Notification never becomes a contact master;
it receives only an immutable, frozen `RecipientSnapshot` for one send and holds no write path into
this registry (§3.2, `CP-INV-12`). The contact point is a tenant-scoped endpoint attached to a Party
by the same composite-foreign-key discipline that makes `party_relationships` same-tenant at the
database (`(tenant_id, party_id) -> parties(tenant_id, id)`), so a contact point can never attach to a
Party of another tenant.

The **keystone invariant** — the property whose collapse makes the whole thing dangerous, the direct
analogue of Money's `CurrencyMismatchError`, UOM's dimension-safety, and Location's coordinate-validity
— is this:

> A usable notification destination requires a **verified** contact point of the **authorized purpose**
> belonging to a **Party of the caller's tenant**. Never `principals.email`; never a cross-tenant
> endpoint; never an unverified or failed endpoint; never a wrong-purpose or wrong-channel endpoint.

This document designs the **contract and the state**, not the ceremony. It models verification *state*
(`unverified` / `verified` / `failed`) and a verification *seam*, and explicitly **defers the
verification ceremony** (OTP/challenge/click-through) to a later, separately authorized slice (§8,
`CP-D-05`). It ends at research. A build requires a separate operator authorization recorded in
`DEC-P4-ENTRY`; nothing here authorizes implementation of ContactPoint or of Notification.

## 2. Research question and method

### 2.1 Research question

What is the smallest Party-owned contact-point model that lets bOPEN resolve a business recipient to a
verified, purpose-authorized, tenant-scoped destination — reusably across products and across the
future Notification foundation — while preserving tenant isolation, endpoint-value privacy,
anti-enumeration, provenance, verification truth, and the extend-only integrity of the built Party
foundation, and **without** turning Party into a messaging system or Notification into a contact
master?

### 2.2 Method and source hierarchy

The research used, in order:

1. the built and disposed `BOPEN-PARTY-001` behavior (migration 010, `party_repositories.py`) and the
   verified hybrid-tenancy machinery (forced RLS, composite FKs, trial→paid `COPY_ORDER`, the
   `tenant_session` freeze, the migration-014 append-only-cascade lesson);
2. [`RESEARCH-MILE-4.2-NOTIFICATION`](MILE-4.2-notification-foundation-research.md) §7.3 and
   [`REVIEW-MILE-4.2-NOTIFICATION`](MILE-4.2-notification-foundation-review.md) §3.1 for the resolver
   contract shape and the `NOTIFY-D-01` requirement;
3. schema.org `ContactPoint` for the concept of a typed, purpose-scoped contact endpoint;
4. vCard (RFC 6350) for the `TEL`/`EMAIL`/`ADR` property model and the `TYPE`/`PREF` parameters;
5. E.164 for the canonical international phone-number form;
6. RFC 5322 for the Internet email address-form requirements;
7. the Location foundation's ISO 19160-1 / UPU S42 address-model reference
   ([`RESEARCH-MILE-4.2-LOCATION`](MILE-4.2-location-foundation-research.md) §7.2) for postal endpoints,
   rather than inventing a second address model;
8. architecture inference and recommendation, clearly separated from those facts.

External materials are informative requirements sources. A future approved bOPEN contract remains
authoritative. No external schema, vocabulary, or code is copied (§16).

## 3. Scope

### 3.1 In scope

- a tenant-scoped, Party-owned `party_contact_points` entity with forced RLS from its first migration;
- a small, governed, **versioned** endpoint-type vocabulary (`email`, `phone`, `postal`) and a small,
  governed, versioned purpose vocabulary;
- endpoint value with type-specific canonical form and validation (RFC 5322 email form, E.164 phone
  form, and a postal form that references the Location address model rather than duplicating it);
- verification **state** (`unverified` / `verified` / `failed`) and effective interval;
- primary-flag semantics, provenance, optimistic revision, and audit metadata;
- a composite foreign key `(tenant_id, party_id) -> parties(tenant_id, id)` for same-tenant integrity;
- append-only verification/lifecycle history that survives both direct mutation and parent cascade;
- the **`NotificationRecipientResolver` contract shape** (input reference + purpose + channel +
  tenant/context → verified `RecipientSnapshot` or explicit refusal) — the *contract*, not the resolver
  implementation and not the Notification engine;
- a verification **seam** (where a future ceremony plugs in) without designing the ceremony;
- tenant isolation, endpoint-value privacy/redaction, anti-enumeration, capabilities, and events;
- the cross-slice registration obligations the built experience already enforces (§12).

### 3.2 Out of scope

- **Notification owning contact data.** Notification receives a frozen snapshot for one send and has no
  write path into this registry; ContactPoint is not a Notification table.
- the verification **ceremony** — OTP generation/delivery, challenge tokens, click-through
  confirmation, retry/lockout policy (later slice, `CP-D-05`);
- consent/preference/suppression policy engines (those are Notification/policy decisions that *read*
  purpose and verification state, not ContactPoint's to own);
- treating `principals.email` (an authentication identifier) as a contact endpoint by any implicit path;
- a global or cross-tenant contact directory, cross-tenant deduplication, or contact-matching service;
- rich communication preferences, channel routing, do-not-disturb windows, or locale-of-contact rules;
- social handles, messaging-app identifiers, device push tokens, and webhook destinations in the first
  slice (later, governed, per-type extensions);
- owning the postal address model — a postal contact point *references* the Location address model
  rather than re-implementing ISO 19160/UPU components;
- sending anything. This extension produces no message and invokes no provider.

### 3.3 Assumptions

- Tenant is the ownership, policy, and isolation boundary; a contact point is never global.
- `BOPEN-PARTY-001` is built and disposed; `parties(tenant_id, id)` is uniquely constrained
  (`unq_party_tenant_id`) precisely so a child table can reference a Party **by tenant**.
- The Notification foundation remains gated and unbuilt; this extension is designed to *precede* it and
  to be usable by it, but does not depend on it existing.
- The Location foundation is gated and unbuilt; the postal endpoint therefore has an ordering decision
  (`CP-D-02`): reference a future `Location`/`AddressVersion`, or carry a minimal structured form now.
- Pooled PostgreSQL with forced RLS is the first storage profile; the contract must survive dedicated
  placement and trial→paid migration.
- Endpoint values are sensitive tenant business data and are classified as such from the first slice.

## 4. Current facts and interpretations

| Class | Statement |
| :--- | :--- |
| Repository fact | The built Party foundation (`010_party_foundation.sql`) has `parties` and `party_relationships` and **no contact-point entity** — no email/phone/postal endpoint attached to a Party. |
| Repository fact | `parties` declares `CONSTRAINT unq_party_tenant_id UNIQUE (tenant_id, id)` and `party_relationships` uses `FOREIGN KEY (tenant_id, from/to_party_id) REFERENCES parties(tenant_id, id)` — the composite-FK pattern this extension mirrors. |
| Repository fact | `principals.email` exists for authentication identity; kernel code explicitly refuses to trust an email claim for subject binding. A principal is an auth identity, not a consented contact. |
| Repository fact | `RESEARCH-MILE-4.2-NOTIFICATION` §7.3 forbids `principals.email` as a default destination and requires a governed resolver; `NOTIFY-D-01` marks the contact source as a pre-build dependency. |
| Repository fact | `REVIEW-MILE-4.2-NOTIFICATION` §3.1 confirms "there is genuinely nothing to resolve a business recipient against today" and names a Party ContactPoint extension as the cleaner long-term path. |
| Repository fact | `INV-MIGRATE-COVERAGE-01` asserts `COPY_ORDER` equals the RLS-classified `TENANT_SCOPED_TABLES`; it caught UOM's `uom_custom_units` on 2026-08-05. |
| Repository fact | Migration 014 changed `workflow_history.fk_wf_instance` from `ON DELETE CASCADE` to `ON DELETE RESTRICT` after a verifier reproduced a parent cascade erasing append-only history. |
| External fact | schema.org `ContactPoint` models a typed endpoint (`email`, `telephone`) with a `contactType`/purpose; vCard (RFC 6350) uses `EMAIL`/`TEL`/`ADR` with `TYPE` and `PREF` parameters. |
| External fact | E.164 defines the canonical international phone-number form; RFC 5322 defines the email address form. |
| Interpretation | A verified endpoint of one purpose does not authorize contact for a different purpose; verification and purpose are separate attributes, not one flag. |
| Recommendation | Add a thin, Party-owned, tenant-scoped `party_contact_points` table with verification state, purpose, and a resolver contract — mirroring the `party_relationships` integrity discipline. |

The `CAPABILITY-MATRIX` names Party as a dependency of Notification. It does not require ContactPoint to
own preferences, consent policy, or a verification ceremony in the first slice.

## 5. Domain distinctions

| Concept | Normative proposal | Must not be confused with |
| :--- | :--- | :--- |
| `ContactPoint` | A Party-owned, tenant-scoped, typed, purpose-classified, verifiable endpoint | A Principal, an authentication identifier, or a Notification record |
| `EndpointType` | Small governed versioned vocabulary (`email`, `phone`, `postal`) | An open free-text field or a channel |
| `EndpointValue` | The canonical, type-validated destination string/reference (sensitive) | A verified/consented destination on its own |
| `Purpose` | Small governed versioned vocabulary the endpoint is authorized for | Authorization to contact for *any* purpose |
| `VerificationState` | `unverified` / `verified` / `failed` — the trust level of the endpoint | Consent, preference, or delivery success |
| `RecipientRef` | A reference (`party_id` + tenant/context) passed to the resolver | A raw destination or a Principal identity |
| `RecipientSnapshot` | The minimal, frozen, verified endpoint returned for **one** send | A continuing consent or a new contact master |
| Primary flag | The default endpoint for a `(party, type)` scope | The only endpoint, or a cross-purpose default |
| Verification seam | The point where a future ceremony transitions state | The ceremony itself (deferred) |

The extension MUST preserve these trust levels, the ContactPoint analogue of Notification's
delivery-truth ladder:

```text
endpoint recorded
  != endpoint syntactically valid (RFC 5322 / E.164 / postal form)
  != endpoint verified (a challenge succeeded)
  != endpoint authorized for THIS purpose
  != endpoint belongs to a Party of the CALLER'S tenant
  != a usable notification destination
```

A destination is usable only when **every** rung holds. The resolver's job is to refuse at the first
rung that fails — uniformly, without revealing which rung or whether the endpoint exists (§10.3).

## 6. Options and recommendation

| Option | Boundary integrity | Reuse across products | Privacy/control | Portability | P0 complexity | Disposition |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| Notification owns its own contact table | 1 | 1 | 2 | 2 | 3 | Reject — Notification becomes a contact master; every other product re-solves recipients |
| Use `principals.email` as the destination | 1 | 2 | 1 | 3 | 5 | Reject — a principal is an auth identity, not a consented contact; cross-tenant/consent unsafe |
| Free-text contact columns on `parties` | 2 | 2 | 2 | 2 | 4 | Reject — no verification state, no purpose, no per-endpoint history, no primary/multi-endpoint |
| Party-owned `party_contact_points` + resolver contract | 5 | 5 | 5 | 5 | 4 | **Recommend** |

The recommendation keeps ContactPoint where it belongs (Party), gives Notification a governed contract
to resolve against, and reuses the exact composite-FK / forced-RLS / append-only discipline already
proven in `party_relationships` and `workflow_history`.

## 7. Proposed model

```text
Party (built: parties)
  └─ ContactPoint[] (party_contact_points)               tenant-scoped, forced RLS
       └─ ContactPointVerificationEvent[] (append-only)  survives cascade (CP-INV-07)

Notification (future) ──resolve(RecipientRef, purpose, channel, ctx)──> RecipientSnapshot | Refusal
                          (read-only contract; no write path into party_contact_points)
```

### 7.1 `party_contact_points` (proposed — not authorized)

Proposed columns (illustrative field list; the frozen DDL is a build-time artifact, `BOPEN-PARTY-002`,
not this document):

- `id` — immutable UUID primary key;
- `tenant_id` — immutable UUID; forced-RLS scope;
- `party_id` — the owning Party;
- **composite FK** `(tenant_id, party_id) -> parties(tenant_id, id)` — same-tenant integrity at the
  database, mirroring `party_relationships` (`CP-INV-02`); deletion action per `CP-D-03`;
- `endpoint_type` — governed vocabulary (`email`|`phone`|`postal`), `CHECK`-constrained and versioned;
- `endpoint_value` — canonical, type-validated (or, for postal, a `Location`/`AddressVersion`
  reference per `CP-D-02`); classified sensitive, encrypted/tokenized where practical (`CP-INV-06`);
- `purpose` — governed vocabulary the endpoint is authorized for (e.g. `security_operational`,
  `transactional`, `billing`, `general`), `CHECK`-constrained and versioned;
- `verification_state` — `unverified` (default) | `verified` | `failed` (`CP-INV-04`);
- `verified_at`, `verification_method` reference (nullable; set only by the verification seam);
- `effective_from`, `effective_to` — the interval during which the endpoint is usable;
- `is_primary` — the default endpoint for its `(party, type[, purpose])` scope; uniqueness enforced so
  at most one live primary exists per scope (`CP-INV-08`, scope decided by `CP-D-04`);
- `provenance` — how the endpoint was captured (self-asserted, imported, admin-entered, etc.);
- `revision` — optimistic concurrency token;
- audit metadata — `created_at`, `updated_at`, creating/updating principal, correlation id.

Uniqueness of the live `(tenant_id, party_id, endpoint_type, normalized_value)` SHOULD be enforced so
the same endpoint is not recorded twice for one Party, without revealing any other tenant's endpoint.

### 7.2 `party_contact_point_verification_events` (proposed append-only)

If verification carries history, an append-only event log records each state transition
(`unverified → verified`, `verified → failed`, re-verification) with method reference, actor,
correlation, and timestamp. This log:

- has **no** `UPDATE`/`DELETE` policy for the application role (append-only), and
- uses a foreign key to `party_contact_points` whose deletion action is **`ON DELETE RESTRICT`** (or a
  tombstone), so a cascade cannot erase it — the migration-014 lesson applied here in advance
  (`CP-INV-07`, `CP-D-03`).

### 7.3 What is deliberately *not* modeled here

- The verification ceremony (OTP, magic link, callback) — a seam only (§8, `CP-D-05`).
- Preference/suppression/consent-withdrawal policy — read by Notification, not owned here.
- Channel routing and locale-of-contact — Notification/policy concerns.

## 8. Verification state and the verification seam

Verification is modeled as **state plus a seam**, not a ceremony:

```text
unverified ──(seam: a challenge succeeds)──> verified
verified   ──(hard bounce / complaint / re-check fails)──> failed
failed     ──(seam: a fresh challenge succeeds)──> verified
```

- The **seam** is the single guarded transition point where a future, separately authorized
  verification slice plugs in (`CP-D-05`). This document designs *that a state exists and that only the
  seam may change it*, not *how the challenge works*.
- `unverified` and `failed` are **distinct** and neither is ever treated as `verified` (`CP-INV-04`).
  `failed` is not merely "not yet verified" — it records that a prior verification was invalidated.
- No API may set `verification_state = verified` directly; only the seam transitions it. A migration or
  admin import writes `unverified` (or a governed, audited exception path — a `CP-D` decision), never a
  silent `verified`.

Until the verification slice exists, the resolver simply refuses every endpoint (all are `unverified`),
which is the safe closed state: no usable destinations, no accidental sends.

## 9. The `NotificationRecipientResolver` contract (shape only)

This is the **contract** Notification calls, owned by Party. It is designed here as a shape; the
resolver implementation is a build-time artifact.

### 9.1 Request

```text
RecipientResolveRequest {
  recipient_ref: { party_id }        # a Party of the caller's tenant; never a Principal, never raw email
  purpose:       <governed purpose code>
  channel:       <governed channel>  # maps to endpoint_type: email->email, sms/voice->phone, postal->postal
  context:       { tenant_id, active-tenant context, correlation_id }
}
```

Notification passes a **reference and an intent**, not a destination. The caller cannot supply a raw
endpoint on this path (raw-destination flows, e.g. an invitation, are a *separate* authorized contract
that owns its own validation — `RESEARCH-MILE-4.2-NOTIFICATION` §7.3).

### 9.2 Successful response — a frozen `RecipientSnapshot`

```text
RecipientSnapshot {
  endpoint_type
  endpoint_value_or_token           # redacted/tokenized per privacy policy
  purpose                           # equals the requested purpose
  verification_state = verified     # the ONLY value that yields a snapshot
  party_ref                         # provenance, not a mutable pointer
  effective_at                      # frozen at resolve time
  resolver_version
}
```

The snapshot is **immutable evidence for one send** and is **not** a new contact master. Notification
stores the snapshot; it never gains a write path into `party_contact_points` (`CP-INV-12`).

### 9.3 Refusal — explicit, uniform, anti-enumerating

The resolver returns an **explicit refusal**, never a raw destination, when any keystone rung fails.
Internally the reasons are distinct (for audit/metrics): `party_not_found_in_tenant`,
`no_contact_point`, `unverified`, `failed_verification`, `wrong_purpose`, `wrong_channel`,
`not_effective`, `cross_tenant`. **Externally**, refusals are uniform and do not reveal which rung
failed or whether the endpoint/party exists in another tenant (`CP-INV-05`). RLS makes a cross-tenant
Party indistinguishable from a non-existent one — the same opaque-refusal posture as the built Party
`get()` and `resolve_context`'s identical-403.

### 9.4 Channel↔type mapping

The mapping (`channel -> endpoint_type`) is a small governed vocabulary decided before build
(`CP-D-06`). A channel with no matching verified endpoint of the authorized purpose is a refusal, not a
fallback to another channel or to `principals.email`.

## 10. Security, tenancy, and privacy

### 10.1 Tenant isolation

- `party_contact_points` and its verification-event log carry immutable `tenant_id`, forced RLS,
  default-deny policies, and fail-closed on missing/ambiguous/inactive context — the exact pattern of
  `parties`/`party_relationships`.
- The composite FK `(tenant_id, party_id) -> parties(tenant_id, id)` makes a cross-tenant attachment
  impossible **at the database**, not in application logic (`CP-INV-02`).
- Every method runs through `db.tenant_session`, so isolation is the RLS policy's property and the
  module's, and nothing else — the `party_repositories.py` contract. There is deliberately no unscoped
  read of a contact point.

### 10.2 Endpoint-value privacy

- Endpoint values (email addresses, phone numbers, postal addresses) are classified **sensitive** from
  the first slice; encrypted or tokenized at rest where practical (`CP-D-07`).
- Logs, events, metrics, traces, and default status responses carry identifiers, safe hashes, endpoint
  *type*, verification *state*, and reason codes — **never** the raw endpoint value (`CP-INV-06`).
- Events (§11.2) MUST NOT broadcast raw endpoints. `party.contact_point.verified.v1` carries the
  contact-point id and type, not the value.

### 10.3 Anti-enumeration

- A contact-point lookup MUST NOT reveal whether an endpoint exists in another tenant. Response body,
  status, timing, logs, and audit differences do not distinguish "no such Party", "Party in another
  tenant", and "Party has no matching endpoint" to an unauthorized caller (`CP-INV-05`).
- Search by raw endpoint value is **not** a general capability. "Does `x@example.com` exist as a
  contact anywhere?" has no answer surface — the same discipline Notification requires for status.

### 10.4 Purpose/consent separation

- A Party relationship, or the mere existence of an endpoint, does **not** authorize contact for every
  purpose. `purpose` is an explicit attribute; the resolver matches it exactly (`CP-INV-09`).
- Removing consent, adding suppression, and revoking verification are separate governed actions, not
  side effects of a resolve or a new endpoint write.

## 11. Proposed capabilities and events

### 11.1 Capabilities (proposed)

- `party.contact_point.create`, `party.contact_point.read`, `party.contact_point.list`;
- `party.contact_point.update` (value/purpose/effective interval, under optimistic revision);
- `party.contact_point.set_primary`;
- `party.contact_point.retire` (tombstone, not hard delete once verified/referenced — `CP-D-03`);
- `party.contact_point.verify` — routed to the (future, deferred) verification seam only;
- `party.contact_point.resolve` — the `NotificationRecipientResolver` entry, **platform/service scope**;
  ordinary read of a raw endpoint value is a separate, higher-privilege capability from resolving a
  destination for an authorized send.

Stable errors distinguish invalid input/context, unauthenticated, unauthorized, missing
entitlement/module, unknown endpoint type/purpose, invalid value form, stale revision, primary-flag
conflict, not-effective, unverified/failed, wrong-purpose, wrong-channel — **without** revealing
recipient/endpoint existence across tenants.

### 11.2 Events (proposed)

- `party.contact_point.added.v1`;
- `party.contact_point.updated.v1`;
- `party.contact_point.verification_state_changed.v1`;
- `party.contact_point.retired.v1`.

Events use the bOPEN envelope and transactional outbox. They carry the contact-point id, type,
verification state, and purpose — **never** the raw endpoint value, and never a full snapshot.
Consumers deduplicate by event id and tolerate replay.

## 12. Cross-slice obligations (named explicitly, from the reviewer's built experience)

These are not optional. They are the concrete lessons the built foundations already encode, and a
build that skips any of them fails the existing suite or reintroduces a fixed defect.

1. **Migration coverage — register in BOTH inventories.** Any new tenant-scoped table MUST be added to
   **both** `TENANT_SCOPED_TABLES` in `tests/isolation/test_rls_database_behavior.py` **and** the
   trial→paid tool's `COPY_ORDER` in `tools/migrate_tenant_to_dedicated.py`. The coverage test
   `INV-MIGRATE-COVERAGE-01` (`test_copy_order_covers_every_tenant_scoped_table`) asserts the two sets
   are equal and **fails the whole suite** otherwise — it caught UOM's `uom_custom_units` on
   2026-08-05. **Copy order (parents before children):** `parties` is already present; place
   `party_contact_points` **after `parties`**, and `party_contact_point_verification_events` **after
   `party_contact_points`**. A missed table is silent data loss on trial→paid, so this is fail-loud by
   design (`CP-INV-10`).

2. **Append-only history must resist BOTH direct mutation AND parent cascade.** If contact points carry
   append-only verification/lifecycle history, that history must survive direct `UPDATE`/`DELETE`
   (no such policy for the application role) **and** parent `CASCADE` deletion. This is the
   **migration-014 lesson**: a verifier reproduced a parent cascade that erased `workflow_history`
   past RLS, fixed at root cause by changing the FK from `ON DELETE CASCADE` to `ON DELETE RESTRICT`.
   Apply it here **in advance**: deleting a Party must **not** silently erase its contact-point
   verification history. Use `ON DELETE RESTRICT` (retire the Party instead of deleting it once it has
   contact points) or a tombstone (`CP-INV-07`, `CP-D-03`).

3. **No new freeze work — the trial→paid freeze already covers contact-point writes.** Because every
   write goes through `db.tenant_session`, a contact-point write during a migrating tenant's window
   hits the same `TenantMigratingError` chokepoint the kernel already enforces
   (`api._load_validated_context`). No new freeze machinery is required; the existing freeze covers
   this table for free. Note it so the build estimate does not double-count it.

4. **Composite FK for same-tenant integrity.** Use `FOREIGN KEY (tenant_id, party_id) REFERENCES
   parties(tenant_id, id)` exactly as `party_relationships` does. This is what makes a cross-tenant
   contact point impossible at the database rather than in application logic (`CP-INV-02`). It relies
   on the existing `unq_party_tenant_id UNIQUE (tenant_id, id)` on `parties`.

## 13. Proposed first implementation slice — not authorized

1. Freeze `BOPEN-PARTY-002`: endpoint-type and purpose vocabularies (versioned), value-form rules
   (RFC 5322 / E.164 / postal-via-Location), verification-state machine, primary-flag scope, the
   `RecipientSnapshot`/refusal schema, capabilities, errors, and events.
2. Add `party_contact_points` (and, if versioned, `party_contact_point_verification_events`) with
   `tenant_id`, the composite FK to `parties(tenant_id, id)`, forced RLS, default-deny policies,
   append-only history controls (`ON DELETE RESTRICT`/tombstone), and migration/rollback/compensation.
3. **Register both new tables in `TENANT_SCOPED_TABLES` and `COPY_ORDER` (parents before children,
   after `parties`)** so `INV-MIGRATE-COVERAGE-01` stays green (§12.1).
4. Implement create/read/list/update/retire and `set_primary` under `db.tenant_session`, optimistic
   revision, and vocabulary `CHECK`s — refusing unknown types/purposes and malformed values.
5. Implement the verification **seam** as a guarded transition that only sets `verified`; ship it
   **closed** (no ceremony), so every endpoint is `unverified` and the resolver refuses all until the
   verification slice is separately authorized (`CP-D-05`).
6. Implement the `NotificationRecipientResolver` contract: `(RecipientRef, purpose, channel, context)`
   → verified `RecipientSnapshot` **or** uniform, anti-enumerating refusal — never `principals.email`,
   never a cross-tenant or unverified endpoint (§9, the keystone).
7. Add the refusal-matrix tests (§14) against live PostgreSQL for RLS, composite-FK, append-only,
   cascade, primary-flag uniqueness, and trial→paid coverage/round-trip.
8. Submit exact candidate evidence for independent EBIV review and separate operator disposition.

Deferred: the verification ceremony (OTP/magic-link/callback), preference/suppression engines, social/
push/webhook endpoint types, cross-tenant contact directories, and any Notification build.

## 14. Required invariants and defensive verification (refusal matrix)

| ID | Invariant | Required refusal/acceptance evidence |
| :--- | :--- | :--- |
| `CP-INV-01` | Tenant isolation | Wrong/missing/inactive context cannot read, list, resolve, verify, or export a foreign Party's contact points |
| `CP-INV-02` | Same-tenant integrity | A contact point cannot attach to a Party of another tenant; the composite FK `(tenant_id, party_id)->parties(tenant_id, id)` refuses it at the database |
| `CP-INV-03` | **Keystone — destination integrity** | The resolver yields a usable destination **only** for a verified contact point of the authorized purpose belonging to a Party of the caller's tenant; unverified, failed, wrong-purpose, wrong-channel, not-effective, cross-tenant, and `principals.email` are all refused |
| `CP-INV-04` | Verification-state truth | `unverified` and `failed` are distinct and never treated as `verified`; only the verification seam transitions to `verified`; no API sets it directly |
| `CP-INV-05` | Anti-enumeration | Response/status/timing/log/audit differences do not reveal whether an endpoint or Party exists in another tenant; raw-endpoint search is not a general capability |
| `CP-INV-06` | Endpoint-value privacy | Logs, events, metrics, traces, and default status omit raw endpoint values; values encrypted/tokenized at rest where practical; events broadcast type/state, not value |
| `CP-INV-07` | Append-only verification evidence | Direct `UPDATE`/`DELETE` **and** parent `CASCADE` cannot erase verification history (`ON DELETE RESTRICT`/tombstone — the migration-014 lesson) |
| `CP-INV-08` | Idempotency/concurrency/primary | Retry creates no duplicate endpoint; stale revision is refused; at most one live primary per governed scope |
| `CP-INV-09` | Purpose/consent separation | A Party relationship or an existing endpoint does not authorize contact for every purpose; purpose is matched exactly |
| `CP-INV-10` | Migration coverage | `party_contact_points` (and its history table) appear in both `TENANT_SCOPED_TABLES` and `COPY_ORDER` (parents before children); `INV-MIGRATE-COVERAGE-01` stays green; trial→paid round-trip preserves ids/history |
| `CP-INV-11` | Vocabulary governance | Endpoint types and purposes are small governed versioned vocabularies; arbitrary strings are refused by `CHECK`/vocabulary |
| `CP-INV-12` | Party owns, Notification consumes | Notification receives only a frozen `RecipientSnapshot` and holds no write path into `party_contact_points`; ContactPoint never becomes a Notification-owned contact master |

Each proposition must trace to a named executed test at an exact commit/tree. Live PostgreSQL is
required for RLS, composite-FK, append-only/cascade, primary-flag uniqueness, and trial→paid
migration/round-trip claims. Verification-ceremony behavior is **not** claimed by this slice (the seam
ships closed). Any untested cross-tenant or verification-state behavior keeps the exit gate closed.

## 15. Risks and unresolved decisions

| ID | Decision/risk | Recommendation before authorization |
| :--- | :--- | :--- |
| `CP-D-01` | First endpoint types | Keep to `email` and `phone` in the first slice; add `postal` with `CP-D-02` resolved; defer social/push/webhook |
| `CP-D-02` | Postal endpoint model & Location ordering | Reference a future `Location`/`AddressVersion` rather than duplicating ISO 19160/UPU components; if Location is not yet built, either defer `postal` or carry a minimal structured form flagged for later migration to a Location reference |
| `CP-D-03` | Deletion vs tombstone (the migration-014 analogue) | Choose `ON DELETE RESTRICT` + retire-not-delete for a Party with contact points, or a tombstone; verification history must survive a Party deletion attempt |
| `CP-D-04` | Primary-flag scope | Decide whether primary is per `(party, type)` or per `(party, type, purpose)`; enforce one-live-primary uniqueness accordingly |
| `CP-D-05` | Verification ceremony | Defer to a separately authorized slice; ship the seam closed; decide OTP/magic-link/callback, retry/lockout, and re-verification triggers there — do not design it now |
| `CP-D-06` | Channel↔type mapping & purpose vocabulary | Freeze the small governed mapping and purpose codes with Notification's purpose model so `wrong_purpose`/`wrong_channel` are well defined |
| `CP-D-07` | Endpoint-value encryption/tokenization | Decide at-rest protection (application-level encryption vs tokenization vs pgcrypto), key custody, and the redaction boundary for logs/events/exports |
| `CP-D-08` | Import/admin-entered provenance | Decide whether an imported endpoint may ever start `verified` (governed, audited exception) or must always start `unverified` |
| `CP-D-09` | Resolve vs read separation | Confirm `resolve` (service/platform scope, returns a send destination) is a distinct, higher-trust capability from reading a raw endpoint value |

`CP-D-02`, `CP-D-03`, and `CP-D-04`/`CP-D-05` are the load-bearing decisions; the rest may be resolved
or explicitly deferred, but none may be silently defaulted at build time.

## 16. Required successor artifacts and exit gates

Before implementation:

1. advisory review of this research closes without a blocking boundary defect;
2. the operator records a **bounded ContactPoint authorization** in `DEC-P4-ENTRY` or its governed
   successor — this extension remains gated until then;
3. `CP-D-01` through `CP-D-09` are resolved or explicitly deferred without silent defaults;
4. `BOPEN-PARTY-002`, the `NotificationRecipientResolver` contract, API/error/event/vocabulary schemas,
   privacy/threat model, migration/rollback/compensation plan, test matrix, and accepted work package
   are frozen;
5. the two new tables are registered in `TENANT_SCOPED_TABLES` and `COPY_ORDER` (parents before
   children) so `INV-MIGRATE-COVERAGE-01` stays green;
6. maker, eligible independent verifier, candidate anchors, evidence paths, and stop conditions are
   named.

Implementation exit requires executed acceptance/refusal tests, live RLS / composite-FK / append-only /
cascade / trial→paid evidence, repository/clean-room checks, traceability, an independent EBIV ballot,
and operator disposition. The Notification build, provider selection, and any production activation
remain separate and gated.

## 17. Source register

Retrieved 2026-08-05. External standards are informative requirements sources unless a future approved
bOPEN artifact explicitly adopts a requirement.

| Source | Evidence class | Use in this research |
| :--- | :--- | :--- |
| `010_party_foundation.sql` (`BOPEN-PARTY-001`) | Built repository artifact | Composite-FK / forced-RLS pattern this extension mirrors; `parties(tenant_id, id)` uniqueness |
| `party_repositories.py` | Built repository artifact | `db.tenant_session` isolation contract; no-unscoped-read discipline |
| [`RESEARCH-MILE-4.2-NOTIFICATION`](MILE-4.2-notification-foundation-research.md) §7.3 | Advisory repository research | Resolver contract shape; prohibition on `principals.email`; `NOTIFY-D-01` |
| [`REVIEW-MILE-4.2-NOTIFICATION`](MILE-4.2-notification-foundation-review.md) §3.1 | Advisory repository review | Confirmation of the dependency and path (a) — a Party ContactPoint extension |
| [`RESEARCH-MILE-4.2-LOCATION`](MILE-4.2-location-foundation-research.md) §7.2 | Advisory repository research | Postal endpoint references the ISO 19160/UPU address model rather than duplicating it |
| `tests/isolation/test_rls_database_behavior.py` (`TENANT_SCOPED_TABLES`) | Built repository artifact | Table-registration obligation (`CP-INV-10`) |
| `tools/migrate_tenant_to_dedicated.py` (`COPY_ORDER`) | Built repository artifact | Copy-order obligation, parents before children (`CP-INV-10`) |
| Migration 014 (`workflow_history` `ON DELETE RESTRICT`) | Built repository artifact | The append-only-cascade lesson (`CP-INV-07`) |
| [schema.org ContactPoint](https://schema.org/ContactPoint) | Vocabulary reference | Typed, purpose-scoped contact-endpoint concept |
| [RFC 6350 — vCard](https://datatracker.ietf.org/doc/html/rfc6350) | IETF standard | `EMAIL`/`TEL`/`ADR` property model, `TYPE`/`PREF` parameters |
| [E.164 — International public telecommunication numbering plan](https://www.itu.int/rec/T-REC-E.164) | ITU-T standard | Canonical international phone-number form |
| [RFC 5322 — Internet Message Format](https://datatracker.ietf.org/doc/html/rfc5322) | IETF standard | Email address-form requirements |

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
