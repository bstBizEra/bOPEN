# EVD-LOCATION-MAKER — Location foundation

**Document ID:** `EVD-LOCATION-MAKER`
**Version:** `1.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision
**Issued:** 2026-08-05
**Implements:** [`DEC-P4-ENTRY`](../../decisions/DEC-P4-ENTRY.md) §11 (authorized); [`RESEARCH-MILE-4.2-LOCATION`](../../01-product/MILE-4.2-location-foundation-research.md)
**Candidate:** `1cde994`
**Blob — `020_location_foundation.sql`:** `9942d7abd5f337146cd4d6f72b25930490347b18`
**Blob — `location_repositories.py`:** `21d978bedd4a6b5fc42e03839ee401bb2f60b37c`
**Blob — `test_location_isolation.py`:** `83f249d2b2a334ab11cb1dd0cce345f2db5c9fef`
**Blob — `test_location_http.py`:** `788870d48c8c66bc4a7cd4f37122af65832c3885`
**Blob — `invariant-traceability.csv`:** `d3b59409cc7c2fe16e5991bd12ea4dbbc3773ca1`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifier:** Codex
**Suites:** canonical **649/649** against PostgreSQL

---

## 1. What this is — and the properties it defends

The Location foundation (`BOPEN-LOC-001`): a tenant-scoped Location Registry that separates a **stable,
immutable place identity** from its versioned addresses, its point geometry observations, its external
identifiers, and a bounded `contains` relationship. Identity is never derived from a formatted address,
a coordinate, or a provider id (`LOC-INV-03`).

Two keystones:

- **Coordinate validity (`LOC-INV-04`)** — a NaN/∞, an out-of-range longitude/latitude, or a
  non-`OGC:CRS84` CRS is **refused**. Enforced twice: `chk_geo_lon`/`chk_geo_lat` at the database (which
  also reject NaN, ordered above every number) and a repository `_coordinate` screen before the insert.
  The API names the fields **`longitude`/`latitude`** (never a bare `[a,b]`) so a caller cannot silently
  transpose the axes.
- **Provider distrust (`LOC-INV-05`/`06`)** — a geometry observation is born a **`candidate`**;
  `accept` is a distinct authorized action that requires an explicit actor **and** the provenance an
  accepted point must carry (source, observed_at, confidence). **"HTTP 200 does not mean accepted."**
  No create path mints an accepted observation.

**Clean-room (`AGENTS.md` §6):** independently implemented from the settled registry model (identity +
versioned address + point observation + provenance + bounded relations), informed by ISO 19160-1 /
UPU S42 / RFC 7946, adopted from no upstream schema.

## 2. Defensive verification

Every proposition asserts the registry **refuses** an unsafe operation — a cross-tenant insert; a
child (address/geometry/relationship) attached to another tenant's location; an out-of-range or NaN
coordinate; a self-link; a **containment cycle**; a duplicate live edge; a second live parent; a second
current address version; a live scheme/value identifier collision; an UPDATE/DELETE of append-only
history; a delete that would erase that history; an undefined lifecycle transition; and the acceptance
of an observation that lacks an actor or provenance — and **admits** the valid case exactly (a
candidate with an actor and full provenance is accepted and becomes the location's current geometry).

## 3. Propositions (traced in `invariant-traceability.csv`)

**Group A — database isolation & integrity** (`tests/isolation/test_location_isolation.py`, executed Python):

| ID | The registry must… | Test |
| :--- | :--- | :--- |
| `LOC-INV-ISOLATION-01` | keep a location invisible to another tenant | `test_a_location_created_in_one_tenant_is_invisible_to_another` |
| `LOC-INV-XTENANT-INSERT-01` | refuse a cross-tenant insert | `test_a_cross_tenant_location_insert_is_refused` |
| `LOC-INV-XTENANT-ADDR-01` | refuse an address on another tenant's location | `test_an_address_version_cannot_attach_to_another_tenants_location` |
| `LOC-INV-XTENANT-GEO-01` | refuse geometry on another tenant's location | `test_a_geometry_observation_cannot_attach_to_another_tenants_location` |
| `LOC-INV-XTENANT-REL-01` | refuse a relationship to another tenant's location | `test_a_relationship_cannot_target_another_tenants_location` |
| `LOC-INV-COORD-LON-01` | refuse an out-of-range longitude | `test_out_of_range_longitude_is_refused` |
| `LOC-INV-COORD-LAT-01` | refuse an out-of-range latitude | `test_out_of_range_latitude_is_refused` |
| `LOC-INV-COORD-NAN-01` | refuse a NaN coordinate | `test_nan_coordinate_is_refused` |
| `LOC-INV-REL-SELF-01` | refuse a self-containment link | `test_a_self_link_is_refused` |
| `LOC-INV-REL-CYCLE-01` | **refuse a containment cycle (keystone)** | `test_a_containment_cycle_is_refused` |
| `LOC-INV-REL-DUP-01` | refuse a duplicate live edge | `test_a_duplicate_live_edge_is_refused` |
| `LOC-INV-REL-PARENT-01` | refuse a second active parent | `test_a_second_active_parent_is_refused` |
| `LOC-INV-ADDR-CURRENT-01` | keep at most one current address version | `test_at_most_one_current_address_version_per_location` |
| `LOC-INV-EXTID-COLLISION-01` | refuse a live scheme/value collision | `test_a_live_scheme_value_collision_is_refused` |
| `LOC-INV-APPEND-ONLY-01` | refuse UPDATE/DELETE of history | `test_recorded_history_cannot_be_updated_or_deleted` |
| `LOC-INV-APPEND-CASCADE-01` | keep history when its location is delete-attempted | `test_recorded_history_survives_an_attempt_to_delete_its_location` |
| `LOC-INV-PARENT-RESTRICT-01` | refuse deleting a location with children | `test_a_location_with_children_cannot_be_deleted` |
| `LOC-INV-IDENTITY-01` | keep the same id across a lifecycle change | `test_a_lifecycle_change_keeps_the_same_id` |

**Group B — HTTP** (`tests/integration/test_location_http.py`, executed HTTP, bearer-gated):

| ID | The kernel must… | Test |
| :--- | :--- | :--- |
| `LOC-INV-HTTP-CRUD-01` | support create/read/list/update | `test_create_read_list_update_a_location` |
| `LOC-INV-HTTP-DUPCODE-01` | refuse a duplicate code (409) | `test_a_duplicate_code_is_refused` |
| `LOC-INV-HTTP-LIFECYCLE-01` | allow a defined transition, refuse an undefined one | `test_lifecycle_transition_and_invalid_transition_refused` |
| `LOC-INV-HTTP-ADDR-01` | keep one current version across add/set-current | `test_address_versioning_and_set_current` |
| `LOC-INV-HTTP-CANDIDATE-01` | leave an observed point a candidate, not accepted **(keystone)** | `test_observe_starts_candidate_and_is_not_accepted` |
| `LOC-INV-HTTP-ACCEPT-PROV-01` | refuse accepting without provenance **(keystone)** | `test_accept_without_provenance_is_refused` |
| `LOC-INV-HTTP-ACCEPT-01` | accept a provenanced candidate and update the current pointer | `test_accept_with_provenance_succeeds_and_updates_current_pointer` |
| `LOC-INV-HTTP-COORD-01` | refuse an out-of-range coordinate (422) **(keystone)** | `test_out_of_range_coordinate_is_422` |
| `LOC-INV-HTTP-UOM-01` | require the accuracy radius to be a UOM length unit | `test_accuracy_radius_length_unit` |
| `LOC-INV-HTTP-EXTID-01` | refuse a live identifier collision (409) | `test_external_identifier_live_collision_is_409` |
| `LOC-INV-HTTP-CYCLE-01` | refuse a containment cycle | `test_relationship_cycle_is_refused` |
| `LOC-INV-HTTP-BEARER-01` | require a bearer to create (401) | `test_creating_a_location_requires_a_bearer` |
| `LOC-INV-HTTP-REDACT-01` | never put coordinates in an audit record | `test_precise_coordinates_never_appear_in_an_audit_record` |

**Attack angle for the verifier (defensive framing).** Confirm each refusal holds and the one
admission is exact:
- Post a longitude of `200`, a latitude of `95`, and a `NaN` → confirm each is **refused** at both the
  database CHECK and the repository screen (`LOC-INV-COORD-*`).
- Build `A contains B`, `B contains C`, then request `C contains A` → confirm the `WITH RECURSIVE`
  walk **refuses** it as a cycle; confirm `A contains A` is refused; confirm a second live parent for a
  child is refused (`LOC-INV-REL-CYCLE-01`/`SELF-01`/`PARENT-01`).
- `observe` a point, read it → confirm it is **`candidate`**, not accepted; `accept` it while it is
  missing source/observed_at/confidence → confirm **refused**; supply an actor + full provenance →
  confirm it becomes **`accepted`** and the location's `current_geometry_observation_id` now points to
  it (`LOC-INV-HTTP-CANDIDATE-01`/`ACCEPT-PROV-01`/`ACCEPT-01`).
- Give an accuracy radius with unit `kg` → confirm **refused** (a length unit is required); with `m` →
  confirm admitted, magnitude an exact `Decimal` (`LOC-INV-HTTP-UOM-01`).
- Record a location event, then attempt to delete its location → confirm **refused** and the history
  survives (`LOC-INV-APPEND-CASCADE-01`); UPDATE/DELETE the history row directly → confirm **refused**
  (`LOC-INV-APPEND-ONLY-01`).
- Accept a geometry observation, then read the audit trail → confirm **no longitude/latitude** appears
  (`LOC-INV-HTTP-REDACT-01`).

## 4. Execution

```text
python tools/run_tests.py     649/649 OK   (live PostgreSQL)
```

- Migration 020 adds the six tables with forced RLS, composite `(tenant_id, parent_id)` FKs
  `ON DELETE RESTRICT` (a location with any child cannot be deleted — retire it; the migration-014
  cascade lesson applied in advance so a parent delete cannot erase append-only history), coordinate
  CHECKs, `OGC:CRS84` CHECK, and the four partial unique indexes (one current address, one live
  identifier, one live edge, one active parent).
- `location_repositories.py` — every method through `db.tenant_session`; the two keystones (provider
  distrust and containment acyclicity) live here because the database cannot see them. Accuracy radius
  is validated as a UOM `length` unit through the tenant's UOM registry (standard + custom), letting a
  foundation **consume** another; a non-length or unknown unit is refused and the magnitude is an exact
  `Decimal`.
- Bearer-gated endpoints for locations (CRUD + lifecycle), address versions (+ set-current), geometry
  observations (+ accept/reject), external identifiers, and relationships. Coordinates are redacted
  from every audit record and never written to `location_history`.
- **Cross-slice, enforced by a control:** all six tables were added to `TENANT_SCOPED_TABLES` and the
  trial→paid `COPY_ORDER` (parents before children). `INV-MIGRATE-COVERAGE-01` and the trial→paid
  round-trip pass with the six tables copied — otherwise a migration would silently strand a tenant's
  locations, addresses, geometry, and history.

## 5. What this does NOT establish (disclosed)

1. **No production geocoding provider (`LOC-D-07`).** The provider-distrust discipline is proven at the
   observation level (candidate → explicit accept with provenance); the live `geocode.request` HTTP
   adapter and any real provider ship with the provider ADR. The first slice is the owned registry.
2. **Point geometry only.** No polygon/geofence, PostGIS, alternative CRS, or spatial/nearby/autocomplete
   search (`LOC-D-09`/`10`) — deferred so no field becomes a cross-tenant existence oracle.
3. **Containment-cycle check is transactional, not serialized.** The `WITH RECURSIVE` walk and the
   insert run in one transaction, and the one-active-parent index keeps the graph a forest; but under
   `READ COMMITTED` two concurrent inserts could each pass the check and together form a cycle. A
   `SELECT … FOR UPDATE` lock on the involved locations or `SERIALIZABLE` isolation would close that
   window — a tracked refinement, disclosed.
4. **Address components are owned and flexible, not certified.** No postal-authority validation or
   address certification; `original_input` is preserved separately from normalized/rendered forms.
5. **Retire, not delete.** A referenced location is retired (tombstone); its address versions, geometry,
   identifiers, relationships, and history are preserved (`LOC-D-12`).
6. **One verifier, not two** (two-agent profile). This maker submission carries no verdict weight.

## 6. Authority

A maker's submission. `EBIV` §8: a passing suite carries no verdict weight.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
