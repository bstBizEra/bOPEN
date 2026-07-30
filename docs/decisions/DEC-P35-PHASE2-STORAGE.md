# DEC-P35-PHASE2-STORAGE — Decisions required before Phase 2 can be persisted

**Decision ID:** `DEC-P35-PHASE2-STORAGE`
**Version:** `1.0.0`
**Status:** **Proposed — decision request raised under `AGENTS.md` §16**
**Issued:** 2026-07-30
**Owner:** Architecture Authority, Engineering Authority, Security Authority
**Governing artifacts:** `BOPEN-IDP-001` §6, §11, §12, §14, §16, §17; `BOPEN-P2-001` §10, §11; `AGENTS.md` §8, §13, §14, §16
**Raised by:** Claude (agent, SARCHI/Cortex roles) — advisory only

---

## 1. Why this exists rather than a migration

Phase 2 holds every piece of its state in Python dictionaries: `membership.py`, `idp_bridge.py`,
`context_service.py` and `delegation.py` are 2,634 lines with 34 in-memory dicts and **zero
database calls**. A restart loses every invitation, every membership transition, every SSO
identity link and every delegated grant, and in a multi-worker deployment each worker holds a
different membership list. Phase 2 is not merely unverified; it is architecturally undeployable.

The obvious next step is a migration creating the eleven missing tables. **It should not be
written yet.**

A column-by-column design pass over all four modules surfaced sixteen questions the repository
cannot answer, and several of them determine what the columns *are* — not how they are named.
`AGENTS.md` §16 lists "tenant ownership is ambiguous" and "two approved artifacts conflict" as
stop conditions; both are met, repeatedly. Writing the migration now would encode unresolved
conflicts into a schema that is append-only after merge, which is the most expensive place to
put a guess.

This record separates what must be decided before any DDL from what can be decided after.

---

## 2. Blocking — a migration cannot be written without these

### 2.1 The identifier format (affects every table)

`UuidIdentifierFactory.new_id` at `membership.py:159` returns `f"{prefix}_{uuid.uuid4()}"`. Every
Phase 2 identifier is prefixed text: `inv_…`, `rcp_…`, `dgr_…`, `sso_…`, `eid_…`, `ctx_…`,
`mem_…`.

Migration 001 declares `memberships.id UUID`. **`mem_<uuid>` cannot be stored in it**, and this
is a live incompatibility that predates Phase 2 storage — it is also why
`membership-transition.json`'s `format: uuid` on `membership_id` can never be satisfied, an open
finding already recorded in the conformance baseline.

- **Option A — store bare UUIDs, move the prefix to the API boundary.** Real UUID columns, real
  foreign keys into the 001 family, and `membership-transition.json` becomes satisfiable. Costs a
  change to `new_id` and to every fixture and audit `subject_id` that asserts on a prefixed
  string.
- **Option B — store `VARCHAR(45)` with a shape CHECK.** No code change, but foreign keys into
  `tenants`, `principals` and `memberships` become impossible without a cast. That is exactly the
  divergence migration 004 was written to repair, reproduced across eleven new tables at the
  moment 004 finished paying for it.

**Recommended: A.** The prefix carries no information the column name does not. Genuinely opaque
provider-supplied values — `ExternalIdentity.subject`, `SsoTransaction.state`, SCIM
`resource_id` — stay `TEXT`; those are not bOPEN identifiers.

### 2.2 `authentication_sessions` has no tenant, by design

`context_service.py:140` states it: *"Authentication session; not tenant-bound (BOPEN-IDP-001
12.1)."* §12.1's own table agrees — tenant-bound: **No**. The session precedes context
establishment, so there is no correct `tenant_id` at insert.

Every other table in the design carries `tenant_id UUID NOT NULL` and the standard policy. This
one cannot, and the three fallbacks all have costs:

| Option | Consequence |
| :--- | :--- |
| RLS enabled, no policy | Denies everything. `get_session` stops working |
| RLS not enabled | Isolation leaves the database, contradicting `AGENTS.md` §8 |
| Principal-scoped policy | Semantically right, but needs an `app.current_principal_id` GUC that no migration establishes. Every connection-setup path must set it, and one that forgets returns silently empty — the failure mode migration 004 describes as "missing data, not a fault" |

There is a second reason it cannot simply be left unprotected: the row holds
`current_context_id`, and joining it to the context table reveals which tenants a principal is
active in. That is cross-tenant information in a table with no tenant policy.

