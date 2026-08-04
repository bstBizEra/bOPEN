# EVD-CONTACTPOINT-MAKER — Party ContactPoint extension

**Document ID:** `EVD-CONTACTPOINT-MAKER`
**Version:** `1.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision
**Issued:** 2026-08-05
**Implements:** [`DEC-P4-ENTRY`](../../decisions/DEC-P4-ENTRY.md) §10 (authorized); [`RESEARCH-MILE-4.2-PARTY-CONTACTPOINT`](../../01-product/MILE-4.2-party-contactpoint-extension-research.md)
**Candidate:** `c48727c`
**Blob — `019_party_contact_points.sql`:** `345304a4f61a2aa9a2cadc5f9e27fe8a6d83206a`
**Blob — `contact_point_repositories.py`:** `642601225e42a3d4abe09df585f4bba98e8cea10`
**Blob — `test_contact_point_isolation.py`:** `a9b2bb4c0aeaf36f2ee7c486e35a87af5e8912ef`
**Blob — `test_contact_point_http.py`:** `6f51bebf36c37cdfecce4a56f111f1cf9ff258de`
**Blob — `invariant-traceability.csv`:** `9c86de18cbc1fcd08773c2af4e933d59b0342b85`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifier:** Codex
**Suites:** canonical **616/616** against PostgreSQL

---

## 1. What this is — and the one property it defends

The Party ContactPoint extension (`BOPEN-PARTY-002`). The built Party foundation has `parties` and
`party_relationships` and **no contact-point entity**, so there is nothing to resolve a business
recipient against — which is exactly why Notification is blocked. This adds the missing entity: a
tenant-scoped, **Party-owned** registry of typed (`email`/`phone`), purpose-classified, verifiable
communication endpoints.

The defended property — the **keystone**, `CP-INV-03` — is that the `NotificationRecipientResolver`
yields a usable destination **only** for a contact point that is **verified**, of the **authorized
purpose**, of the requested **channel's type**, currently **effective**, and belonging to a **Party of
the caller's tenant**. It **never** falls back to `principals.email` (a principal is an auth identity,
not a consented contact — the same reason the kernel refuses to trust an email claim for subject
binding). Unverified, failed, wrong-purpose, wrong-channel, not-effective and cross-tenant are all
refused **uniformly**, as one `RecipientUnresolved`, without revealing which rung failed (`CP-INV-05`).

**Clean-room (`AGENTS.md` §6):** independently implemented from the settled contact-registry model
(typed endpoint + verification state + purpose + effective interval), adopted from no upstream schema.

## 2. Defensive verification

Every proposition asserts the extension **refuses** an operation that would be unsafe — a cross-tenant
insert, a contact point on another tenant's Party, an unknown type/purpose, a duplicate endpoint, a
second live primary, an UPDATE/DELETE of append-only verification history, a delete that would erase
that history, and every non-qualifying resolve (unverified / wrong-purpose / wrong-channel /
cross-tenant / no-contact-point-so-never-`principals.email`) — and **admits** a valid one exactly (a
verified, purpose-matched, effective endpoint resolves to a snapshot).

## 3. Propositions (traced in `invariant-traceability.csv`)

**Group A — database isolation & integrity** (`tests/isolation/test_contact_point_isolation.py`, executed Python):

| ID | The extension must… | Test |
| :--- | :--- | :--- |
| `CP-INV-ISOLATION-01` | keep a contact point invisible to another tenant | `test_a_contact_point_created_in_one_tenant_is_invisible_to_another` |
| `CP-INV-XTENANT-INSERT-01` | refuse a cross-tenant insert | `test_a_cross_tenant_contact_point_insert_is_refused` |
| `CP-INV-XTENANT-PARTY-01` | refuse attaching to another tenant's Party | `test_a_contact_point_cannot_attach_to_another_tenants_party` |
| `CP-INV-VOCAB-TYPE-01` | refuse an unknown endpoint type | `test_an_unknown_endpoint_type_is_refused` |
| `CP-INV-VOCAB-PURPOSE-01` | refuse an unknown purpose | `test_an_unknown_purpose_is_refused` |
| `CP-INV-DUP-01` | refuse a duplicate endpoint for one Party | `test_a_duplicate_endpoint_for_one_party_is_refused` |
| `CP-INV-PRIMARY-01` | allow at most one live primary per (party, type) | `test_at_most_one_live_primary_per_party_and_type` |
| `CP-INV-APPEND-ONLY-01` | refuse UPDATE/DELETE of a verification event | `test_recorded_verification_events_cannot_be_updated_or_deleted` |
| `CP-INV-APPEND-CASCADE-01` | keep verification history when its contact point is delete-attempted | `test_recorded_verification_survives_an_attempt_to_delete_its_contact_point` |
| `CP-INV-PARTY-RESTRICT-01` | refuse deleting a Party that has a contact point | `test_a_party_with_a_contact_point_cannot_be_deleted` |

**Group B — HTTP** (`tests/integration/test_contact_point_http.py`, executed HTTP, bearer-gated):

| ID | The kernel must… | Test |
| :--- | :--- | :--- |
| `CP-INV-HTTP-CRUD-01` | support create/read/list/update/retire | `test_create_read_list_update_retire_a_contact_point` |
| `CP-INV-HTTP-STALE-01` | refuse a stale-revision update (409) | `test_a_stale_revision_update_is_refused` |
| `CP-INV-HTTP-MALFORMED-01` | refuse a malformed endpoint (422) | `test_a_malformed_endpoint_is_refused` |
| `CP-INV-HTTP-RESOLVE-01` | resolve a verified purpose-matched endpoint to a snapshot **(keystone)** | `test_verify_then_resolve_returns_the_snapshot` |
| `CP-INV-HTTP-UNVERIFIED-01` | refuse resolving an unverified endpoint | `test_resolve_refuses_an_unverified_endpoint` |
| `CP-INV-HTTP-PURPOSE-01` | refuse resolving a wrong-purpose endpoint | `test_resolve_refuses_a_wrong_purpose_endpoint` |
| `CP-INV-HTTP-CHANNEL-01` | refuse resolving a wrong-channel endpoint | `test_resolve_refuses_a_wrong_channel_endpoint` |
| `CP-INV-HTTP-NOEMAIL-01` | never fall back to `principals.email` **(keystone)** | `test_resolve_never_uses_principals_email` |
| `CP-INV-HTTP-XTENANT-01` | refuse resolving across tenants | `test_resolve_refuses_across_tenants` |
| `CP-INV-HTTP-ISOLATION-01` | keep a contact point private to its tenant | `test_a_contact_point_is_private_to_its_tenant` |
| `CP-INV-HTTP-BEARER-01` | require a bearer to create (401) | `test_creating_a_contact_point_requires_a_bearer` |
| `CP-INV-HTTP-RESOLVE-BEARER-01` | require a bearer to resolve (401) | `test_resolving_requires_a_bearer` |

**Attack angle for the verifier (defensive framing).** Confirm each of these *refusals* holds and the
one *admission* is exact:
- Create a Party in tenant A, a contact point in tenant B pointing at A's `party_id` → confirm the
  composite FK **refuses** it (`CP-INV-XTENANT-PARTY-01`).
- Create an `email` contact point, do **not** verify it, `resolve-recipient` → confirm it **refuses**
  (`CP-INV-HTTP-UNVERIFIED-01`); then `verify`, `resolve` → confirm the snapshot **is** returned and its
  value is exactly the stored endpoint (`CP-INV-HTTP-RESOLVE-01`).
- Verify a `billing`-purpose endpoint, resolve with purpose `security_operational` → confirm it
  **refuses** (`CP-INV-HTTP-PURPOSE-01`); resolve channel `sms` when only an `email` is verified →
  confirm it **refuses** (`CP-INV-HTTP-CHANNEL-01`).
- Create a principal with an email and a Party with **no** contact point, resolve → confirm it
  **refuses** and does not surface the principal's email (`CP-INV-HTTP-NOEMAIL-01`).
- Record a verification event, then attempt to delete its contact point → confirm the delete is
  **refused** and the event survives (`CP-INV-APPEND-CASCADE-01`); attempt to UPDATE/DELETE the event
  row directly → confirm it is **refused** (`CP-INV-APPEND-ONLY-01`).
- Set a primary `email`, set a second `email` primary for the same Party → confirm the second is
  **refused** while a `phone` primary is **admitted** (`CP-INV-PRIMARY-01`).

## 4. Execution

```text
python tools/run_tests.py     616/616 OK   (live PostgreSQL)
```

- Migration 019 adds `party_contact_points` (composite FK `(tenant_id, party_id) → parties(tenant_id,
  id)` **ON DELETE RESTRICT**; forced RLS `FOR ALL`; `unq_cp_party_endpoint`; the partial unique index
  `unq_cp_primary` for one live primary per (party, type)) and the append-only
  `party_contact_point_verification_events` (composite FK **ON DELETE RESTRICT**; SELECT+INSERT policies
  only). The migration-014 lesson is applied in advance: a Party or contact-point deletion cannot
  cascade past row security to erase verification evidence — it is refused.
- `contact_point_repositories.py` — every method through `db.tenant_session`; `verify_by_assertion`
  transitions to `verified` and inserts the append-only event **in one transaction**; `resolve` is the
  keystone (verified + purpose + channel→type + effective + tenant via RLS; never `principals.email`;
  uniform refusal). The endpoint value is redacted from every audit record.
- Bearer-gated endpoints: `POST/GET .../contact-points`, `GET/PUT/DELETE .../contact-points/{id}`,
  `.../verify`, `.../set-primary`, and `POST /v1/parties/{party_id}/resolve-recipient`.
- **Cross-slice, enforced by a control:** both new tables were added to `TENANT_SCOPED_TABLES` and the
  trial→paid `COPY_ORDER` (parents before children). `INV-MIGRATE-COVERAGE-01` and the full trial→paid
  round-trip (`test_trial_to_paid`) both pass with the two tables copied — otherwise a trial→paid
  migration would silently leave a tenant's contact points and their verification history behind.

## 5. What this does NOT establish (disclosed)

1. **`email` and `phone` only.** `postal` is **deferred** — it depends on the Location foundation, which
   is gated and unbuilt (`CP-D-01`/`CP-D-02`); social/push/webhook likewise deferred.
2. **The verification ceremony is deferred (`CP-D-05`).** The one path to `verified` in this slice is a
   **governed, audited administrative assertion** (`verification_method='administrative_assertion'`,
   recorded in the append-only history). This makes a real verified destination exist — so Notification
   is functionally unblocked — but "verified" here means *administratively asserted*, distinct from a
   challenge (OTP/magic-link), which is a follow-up slice. `verify_by_assertion` is idempotent (a
   re-assertion re-records the transition) and no create/update path can mint a verified endpoint.
3. **Changing an endpoint value resets verification to `unverified`** — a changed address has not been
   verified; a purpose-only update preserves verification.
4. **Retire is a tombstone, not a hard delete** — a retired endpoint keeps its row and its append-only
   verification history and is no longer effective (so the resolver will not return it).
5. **The resolver returns a per-send snapshot, not a continuing consent.** Notification consumes it;
   Party owns the endpoint (`CP-INV-12`). Notification itself is still gated — this unblocks its
   recipient dependency, it does not build Notification.
6. **One verifier, not two** (two-agent profile). This maker submission carries no verdict weight.

## 6. Authority

A maker's submission. `EBIV` §8: a passing suite carries no verdict weight.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
