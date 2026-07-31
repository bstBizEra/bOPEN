# BOPEN-PRD-P35-002 — Tenant Privacy and Platform Observability Product Requirements

**Document ID:** `BOPEN-PRD-P35-002`
**Version:** `0.1.0`
**Status:** Proposed — assists `WP-P35-06`; no implementation authority
**Issued:** 2026-07-31
**Owner:** Product Authority (approval pending)
**Classification:** Product Requirements Candidate
**Governing artifacts:** `BOPEN-TENANT-001`, `BOPEN-AUTHZ-001`, `BOPEN-REQ-001`, `BOPEN-GOV-EBIV-001`, `AGENTS.md` §7, §8, §10, §14, §16, §23
**Governing decisions:** [`DEC-P35-TENANCY-MODEL`](../decisions/DEC-P35-TENANCY-MODEL.md) §8 (approved), [`DEC-P35-CONTROL-PLANE`](../decisions/DEC-P35-CONTROL-PLANE.md) (**proposed, unreviewed**)
**Assisted plan:** [`WP-P35-06`](../work-packages/BOPEN-P35-006-SHARD-ROUTING.md)
**Baseline:** `arch-baseline/2026-07-31-rls-option-c`
**Relationship to `BOPEN-PRD-P35-001`:** additive. That PRD addresses runtime assurance of the single-database kernel and remains valid. This one addresses the hybrid-placement architecture that supersedes it.

---

## 1. Purpose and authority boundary

`DEC-P35-TENANCY-MODEL` §8 changed the tenancy model to hybrid placement: a dedicated database
per tenant by default, a shared row-level-security pool for trial and free tier. The operator
additionally requires that tenant privacy must not blind the platform to performance, capacity
and business analysis.

This PRD translates that architecture into requirements that can be built and refuted. It does
not amend a normative specification, authorize implementation, or ratify
`DEC-P35-CONTROL-PLANE`, which remains unreviewed by the Security and Privacy Authorities.

## 2. Problem statement — established by inspection, 2026-07-31

The current schema was designed for one database. Splitting it across a control plane and
per-tenant data planes is not a deployment change; it breaks mechanisms that presently do real
work. Five findings, each verified against the migrations at `arch-baseline/2026-07-31-rls-option-c`.

### F-1 — Foreign keys cannot span databases, and **twelve** of them would have to

Counted from `pg_constraint` on the live verification instance, 2026-07-31 — not estimated from
reading the migrations. An earlier draft of this PRD said five; the measurement corrected it
upward, which is the direction that matters.

| Child | Column | Parent |
| :--- | :--- | :--- |
| `active_contexts` | `membership_id` | `memberships` |
| `active_contexts` | `principal_id` | `principals` |
| `active_contexts` | `tenant_id` | `tenants` |
| `audit_events` | `principal_id` | `principals` |
| `audit_events` | `tenant_id` | `tenants` |
| `lifecycle_events` | `tenant_id` | `tenants` |
| `memberships` | `principal_id` | `principals` |
| `memberships` | `tenant_id` | `tenants` |
| `rate_limit_counters` | `tenant_id` | `tenants` |
| `rate_limit_policies` | `tenant_id` | `tenants` |
| `tenant_feature_toggles` | `tenant_id` | `tenants` |
| `tenant_resources` | `tenant_id` | `tenants` |

Under dedicated placement, `tenants` and `principals` are control-plane rows while
`tenant_resources` and the tenant's business tables are tenant-database rows. **PostgreSQL
cannot enforce a foreign key across databases.** Every one of these constraints silently degrades
from a database guarantee to an application convention.

Reproduce:

```sql
SELECT c.conrelid::regclass, a.attname, c.confrelid::regclass
FROM pg_constraint c JOIN pg_attribute a
  ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
WHERE c.contype = 'f'
  AND c.confrelid::regclass::text IN ('tenants','principals','active_contexts','memberships');
```

