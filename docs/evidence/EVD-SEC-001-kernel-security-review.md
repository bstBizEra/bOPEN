# Evidence Record: Platform Kernel Adversarial Security Review

**Evidence ID:** `EVD-SEC-001`
**Work Package:** `BOPEN-P35-001`
**Status:** Seven findings closed, one recorded and not closed
**Issued:** 2026-07-30
**Classification:** Governed Evidence Record
**Admissibility:** BOPEN-GOV-EBIV-001 R1 (executed), R2 (measured), R4 (adversarial)

---

## 1. What this record is

An adversarial review of the Phase 1 and Phase 2 kernel runtime, and the remediation of what it
found. Nine findings are recorded: eight raised by the review, one found while remediating.

Every finding below was reproduced by execution against the live verification database or the
HTTP surface before it was changed, and every fix was re-run against the same reproduction
afterwards. Nothing here is argued from reading the code alone. Where reproduction contradicted
the original report, the measurement is what is recorded — this happened three times, and in two
of those the defect was wider than reported.

**This record is not a clearance.** It states what was tested, what was found, what was fixed and
what remains open. Whether the remaining items are acceptable is a Completion Authority decision
under BOPEN-GOV-EBIV-001 §6.3, and the maker of every change below cannot make it.

---

## 2. Findings

| ID | Severity | Summary | Disposition |
|---|---|---|---|
| F1 | HIGH | Nested sessions leaked tenant scope; complete cross-tenant read and write | Closed — `09ec9d7` |
| F2 | HIGH | Unauthenticated caller obtained an owner bearer token | Closed — `aeb4f2d` |
| F3 | MEDIUM | Caller chose which audit bucket its own denial was filed in | Closed — `3216b46`, migration 008 |
| F4 | MEDIUM | Credential prohibition saw only the top level of `metadata` | Closed — `c736977` |
| F5 | MEDIUM | `tenants`, `principals`, `schema_migrations` had no row-level security | Closed — `49e4c4b`, migration 007 |
| F6 | LOW | `POST /v1/principals` is an account-existence oracle | **Recorded, not closed** — `b1511c5` |
| F7 | LOW | Authorization decision evaluated, audit write failed, HTTP 500 | Closed — `b1511c5` |
| F8 | LOW | Token identifier claims were not type-checked | Closed — `b1511c5` |
| F9 | MEDIUM | Tenant provisioned naming a third party as owner, without consent | Closed — `323a141` |

F9 was not in the original report. It surfaced while remediating F5: once a principal's
visibility derives from membership, the question "what can create a membership?" becomes
load-bearing, and provisioning creates one from a caller-supplied identifier.

---

## 3. The findings that mattered most

### F1 — the isolation bypass

`set_config(..., is_local => true)` is discarded when its transaction ends. That is true of the
outermost transaction. `conn.transaction()` entered on a connection already inside one emits a
SAVEPOINT, and PostgreSQL reverts `SET LOCAL` on savepoint ROLLBACK but **not** on RELEASE.

So a nested session that exited *cleanly* left the inner tenant in force in the enclosing block:

```
outer opened for B, reads          -> 0 rows          (correct)
nested session for A, exits cleanly
outer, same block, reads           -> ['A-SECRET']    (tenant A's row)
tenant in force in the outer block -> A
```

Cross-tenant read and write, both directions, with row-level security fully enabled and every
policy intact — because the policy was being told the wrong tenant. `db.py`'s own module
docstring calls this the failure that voids everything else.

The inner-raises path was always correct, because savepoint ROLLBACK does revert the setting.
Only the clean exit leaked, which is why no test caught it.

Nesting is now **refused** rather than repaired. Restoring the outer value on exit would work and
would leave nesting looking safe, which would make the next variant of this bug quiet again. Both
directions are refused, not only the dangerous one: a system session nested in a tenant session
fails closed (reads as "no data"), a tenant session nested in a system session fails open. A rule
with an exception is a rule somebody has to remember.

### F2 — an owner token for anyone