**This is a change to the isolation model**, which `AGENTS.md` §15 makes a designated-review item.
The moment this table exists, "every table carrying tenant data has a tenant policy" stops being
a true description of the schema, and the next person auditing it will find a table without one
and have to work out whether that is a bug.

### 2.3 `delegated_grants` under row-level security breaks delegation entirely

`ContextSwitchService.switch` resolves a delegated grant at `context_service.py:390` — **before**
any context exists for the target tenant, which is the entire point of a context switch.

A policy of `target_tenant_id = current_setting('app.current_tenant_id')::uuid` hides exactly the
row that authorizes the switch, because at that moment the session variable holds the previous
tenant or nothing. Every delegated context switch would fail with the generic
`NO_ACTIVE_RELATIONSHIP` denial, indistinguishable from a real refusal. A grant nobody can use.

The workable option is a `SECURITY DEFINER` lookup that sets the tenant for the duration of an
exact-match query on `(source_principal_id, target_tenant_id)` — safe because it returns nothing
when no grant exists and so cannot enumerate. **But it introduces a privileged code path that
does not exist today**, which is a security-review surface, not a schema detail.

### 2.4 `IssuedContext` and `active_contexts` model one concept incompatibly

Migration 003 already created `active_contexts` and enforces, at `003:48-50`:

```sql
CREATE UNIQUE INDEX unq_live_context_per_tenant_principal
    ON active_contexts (tenant_id, principal_id) WHERE revoked_at IS NULL;
```

`ContextSwitchService.supersede` marks only `session.current_context_id` — **per session**. So a
principal holding two sessions can hold two non-superseded contexts in one tenant, which that
index rejects outright.

Either the code violates an invariant migration 003 already enforces, or 003's invariant is
wrong. Both cannot stand.

**Recommended: extend `active_contexts`** rather than create a second table. It already has the
policy, the index and the correlation column; it needs `session_id`, `delegated_grant_id`,
`roles`, `scopes`, `jti`, `superseded_at`, and `membership_id` relaxed to nullable. One context
table, one invariant.

### 2.5 `group_role_mappings` — the resolver and its own docstring disagree

`resolve_mapping` at `idp_bridge.py:280` matches on `(directory_id, group_external_id)` and
ignores `mapping_policy_version`. The docstring four lines above says the version is part of the
key.

- Key on `(directory_id, group_external_id)` → the resolver is right, but the version becomes a
  passive attribute and two policy versions can never coexist.
- Key on all three → the docstring is right, but the resolver becomes `LIMIT 1` without an
  `ORDER BY`. **Nondeterministic role assignment.**

Neither is a schema-only fix, and this table translates external group membership into a bOPEN
role. It should not be created until the key is decided.

### 2.6 Overlapping delegated grants are nondeterministic

`find_usable` returns the first match and `create` never checks for an overlap, so two active
grants for one principal and tenant with different `approved_roles` are permitted and
`context_service.py:403` takes whichever the iteration reaches. In SQL that becomes `LIMIT 1`
with no total order.

Either a partial unique index forbidding overlap — which may be operationally wrong, since a
partner grant and a support grant could legitimately coexist — or a stated tie-break rule.

---

## 3. Security findings that constrain the DDL

These are not open questions. They are constraints the migration must respect, recorded so they
are not rediscovered at review time.

### 3.1 `IssuedContext.access_token` must never become a column

`context_service.py:164` holds the complete signed JWT. A row would be a live bearer credential
for the token's five-minute lifetime, and a `SELECT` across the table would be simultaneous
takeover of every active context in every tenant in the result.

The sharpest part is the asymmetry inside this repository. `kernel_core/audit.py:42-46` lists
`"access_token"` in `PROHIBITED_METADATA_KEYS` and **raises** on it, and `audit.py:52` carries a
JWT-shaped-value regex to catch it under an innocent key. The audit path refuses this value with
an exception. Persisting the session store as written would place the same value in a queryable
table.

It is also unnecessary: nothing reads `access_token` back after issuance. Store `jti` — already
minted per token, already in the claim set per `BOPEN-IDP-001` §12.2, and the standard revocation
handle.

### 3.2 `SsoTransaction.state` and `nonce` must be stored as digests

Both are `secrets.token_urlsafe(24)`. The store is keyed by `state`, so possession selects an
in-flight transaction; `nonce` is the OIDC replay control named in §16.

`Invitation` already does this correctly — `membership.py:845` persists only
`self.hasher.hash(raw_token)` and the docstring states the raw token is never held. Both values
are looked up by exact equality, so hashing costs nothing functionally.