This is the central risk of the change. `AGENTS.md` §8 requires *"database enforcement, not only
application filtering"*, and commit `105b4df` already recorded 6,537 rows that no foreign key
would have permitted — evidence that this codebase does produce orphans when nothing stops it.

### F-2 — `principals.email` is globally unique, which forces principals into the control plane

Confirmed on the live instance: `principals_email_key`, a unique btree index on
`principals(email)`. Global uniqueness cannot be enforced across N databases, so
`principals` must be control-plane. That is architecturally correct — invariant 1 makes a
principal broader than any one tenant — but it has a consequence the control-plane record does
not yet state: **the control plane necessarily holds email addresses, which are personal data.**

`DEC-P35-CONTROL-PLANE` §4 currently prohibits "free-text content — names, addresses" from
crossing the boundary. That prohibition is aimed at tenant *business* content and, read
literally, forbids the principal registry the platform cannot function without. It needs
refining before it is ratified, not after.

### F-3 — Audit events carry business identifiers

`audit_events` holds `action`, `resource_type` and `resource_id`. Platform-wide security
monitoring wants these in the control plane. Tenant privacy wants them inside the tenant
boundary. `resource_id` names a tenant's business object.

Both placements are defensible and they are not compatible. This is an open decision, not an
implementation detail, and building either way answers it by default.

### F-4 — Metering already sits outside referential integrity

`usage_meter_balances.tenant_id` is `character varying` while `tenants.id` is `uuid`, and
`pg_constraint` reports **0** foreign keys on that table. Both confirmed on the live instance.
The type disagreement is pre-existing and known. It means metering is *already*
plane-portable — an accident that happens to help, but one that should become deliberate rather
than remaining an inconsistency nobody chose.

### F-6 — F-1 counted foreign keys. Nobody counted RLS policies with cross-plane dependencies *(added 2026-08-01)*

Migration `007_registry_table_isolation.sql` closed a **measured** cross-tenant disclosure — one
tenant session reading 7,631 tenant rows and 6,657 principal rows including email addresses. The
policy that closed it:

```sql
CREATE POLICY principals_read ON principals
    FOR SELECT
    USING (
        NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL
        OR EXISTS (
            SELECT 1 FROM memberships m
            WHERE m.principal_id = principals.id
              AND m.tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
    );
```

**That policy is a subquery from `principals` into `memberships`.** F-2 forces `principals` into
the control plane; `memberships` is tenant-scoped by RLS. Split them across databases and
PostgreSQL cannot evaluate the subquery — for the same reason it cannot enforce the twelve
foreign keys in F-1.

**The disclosure fix does not survive the split** unless `memberships` is placed control-plane or
duplicated. Two consequences:

1. F-1 enumerated foreign keys. **It did not enumerate RLS policies whose `USING` clause reaches
   another table.**

   **Enumerated 2026-08-01 against the live catalogue** (`D-CP-003`, `DEC-P35-CONTROL-PLANE-DOCKET`
   §3.3). `pg_policies` reports **27 active policies across 16 tables**; every `qual` and
   `with_check` expression was inspected. **Exactly one carries a cross-plane dependency:**
   `principals_read` on `principals`, whose `USING` clause is
   `EXISTS (SELECT 1 FROM memberships …)`.

   That is a materially better result than F-6 first assumed — the exposure is one policy, not an
   uncounted class. It does not dissolve the finding: `principals` is control-plane by F-2 and
   `memberships` is tenant-scoped, so the policy still cannot be evaluated across a split, and the
   6,657-row disclosure it closed still reopens unless `memberships` is co-located, the relation
   is projected, or the policy is replaced.

   `PRD-P35B-PLANE-001` is no longer blocked on *counting*. It is blocked on **deciding
   `memberships`' plane**, which is a single decision rather than an open survey.
2. Worse, and less obvious: in the control plane **every session is unscoped by construction** —
   no `app.current_tenant_id` is set. Every policy in migration 007 grants full read to an
   unscoped session via its `… IS NULL OR …` branch. Migration 007 says so itself under "What
   this does not close": *"The unscoped path itself. `system_session` still sees the entire
   registry."* **Moving `principals` to a control plane where all sessions are unscoped converts
   that stated residual risk into the normal operating mode.**