A client with no prior state and no credential header: `POST /v1/contexts` → 201, a signed token
with `roles: ["owner"]`, and ALLOW on `/v1/authorize`.

Not a removed check. Phase 1 has no authentication mechanism at all, by work-package scope. The
sharp part of the review's criticism was right: every other trust boundary in the module is
documented, so an undocumented gap on the endpoint that issues credentials reads as an oversight
rather than a deferred phase. And the danger is that it *looks finished* — signed tokens, JWKS,
RLS, an audit trail. The missing half is invisible from outside.

The kernel now refuses by default; the operator must affirm the deployment is not production, the
same shape as `BOPEN_DB_NON_PRODUCTION` guarding the destructive rollback. 503 rather than 401 is
deliberate: no credential the caller could supply would change the answer, and 401 would imply one
exists.

### F5 — the registry in the open

```
a session scoped to one tenant read     7631 rows from tenants
                                        6657 rows from principals, including emails
                                           1 row  from tenant_resources   (correct)
```

The third line is the whole finding. Isolation worked exactly as designed on every table it had
been applied to, while the list of who the customers are and every user's email address sat beside
it unprotected. Any tenant could enumerate the deployment's entire customer base.

`tenants` and `principals` carry no `tenant_id`, so `tenant_id = current_tenant` is inexpressible
on them — and inexpressible was treated as inapplicable. Migration 007 names a second class of
table with its own rule rather than adding an exception to the first.

Reads and writes are separate policies. `FOR ALL` with a single `USING` reuses it as the
`WITH CHECK`, so the read permission would have carried UPDATE with it, on the table whose
`status` column holds `suspended` and `terminated` — a suspended tenant could have reactivated
itself. Closing a disclosure by opening an escalation is not a fix.

Six migrations passed without this being noticed because every test asserted against a table that
already had a policy; absence was invisible. The suite now enumerates the live schema instead of a
list, and a table in none of the three classes fails. **On its first run that test reported four
more tables no assertion had ever named** — `lifecycle_events`, `rate_limit_counters`,
`rate_limit_policies`, `tenant_feature_toggles`. All four were already enabled, forced and
policied, so unlike the registry they were never a disclosure; they were simply outside the suite,
which is the condition `tenants` was in and is only harmless until it isn't.

### F3 — choosing where your own denial is filed

The sink decided whether an event was tenant-scoped by matching `tenant_id` against the strings
`unknown` and `scoped`. On the context-switch denial path that value is the request body's tenant
field, passed straight through. So the caller chose the route:

```
two identical denials, differing only in the tenant the attacker named
  requested = <a real tenant>  -> visible in that tenant's audit trail
  requested = "unknown"        -> written with a NULL tenant, readable by nobody
```

Repeated failed switches are the signal a defender looks for.

`lifecycle_events` has modelled this correctly since migration 005 — `chk_lifecycle_scope` plus a
constraint requiring identifier and scope to agree. The database had the concept; the envelope did
not carry it, so the sink rebuilt it from a caller-controlled string. That is the defect, not the
sentinel values, which are legitimate.

Two halves, both required. The producer now states the scope and reaches it by parsing, so
`unknown` is one unresolvable string among infinitely many. Migration 008 gives the unscoped bucket
a reader — migration 006 recorded that reading those rows "needs an administrative path that does
not exist yet", and that gap is what made the destination worth choosing. Readable only from a
session that is itself unscoped; without that condition it would expose every deployment-wide
authentication failure to every tenant, which would be worse than the finding.

### F9 — provisioning without consent

```
POST /v1/tenants  owner_principal_id = <someone else's principal>  -> 201
```

A tenant exists with a third party bound to it as owner, who never agreed. Phase 2's invitation
engine models exactly that consent — invited, then accepted — and this path goes around it.

Same root cause as F2: the endpoint acts on an identity the caller asserts and Phase 1 cannot
verify. The guard was therefore generalised rather than duplicated, and renamed for the assertion
rather than for either endpoint, so the next endpoint that trusts an unproven claim has an obvious
place to attach.