One honest caveat: `hmac.compare_digest` is constant-time; a SQL index probe is not. Against a
192-bit random value this is not a practical attack, but it is a change from the property the
code states and should be recorded rather than assumed away.

### 3.3 Do not create a `pkce_challenge` column

`idp_bridge.py:394` generates fresh randomness labelled `pkce_challenge`. A PKCE challenge is
`BASE64URL(SHA256(verifier))` and no verifier exists anywhere in the module; `complete_sso` never
reads it. `BOPEN-IDP-001` §19 requires PKCE for conformance and it is not implemented.

Persisting the column would give the schema the appearance of PKCE support without the mechanism,
which is worse than the gap staying visible.

### 3.4 The idempotency store must not serialise its result

`membership.py:864` stores an entire `IssuedInvitation` — including `raw_token`, the credential
`:845` was careful never to persist. Serialising that result would defeat `INV-P2-002` through
the back door, in the one module that gets token handling right everywhere else.

The table must hold `(idempotency_key, payload_fingerprint, result_kind, result_ref)` and never a
serialised object. **Consequence needing a decision:** a replayed `issue()` currently returns the
prior raw token. If the token is not stored, replay cannot return it — so either replay returns
the invitation without a token, or duplicate issuance is refused. That is a change to `issue()`'s
contract.

### 3.5 `email_normalized` must carry no unique constraint and no index

`BOPEN-IDP-001` §6.1: email alone must never establish identity equivalence. The code honours it
— `find_identity` compares only the canonical `(connection_id, issuer, subject)` tuple, and
`email_snapshot` is written and never compared. An index on it is the first step toward someone
writing a lookup by it.

---

## 4. Findings that are gaps rather than decisions

Recorded so the migration is not written as though the code were complete.

| Finding | Evidence |
| :--- | :--- |
| `IdentityProviderConnection` has no create, suspend or retire path; `verify_connection` does `draft → active` in one step | Three of five states are unreachable; every construction site is a test |
| `ExternalIdentity.status` never becomes `disabled` or `unlinked` | The only writer takes the dataclass default |
| `ExternalIdentity.version` and `SCIMDirectory.version` are never incremented | Optimistic concurrency exists on paper only |
| `ContextInvalidationObligation.discharged` is never set true | The obligation-to-revocation loop is driven manually in tests, not by the record |
| `membership_transition_receipts` has no repository | Nothing queries receipts, so the access patterns that justify indexes do not exist |
| `TransitionReceipt.event_id` has no resolvable referent | The dispatcher mints its own UUID; `audit_events.id` mints another. Invariant 11's correlation is not established |
| `AuthenticationSession` is the only mutable, unversioned type, mutated in place behind a read-then-write guard | Two concurrent switches on one session both pass and both write |
| Replay caches are globally unqualified and unbounded | One IdP's assertion id can permanently block another's; §16 requires a *bounded* cache |
| `scim-event.json` calls `external_id` tenant-scoped; the code scopes it per directory | Two approved artifacts disagree — itself a §16 stop condition |

---

## 5. Recommendation

**Do not author the Phase 2 migration until §2 is decided.** Six blocking items, of which §2.1
and §2.4 change the shape of nearly every table and §2.2 changes the isolation model.

A sequence that does not require deciding everything at once:

1. **§2.1 first.** It is repository-wide, it unblocks the rest, and it is the only one whose cost
   is mostly mechanical.
2. **§2.4 next.** It decides whether there are ten tables or nine, and extending `active_contexts`
   is cheaper than reconciling two context tables afterwards.
3. **§2.2 and §2.3 together.** Both concern the isolation model and both need security review;
   deciding them apart risks two different answers to one question.
4. **§2.5 and §2.6** can follow, since they affect one table each.

Section 3 needs no decision — those constraints hold whatever is decided in §2, and stating them
now means the migration is reviewed against them rather than after them.

## 6. What is not being claimed

No file was created or modified to produce this record. No migration was written. The design pass
that produced it read the code and cited `file:line` for every claim; the three most consequential
— the bearer token in `IssuedContext`, the audit dispatcher's prohibition of that exact key, and
the incompatibility between `active_contexts`' unique index and per-session supersession — were
re-verified independently before this was recorded.

This is a decision request. No agent has the authority to resolve any item in §2.

## 7. Provenance

Raised by Claude (agent, SARCHI) on 2026-07-30. Advisory only —
`execution_authority: false`, `approval_authority: false`, `risk_class: high`.

---