`PRD-P35B-CRED-001` constrains the control plane's access to *tenant* databases. **Nothing yet
constrains access within the control plane**, which is where the principal registry and its email
addresses would live.

This is a blocking input to `PRD-P35B-PLANE-001`, not a downstream concern.

### F-5 — Nothing in the schema records placement

There is no column, table or configuration naming which database serves a tenant. Placement is
the new load-bearing concept and it currently does not exist anywhere in the model.

## 3. Product outcomes

| ID | Outcome |
| :--- | :--- |
| `O-1` | A tenant's business data is unreadable by the platform, structurally rather than by policy |
| `O-2` | The platform retains capacity planning, performance management and billing without reading business data |
| `O-3` | Referential integrity lost to the plane split is replaced by an enforced mechanism, not by convention |
| `O-4` | A tenant can be told, accurately, what is held about it |
| `O-5` | Trial-tier tenants sharing a pool are told they are sharing |

## 4. Scope

**In scope:** plane assignment for every existing table; cross-plane integrity; placement
recording and routing; telemetry content rules; control-plane credential boundary; per-placement
migration uniformity; tenant-visible disclosure.

**Out of scope:** rebalancing a tenant between placements (deferred by `WP-P35-06`); the consent
mechanism for business-content analysis (`DEC-P35-CONTROL-PLANE` §5 tier 3); Phase 4 products;
any change to `ADR-0005` or to row-level security for the shared pool.

## 5. Functional requirements

### PRD-P35B-PLANE-001 — Every table has exactly one declared plane

Each of the 16 tables carries a recorded plane assignment: `control`, `tenant`, or `both`
(schema present in each tenant database). An unassigned table blocks implementation.
**Falsifiable:** a test enumerates tables in the live schema and fails on any not present in the
assignment register.
*Addresses F-1, F-3, F-4.*

### PRD-P35B-INTEGRITY-001 — Every foreign key lost to the split is replaced by an enforced check

For each cross-plane reference identified in F-1, either the reference is eliminated by
denormalisation, or a mechanism refuses the orphan at write time. A comment, a code review
convention, or "the application always sets it" does not satisfy this.
**Falsifiable:** for each replaced constraint, a negative probe attempts to create the orphan the
old foreign key would have refused, and it must fail.
*Addresses F-1, and the 6,537 rows in `105b4df`.*

### PRD-P35B-PLACE-001 — Placement is explicit, recorded at provisioning, and immutable

`POST /v1/tenants` records placement kind (`dedicated` or `shared`) and target at creation.
Placement cannot change without a governed migration.
**Falsifiable:** a tenant provisioned as `dedicated` has a placement row naming a database that
is not the shared pool; an attempt to mutate placement through the API is refused.
*Addresses F-5.*

### PRD-P35B-PLACE-002 — A dedicated tenant is unroutable to the shared pool

By construction, not convention. This is the isolation guarantee of Option D; its failure would
look like ordinary operation.
**Falsifiable:** with a dedicated tenant configured, a probe forcing shared-pool resolution must
raise, not return an empty result. Mirrors `WP-P35-06` `A-15`.

### PRD-P35B-PLACE-003 — An unplaced tenant is refused, never defaulted

A tenant with no placement raises. Defaulting would write a private tenant's rows into a shared
database, and row-level security would not catch it because the session would be correctly scoped
to a tenant with no rows there.
**Falsifiable:** a request for an unplaced tenant returns an error; a test asserts it is not an
empty success. Mirrors `WP-P35-06` `A-09`.

### PRD-P35B-CRED-001 — The control plane holds no credential for any tenant database

The control-plane role has no grant on any tenant database. Aggregates are pushed outward from
tenant databases; they are never pulled.
**Falsifiable:** a probe using control-plane credentials attempts to connect to a tenant database
and to select from a tenant business table, and is refused by PostgreSQL — not by application
code.
*This is what makes `O-1` structural. Without it, privacy depends on the platform choosing not to
look.*