---

## 4. Open, and why

### F6 — account-existence oracle, not closed

`POST /v1/principals` answers 409 for a registered address and 201 for one that is not,
distinguishable by anyone with no credential. Confirmed by execution.

Not patched because the fix is not available at this layer: a registration call that returns the
new principal's identifier synchronously must tell the caller whether it created one. Removing the
oracle means registration becomes asynchronous behind address verification — `WP-P35-05`, the same
work package that gives the endpoint any authentication at all. Returning 201 for a duplicate would
hide the oracle from a reader of the code without closing it, since timing and the absent
identifier still answer the question.

What did change is real: the 409 was produced by searching the driver's error message for `unique`
or `duplicate`. That passed only because of the wording psycopg happens to use — a driver upgrade
or a non-English server locale would have turned every duplicate address into an unhandled 500, and
the endpoint would have looked correct until production.

### Carried forward, recorded in the migrations that create them

- **The unscoped path still sees the whole registry**, and is reachable from request handling.
  What constrains it is the repository surface, not the database. Migration 007 §"What this does
  not close".
- **Nothing yet reads the operator audit bucket.** Migration 008 makes the rows reachable; who may
  run that query is an authorization question above the RLS layer.
- **Constraint-check disclosure.** PostgreSQL evaluates referential-integrity and uniqueness checks
  with row security bypassed, by design, so a failed insert can reveal that a row exists which the
  caller cannot see. Asserted directly in the isolation suite so it stays a known property rather
  than becoming a surprise — migration 007 depends on the same behaviour for correctness.
- **A tenant can bind a principal it cannot read into its own tenant**, given that principal's
  UUID. The database cannot fix this without inverting the model, because visibility derives from
  the membership. The control is consent, which is F9's guard and ultimately `WP-P35-05`.

---

## 5. Method

Reproduce, fix, re-run the reproduction, then mutate the fix and confirm the suite goes red.

**Mutation results — 34 mutations, 34 killed.** Two survived their first run and both were real
coverage gaps rather than false alarms:

- the sink accepting an event with no declared scope;
- the denial path passing the request value straight through — *the actual attack path*, which no
  test drove through the service.

The second is the instructive one. Asserting only that unresolvable denials reach the operator
bucket would have passed against a producer that filed *everything* as unscoped, so the resolvable
case has to be asserted alongside it. A test that cannot fail for the right reason is not evidence.

Three corrections were made against the original report or against my own first measurement, and
they are recorded because a review that only confirms itself is not a review:

1. **F4 was wider than reported.** Reported as one level of nesting; measured as ten of twelve
   probe shapes, including non-string keys silently coerced by `json.dumps`, and `NaN`, which
   PostgreSQL rejects outright so the audit row is lost rather than corrupted.
2. **A leak scan was run through a blind session.** The first end-to-end check for credential-
   bearing rows used a system session, which RLS makes blind to tenant rows; it reported zero and
   the foreign-key violation on cleanup proved a row existed. Re-measured as a `BYPASSRLS` role,
   which then found one credential-bearing row left by the pre-fix reproduction. It was removed.
3. **A foreign-key probe tested nothing.** An insert intended to test referential integrity against
   an invisible parent was refused by the child table's own policy before reaching the check. The
   probe was rebuilt against `memberships.principal_id`, where the condition actually holds.

---

## 6. Verification state

| Check | Result |
|---|---|
| `tools/run_tests.py` | 409 / 409 |
| `tools/validate_repository.py` | PASS |
| `tools/check_clean_room.py` | PASS |
| `tools/check_evidence_anchors.py` | PASS |
| `tools/check_contract_conformance.py` | PASS |
| gitleaks | no leaks |
| Migration round trips | 007 and 008 rolled back and re-applied, state verified both ways |

All probe rows created during reproduction were removed, including one credential-bearing
`lifecycle_events` row written before the F4 fix.

### 6.1 Anchors

Full object identifiers, emitted by `git rev-parse` rather than transcribed. R3 rejects
abbreviations: a seven-character prefix that matches says nothing about the other thirty-three.

