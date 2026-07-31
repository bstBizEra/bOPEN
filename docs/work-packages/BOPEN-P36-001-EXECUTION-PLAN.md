# BOPEN-P36-001 — Phase 3.6 Tenant Privacy and Platform Observability

**Status:** **Proposed — entry blocked pending Security and Privacy review of `DEC-P35-CONTROL-PLANE`**
**Version:** `1.0.0`
**Issued:** 2026-07-31
**Owner:** Engineering Authority
**Requirements:** [`BOPEN-PRD-P35-002`](../02-requirements/BOPEN-PRD-P35-002.md)
**Decisions:** [`DEC-P35-TENANCY-MODEL`](../decisions/DEC-P35-TENANCY-MODEL.md) §8 *(approved)*, [`DEC-P35-CONTROL-PLANE`](../decisions/DEC-P35-CONTROL-PLANE.md) *(proposed)*
**Baseline:** `arch-baseline/2026-07-31-rls-option-c`
**Governing artifacts:** `BOPEN-TENANT-001`, `BOPEN-AUTHZ-001`, `AGENTS.md` §7, §8, §10, §14, §23

---

## Objective

Make tenant privacy structural: a dedicated database per tenant by default, a shared row-level
security pool for trial and free tier, and a control plane that can answer every operational and
commercial question without reading a tenant business row.

The measure of completion is not that placement works. It is that **the platform cannot read
tenant business data even if its own code asks**, and that a test fails if that becomes possible.

## What makes this hard

Not placement. Twelve foreign keys reference `tenants`, `principals`, `memberships` or
`active_contexts`, and PostgreSQL cannot enforce a foreign key across databases. Splitting the
planes turns all twelve from a database guarantee into an application convention, in a repository
where commit `105b4df` already recorded 6,537 rows that no foreign key would have permitted.

Everything else in this plan is ordinary work. That is the part that can go quietly wrong.

## Entry gate

**Blocked.** `DEC-P35-CONTROL-PLANE` requires Security and Privacy Authority review, which must
resolve:

1. **F-2** — the control plane necessarily holds personal data (`principals.email` is globally
   unique and cannot be sharded). §4 of that record, as drafted, forbids it. Refine before
   ratifying.
2. **F-3** — `audit_events` carries `resource_id`; security monitoring wants it central, privacy
   wants it tenant-side. Both defensible, incompatible.

No work package below may begin before that review records an outcome.

## Deliverables

| ID | Deliverable | Work package |
| :--- | :--- | :--- |
| D-16 | Plane assignment register — every table declared `control`, `tenant` or `both` | `WP-P36-01` |
| D-17 | Cross-plane integrity mechanism replacing the twelve foreign keys | `WP-P36-01` |
| D-18 | Placement recording at provisioning; kind and target, immutable | `WP-P35-06` |
| D-19 | Placement resolver in `db.py` — tenant → connection target | `WP-P35-06` |
| D-20 | Per-placement migration orchestration and uniformity refusal | `WP-P36-03` |
| D-21 | Control-plane credential boundary — no grant on any tenant database | `WP-P36-02` |
| D-22 | Telemetry literal normalisation | `WP-P36-02` |
| D-23 | Personal-data register for the control plane | `WP-P36-02` |
| D-24 | Tenant disclosure endpoint — placement kind and telemetry categories | `WP-P36-03` |
| D-25 | Cross-plane and per-placement conformance suites | all |

## Acceptance criteria

Each maps to a `BOPEN-PRD-P35-002` proposition and inherits its removal probe.

| ID | Criterion | PRD |
| :--- | :--- | :--- |
| A-17 | Every live table has a declared plane; an undeclared table blocks startup | `P35B-T001` |
| A-18 | Every replaced foreign key has a negative probe creating the orphan it must refuse | `P35B-T002` |
| A-19 | A `dedicated` tenant is unroutable to the shared pool, by construction | `P35B-T003` |
| A-20 | An unplaced tenant raises; it never defaults | `P35B-T004` |
| A-21 | Control-plane credentials are refused by PostgreSQL on tenant business tables | `P35B-T005` |
| A-22 | A sentinel value in a tenant row appears in no control-plane record | `P35B-T006` |
| A-23 | An undeclared personal-data column fails the register check | `P35B-T007` |
| A-24 | A placement behind on migrations is refused service | `P35B-T008` |
| A-25 | A shared-pool tenant is told it is shared | `P35B-T009` |
| A-26 | The shared pool still passes all 38 isolation tests | `P35B-T010` |

**A-21 is the one that carries the guarantee.** It must be enforced by PostgreSQL privileges, not
by application code declining to issue a query.

## Sequence

Dependency-ordered. Each stage gates the next.

```text
0  Security + Privacy review of DEC-P35-CONTROL-PLANE          [BLOCKING]
   └─ resolves F-2 (control-plane PII) and F-3 (audit placement)

1  WP-P36-01  plane assignment register (D-16)                 cheap, unblocks everything
   └─ then cross-plane integrity design + probes (D-17)        HIGHEST RISK — do early

2  WP-P35-06  placement recording and resolver (D-18, D-19)    already accepted, generalized

3  WP-P36-02  credential boundary, telemetry, PII register     (D-21, D-22, D-23)
              A-21 lands here

4  WP-P36-03  migration uniformity, disclosure                 (D-20, D-24)

5  conformance suites per placement (D-25)                     runs continuously from stage 2
```

Stage 1's integrity work is placed before placement routing deliberately. Building routing first
would let tenants be placed into a topology whose integrity story is still unwritten, and the
orphans would be created before the mechanism that refuses them exists.

## Out of scope

Rebalancing a tenant between placements; the consent mechanism for business-content analysis
(`DEC-P35-CONTROL-PLANE` §5 tier 3); Phase 4; any change to `ADR-0005` or to row-level security
for the shared pool.

## Risks

| Risk | Mitigation |
| :--- | :--- |
| Cross-plane orphans, silently | A-18 requires a negative probe per replaced constraint. No probe, no replacement |
| A dedicated tenant lands in the shared pool | A-19; failure would look like ordinary operation, so it is probed rather than asserted |
| Control plane accumulates business data by increments | A-22's sentinel probe, plus the §3 register being exhaustive by intent |
| N databases multiply client connections | Measure pool sizing per placement before increasing placement count |
| Provisioning becomes slow | Creating a database and running 9 migrations is not HTTP-request-shaped; make it asynchronous with observable state |
| Operational cost of N databases | Real, and the price of the guarantee. Recorded rather than discovered |

## Rollback

Configure a single shared placement. D-18 through D-22 are inert under a single-placement map, so
rollback is configuration rather than code removal — the same property that made `WP-P35-05a`
additive.

The baseline `arch-baseline/2026-07-31-rls-option-c` restores the pre-hybrid tree if the
architecture itself must be reverted.

## Roles

| Role | Assignee |
| :--- | :--- |
| Maker | *unassigned* |
| Independent checker | *unassigned — must not be the maker* |
| Security reviewer | **required, not optional** — this work package changes a privacy boundary |
| Completion authority | Operator |

## Authority

`DEC-P35-TENANCY-MODEL` §8 authorizes the placement model. Nothing authorizes the control-plane
data flow until `DEC-P35-CONTROL-PLANE` is reviewed. Production activation remains unauthorized.
Completion requires an independent verifier under `BOPEN-GOV-EBIV-001`.
