# MILE-4.2 — Calendar foundation, advisory review

**Document ID:** `REVIEW-MILE-4.2-CALENDAR`
**Version:** `1.0.0`
**Status:** **Advisory review — no authorization, no build.** Calendar remains gated ([`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §9). This closes the review step for Calendar — the **last** of the operator's sequence (Document → Location → Notification → **Calendar**). Recording this review lets the four-foundation research sequence be described as *reviewed as advisory planning*; it does **not** approve, authorize, implement, or confirm any of the four.
**Issued:** 2026-08-05
**Reviewer:** Claude (agent, Motor role) — advisory only, no approval authority
**Subject:** [`RESEARCH-MILE-4.2-CALENDAR`](MILE-4.2-calendar-foundation-research.md) (authored by Codex) and [the Calendar foundation page](../05-foundation/calendar/README.md)
**Reviewer standpoint:** built and disposed the Party/Money/Workflow/UOM foundations, the Party ContactPoint extension, and the hybrid-tenancy machinery (placement, dedicated-DB provisioning, trial→paid migration, the `tenant_session` freeze), so this review focuses on cross-foundation interactions — especially with the just-disposed UOM and Workflow foundations — on the new operational surface the kernel does not yet have (a versioned external-data dependency), and on alignment with the verified patterns.

---

## 1. Overall assessment

**The most disciplined boundary of the four research slices, and correctly the narrowest — recommend
proceeding to authorization once `CAL-D-01`–`CAL-D-14` are resolved and the civil-time/tzdb ADR is
written.** The recommended shape — a **versioned Business Calendar and Working-Time evaluator**
(named IANA zone, weekly local-time intervals, full-day replacement overrides, immutable published
versions, five bounded pure queries) that is explicitly *not* a meeting calendar, booking system,
shift planner, workflow timer, reminder service, or general recurrence engine — is exactly the right
foundation, and the exclusion list (§3.2) is the strongest of the four: `RRULE`/`RDATE`/`EXDATE`,
CalDAV, attendees, free/busy, composition, and holiday-provider automation are all held out of the
first slice by name.

**The sequential process has compounded to its conclusion:** this research arrives with every prior
cross-slice finding already folded in — §11.2 requires each new table to be registered in *both* the
tenant-scoped inventory *and* the trial→paid `COPY_ORDER` with parent-before-child order; `CAL-INV-14`
refuses **parent cascade** deletion of append-only evidence (the migration-014 lesson, now proven three
times — Workflow, ContactPoint, and here); §11.4 freezes trial→paid writes "at the existing
tenant-session chokepoint" (a direct reference to the freeze built and disposed on 2026-08-05); and
`CAL-INV-17` states the Calendar-cannot-authorize boundary that mirrors Notification's truth-ladder and
the kernel's "a header cannot create authority" rule. Those arrive already handled.

## 2. The keystone is civil-time correctness under DST + reproducibility — affirm it

Calendar's equivalent of Money's currency-mismatch, UOM's dimension-safety, Location's coordinate-
validity, and Notification's truth-ladder is the pair **`CAL-INV-06` (gap/fold policy)** and
**`CAL-INV-12` (tzdb drift)**: the one property whose collapse makes the foundation dangerous is a
runtime that **silently guesses** through a daylight-saving or political time-zone change. The research
holds it firmly and fail-closed, and the two hardest, most correct stances are the ones to defend in
`BOPEN-CAL-001`:

- **A fixed offset is not a time zone** (§8.1, `CAL-INV-03`): `+07:00` is refused as a `time_zone_id`;
  only a named IANA identifier (`Asia/Vientiane`, `Asia/Bangkok`) is accepted. This is the exact mirror
  of Location's "name the axes so a caller cannot silently transpose" — the contract makes the unsafe
  input unrepresentable rather than mis-evaluated.
- **A gap or fold without an explicit published policy is refused** (`CAL-INV-06`), defaulting to
  `reject_evaluation` until a business interpretation is chosen — the same fail-closed posture the
  kernel enforces at every boundary. A later relaxed policy is a **new version**, not a runtime default
  change (§8.2). Keep a live probe for each: a nonexistent local time (spring-forward gap) and an
  ambiguous one (fall-back fold), each asserting the refusal *and* the deterministic instant once a
  policy is selected.
- **Reproducibility is fail-closed** (§8.3 point 7, `CAL-INV-12`): the runtime must **refuse to claim**
  historical reproducibility when the tzdb rules that produced a past decision are unavailable —
  `tzdb_version_at_publish` alone is not evidence if the evaluator can no longer run that version. This
  is the right hill; it is also the hardest to test, and it is what makes the tzdb dependency a
  first-class design problem rather than a footnote (see §3.2 below).

## 3. Cross-foundation and platform interactions (this review's main value)

1. **Elapsed working duration should be a UOM `time` quantity, not a parallel number+unit.**
   `working_duration_between` and `add_working_duration` (§9.4/§9.5) return an *elapsed timeline
   duration*. Duration in the **time** dimension is exactly what the just-disposed UOM foundation
   exists for. Recommend the duration cross the boundary as a UOM `Quantity` in a known time unit
   (seconds/hours), computed as **exact `Decimal` over the instant timeline, never a float** (the
   Money/UOM never-float discipline — `CAL-INV-11`'s "elapsed timeline duration" is naturally exact
   seconds, so store/compute it exactly). This is the same "let a foundation *consume* another" chance
   the Location review raised for its accuracy radius, and it keeps Calendar from growing a second,
   unvalidated duration vocabulary. Caveat worth stating in the ADR: a UOM time quantity is a pure
   elapsed count — it is explicitly **not** payroll/nominal wall-clock hours (`CAL-INV-11`), and a
   consumer must not reuse it as such.

2. **The tzdb is the kernel's first versioned external-data dependency — the biggest new surface, and
   it is greenfield.** Everything in the kernel today is self-contained; there is no pinned, impact-
   tested, retained external ruleset. `CAL-INV-12` and §8.3/§11.4 are correct and necessary, but they
   are **new operational infrastructure**, not a variation on an existing pattern: pinning and reporting
   the runtime tzdb version, comparing resolved intervals before/after an upgrade, identifying affected
   versions/consumers within a bounded horizon, and **retaining enough old rules or derived interval
   snapshots to reproduce past decisions**. This is Calendar's equivalent of Notification's worker/queue
   — it deserves its own **civil-time/tzdb supply-chain ADR** (version inventory, update/rollback,
   impact tests, retention horizon, stale-version alerting), and the first-slice estimate must reflect
   that it builds a governed dependency, not just tables and queries.

3. **Six new tenant-scoped tables → the two-place registration + the three-times-proven cascade
   rule.** `business_calendars`, `calendar_versions`, `calendar_weekly_intervals`,
   `calendar_day_overrides`, `calendar_override_intervals`, and append-only `calendar_history` all go in
   `TENANT_SCOPED_TABLES` and the migrate tool's `COPY_ORDER` (parents before children:
   `business_calendars` → `calendar_versions` → weekly/overrides → `calendar_override_intervals` →
   `calendar_history`). `INV-MIGRATE-COVERAGE-01` will enforce it, and the `tenant_session` freeze
   covers Calendar writes for free. `CAL-INV-14`'s "parent cascade cannot erase published
   versions/overrides/history" must be built with **`ON DELETE RESTRICT`** on the durable referents
   (history→version, override_intervals→day_override, day_override→version), exactly as Workflow's
   migration 014 and ContactPoint's migration 019 did — an append-only table with SELECT+INSERT-only
   RLS is *still* erasable via a parent FK with `ON DELETE CASCADE` because PostgreSQL performs FK
   actions past row security. This is now a settled pattern; name it in `BOPEN-CAL-001` so `CAL-INV-14`
   tests a real parent-delete, not only a direct UPDATE/DELETE.

4. **"Overlapping published effective windows are refused" (`CAL-INV-08`) needs a real mechanism, not
   an application check.** Refusing two published versions whose effective intervals overlap is a
   range-overlap constraint a row-level `CHECK` cannot see across rows — the same shape as the Location
   review's containment-cycle finding and ContactPoint's one-live-primary partial index. The natural
   mechanism is a PostgreSQL **`EXCLUDE` constraint over a `tstzrange` with GiST** (scoped by
   `tenant_id, calendar_id`), so the database refuses an overlapping effective window atomically under
   concurrency. Name the mechanism so `CAL-INV-08` tests a genuine concurrent overlap, not just a
   sequential app-level guard.

5. **Publication events belong on the audit/lifecycle envelope, not `usage_outbox`.** §11.3/§12.2 route
   `calendar.version_published.v1` and friends through the bOPEN envelope/outbox. As the Notification
   review noted, the kernel's `usage_outbox` (migration 002) is metering-shaped and the audit trail is
   append-only history; Calendar's domain events should reuse the **Workflow lifecycle-event/audit
   envelope** pattern (rule identity + content hash + safe metadata, *not* an unbounded expansion of
   intervals), and queries correctly emit **no** event by default (§12.2). Consistent; just confirm it
   binds to the established envelope rather than inventing a parallel one.

## 4. Minor notes

- **`bPro` operating hours as the first consumer (`CAL-D-01`)** is the right early pick, and
  `Asia/Vientiane`/`Asia/Bangkok` as the first zone continues the Thai/Lao locale thread the UOM Thai
  land units and Location's Thai address profile already set — good continuity, and it exercises a real
  DST-free zone plus a nearby DST zone for the fixtures (§14).
- **Half-open intervals `[start, end)` and explicit cross-midnight split (`CAL-D-03`)** are correct —
  half-open avoids double-counting adjacent windows (the same discipline used elsewhere), and an
  explicit split keeps overlap validation and query logic visible rather than hiding a wrap.
- **The import seam refuses unsupported recurrence rather than approximating it (`CAL-INV-16`, §10)** is
  the right "defer, don't half-build" stance — the mirror of UOM refusing affine units loudly and
  Location treating a geocoder result as a candidate requiring acceptance. Parsing into a *candidate*
  that returns unsupported constructs, never silently dropping them, is exactly right.
- **Retirement is a tombstone that preserves versions/history (§7.1, `CAL-INV-09`)** — the same
  retire-not-delete rule ContactPoint used; consumers must define whether historical evaluation against
  a retired explicit version stays allowed (`CAL-D-12`), which is the correct open question to force.

## 5. Recommendation and what remains before any build

The design is ready to move toward a first slice **after**: the operator resolves `CAL-D-01`–`CAL-D-14`
without silent defaults (especially `CAL-D-04` gap/fold policy, `CAL-D-06` tzdb lifecycle/retention,
and `CAL-D-07` effective-window precedence); the build plan adopts §3 above (UOM time quantity for
duration, the `ON DELETE RESTRICT` cascade rule, the `EXCLUDE`/`tstzrange` overlap mechanism, the
audit-envelope events, the two-place table registration); the new **civil-time/tzdb supply-chain ADR**
is written; and the successor artifacts (a `DEC-P4-ENTRY` bounded authorization recorded **before** any
build, `BOPEN-CAL-001`, API/error/event schemas, migration/rollback/compensation, dependency policy,
operations runbooks, and the test matrix — including the §14 fixtures: a no-DST zone, a forward gap, a
backward fold, a rule change across tzdb fixtures, a date override, and an interval at local midnight)
are frozen, as for Money/Workflow/UOM/ContactPoint.

This review authorizes nothing and builds nothing. **Sequence close:** with this record, the four
research foundations (Document, Location, Notification, Calendar) are **reviewed as advisory planning**
— each review record now exists and its conditions remain visible. This is explicitly **not** four
foundations approved, authorized, implemented, confirmed, or production-ready; every one remains gated
and enters build only on its own recorded operator authorization. This close covers **only** the four
sequenced foundations; the separately-tracked **Asset** research is not part of this sequence, and its
open Medium strict-checker finding stands — the combined documentation bundle is **not** asserted to
pass strict in full.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