### PRD-P35B-TELEM-001 — Telemetry carries no literals from tenant data

Query logs, error messages, traces and metrics labels must not contain values from tenant
business rows. Slow-query logging must normalise literals before storage.
**Falsifiable:** a probe writes a distinctive sentinel value into a tenant business row, triggers
an error and a slow query on it, and asserts the sentinel appears in no control-plane record.

### PRD-P35B-PII-001 — Control-plane personal data is declared, bounded and justified

Per F-2 the control plane holds principal email addresses. The set of personal data it holds is
enumerated, each item justified by a platform function that cannot work without it, and reviewed
by the Privacy Authority.
**Falsifiable:** a test compares control-plane columns against the declared register and fails on
any undeclared column of a personal-data type.

### PRD-P35B-AUDIT-001 — The audit split is decided before it is built

Per F-3, record whether `resource_id` and `resource_type` remain tenant-side, are redacted, or
cross to the control plane — with the security-monitoring consequence of the choice stated.
**Falsifiable:** the decision record exists and names the disposition; implementation matching
neither disposition fails review.
*This requirement is deliberately a decision gate rather than a behaviour.*

### PRD-P35B-MIG-001 — Migration state is uniform across placements before service

The kernel refuses to serve from a placement whose applied-migration set differs from the
control-plane expectation.
**Falsifiable:** a placement is put one migration behind and the kernel refuses to serve it.
Mirrors `WP-P35-06` `A-13`.

### PRD-P35B-DISCLOSE-001 — A tenant can see what is held about it, and its placement kind

A tenant can retrieve the telemetry and aggregate categories held about it, and whether it is on
a dedicated database or a shared pool.
**Falsifiable:** a shared-pool tenant's response states it is shared; a dedicated tenant's states
it is dedicated; the telemetry categories returned match the `DEC-P35-CONTROL-PLANE` §3 register.
*Addresses `O-4`, `O-5`. This is the cheapest mechanism for keeping the boundary honest — a
boundary the tenant can inspect is one that gets noticed when it moves.*

## 6. Non-functional requirements

| ID | Requirement |
| :--- | :--- |
| `NFR-1` | Connection-pool sizing is measured per placement before placement count increases; N databases multiply client-side connections |
| `NFR-2` | Provisioning a dedicated tenant completes within a bounded time, or is asynchronous with observable state — creating a database and running 9 migrations is not an HTTP-request-shaped operation |
| `NFR-3` | Control-plane unavailability degrades to refusal, never to defaulted placement |
| `NFR-4` | The shared pool continues to pass all 38 existing isolation tests |

## 7. Required user journeys

**7.1 Provision a dedicated tenant.** Create tenant → database created → migrations applied →
placement recorded → first context issued against the dedicated database → the platform records
usage without reading any business row.

**7.2 Provision a trial tenant.** Create tenant on shared pool → placement recorded as `shared` →
tenant is told it is sharing → RLS enforces isolation → all 38 isolation tests still apply.

**7.3 Operator answers a capacity question.** Without a tenant-database credential: retrieve call
volume, storage, latency and quota consumption per tenant from the control plane.

**7.4 Tenant asks what is held about it.** Retrieve placement kind and telemetry categories, and
the answer matches the §3 register of `DEC-P35-CONTROL-PLANE`.

## 8. Delivery sequence

1. `DEC-P35-CONTROL-PLANE` reviewed by Security and Privacy Authorities — **blocking**. F-2 and
   F-3 must be resolved in that review.
2. `PRD-P35B-PLANE-001` — plane assignment register. Cheap, and everything downstream depends on it.
3. `PRD-P35B-INTEGRITY-001` — cross-plane integrity design. Highest technical risk; do it early.
4. `PRD-P35B-PLACE-001..003` — placement recording and routing (`WP-P35-06`).
5. `PRD-P35B-CRED-001`, `TELEM-001`, `PII-001` — the privacy boundary.
6. `PRD-P35B-MIG-001`, `DISCLOSE-001`.