# Addendum A — §2.2 and §2.3 resolved by measurement, 2026-07-30

Two of the six blocking items were open because the standard remedy was assumed rather than
tested. Both were tested against PostgreSQL 17.10 on the verification instance, and one
assumption turned out to be wrong in a way that matters.

## A.1 `SECURITY DEFINER` is a total row-level-security bypass, not a narrow one

§2.3 proposed a `SECURITY DEFINER` function so the delegated-grant lookup could see a row the
caller's tenant context hides. That is the conventional answer. It is also far more dangerous
here than the framing suggested.

**Probe.** Two tenants, one row each in `tenant_feature_toggles`. The application role queries
directly, then through a `SECURITY DEFINER` function owned by the superuser — same session, same
tenant context:

| Path | Rows returned |
| :--- | ---: |
| Direct query, tenant A context | **1** |
| Same query inside a superuser-owned `SECURITY DEFINER` function | **2** |

The function returned both tenants' rows. `FORCE ROW LEVEL SECURITY` did not prevent it, because
inside the function `current_user` is the owner, and PostgreSQL states that *"superusers and
roles with the BYPASSRLS attribute always bypass the row security system"*.

The consequence the original proposal understated: **the bypass cannot be scoped to one table.**
`BYPASSRLS` is a role attribute and superuser status is global, so any function built this way
holds the capability to read every tenant's rows in every table, however narrow its body is. Add
the `search_path` hijack PostgreSQL documents for exactly this function class, and a flaw in one
narrow function becomes a whole-database disclosure.

## A.2 The lookup does not need a bypass at all

The premise was that a `target_tenant_id` policy hides the row authorizing a context switch,
because the switch happens before a context exists for that tenant.

True — and the remedy is smaller than it looked. **The requested tenant is known**: it is
`command.tenant_id`, the tenant being switched to. Opening a session for *that* tenant makes the
policy match, with no bypass and no privileged code path.

**Probe.** A session opened for tenant B, used for three queries:

| Query inside a session opened for B | Rows |
| :--- | ---: |
| B's own row | **1** |
| A's row | **0** |
| Unqualified count over the table | **1** |

The session reaches exactly one tenant's rows — precisely what the grant lookup needs and nothing
more.

**Why this does not weaken isolation.** The caller does not set the session variable; the kernel
does, from the tenant the request is already about. The lookup is a parameterised match on
`(source_principal_id, target_tenant_id)` returning a row only when a grant genuinely exists, so
it discloses exactly the fact the authorization decision was about to disclose anyway. There is
no enumeration: an attacker must already know both identifiers and learns only the answer to the
question asked.

**The discipline that makes it safe** is that the session is used for one query and closed. A
session opened for an unvalidated tenant is safe only while nothing else runs inside it, so the
repository method must not grow a second statement. That is a reviewable property of one
function, not a capability living in the database.

**Recommendation for §2.3: no `SECURITY DEFINER`.** Resolve the grant inside a
`tenant_session(command.tenant_id)` restricted to a single parameterised lookup.

## A.3 §2.2 — the session table, answered the same way

`authentication_sessions` has no tenant by design, so it cannot carry the policy every other
table carries. PostgreSQL's default-deny confirms the trap: *"If no policy exists for the table, a
default-deny policy is used"* — enabling row security without a policy denies everything,
including the kernel's own reads.

The correct policy is principal-scoped, matching `BOPEN-IDP-001` §12.1's "restricted to the
principal and client". It needs an `app.current_principal_id` setting no migration establishes
today.

The objection in §2.2 was that a connection path forgetting to set it returns silently empty —
the failure mode migration 004 calls "missing data, not a fault".

**That objection has an answer, and the precedent is already here.**
`platform_kernel.db.tenant_session` refuses an empty tenant identifier rather than opening a
session that would match nothing, precisely so absence fails loudly instead of reading as "this
tenant has no data". A `principal_session` helper built the same way carries the same protection.
The risk was never the second variable; it was a helper that tolerates an empty one, and this
codebase already declines to build that.

**Recommendation for §2.2:** principal-scoped policy plus a `principal_session` helper that
refuses an empty principal, mirroring `tenant_session`. It remains a change to the isolation
model and a designated review item under `AGENTS.md` §15 — what changes is that the objection
making it look unsafe now has a precedent-backed answer.

## A.4 What this addendum does not do

It does not resolve §2.1, §2.4, §2.5 or §2.6, and it does not approve §2.2 or §2.3. It replaces
two assumed remedies with measured ones and narrows what is being asked for.

