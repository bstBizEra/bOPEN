# DEC-P35-IDP-SPLIT — Split `WP-P35-05` into an authentication boundary and a federation integration

**Decision ID:** `DEC-P35-IDP-SPLIT`
**Version:** `1.0.0`
**Status:** **Approved — ratified by the operator 2026-07-31**
**Issued:** 2026-07-31
**Owner:** Architecture Authority & Engineering Authority
**Governing artifacts:** `AGENTS.md` §16, §20.2, §22; `BOPEN-GOV-EBIV-001`; `BOPEN-IDP-001` §12; [`DEC-P35-RUNTIME`](DEC-P35-RUNTIME.md); [`DEC-P35-AUTH-BOUNDARY`](DEC-P35-AUTH-BOUNDARY.md); [`DEC-P35-DOCKET`](DEC-P35-DOCKET.md) §7
**Amends:** [`BOPEN-P35-001`](../work-packages/BOPEN-P35-001-EXECUTION-PLAN.md) scope

---

## 1. Why this record exists

`DEC-P35-DOCKET` §7 requires a new governed decision to change an accepted work package rather
than an edit to the docket. `BOPEN-P35-001` was accepted on 2026-07-31, so re-scoping
`WP-P35-05` needs this record.

## 2. Question

`WP-P35-05` is blocked by `D-P35-011`..`D-P35-014`, all Proposed. `D-P35-014` is a **licensing
re-verification** of BoxyHQ Jackson, because `DEC-0003`'s evidence has aged.

Should a runtime milestone remain blocked on a third-party licensing question?

## 3. Finding of fact — two different things are bundled in one work package

| Concern | Needs a vendor? | Closes what |
| :--- | :--- | :--- |
| The kernel cannot authenticate anyone | **No** | `POST /v1/contexts` issues an owner bearer token to any caller who knows three identifiers |
| Enterprise federation to each tenant's IdP | **Yes** — BoxyHQ | SAML/OIDC/SCIM brokering, per-tenant connections |

The first is the security hazard. `api.py` refuses context issuance with 503 — *"there is no
credential the caller could have supplied that would change the answer"* — unless
`BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION` is set. **That guard is a flag, not a
mechanism.** Any deployment that sets it hands an owner token to anyone who can reach it.

`DEC-P35-AUTH-BOUNDARY` §2 already separates these: the kernel owns principals, sessions and
normalized protocol results, and *does not become an IdP*. Kernel authentication is kernel work;
the broker is integration work.

### 3.1 Correction to the advice that prompted this record

The recommendation that led here stated that splitting removes the blockers from the
authentication half, leaving only the design decisions. **That understated the position.**

There is no persistence for identity connections or external identity bindings. Migrations
`001`..`009` define `tenants`, `principals`, `memberships`, `active_contexts`, `audit_events`,
`lifecycle_events` and the entitlement tables — and no `sso_connections`, `external_identities`
or `authentication_sessions`.

A full per-tenant connection model therefore needs new persistence, which needs
`D-P35-004`..`D-P35-010`, which are unratified. Splitting removes the *vendor* from the critical
path. It does not remove the *storage* decisions. That is recorded here rather than discovered
later.

## 4. Decision

`WP-P35-05` is split into two work packages. **Ratified.**

### `WP-P35-05a` — Kernel authentication boundary *(remains in Phase 3.5)*

The kernel stops issuing a context to an unauthenticated caller. Scoped to what needs no new
table:

- A single trusted external authenticator, configured by environment, asserting principal
  identity in a signed, short-lived, audience-bound token.
- Context issuance requires that assertion whenever an authenticator is configured.
- **Configuring an authenticator must not be overridable by
  `BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION`.** A development escape that can disable a
  configured authenticator is not a boundary; it is a switch.
- Binding is by issuer and subject. **Never by email equality** (`D-P35-012`).
- The assertion is never persisted (`D-P35-010`).

**Explicitly not in `05a`:** per-tenant connections, multiple issuers, SCIM provisioning, and any
new table. A deployment using `05a` has one authenticator for the whole kernel. That is a real
limitation and is recorded as such — it is a boundary where there was none, not federation.

### `WP-P35-05b` — Enterprise IdP federation *(moved out of Phase 3.5)*

BoxyHQ Jackson integration, per-tenant connections, SAML/OIDC/SCIM. Remains blocked by
`D-P35-011`..`D-P35-014` **and** by `D-P35-004`..`D-P35-010` for its connection storage.
Sequenced after those decisions; not a Phase 3.5 deliverable.

## 5. Why this does not weaken the gate

`DEC-P35-RUNTIME` §6 already scopes the downstream dependency:

> Phase 4 entry is deferred until `WP-P35-01`..`WP-P35-03` report admissible evidence.

`WP-P35-05` was never a Phase 4 entry condition. Moving `05b` out changes no gate. `05a` is
added to Phase 3.5's security surface rather than removed from it: the phase now closes a hole
it previously only documented.

## 6. Decision and approver

| Field | Value |
| :--- | :--- |
| **Decision** | **ACCEPT.** Split `WP-P35-05` into `05a` (in Phase 3.5) and `05b` (moved out, blocked) |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — acting as Architecture Authority and Engineering Authority |
| **Decision timestamp** | 2026-07-31 |
| **Security review** | Not separately assigned. This decision **adds** an authentication requirement and relaxes nothing; the security-bearing constraints it inherits (`D-P35-010`, `D-P35-012`) are applied as recommended, not varied |
| **Recorded by** | Claude (agent, Motor role), transcribing an operator decision. `execution_authority: false`, `approval_authority: false` |

### 6.1 What remains unratified

`D-P35-004`..`D-P35-014` are **not** ratified by this record. `05a` is implementable only because
it is scoped to require no new persistence and no per-tenant connection model. Any widening of
`05a` beyond §4 re-encounters those decisions and must stop.

## 7. Maker and verifier

`05a` maker: **Claude** (`claude@bst.local`), continuing the alternation in `DEC-P35-DOCKET`
§5.2. Codex does not touch it and therefore remains eligible to verify it, as it is for
`WP-P35-04`. `05b` maker: named when unblocked.

## 8. Rollback

`05a` is additive: a configured authenticator changes behaviour only where one is configured. A
deployment with none behaves exactly as before. Rollback is removing the configuration, then the
code.