| Finding | Remediation | Commit OID |
|---|---|---|
| F1 | refuse session nesting across scopes | `09ec9d71695fb3dae7a35790d58705d3018fb387` |
| F2 | refuse context issuance unless affirmed non-production | `aeb4f2d832acbfb5f16416e9c4a8356c804f5faf` |
| F4 | bound the audit metadata value space | `c73697786581f4b7ca6668e1f91fccfc53af61a5` |
| F5 | row-level security on the registry tables (migration 007) | `49e4c4b207073c103fd6d376cef5c9c5099a2a86` |
| F3 | producer-stated tenant scope, unscoped reader (migration 008) | `3216b46a06829d215f1e9566181d6ac61cbcfb39` |
| F6, F7, F8 | boundary limits and token claim types | `b1511c59d7e1ee67615154fc185cf2ba562f031e` |
| F9 | one guard over every unproven-identity endpoint | `323a1417bb4ee7b4a6b6e22f8c01fe6801d4c01d` |

Reviewed commit oid: `323a1417bb4ee7b4a6b6e22f8c01fe6801d4c01d`
Candidate tree oid: `91629fb293b15c4871c9308bb7d148491073c278`

### 6.2 What the anchor check does and does not cover

`tools/check_evidence_anchors.py` resolves the OIDs above against real git objects, rejects any
that is abbreviated, and checks the object type wherever a recognised label states one.

It reported PASS against an earlier draft of this record that carried seven-character SHAs,
because unlabelled abbreviations were not recognised as anchors at all and there was nothing to
resolve. Rewriting them at full length was not enough either: a second mutation, altering one
digit of a commit OID inside the remediation table, still passed — only labelled lines were being
examined, so an identifier in a table cell or in prose was invisible.

That is R3's own failure mode reached through the tool built to prevent it, so the tool was fixed
rather than the document reshaped to fit it. Full-length identifiers are now checked wherever they
appear, for existence; type is still checked only where a label says what was intended, because
guessing would produce failures that are wrong rather than strict.

The extension immediately flagged a real quotation — the fabricated OID that
`docs/evidence/phase-3/completion-decision.md` retains on purpose in its correction notice. A
notice that cannot name the wrong value records nothing, so an explicit `anchors:off` region
marker was added, and the count of exempted identifiers is printed on every run whether or not
anything failed. An exemption visible only in a document's source is one nobody reviewing the
output knows about.

It still does **not** verify migration checksums or file paths. Those are re-derived by command
rather than asserted here, so that nothing in this record depends on a claim no tool checks:

```
python tools/db_bootstrap.py --status      # ledger: version, filename, SHA-256 per migration
python tools/run_tests.py                  # 409/409
```

A record whose facts are only as good as the author's transcription is what R3 exists to prevent,
and stating which half of this document is machine-checked is part of not reproducing that.

---

## 7. Authority

Under BOPEN-GOV-EBIV-001 §7.1 a verifier is bound to the git author of the work verified. Every
commit referenced here has the same author, so **quorum is unreachable and no verification ballot
is recorded**. This is the zero-verifier condition of §6.3, escalated rather than worked around:
the maker cannot vote on the maker's own work, and recording a self-verification would be worth
less than recording none.

What is offered instead is reproducibility. Every claim above is a command that can be re-run, and
each fix has mutations that must turn the suite red. That is evidence a verifier can check without
trusting the maker — it is not a substitute for one.

**Requires Completion Authority decision:** whether the four carried-forward items and F6 are
acceptable for the current phase, or block it.

---

## 8. Cross-references

- Governance: [BOPEN-GOV-EBIV-001](../00-governance/BOPEN-GOV-EBIV-001.md) — verification protocol
- Isolation: [BOPEN-TENANT-001](../04-platform/BOPEN-TENANT-001.md) — F1, F5
- Authorization: [BOPEN-AUTHZ-001](../04-platform/BOPEN-AUTHZ-001.md) — F7
- Identity: BOPEN-IDP-001 §12.4 (F8), §15 (F3, F4)
- Secrets: [BOPEN-SEC-VAULT-001](../07-security/secrets/BOPEN-SEC-VAULT-001.md) — credential registry
- Migrations: `infrastructure/database/007_registry_table_isolation.sql`,
  `infrastructure/database/008_lifecycle_unscoped_read.sql`