The `SECURITY DEFINER` finding stands on its own regardless of any decision: **that pattern
should not enter this repository for tenant-scoped reads**, because the capability it creates
cannot be limited to the table it was written for.

Probes were run against the verification instance and their fixtures removed. Advisory only —
`execution_authority: false`, `approval_authority: false`.

---

# Addendum B — §2.1 priced by measurement, 2026-07-30

§2.1 recommended Option A and stated Option B's cost as an inference: *"foreign keys into
`tenants`, `principals` and `memberships` become impossible without a cast."* That was reasoning.
The repository can be measured instead, because it already contains tables that took Option B.

## B.1 What the live schema shows

Every identifier column in the `public` schema, grouped by type, and the foreign-key count of the
table it belongs to:

| table | uuid id-columns | varchar id-columns | foreign keys |
|---|---|---|---|
| `quota_reservations` | 0 | 4 | **0** |
| `tenant_entitlement_overrides` | 0 | 3 | **0** |
| `tenant_entitlement_plans` | 0 | 2 | **0** |
| `usage_meter_balances` | 0 | 3 | **0** |
| `usage_outbox` | 0 | 6 | **0** |
| `memberships` | 3 | 0 | 2 |
| `tenant_resources` | 2 | 0 | 1 |
| `active_contexts` | 4 | 1 | 3 |
| `audit_events` | 4 | 2 | 3 |
| `lifecycle_events` | 2 | 4 | 1 |

The five tables with no uuid identifier column have no referential integrity at all. Every
foreign key in the schema sits on a uuid column. `lifecycle_events` shows the mechanism plainly
within a single table: its uuid columns carry the foreign key, its varchar ones do not.

The cause is specific and worth stating precisely, because the general claim would be wrong.
`VARCHAR` columns can perfectly well carry foreign keys. These do not, because the keys they
would have to reference — `tenants.id` and `principals.id` — are `UUID`, and PostgreSQL will not
create a foreign key across those types. Option B does not forbid referential integrity in
general; it forbids it *against the tables Phase 2 must reference*, which is every one of them.

Those five tables are the migration 002 family. They are not a hypothetical: they are what
Option B looks like eighteen months in.

## B.2 The cast, measured

```
identifier as Phase 2 mints it: inv_decadffb-b654-4990-8b0c-850046e0761c   (40 chars)
  prefixed -> uuid column   InvalidTextRepresentation
  bare     -> uuid column   OK
```

The prefixed form is not a formatting preference that a column type could be widened to accept.
It is not a UUID, and no `UUID` column will take it.

## B.3 What this changes and what it does not

It changes nothing about the recommendation, which was already A. It changes the standing of the
argument: the cost of B is no longer predicted, it is observed on five existing tables, and the
count of tables that would join them is eight rather than the eleven §2.1 estimated — the Phase 2
concept inventory has since been measured directly (`invitations`, `idp_connections`,
`external_identities`, `sso_transactions`, `scim_directories`, `group_role_mappings`,
`delegated_grants`, `authentication_sessions`).

It does not make the decision. A is a recommendation with a measured price attached to its
alternative; choosing to pay that price is a product decision, and the operator may have reasons
this document cannot see — a satellite product already storing prefixed identifiers, for one.

## B.4 Two further facts the same measurement surfaced

**`delegated_grants` names its tenant column `target_tenant_id`.** Every row-level-security policy
in the schema compares a column named `tenant_id`. A policy over a differently-named column has
to be written differently, and differing policy text across otherwise-identical policies is where
mistakes live — F5 in `EVD-SEC-001` was a table whose policy was simply never written. Renaming to
`tenant_id` at the storage boundary, or adding it alongside, is a decision that belongs with §2.1
because it is the same kind of decision: whether the storage layer speaks one identifier
vocabulary or several.

**`group_role_mappings` carries no tenant column at all.** It hangs off `directory_id`. Under the
classification introduced by migration 007 it is therefore genuinely unclassified: either it
denormalises `tenant_id` and becomes tenant-scoped like the rest, or its policy is written as an
`EXISTS` subquery against `scim_directories`. Both work. They differ in whether a future reader
can tell what the policy protects by looking at the table. This is §2.5's neighbour and should be
decided with it.

## B.5 Provenance

Source — measured against the verification instance on 2026-07-30 via `information_schema.columns`
and `pg_constraint`, after migrations 001–008. No fixtures created; the queries are read-only.
Advisory only — `execution_authority: false`, `approval_authority: false`.
