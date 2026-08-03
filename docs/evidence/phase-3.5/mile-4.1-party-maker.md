# EVD-MILE-4.1-MAKER — Party & Relationship Foundation (BOPEN-PARTY-001)

**Document ID:** `EVD-MILE-4.1-MAKER`
**Version:** `1.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision
**Issued:** 2026-08-03
**Implements:** [`DEC-P4-ENTRY`](../../decisions/DEC-P4-ENTRY.md) MILE-4.1 (`BOPEN-PARTY-001`), Phase 4 first slice
**Candidate:** the commit carrying this submission (DB layer at `eec7957`, HTTP layer at `4317880`)
**Blob — `party_repositories.py`:** `a9c306d3502951a13fb0739997d0b51c19ea91cc`
**Blob — `api.py`:** `9d6acd339095876c665f050234164b5d41e2cb49`
**Blob — `010_party_foundation.sql`:** `fee41d903bbcc247acf0607c5616332cfc9f75b0`
**Blob — `invariant-traceability.csv`:** `a9eace5e778c02de458a13b2af08ea78025b1218`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifier:** Codex
**Suites:** canonical **498/498** against PostgreSQL

---

## 1. What this is — the Phase 3.5 isolation boundary, now on real business data

A **party** is a business entity (person or organization) owned by a tenant — a customer, a vendor —
distinct from a **principal** (an authentication identity). MILE-4.1 is the first Phase 4 slice and
the dependency root every foundation and satellite product will build on. Its point, beyond CRUD, is
to prove the Phase 3.5 tenant-isolation boundary holds for **real business data**, not only kernel
entities: a party is tenant-scoped by row-level security from its first migration, and a relationship
cannot be formed across tenants at all.

## 2. Defensive verification

Every isolation and integrity proposition below asserts the platform **refuses** a cross-tenant or
invalid operation and **admits** a valid one. There is no offensive objective.

## 3. Propositions (traced in `invariant-traceability.csv`)

**Group A — database layer** (`tests/isolation/test_party_isolation.py`, executed SQL):

| ID | The database must… | Test |
| :--- | :--- | :--- |
| `P4-PARTY-01` | keep a party invisible to another tenant (RLS) | `test_a_party_created_in_one_tenant_is_invisible_to_another` |
| `P4-PARTY-02` | refuse a cross-tenant party INSERT | `test_a_cross_tenant_party_insert_is_refused` |
| `P4-PARTY-03` | refuse an unknown `party_type` | `test_an_unknown_party_type_is_refused` |
| `P4-PARTY-04` | refuse a self-relationship | `test_a_party_cannot_relate_to_itself` |
| `P4-PARTY-05` | refuse a relationship linking parties across tenants | `test_a_relationship_cannot_cross_tenants` |
| `P4-PARTY-06` | admit a valid same-tenant relationship | `test_a_valid_same_tenant_relationship_is_accepted` |

**Group B — HTTP layer** (`tests/integration/test_party_http.py`, executed HTTP, bearer-gated):

| ID | The kernel must… | Test |
| :--- | :--- | :--- |
| `P4-PARTY-HTTP-01` | create and read a party over HTTP under its tenant | `test_create_and_read_a_party` |
| `P4-PARTY-HTTP-02` | create a same-tenant relationship over HTTP | `test_a_relationship_between_two_parties_in_a_tenant` |
| `P4-PARTY-HTTP-03` | keep a party invisible to another tenant over HTTP | `test_a_party_is_invisible_to_another_tenant_over_http` |
| `P4-PARTY-HTTP-04` | refuse a cross-tenant relationship over HTTP (422) | `test_a_relationship_cannot_cross_tenants_over_http` |
| `P4-PARTY-HTTP-05` | refuse a self-relationship over HTTP (422) | `test_a_self_relationship_is_refused` |
| `P4-PARTY-HTTP-06` | require a bearer to create a party (401 without) | `test_creating_a_party_requires_a_bearer` |
| `P4-PARTY-HTTP-07` | refuse an unknown `party_type` over HTTP (422) | `test_an_unknown_party_type_is_refused` |

**Attack angle for the verifier:** with tenant B's bearer, read or link to tenant A's party
(`P4-PARTY-HTTP-03/04`) — both must be refused; the party comes from the signed context, so an
`X-Tenant-ID` header cannot redirect it. A party endpoint is bearer-only (`P4-PARTY-HTTP-06`).

## 4. Execution

```text
python tools/run_tests.py     498/498 OK   (live PostgreSQL)
```

Migration 010 gives `parties` and `party_relationships` `FORCE ROW LEVEL SECURITY` with a
`WITH CHECK` isolation policy, a `chk_party_type`, a `chk_no_self_relationship`, and a composite
foreign key `(tenant_id, party_id) → parties(tenant_id, id)` that makes a cross-tenant relationship
impossible at the database. `PartyRepository` runs every statement through `db.tenant_session` (which
resolves placement, WP-P35-06) and translates the database's refusals to 422/404 rather than a 500.
A runnable end-to-end demonstration is `scripts/demo_business_scenario.py`.

## 5. What this does NOT establish (disclosed)

1. **Party is distinct from principal**, and MILE-4.1 does not link them — a person-party may never
   become a principal; that mapping is out of this slice.
2. **No vendor/supplier/customer role vocabulary** on a party yet — a later slice.
3. **No update/delete** — create and read only; lifecycle is out of this slice.
4. `verify_connection_serves` for dedicated placement is inherited from WP-P35-06, exercised
   structurally, not against a live dedicated database.

## 6. Authority

A maker's submission. `EBIV` §8: a passing suite carries no verdict weight.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