---

# Addendum A — F10, found while pricing the identifier decision, 2026-07-30

Appended rather than folded into section 2, under the extend-only rule. The record above stands
as issued.

## A.1 What was measured

Pricing `DEC-P35-PHASE2-STORAGE` §2.1 required knowing what the absence of a foreign key actually
costs, so the live schema was audited for rows a foreign key would have refused:

| table | rows | orphaned | share |
|---|---|---|---|
| `usage_meter_balances` | 2812 | 2812 | **100%** |
| `quota_reservations` | 2510 | 2510 | **100%** |
| `usage_outbox` | 1215 | 1215 | **100%** |
| `tenant_entitlement_plans` | 354 | 0 | 0% |
| `memberships` (control, has FK) | 5607 | 0 | 0% |
| `tenant_resources` (control, has FK) | 4868 | 0 | 0% |

6,537 rows name a tenant that does not exist in `tenants`.

The 100%-versus-0% split needed explaining before it could be called anything, since a uniform
result usually means the query is wrong. It is not the identifier format: sampled values from both
groups are canonical lowercase UUIDs, and a case-variance check returned zero across all five
text-keyed tables.

## A.2 The mechanism, demonstrated side by side

One session, one tenant identifier that exists nowhere, two tables:

```
tenant 8b56258a-… exists in tenants: False
  usage_meter_balances (text tenant_id, no FK) -> ACCEPTED
  tenant_resources     (uuid tenant_id, FK)    -> refused, ForeignKeyViolation

a session for a tenant that does not exist reads back 1 of its own metering rows
```

Row-level security does not help here and was never going to: `set_config` sets a value, it does
not assert that the value names anything. The only control that would have refused the write is
the foreign key, and the foreign key is impossible because `tenant_id` is `VARCHAR(64)` while
`tenants.id` is `UUID`.

## A.3 Severity, stated conservatively

**LOW-MEDIUM. Not a cross-tenant disclosure.** Every read is still scoped by the policy, and the
orphaned rows belong to a tenant nobody can open a session for, so nothing leaks. This is a
lifecycle and integrity defect, not an isolation one.

What it does cost:

- **Tenant deletion strands data silently.** `memberships` and `tenant_resources` cascade from
  `tenants`; the five text-keyed tables cannot, so a deleted tenant's usage counters, quota
  reservations and outbox entries persist with no owner, no reader and no sweep. The 6,537 rows
  are that, already happening in the verification instance.
- **Nothing detects it.** Absent the foreign key, the first thing that notices is a query somebody
  writes on purpose. This one was written to price a decision, not to find a defect.

## A.4 Deliberately not fixed

Fixing it means adding a foreign key, which means changing `tenant_id` from `VARCHAR(64)` to
`UUID` on five populated tables. That is §2.1's decision, and it is the operator's. Taking it here
by writing the migration would resolve a reserved decision by code default, which is what
`DEC-P35-RUNTIME` exists to prevent.

So F10 changes nothing about the recommendation and everything about its weight. §2.1 argued that
Option B forfeits referential integrity; Addendum B showed five tables that had already forfeited
it; this shows the forfeit has been collecting rows the whole time. The eight Phase 2 tables
inherit this if the same choice is made again.

The orphaned rows are left in place. They are the evidence, and removing them would leave the
claim resting on this document alone.

## A.5 Provenance

Source — read-only audit of the verification instance on 2026-07-30 via `pg_constraint` and
per-table `NOT EXISTS` counts, run as a `BYPASSRLS` role so the policies could not hide the rows
being counted; plus one write probe whose two rows were removed. Advisory only —
`execution_authority: false`, `approval_authority: false`.