## 9. Acceptance matrix

| ID | Proposition | Removal probe |
| :--- | :--- | :--- |
| `P35B-T001` | Every live table has a declared plane | Add a table, omit it from the register — the test must fail |
| `P35B-T002` | Cross-plane orphans are refused at write | Remove the replacement check — the orphan probe must succeed, failing the test |
| `P35B-T003` | Dedicated tenants never resolve to the shared pool | Remove the placement-kind guard — the probe must route and the test fail |
| `P35B-T004` | Unplaced tenants raise rather than default | Add a default placement — the test must fail |
| `P35B-T005` | Control-plane credentials cannot read tenant business tables | Grant the control-plane role SELECT — the test must fail |
| `P35B-T006` | No tenant literal reaches control-plane records | Disable literal normalisation — the sentinel must appear and the test fail |
| `P35B-T007` | Undeclared personal-data columns are refused | Add an undeclared email column — the test must fail |
| `P35B-T008` | A placement behind on migrations is refused service | Relax the check — the test must fail |
| `P35B-T009` | Shared-pool tenants are told they are shared | Return `dedicated` for all — the test must fail |
| `P35B-T010` | The shared pool still passes all 38 isolation tests | Disable one RLS policy — the suite must fail |

A test whose named mechanism can be removed without it failing is inadmissible under
`BOPEN-GOV-EBIV-001` R4.

## 10. Risks and open decisions

| Risk | Note |
| :--- | :--- |
| **Cross-plane integrity loss (F-1)** | The most serious. Application-enforced integrity has already failed in this repository once, measurably |
| **Audit placement undecided (F-3)** | Blocks security monitoring design; must be decided, not defaulted |
| **Control-plane PII (F-2)** | `DEC-P35-CONTROL-PLANE` §4 as drafted forbids what the platform requires; refine before ratifying |
| **Operational cost of N databases** | 9 migrations × N tenants per release; backup and restore per tenant. Real, and the price of the privacy guarantee |
| **Placement is effectively permanent** | Rebalancing deferred by `WP-P35-06`. Decide before tenant count makes it expensive |

## 11. Traceability

| Requirement | Governing artifact | Work package |
| :--- | :--- | :--- |
| `PLANE-001`, `INTEGRITY-001` | `AGENTS.md` §8, §14 | `WP-P35-06` |
| `PLACE-001..003` | `BOPEN-TENANT-001`, `DEC-P35-TENANCY-MODEL` §8 | `WP-P35-06` `A-09`, `A-15` |
| `CRED-001`, `TELEM-001`, `PII-001` | `DEC-P35-CONTROL-PLANE` §3, §4, §6 | pending review |
| `AUDIT-001` | `BOPEN-AUTHZ-001`, `AGENTS.md` §7 invariant 11 | pending decision |
| `MIG-001` | `AGENTS.md` §14 | `WP-P35-06` `A-13` |
| `DISCLOSE-001` | `DEC-P35-CONTROL-PLANE` §7 | pending review |

## 12. Provenance

Findings F-1 through F-5 were established by direct inspection at
`arch-baseline/2026-07-31-rls-option-c`, not by projection. F-1, F-2 and F-4 were then **queried
against the live PostgreSQL verification instance** via `pg_catalog`, and the query for F-1 is
included above so the count can be reproduced rather than trusted.

That verification step earned its place. Reading the migrations gave F-1 as five foreign keys;
the database reported twelve. A first attempt to check it returned zero rows and looked like a
refutation — that was `information_schema.constraint_column_usage` filtering by table ownership
under the unprivileged application role, not an absence of constraints. Both the undercount and
the false negative are recorded because a PRD whose findings were never executed is the kind of
evidence `BOPEN-GOV-EBIV-001` R1 exists to refuse.

Prepared by Claude (agent, Motor role) as a requirements candidate.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
```
