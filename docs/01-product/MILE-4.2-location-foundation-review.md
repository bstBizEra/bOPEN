# MILE-4.2 — Location foundation, advisory review

**Document ID:** `REVIEW-MILE-4.2-LOCATION`
**Version:** `1.0.0`
**Status:** **Advisory review — no authorization, no build.** Location remains gated ([`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §9). This closes the review step for Location in the operator's sequence (Document → **Location** → Notification → Calendar); Notification's research enters next.
**Issued:** 2026-08-05
**Reviewer:** Claude (agent, Motor role) — advisory only, no approval authority
**Subject:** [`RESEARCH-MILE-4.2-LOCATION`](MILE-4.2-location-foundation-research.md) (authored by Codex) and [the Location foundation page](../05-foundation/location/README.md)
**Reviewer standpoint:** built and disposed the Party/Money/Workflow/UOM foundations and the hybrid-tenancy machinery (placement, dedicated-DB provisioning, trial→paid migration), so this review focuses on alignment with those verified patterns and on cross-foundation interactions — especially with the just-disposed UOM foundation.

---

## 1. Overall assessment

**Sound, well-bounded, and notably more mature than the Document research on the cross-slice front —
recommend proceeding to authorization once the LOC-D decisions are made.** The recommended shape — a
thin, tenant-scoped Location Registry separating stable identity, versioned addresses, point
`GeometryObservation`s (with provenance), external identifiers and bounded relationships, behind a
provider-neutral geocoding adapter — is the right foundation. The boundary is disciplined (no GIS,
PostGIS, routing, telemetry, geofence, or cadastral authority in the first slice), matching how Money
and UOM were scoped.

**The sequential process is visibly working:** this research already folded in the three cross-slice
obligations the Document review raised — §9.2 requires every new table to be registered in *both* the
tenant-scoped inventory *and* the trial→paid `COPY_ORDER`; `LOC-INV-12` refuses **cascade** deletion of
append-only history (the migration-014 lesson); and `LOC-INV-15`/§9.4 require trial→paid + backup
evidence that identifiers/history/references stay resolvable. Those were the review's main Document
findings, and they arrived pre-addressed here. Good.

## 2. Alignment and strengths

- **Identity is not derived from mutable data** (`LOC-INV-03`, §5): the internal Location ID is
  immutable and never a formatted address, coordinate, or provider ID. This is the same discipline
  Document applied to `Document` vs content, and it is correct.
- **Provider distrust is explicit** (`LOC-INV-06`, §8): a geocoder result is a *candidate* requiring
  authorized acceptance; "HTTP 200 does not mean accepted" is exactly the fail-closed posture the
  kernel enforces elsewhere, and the mirror of Document's scanner-outage-fails-closed rule.
- **Provenance separated from precision** (§5): "number of decimal digits MUST NOT be treated as
  measured accuracy" — a genuinely important distinction, and it protects against the classic
  false-accuracy bug.
- **The refusal matrix (§12)** is strong and maps to EBIV R2/R4/R5; `LOC-INV-04` (coordinate validity)
  is the right keystone (see §3 below).

## 3. Coordinate validity is the keystone — affirm it, and one footgun

`LOC-INV-04` is Location's equivalent of Money's currency-mismatch and UOM's dimension-safety: the one
property whose absence makes the foundation dangerous. Two points to keep sharp in `BOPEN-LOC-001`:

- **The reversed-axis case is the real-world trap.** RFC 7946 mandates `[longitude, latitude]`, but
  humans, GPS devices and many APIs say *lat, lon*. A swapped pair often *passes* range checks (e.g.
  Bangkok `13.7, 100.5` reversed to `100.5, 13.7` — longitude 100.5 is valid, latitude 13.7 is valid,
  so both orderings validate individually). Range validation alone will not catch a transposition. The
  contract should make the axis order unambiguous at the boundary (name the fields `longitude`/
  `latitude`, not a bare `[a, b]`) so a caller cannot silently transpose. This is worth an explicit
  test beyond the range check.

## 4. Cross-foundation interactions to fold into the build plan (this review's main value)

1. **Accuracy radius should use the UOM foundation, not a parallel unit field.** `GeometryObservation`
   carries "accuracy radius and its unit" (§7.3). An accuracy radius is a **length** — exactly what
   the just-disposed UOM foundation exists for. Recommend the accuracy unit be a **known UOM length
   unit** (`m`, `km`), validated through `platform_kernel/uom.py`, rather than a free-form string.
   Otherwise Location grows a second, unvalidated unit vocabulary that can drift from UOM (someone
   writes `meters` vs `metre` vs `m`). This is the first real chance to let a foundation *consume*
   another; the accuracy magnitude is then a `Quantity`, dimension-safe by construction.

2. **Store coordinates as exact decimal, never float — the Money/UOM discipline (`LOC-D-04`).** A
   longitude/latitude in binary `float` drifts the way `0.1 + 0.2` does; round-tripping a stored point
   must return the same value. Store as `NUMERIC` (e.g. `NUMERIC(9,6)` ≈ 0.11 m at the equator, or
   more) and keep the magnitude a `Decimal` end to end, exactly as Money bans float and UOM uses
   `Decimal`. Record accuracy separately from numeric precision (the research already says this — good;
   this just names the storage type to make `LOC-INV-04`'s round-trip testable).

3. **Containment cycle refusal (`LOC-INV-09`) needs a real mechanism, not just a self-link CHECK.**
   Party relationships only had to refuse *self*-links and *cross-tenant* endpoints (a composite FK +
   a CHECK). A `contains` **hierarchy** additionally has to refuse a *cycle* (`A contains B contains
   A`, or longer), which a row-level CHECK cannot see. This wants a recursive check (a `WITH RECURSIVE`
   walk on insert, or an application-level ancestor check in the same transaction) plus "one active
   parent per hierarchy". Name the mechanism in `BOPEN-LOC-001` so `LOC-INV-09` tests a real cycle,
   not just a self-link.

4. **Six new tenant-scoped tables → the two-place registration the research already names (§9.2).**
   `locations`, `location_address_versions`, `location_geometry_observations`,
   `location_external_identifiers`, `location_relationships`, `location_history` all go in
   `TENANT_SCOPED_TABLES` and the migrate tool's `COPY_ORDER` (parents before children:
   `locations` → the rest → `location_history`). The research names this; I confirm the control
   (`INV-MIGRATE-COVERAGE-01`) will enforce it, and the freeze covers Location writes for free.

## 5. Minor notes

- **Thai/Lao address profile (`LOC-D-03`)** is the right early priority — it pairs with the UOM Thai
  land units and the PropTech reference consumer, and script/locale handling is easy to get wrong late.
- **Point equality ≠ place identity** (§5) is correctly stated; make sure autocomplete/search (deferred)
  never becomes a cross-tenant existence oracle (`LOC-INV-01`), the same trap the placement seam's
  mis-route guard addresses.
- **`OGC:CRS84` fixed for the first slice** is the right call; JSON-FG as a *future* seam (not
  implemented) matches the "defer, don't half-build" discipline.

## 6. Recommendation and what remains before any build

The design is ready to move toward a first slice **after**: the operator resolves `LOC-D-01`–`LOC-D-12`
(reference consumer, address model, point storage/precision, relationship scope, privacy
classification, provider ADR, search, deletion) without silent defaults; the build plan adopts §4
above (UOM for accuracy, decimal coordinates, a real cycle mechanism, the two-place table
registration); and the successor artifacts (a `DEC-P4-ENTRY` gate amendment, `BOPEN-LOC-001`, privacy
and provider ADRs, threat model, migration/rollback plan, test matrix) are frozen with authorization
recorded **before** any build, as for Money/Workflow/UOM.

This review authorizes nothing and builds nothing. Location remains gated; Notification's research is
the next step in the operator's sequence.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
