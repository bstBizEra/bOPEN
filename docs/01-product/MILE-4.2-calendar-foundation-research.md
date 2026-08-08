# MILE-4.2 — Calendar foundation, research & design

**Document ID:** `RESEARCH-MILE-4.2-CALENDAR`  
**Version:** `1.0.0`  
**Status:** **Research — advisory. Final sequential research slice; buildable only on separate operator authorization.** Calendar remains gated by [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §9.  
**Issued:** 2026-08-05  
**Owner:** Architecture & Engineering Authority  
**Raised by:** Codex (agent, advisory role) — research and planning only; no approval authority  
**Entry evidence:** [`REVIEW-MILE-4.2-NOTIFICATION`](MILE-4.2-notification-foundation-review.md) was recorded at commit `08a48795d7a1037051ed21e27f9ff3099da16943`; the operator explicitly entered Calendar research on 2026-08-05.  
**Governing:** `AGENTS.md` §§2, 7–15; [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md); [`CAPABILITY-MATRIX`](CAPABILITY-MATRIX.md)  
**Dependent artifacts:** Future `BOPEN-CAL-001`, civil-time/tzdb ADR, accepted work package, API/event contracts, migration and recovery plan, test matrix, and EBIV evidence  
**Clean-room:** IETF and IANA specifications are requirements sources only. No external calendar-server code, schema, recurrence implementation, or tests are copied.

---

## 1. Executive summary

The recommended foundation is a **versioned Business Calendar and Working-Time service**. It defines
a tenant's named calendars, IANA time zone, weekly local-time working intervals, explicit date
overrides/closures, effective versions, and deterministic bounded queries such as:

- is this instant working time?
- what are the next opening and closing instants?
- what is the next working instant?
- how much elapsed working duration lies inside a bounded interval?
- what instant results after adding a bounded working duration?

It is **not** a personal/meeting calendar, booking system, workforce shift planner, resource-capacity
scheduler, workflow timer, SLA engine, reminder service, payroll calculator, or general recurrence
engine. The first slice deliberately avoids arbitrary iCalendar `RRULE`, attendee scheduling,
free/busy, Calendar composition/inheritance, and automated holiday-provider synchronization.

The core property is **civil-time correctness with reproducible rules**: weekly business hours are
stored as local civil-time rules in a named IANA zone, evaluated to instants using an explicit
ambiguous/nonexistent-time policy and a recorded tzdb version. A fixed UTC offset is not a time zone,
and the runtime MUST NOT silently guess through daylight-saving or political time-zone changes.

This is the fourth and final research slice in the operator's sequence: Document → Location →
Notification → Calendar. Research review may close the sequence, but it does not authorize any of
the four foundations to build.

## 2. Research question and method

### 2.1 Research question

What is the smallest reusable Calendar foundation that lets bOPEN products evaluate business
working time consistently across countries and time-zone changes without importing meetings,
bookings, shifts, workflow timers, payroll, or unrestricted recurrence into the platform foundation?

### 2.2 Method and source hierarchy

The research used, in order:

1. approved bOPEN boundaries, product composition, and the authorized Workflow State Engine scope;
2. RFC 5545 iCalendar for date/time, time-zone, recurrence, and invalid-instance behavior;
3. IANA Time Zone Database for versioned civil-time rules and current update evidence;
4. RFC 8984 JSCalendar as a modern JSON requirements source for time-zone and recurrence concepts;
5. RFC 4791 CalDAV as a comparison showing the larger server/synchronization scope being excluded;
6. architecture inference and recommendations, explicitly separated from those sources.

External standards remain informative until adopted by an approved bOPEN contract. Current web
research was required because the IANA tzdb changes over time.

## 3. Scope

### 3.1 In scope

- tenant-owned named business-calendar identity and lifecycle;
- immutable published Calendar versions with effective intervals;
- IANA time-zone identifier and tzdb publication/evaluation version evidence;
- weekly local-date/time working intervals;
- explicit local-date day overrides containing replacement intervals or a full closure;
- explicit ambiguous-time and nonexistent-time evaluation policy;
- bounded pure queries for working state, opening/closing, next working instant, elapsed working
  duration, and adding elapsed working duration;
- optional labels/source provenance for tenant-accepted holidays/closures;
- idempotency, optimistic concurrency, RLS, tenant-safe cache, append-only history, audit, events,
  migration, backup/restore, and verification controls;
- a future import/export adapter seam that refuses unsupported recurrence rather than approximating it.

### 3.2 Out of scope

- personal calendars, meetings, invitations, attendees, RSVP, free/busy, and calendar sharing;
- CalDAV/WebDAV synchronization and offline-client conflict resolution;
- appointments, reservations, booking, capacity allocation, and resource scheduling;
- employee shifts, rosters, leave, attendance, payroll, overtime, and labor-law decisions;
- workflow timers, SLA deadlines, escalation, task due dates, reminders, and delayed jobs;
- arbitrary RFC 5545/JSCalendar recurrence, `RRULE`, `RDATE`, `EXDATE`, recurrence exceptions, and
  non-Gregorian recurrence in the first slice;
- automatic public-holiday truth or unreviewed provider-feed activation;
- Calendar inheritance, overlays, unions/intersections, and multi-calendar composition;
- astronomical calendars, leap-second-sensitive measurement, and pre-1970 historical authority;
- timezone creation/editing by tenants or fixed-offset-only zones;
- using a Calendar evaluation as permission, approval, or proof a business action completed.

### 3.3 Assumptions

- Tenant is the ownership, policy, isolation, and quota boundary.
- Product modules reference a Business Calendar; the Calendar foundation does not own their
  resources, bookings, shifts, workflows, or deadlines.
- The authorized Workflow State Engine has no timers; Calendar does not silently add them. A future
  timer/scheduler slice may query Calendar but requires its own authorization and durable runtime.
- Weekly working intervals and day overrides are sufficient for the first real consumers.
- All business-calendar calculations use the proleptic Gregorian civil calendar in the first slice.
- Pooled PostgreSQL with forced RLS is the first storage profile; contracts survive future dedicated
  placement.
- IANA tzdb is an external versioned dependency; bOPEN does not invent or edit civil-time rules.

## 4. Facts, interpretations, and recommendation

| Class | Statement |
| :--- | :--- |
| Repository fact | `CAPABILITY-MATRIX` defines Calendar & Schedules as operating hours, shifts, and holiday calendars consumed by bFleet, bPro, and Tourism. |
| Repository fact | Workflow's authorized and disposed slice explicitly excludes timers; Calendar remains separately gated. |
| Repository fact | Notification research/review excludes workflow timers and reminder scheduling, preserving Calendar's separate boundary. |
| External fact | RFC 5545 distinguishes UTC, local time with zone reference, and floating local time, and defines extensive recurrence behavior. |
| External fact | RFC 5545 says invalid dates/nonexistent local times generated by recurrence are ignored rather than counted. |
| External fact | IANA tzdb is updated when political bodies change time-zone boundaries, offsets, or daylight-saving rules; `2026c` was current at retrieval. |
| External fact | JSCalendar supports named time zones, custom zone definitions, recurrence rules, and overrides—broader than this first slice. |
| External fact | CalDAV defines calendar collections, synchronization/concurrency, queries, recurrence resources, and free/busy—server capabilities excluded here. |
| Interpretation | A fixed offset or unversioned local timestamp cannot reproduce working-time decisions across rule changes. |
| Recommendation | Implement a narrow versioned working-time evaluator: weekly rules + full-day replacement overrides + explicit time-zone policies + bounded queries. |

The approved matrix's “shifts” breadth is a future consumer direction, not authority to build employee
rostering into the foundation. A shift planner may consume working-time rules later.

## 5. Domain distinctions

| Concept | Normative proposal | Must not be confused with |
| :--- | :--- | :--- |
| `BusinessCalendar` | Stable tenant-owned identity for one named working-time policy | Meeting calendar, resource schedule, workflow, or timezone |
| `CalendarVersion` | Immutable effective rule set used for deterministic evaluation | Mutable current row or software/tzdb version |
| Weekly interval | Local civil-time working window attached to weekday | Permanently equivalent UTC interval |
| `DayOverride` | One local date whose full interval set replaces the weekly rule | Recurring event exception, leave request, or workflow exception |
| Closure/holiday label | Tenant-accepted reason/source on an override | Globally authoritative public-holiday law |
| IANA time zone | Versioned rules mapping local civil times to instants | Fixed UTC offset, locale, or country |
| Instant | Unique point on the UTC timeline | Local date/time that may be ambiguous or nonexistent |
| Elapsed working duration | Timeline duration inside resolved working intervals | Payroll hours or nominal wall-clock duration |
| Calendar assignment | Consumer-owned reference to a Calendar | Calendar ownership of Asset/Party/Location/Product |

The foundation MUST keep rule definition, rule publication, evaluation, and consumer action separate.
An answer that an instant is working time does not grant authorization or require a workflow
transition.

## 6. Options and recommendation

| Option | Boundary integrity | Civil-time correctness | Interoperability | P0 complexity | Reversibility | Disposition |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| Full iCalendar/CalDAV scheduling server | 2 | 5 | 5 | 1 | 2 | Reject for first slice — meetings, sync, recurrence, and sharing are out of scope |
| Product-specific dates/fixed UTC offsets | 1 | 1 | 2 | 5 | 2 | Reject — DST/political changes and duplicated policy create drift |
| General RRULE recurrence library as foundation | 3 | 4 | 5 | 2 | 3 | Defer — expansion, invalid instances, exceptions, and denial-of-service surface are too broad |
| Versioned weekly rules + day overrides + bounded evaluator | 5 | 5 | 4 | 5 | 5 | **Recommend** |

The recommendation is intentionally less expressive than RFC 5545. Unsupported recurrence is refused
loudly, not translated approximately into weekly rules.

## 7. Proposed model

```text
BusinessCalendar
  ├─ CalendarVersion[]
  │    ├─ WeeklyWorkingInterval[]
  │    └─ DayOverride[]
  │          └─ OverrideInterval[]
  └─ CalendarHistory[]

Product / Location / Asset / Party / Organization assignment
  └─ governed reference ──> BusinessCalendar.id or published version
```

### 7.1 `BusinessCalendar`

Proposed fields: immutable `id` and `tenant_id`, tenant-scoped unique `code`, `name`, description,
calendar lifecycle, current published version reference, optimistic revision, and audit/correlation
metadata.

```text
calendar: active <-> inactive -> retired (terminal)
```

Retirement prevents new assignment/evaluation for current operations according to policy but retains
versions and history for past evidence. Consumers must define whether historical evaluation against a
retired explicit version remains allowed.

### 7.2 `CalendarVersion`

Proposed fields:

- immutable version ID, tenant/calendar IDs, version number, status;
- IANA `time_zone_id`;
- `tzdb_version_at_publish` and civil-time evaluation policy version;
- ambiguous-local-time and nonexistent-local-time policies;
- effective-from and optional effective-to instants/dates under a frozen contract;
- change reason, source/provenance, creator/publisher, created/published timestamps;
- content hash and revision.

```text
version: draft -> published -> superseded
                 └──────────> withdrawn (exceptional, audited)
```

Drafts may change with optimistic concurrency. Published versions and their intervals/overrides are
immutable. Corrections publish a new version; they do not rewrite past rules. Overlapping effective
published versions are refused unless a future approved precedence model exists.

### 7.3 `WeeklyWorkingInterval`

Proposed representation:

- weekday `MO` through `SU`;
- local start and end as validated minute/second-of-day values under one precision policy;
- half-open interval `[start, end)`;
- optional label/classification with no payroll semantics;
- deterministic ordering and version ownership.

Zero/negative duration and same-day overlaps are refused. A cross-midnight input is normalized into
two intervals attached to adjacent weekdays before publication, or refused if the contract selects
explicit splitting only. The first slice SHOULD use explicit split intervals so query logic and
overlap validation stay visible.

### 7.4 `DayOverride`

One override per local calendar date replaces the entire weekly interval set for that date:

- empty interval set = closed day;
- non-empty validated interval set = replacement working windows;
- label/reason/source/provider reference and tenant acceptance evidence;
- published version ownership.

This single replacement rule avoids hidden precedence between “holiday”, “special opening”, and
weekly hours. Multiple conflicting overrides for the same version/date are refused.

### 7.5 Evaluation evidence

Each response SHOULD identify:

- tenant/calendar/version;
- IANA zone;
- tzdb version used by the evaluator;
- civil-time policy version;
- input instant/range/duration and bounded horizon;
- resolved interval or reason for non-working/no-result;
- evaluation timestamp and correlation ID where audit is required.

High-volume pure queries do not automatically create a domain event. Consumers making material state
changes store enough evaluation evidence in their own transaction/audit to explain the decision.

## 8. Civil-time correctness

### 8.1 Types and conversion rules

- Instants at API boundaries use offset-aware/UTC timestamps.
- Weekly intervals and overrides use local civil date/time under the Calendar's named IANA zone.
- Floating time without a Calendar zone is not accepted for working-time evaluation.
- A fixed offset such as `+07:00` is not accepted as `time_zone_id`; use `Asia/Vientiane` or another
  valid IANA identifier.
- Calendar locale and week-start presentation are separate from time-zone rules.
- Interval boundaries are half-open so adjacent windows do not double-count.
- Evaluation converts local boundaries to instants once under the selected policy, then performs
  ordering and elapsed-duration arithmetic on the instant timeline.

### 8.2 Ambiguous and nonexistent local times

Clock changes can create:

- a **gap**: a local time does not exist;
- a **fold**: a local time maps to two instants.

The runtime MUST NOT guess silently. The contract must select explicit policies, proposed as:

- nonexistent boundary: `reject_evaluation` or `shift_forward_to_first_valid`;
- ambiguous boundary: `earlier_offset`, `later_offset`, or `reject_evaluation`.

Recommendation: require the policy on every published Calendar version; use fail-closed
`reject_evaluation` until the operator/product chooses a business interpretation. A later relaxed
policy is a new version, not a runtime default change.

### 8.3 tzdb change management

IANA time-zone rules change. The operational design SHOULD:

1. pin and report the runtime tzdb version;
2. subscribe to/update through governed dependency release procedures;
3. compare upcoming resolved working intervals before and after a tzdb upgrade;
4. identify affected Calendar versions/consumers within a bounded future horizon;
5. require review/new version where the effective business schedule changes materially;
6. retain the version used for each material evaluation and preserve enough historical rules or
   derived evidence to reproduce past decisions;
7. refuse to claim historical reproducibility when the required tzdb rules are unavailable.

`tzdb_version_at_publish` alone is not sufficient evidence if the runtime cannot evaluate that old
version. The ADR must decide whether to retain tzdb artifacts, derived interval snapshots, or both for
the required retention horizon.

### 8.4 Working-duration semantics

The recommended first-slice duration is **elapsed timeline duration** inside resolved working
intervals. A local work window that spans an offset change may contain a different number of elapsed
hours than its wall-clock labels suggest. Payroll/nominal-hours calculations are excluded and must
not reuse this result without their own contract.

`add_working_duration` and range-duration queries require a maximum input duration/range, maximum
calendar search horizon, iteration ceiling, and explicit `no_working_time_within_horizon` result.
Unbounded search is refused.

## 9. Query contract

Proposed pure operations:

### 9.1 `is_working_instant`

Input: Calendar/version reference and instant. Output: boolean, resolved version/zone/tzdb policy,
matching interval or non-working reason, and safe evidence metadata.

### 9.2 `next_transition`

Input: Calendar/version reference, instant, direction/type, and bounded horizon. Output: next opening
or closing instant, or explicit no-result-within-horizon.

### 9.3 `next_working_instant`

Returns the input instant if already working under the agreed inclusivity rule; otherwise the next
opening inside the horizon.

### 9.4 `working_duration_between`

Returns elapsed duration of the intersection between the input instant range and resolved working
intervals. Negative/reversed/unbounded ranges are refused.

### 9.5 `add_working_duration`

Adds a non-negative bounded elapsed duration across working intervals and returns the resulting
instant plus evaluation evidence. Negative duration/backward calculation is deferred unless explicitly
authorized.

No operation schedules a job, changes a workflow, creates a booking, or sends a notification.

## 10. Interoperability boundary

RFC 5545 and JSCalendar inform names, time-zone handling, and future import/export, but the first
owned contract is narrower:

- accepted: one named zone, weekly intervals, explicit local-date replacement overrides;
- refused: arbitrary `RRULE`, `RDATE`, `EXDATE`, recurrence overrides, custom time-zone definitions,
  floating time, attendees, VEVENT/VTODO semantics, and CalDAV synchronization;
- import, if later authorized, parses into a **candidate** and returns unsupported constructs; it does
  not silently discard or approximate them;
- export labels the supported subset and does not claim round-trip fidelity for unsupported source
  data;
- imported holiday/calendar data requires explicit tenant acceptance before publication.

A general recurrence engine and CalDAV server are later products/capabilities, not hidden adapters.

## 11. Security, tenancy, consistency, and operations

### 11.1 Execution chain and authorization

An authenticated **Principal** with active **Membership** operates through server-validated **active
tenant context**. **Authorization**, **entitlement**, module availability, calendar lifecycle,
publication authority, query scope, import/export authority, and quotas are separate gates.
Commercial access and action permission remain distinct.

Capabilities separate read/evaluate, draft management, publication, lifecycle, import/export, and
bulk evaluation. Support access requires a time-bounded audited grant.

### 11.2 Tenant isolation

- All tenant-owned tables carry immutable `tenant_id`, tenant-inclusive foreign keys/uniqueness,
  forced RLS, default-deny policies, and fail-closed missing/ambiguous/inactive context.
- Cross-tenant disclosure through direct IDs, version lookup, evaluation, cache, imports, exports,
  analytics, events, logs, errors, timing, and bulk queries is zero.
- New tables remain aligned between the repository tenant-scoped inventory and trial→paid
  `COPY_ORDER`, with parent-before-child copy and live migration evidence.
- Cache keys include tenant, authorization/evaluation scope, Calendar/version/hash, tzdb/policy
  version, operation, bounded inputs, and expiry.

### 11.3 Transactions and append-only evidence

- Draft writes, publication, retirement, and assignments use idempotency, expected revision,
  explicit transactions, audit correlation, and transactional outbox.
- Publication atomically freezes version/rules/overrides, validates effective-window uniqueness,
  advances the current reference, appends history, and records its event.
- Published rules, overrides, and history are append-only. Direct mutation/deletion and parent
  cascade deletion are refused; retirement/tombstone preserves evidence.
- Pure query operations are side-effect free. Material consumers store their own decision evidence;
  Calendar cannot become a hidden source of mutable historical truth.

### 11.4 Operations and recovery

- tzdb is a governed supply-chain dependency with version inventory, update/rollback procedure,
  compatibility/impact tests, provenance, and alerting for stale versions.
- Metrics cover evaluation latency, bounded no-result, invalid civil time, tzdb mismatch, cache hit,
  publication conflict, failed import, and tenant fairness without sensitive labels.
- Backup/restore preserves Calendar identity, published versions, rules, overrides, history,
  effective windows, content hashes, and migration state.
- Trial→paid migration freezes writes at the existing tenant-session chokepoint; copy/recovery tests
  prove identical evaluation and cross-tenant denial before/after placement change.
- Runbooks cover tzdb upgrade/regression, invalid/fold/gap results, stuck publication, cache purge,
  restore, migration, and emergency version withdrawal.

## 12. Proposed capabilities and events

### 12.1 Capabilities

- `calendar.create`, `calendar.read`, `calendar.list`;
- `calendar.draft.manage`;
- `calendar.publish`;
- `calendar.transition`;
- `calendar.evaluate`;
- `calendar.evaluate_bulk`;
- `calendar.import`, `calendar.export` — deferred unless included explicitly;
- `calendar.tzdb.manage` — platform/operator operational scope only.

Stable errors must distinguish invalid context, unauthenticated, unauthorized, missing entitlement,
disabled module, invalid/unknown/fixed-offset zone, ambiguous/nonexistent local time, interval overlap,
invalid override, published mutation, effective-version conflict, stale revision, unsupported
recurrence/import, horizon/complexity limit, unavailable tzdb version, retired calendar, and no result
within horizon—without revealing foreign Calendar existence.

### 12.2 Events

- `calendar.created.v1`;
- `calendar.version_published.v1`;
- `calendar.lifecycle_changed.v1`;
- `calendar.version_withdrawn.v1`;
- `calendar.tzdb_impact_detected.v1` — operational event, only if its contract is later accepted.

Queries do not emit domain events by default. Events use the bOPEN envelope/outbox, contain rule
identity/hash and safe metadata rather than an unbounded expansion of intervals, and support
deduplication/replay. Consumers MUST NOT treat an event as authority to reschedule or transition a
resource without their own current decision.

## 13. Proposed first implementation slice — not authorized

1. Freeze `BOPEN-CAL-001`, civil-time types, zone/tzdb policy, interval precision/splitting,
   day-override replacement semantics, version/lifecycle/effective rules, bounded query/error
   contracts, capabilities, events, retention, and evidence requirements.
2. Add `business_calendars`, `calendar_versions`, `calendar_weekly_intervals`,
   `calendar_day_overrides`, `calendar_override_intervals`, and append-only `calendar_history` with
   forced RLS, tenant-inclusive integrity, cascade protection, migration/rollback/compensation, and
   trial→paid copy ordering.
3. Implement Calendar create/read/list, draft/version editing, validation, publish, lifecycle, and
   immutable history.
4. Implement weekly intervals and one full replacement override per local date.
5. Implement `is_working_instant`, opening/closing transition, next working instant,
   elapsed-working-duration, and add-elapsed-working-duration with explicit horizon/complexity limits.
6. Bind IANA zone identifiers and runtime tzdb version; implement fold/gap policies and tzdb impact
   test fixtures. Do not accept custom zones or fixed offsets as zone IDs.
7. Add authorization/entitlement separation, RLS, idempotency, concurrency, cache isolation,
   append-only/cascade, outbox/audit, tzdb drift, invalid civil time, migration, backup/restore, and
   bounded-complexity tests.
8. Validate with **bPro operating hours** as the recommended first consumer, then bFleet depot hours.
   Do not build booking, shifts, reminders, or workflow timers in the foundation work package.
9. Submit maker evidence against an exact candidate for independent EBIV ballot and separate operator
   disposition.

Deferred: import/export, arbitrary recurrence, Calendar composition/overlays, holiday providers,
resource booking, shifts/leave/payroll, notification scheduling, timers/jobs, CalDAV, custom zones,
and non-Gregorian calendars.

## 14. Required invariants and defensive verification

| ID | Invariant | Required refusal/acceptance evidence |
| :--- | :--- | :--- |
| `CAL-INV-01` | Tenant isolation | Wrong/missing/inactive context cannot read, infer, publish, evaluate, cache, import/export, migrate, or receive events for foreign Calendars |
| `CAL-INV-02` | Independent gates | Unauthenticated, unauthorized, missing-entitlement, disabled-module, expired-grant, publication-denied, and bulk-query-denied cases fail independently |
| `CAL-INV-03` | Time-zone identity | Unknown zone, fixed-offset-only zone, custom/unapproved zone, and unavailable required tzdb version are refused |
| `CAL-INV-04` | Interval validity | Zero/negative, overlap, out-of-range, invalid precision, and unsplit/unsupported cross-midnight interval are refused |
| `CAL-INV-05` | Override precedence | One date override fully replaces weekly intervals; duplicates/conflicts/invalid dates or overlaps are refused |
| `CAL-INV-06` | Gap/fold policy | Ambiguous/nonexistent boundary without the published explicit policy is refused; selected policy yields deterministic expected instants |
| `CAL-INV-07` | Version immutability | Published rule/override/hash/effective metadata cannot be mutated; correction requires a new version |
| `CAL-INV-08` | Effective version | Overlapping published effective windows and evaluation with no eligible version are refused explicitly |
| `CAL-INV-09` | Lifecycle | Invalid transition, new current use after retirement, and unauthorized withdrawal are refused; history remains queryable under policy |
| `CAL-INV-10` | Bounded evaluation | Unbounded range/duration, excessive horizon/iterations, reversed range, and unsupported negative duration are refused loudly |
| `CAL-INV-11` | Duration truth | Elapsed timeline duration is computed across resolved instants and is never labeled payroll/nominal wall-clock hours |
| `CAL-INV-12` | tzdb drift | Version mismatch/upgrade impact is visible; runtime does not silently claim historical reproducibility without required rules/evidence |
| `CAL-INV-13` | Idempotency/concurrency | Retry duplicates no Calendar/version/history/event; stale draft/publication revision is refused |
| `CAL-INV-14` | Append-only evidence | Direct update/delete and parent cascade cannot erase published versions, overrides, content hash, or history |
| `CAL-INV-15` | Cache isolation | Cache key/result is tenant, version, tzdb/policy, operation, scope, and input bound; prior-tenant/session state cannot leak |
| `CAL-INV-16` | Recurrence refusal | RRULE/RDATE/EXDATE/custom zone/floating-time/unsupported import is refused rather than dropped or approximated |
| `CAL-INV-17` | Workflow boundary | Evaluation/event cannot grant permission, advance workflow, schedule a job, send a notification, or prove business completion |
| `CAL-INV-18` | Migration/recovery | Trial→paid, rollback/compensation, backup/restore, and cache rebuild preserve exact evaluation evidence and cross-tenant denial |

Each proposition must trace to a named executed test at an exact commit/tree. Live PostgreSQL is
required for RLS, effective uniqueness, append-only/cascade, publication concurrency, migration, and
recovery claims. Time-zone fixtures must cover at least a zone without DST, forward gap, backward
fold, rule change across tzdb fixtures, date override, and interval at local midnight. Unknown
civil-time, tzdb, cross-tenant, or bounded-search behavior keeps the exit gate closed.

## 15. Risks and unresolved decisions

| ID | Decision/risk | Recommendation before authorization |
| :--- | :--- | :--- |
| `CAL-D-01` | Reference consumer | Select bPro operating hours first; bFleet depot hours second |
| `CAL-D-02` | First query set | Include the five bounded operations in §9; define maximum range, duration, horizon, and iterations |
| `CAL-D-03` | Interval representation | Use half-open local intervals and explicit split at midnight; freeze second/minute precision |
| `CAL-D-04` | Gap/fold policy | Require explicit version policy; default fail closed until business semantics are chosen |
| `CAL-D-05` | Duration semantics | Use elapsed timeline duration; payroll/nominal wall-clock calculations remain out of scope |
| `CAL-D-06` | tzdb lifecycle | Pin runtime version, impact-test upgrades, decide retained rules/derived evidence, rollback, and stale-version alerting |
| `CAL-D-07` | Version effective windows | Define date-vs-instant boundary and publication precedence; refuse overlap in first slice |
| `CAL-D-08` | Calendar assignment | Consumers own references; decide pinned version vs effective Calendar identity without adding composition |
| `CAL-D-09` | Calendar composition | Defer tenant/site/region overlays, union/intersection, and inheritance to a separate semantics slice |
| `CAL-D-10` | Holiday sources | Tenant accepts explicit overrides; provider/feed import and legal authority are deferred |
| `CAL-D-11` | Import/export | Defer first slice or accept a narrow candidate-only subset that refuses all unsupported recurrence |
| `CAL-D-12` | Withdrawal/retirement | Define exceptional authority, effects on historical queries, assignment, cache, events, and evidence |
| `CAL-D-13` | Evaluation audit | Define which material/high-volume queries are audited and what consumers must persist |
| `CAL-D-14` | Retention/reproduction | Define retention for rules, tzdb evidence, derived intervals, audit, backups, and deletion/tombstone |

These decisions must be resolved or explicitly deferred. Implementation defaults must not silently
choose DST behavior, duration meaning, Calendar precedence, recurrence, or historical assurance.

## 16. Required successor artifacts and sequence close

Before implementation:

1. operator review of this research closes the Calendar step and the four-foundation research
   sequence without implying build authorization;
2. operator records a bounded Calendar authorization in `DEC-P4-ENTRY` or its governed successor;
3. `CAL-D-01` through `CAL-D-14` are resolved or explicitly deferred;
4. `BOPEN-CAL-001`, civil-time/tzdb ADR, API/error/event schemas, migration and
   rollback/compensation, dependency/supply-chain policy, operations runbooks, test matrix, and
   accepted work package are frozen;
5. any timer/worker, recurrence, CalDAV, composition, holiday provider, alternative chronology, or
   trust-boundary expansion receives its own authorization and ADR/baseline where required;
6. maker, eligible independent verifier, evidence paths, candidate anchors, and stop conditions are
   named.

Implementation exit requires executed acceptance/refusal tests, live RLS/concurrency/migration and
backup/restore evidence, tzdb version/upgrade/rollback evidence, repository/clean-room checks,
traceability, independent EBIV ballot, and operator disposition. Release, deployment, scheduling
runtime, and production activation remain separate.

After the Calendar advisory review, the research sequence may be described as **reviewed as advisory
planning** only if each review record actually exists and its conditions remain visible. It MUST NOT
be described as four foundations approved, authorized, implemented, confirmed, or production-ready.

## 17. Source register

Retrieved 2026-08-05. IANA listed tzdb `2026c` (released 2026-07-08) as current at retrieval. External
standards are informative requirements sources unless adopted by an approved bOPEN artifact.

| Source | Evidence class | Use in this research |
| :--- | :--- | :--- |
| [`CAPABILITY-MATRIX`](CAPABILITY-MATRIX.md) | Approved repository specification | Foundation purpose, consumers, and future shift breadth |
| [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §9 | Repository authority record | Current Calendar gate status |
| [`REVIEW-MILE-4.2-NOTIFICATION`](MILE-4.2-notification-foundation-review.md) | Advisory repository review | Sequential entry evidence only |
| [RFC 5545 — iCalendar](https://datatracker.ietf.org/doc/html/rfc5545) | IETF standard | Civil date/time, named zone, recurrence, invalid-instance, and interoperability requirements |
| [IANA Time Zone Database](https://www.iana.org/time-zones) | IANA operational standard data | Versioned civil-time rules and current release evidence |
| [RFC 8984 — JSCalendar](https://datatracker.ietf.org/doc/html/rfc8984) | IETF standard | JSON time-zone, recurrence, and override comparison; broader scope deferred |
| [RFC 4791 — CalDAV](https://datatracker.ietf.org/doc/html/rfc4791) | IETF standard | Calendar-server, synchronization, recurrence-resource, query, and free/busy comparison; excluded scope |

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
