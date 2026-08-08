# MILE-4.2 — Location foundation, research & design

**Document ID:** `RESEARCH-MILE-4.2-LOCATION`  
**Version:** `1.0.0`  
**Status:** **Research — advisory. Current sequential research slice; buildable only on separate operator authorization.** Location remains gated by [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §9.  
**Issued:** 2026-08-05  
**Owner:** Architecture & Engineering Authority  
**Raised by:** Codex (agent, advisory role) — research and planning only; no approval authority  
**Entry evidence:** The preceding Document research review was recorded at commit `6aa2d0be5cf339ebec54ff55369e147904aee214`; the operator explicitly entered Location research on 2026-08-05.  
**Governing:** `AGENTS.md` §§2, 7–15; [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md); [`CAPABILITY-MATRIX`](CAPABILITY-MATRIX.md)  
**Dependent artifacts:** Future `BOPEN-LOC-001`, accepted work package, privacy and provider ADRs, contracts, migration/rollback plan, threat model, test matrix, and EBIV evidence  
**Clean-room:** Standards and provider documentation are requirements sources only. No external schema, implementation, migration, test, or proprietary data is copied into bOPEN.

---

## 1. Executive summary

The recommended foundation is a **tenant-scoped Location Registry** that separates:

1. stable identity for a named place or site;
2. one or more versioned postal/civic address descriptions;
3. point geometry observations with explicit coordinate reference, accuracy, time, and provenance;
4. external identifiers and bounded relationships between locations.

The first slice should support reusable places, locale-aware addresses, optional WGS 84 points,
provenance, lifecycle, and a provider-neutral geocoding seam. It should **not** attempt to be a GIS,
map server, routing engine, live GPS tracker, cadastral registry, or geofence platform.

This boundary gives bFleet, Logistics/LDM, PropTech, Agriculture, Tourism, Asset, and Document a shared
place identity without moving their product-specific semantics into bOPEN. Research completion does
not authorize implementation. After this research is reviewed, Notification is the next research
slice in the recorded sequence.

## 2. Research question and method

### 2.1 Research question

What is the smallest reusable Location foundation that safely represents places, addresses, and
point coordinates across bOPEN products while preserving tenant isolation, privacy, provenance,
international address variation, provider portability, and a future path to richer geospatial
capabilities?

### 2.2 Method and evidence hierarchy

The review used, in order:

1. approved repository decisions and product/foundation boundaries;
2. ISO 19160-1's address conceptual model;
3. UPU S42 international address components and country templates;
4. IETF RFC 7946 GeoJSON for WGS 84 geometry interchange;
5. OGC JSON-FG 1.0 as a future extension seam for alternate CRS and temporal geometry;
6. architecture inference and recommendations clearly separated from those facts.

External materials are informative inputs. A future approved bOPEN contract remains authoritative.

## 3. Scope

### 3.1 In scope

- stable, immutable, tenant-owned identity for a place/site;
- tenant-scoped code, name, type vocabulary, lifecycle, and optimistic revision;
- versioned structured address components plus original and rendered address forms;
- language, script, country/template provenance, verification status, and effective interval;
- optional point geometry encoded for interchange as GeoJSON/WGS 84 longitude-latitude;
- explicit accuracy, capture method, source, observed time, and acceptance state;
- external location/provider identifiers with scheme and provenance;
- bounded, typed, effective-dated location relationships;
- provider-neutral geocode and reverse-geocode request/result contracts;
- RLS, authorization, privacy classes, idempotency, audit, events, retention, migration, and recovery;
- future extension seams for polygon/geofence and alternative CRS without implementing them now.

### 3.2 Out of scope

- routing, navigation, traffic, travel-time, distance-matrix, and dispatch optimization;
- live vehicle/device/person telemetry and tracking history;
- map tiles, cartography, general GIS editing, arbitrary spatial joins, and spatial analytics;
- polygons, geofences, lines, areas, altitude, indoor positioning, and 3D geometry in the first slice;
- legal cadastral boundaries, land title, survey authority, address certification, or jurisdictional
  adjudication;
- warehouse bins, rental units, hotel rooms, parking spaces, routes, stops, and other product-owned
  operational semantics;
- declaring an external geocoder result to be authoritative automatically;
- a global address master or cross-tenant deduplication service;
- product-specific asset movement or party-address assignment history.

### 3.3 Assumptions

- Tenant is the ownership, policy, and isolation boundary; Location has no global shared tenant data
  in the first slice.
- Party, Organization, Legal Entity, Asset, and Document may reference a Location through their own
  governed contracts. Location does not own those entities or their business relationship semantics.
- Pooled PostgreSQL with forced RLS is the first storage profile; contracts must survive future
  dedicated placement.
- First-slice geometry is a point only. A later approved ADR may add PostGIS, polygons, geofences,
  spatial indexes, alternative CRS, and topology.
- No production geocoding/map provider is selected by this research.

## 4. Current facts and architecture interpretations

| Class | Statement |
| :--- | :--- |
| Repository fact | `CAPABILITY-MATRIX` defines Location & Geography as physical sites, addresses, geofences, and GPS points, depending on Tenant and consumed by bFleet, LDM, and PropTech. |
| Repository fact | Asset currently names Location as a dependency, while the Asset research narrows first-slice use to an optional reference so Location's separate gate is preserved. |
| Repository fact | Location remains gated by `DEC-P4-ENTRY` §9; entering research is not build authorization. |
| External fact | ISO 19160-1 defines an implementation-independent address conceptual model including lifecycle, metadata, and aliases. |
| External fact | UPU S42 separates generic international address elements from country-specific templates and rendering order. |
| External fact | RFC 7946 GeoJSON uses WGS 84 and longitude-latitude coordinate order for its geometry positions. |
| External fact | OGC JSON-FG 1.0 extends GeoJSON for alternate coordinate reference systems and temporal characteristics. |
| Interpretation | Location identity cannot safely be derived from a formatted address, coordinate pair, or provider result. |
| Recommendation | Use a thin Location Registry with versioned addresses, point observations, provenance, and replaceable provider adapters. |

The approved matrix's geofence and GPS breadth remains a future capability direction. It does not
require those hard geospatial and telemetry behaviors in the first authorized slice.

## 5. Domain distinctions

| Concept | Normative proposal | Must not be confused with |
| :--- | :--- | :--- |
| `Location` | Stable tenant-owned identity for a named place/site | Address, coordinate, Tenant, Organization, Legal Entity, or Asset |
| `AddressVersion` | Effective-dated postal/civic description with components, rendering, locale, and provenance | Guaranteed unique identity, geometry, or verified legal boundary |
| `GeometryObservation` | Point plus CRS, accuracy, method, source, observed time, and acceptance state | Permanent truth, live telemetry, or ownership |
| `ExternalLocationIdentifier` | Scheme/value reference issued by a provider or external registry | bOPEN immutable Location ID |
| `LocationRelationship` | Typed, effective relation between two locations | One universally true hierarchy |
| Jurisdiction reference | Versioned external code/name observation | Tenant, legal entity, or bOPEN's legal assertion |
| Geocode candidate | Provider-produced address-to-point observation | Automatically accepted current geometry |
| Reverse-geocode candidate | Provider-produced point-to-address observation | Certified address or proof of presence |

A place can have no postal address, several historical/locale address forms, multiple entrances, or a
point with uncertain accuracy. Several places may share an address or coordinate. Therefore:

- internal Location ID MUST be immutable and never derived from mutable external data;
- formatted address MUST NOT be the uniqueness key;
- point equality MUST NOT imply place identity;
- number of decimal digits MUST NOT be treated as measured accuracy;
- a provider result MUST retain its provider, request, time, and confidence provenance.

## 6. Options and recommendation

| Option | Boundary integrity | International address fit | Privacy/control | Portability | P0 complexity | Disposition |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| Full GIS/geospatial platform in bOPEN | 2 | 5 | 2 | 3 | 1 | Reject for first slice — excessive topology/provider/operations scope |
| Free-form address and latitude/longitude in each product | 1 | 2 | 2 | 3 | 5 | Reject — duplicated identity, provenance, privacy, and formatting behavior |
| Provider-owned place ID as bOPEN identity | 1 | 3 | 2 | 1 | 4 | Reject — vendor lock-in and provider lifecycle becomes domain identity |
| Thin registry + address versions + point observations + adapters | 5 | 5 | 5 | 5 | 4 | **Recommend** |

The recommendation is intentionally reversible. It provides stable identity and contracts now while
leaving PostGIS, richer geometry, routing, and specialized providers to evidence-driven later ADRs.

## 7. Proposed model

```text
Location
  ├─ AddressVersion[]
  ├─ GeometryObservation[]
  ├─ ExternalLocationIdentifier[]
  ├─ LocationRelationship[]
  └─ LocationHistory[]

Party / Organization / Asset / Document / Product extension
  └─ governed reference or assignment ──> Location.id
```

### 7.1 `Location`

Proposed minimum fields:

- immutable `id`, `tenant_id`;
- tenant-scoped unique `code` and human `name`;
- governed `location_type` vocabulary;
- `lifecycle_state`, `revision`;
- current accepted address/point references where useful, without deleting their histories;
- `created_at`, `updated_at`, creator/updater principal and correlation metadata.

### 7.2 `AddressVersion`

Proposed information groups:

- `id`, `tenant_id`, `location_id`, version and effective interval;
- ISO country code plus structured premise, thoroughfare, locality, administrative-area, postal-code,
  delivery-service, and organization/recipient fields as supported by the chosen contract;
- original input preserved separately from normalized components and formatted output;
- language and script tags, template/profile version, source, verification status, and confidence;
- lifecycle/audit metadata and expected parent revision.

The contract SHOULD model components flexibly enough for country variation without reducing every
address to unvalidated key/value data. A country template controls rendering; it does not change the
Location identity.

### 7.3 `GeometryObservation`

Proposed minimum fields:

- `id`, `tenant_id`, `location_id`;
- point longitude and latitude, explicit `crs` fixed to `OGC:CRS84`/WGS 84 for the first slice;
- accuracy radius and its unit, capture/geocode method, provider/source, confidence;
- `observed_at`, `received_at`, acceptance state, accepted/rejected by and reason;
- provider request/result correlation without storing provider secrets.

The API representation uses GeoJSON `Point` coordinates `[longitude, latitude]`. Storage type and
numeric precision remain a contract/ADR decision. First-slice point storage MUST NOT imply support
for generic spatial query or legal survey accuracy.

### 7.4 `ExternalLocationIdentifier`

Proposed fields: scheme, value, issuer/provider, effective interval, provenance, and primary flag.
Uniqueness is tenant-scoped by governed scheme policy. Provider IDs can change or disappear without
changing `Location.id`.

### 7.5 `LocationRelationship`

Proposed first-slice relationship: effective-dated `contains` between two same-tenant locations.
Self-links, cross-tenant targets, invalid intervals, and containment cycles are refused. Broader
relationship types and multi-hierarchy semantics require later evidence and vocabulary decisions.

### 7.6 Lifecycle and candidate acceptance

```text
location: proposed -> active <-> inactive -> retired (terminal)

provider observation: received -> candidate -> accepted | rejected | superseded
```

Retirement preserves identity, address versions, observations, relationships, references, and audit.
A provider response never advances to `accepted` solely because an HTTP request succeeded.

## 8. Provider-neutral geocoding seam

```text
authorized request
  -> tenant policy + quota
  -> canonical provider request
  -> provider adapter
  -> bounded candidate response
  -> validation + provenance
  -> explicit accept/reject action
  -> history + event + audit
```

The owned adapter contract SHOULD include:

- forward and reverse operation, request ID, locale, country bias, bounded candidate count;
- normalized candidate address, WGS 84 point, confidence/quality indicators, provider identifier;
- provider terms/profile version, cache/retention constraints, rate-limit and retry classification;
- timeout, invalid/malformed response, partial response, no-result, ambiguous-result, and provider
  unavailable semantics;
- redaction, tenant-safe logging, metrics, and correlation requirements.

Provider selection, credentials, billing, residency, terms, caching rights, acceptable accuracy, and
fallback/failover require a separate ADR. A fake deterministic adapter supports contract tests; it is
not production evidence.

## 9. Security, tenancy, privacy, and operations

### 9.1 Execution and authorization chain

An authenticated **Principal** with an active **Membership** operates through server-validated
**active tenant context**. **Authorization**, **entitlement**, module availability, lifecycle, privacy
classification, and export/provider policy are separate gates. Commercial access and action
permission remain distinct.

Capabilities SHOULD separate ordinary location metadata/address reads from precise geometry,
geocoding, relationship mutation, bulk search, and export. Support access requires an explicit,
time-bounded, audited grant.

### 9.2 Tenant isolation

- Every tenant-owned table MUST carry immutable `tenant_id`, tenant-inclusive foreign keys and
  uniqueness, forced RLS, default-deny policies, and fail-closed missing context.
- Cross-tenant disclosure through direct IDs, address search, autocomplete, nearby lookup, cache,
  exports, analytics, events, logs, errors, provider callbacks, and timing/candidate counts is zero.
- All new tables MUST be registered consistently in the repository's tenant-scoped table inventory
  and trial→paid `COPY_ORDER`, with parent-before-child copy and live migration evidence.
- External provider responses MUST bind to server-held tenant/request context; an untrusted tenant ID
  in a callback or response never establishes authority.

### 9.3 Privacy and data minimization

- Address and approximate site data are tenant business data; precise geometry MAY receive a higher
  classification based on product, subject, and purpose.
- Exact home/person/device coordinates are not a default foundation use case. Products must provide
  purpose, retention, authorization, and lawful-policy decisions before such data enters scope.
- API fields, exports, cache values, events, logs, metrics, traces, and provider requests disclose
  only the precision necessary for the authorized purpose.
- The system SHOULD support derived/coarsened output without mutating the authoritative observation;
  rounding is presentation/privacy behavior, not a false claim of measurement accuracy.
- Retention, deletion/tombstone, backup, restore, provider deletion, and support-access evidence must
  be defined before production qualification.

### 9.4 Consistency and recovery

- Mutations use explicit transactions, expected revision, idempotency key, correlation ID, audit, and
  transactional outbox.
- Accepted address/geometry pointers and append-only history change atomically.
- Provider calls occur outside the database transaction through a durable job/outbox boundary;
  retries are bounded and idempotent.
- Partial provider failure cannot create an accepted observation. Recovery/reconciliation exposes
  pending, failed, and ambiguous states without silent promotion.
- Cache keys include tenant, capability/privacy scope, location/revision, query, locale, provider
  policy/version, and bounded expiry.
- Backup/restore and trial→paid placement tests prove identifiers, observations, histories, and
  external references remain resolvable after recovery/migration.

## 10. Proposed capabilities, API surface, and events

### 10.1 Capabilities

- `location.create`, `location.read`, `location.list`, `location.update`;
- `location.transition`;
- `location.address.manage`;
- `location.geometry.read_precise`, `location.geometry.manage`;
- `location.external_identifier.manage`;
- `location.relationship.manage`;
- `location.geocode.request`, `location.geocode.accept`;
- `location.export`.

The future contract must define stable error codes for invalid context, unauthorized action, privacy
denial, unsupported CRS/geometry, invalid coordinates/address, stale revision, duplicate identifier,
relationship cycle, provider unavailable/ambiguous/no-result, quota, and invalid state transition.

### 10.2 Events

- `location.registered.v1`;
- `location.updated.v1`;
- `location.lifecycle_changed.v1`;
- `location.address_changed.v1`;
- `location.geometry_observation_accepted.v1`;
- `location.external_identifier_changed.v1`;
- `location.relationship_changed.v1`.

Events use the bOPEN event envelope and transactional outbox. Precise coordinates, full sensitive
addresses, provider raw responses, and secrets MUST NOT be broadcast in a general event. Audience
contracts define safe precision and fields; consumers deduplicate by event ID and tolerate replay.

## 11. Proposed first implementation slice — not authorized

1. Freeze `BOPEN-LOC-001`, type/relationship/address vocabularies, WGS 84 point contract, privacy
   classes, lifecycle/candidate states, capabilities, API/errors, events, and provider adapter.
2. Add `locations`, `location_address_versions`, `location_geometry_observations`,
   `location_external_identifiers`, `location_relationships`, and append-only `location_history` with
   tenant-inclusive integrity, forced RLS, migration/rollback/compensation, and copy ordering.
3. Implement Location create/read/update/list and lifecycle transitions.
4. Implement address versioning with original, structured, rendered, locale, profile, effective
   interval, verification state, and provenance.
5. Implement optional point observations and explicit acceptance/rejection; GeoJSON Point is the API
   interchange form. No generic nearby/spatial query in the first slice.
6. Implement external identifiers and a constrained `contains` relationship with cycle refusal.
7. Implement a deterministic fake geocoder adapter and provider conformance suite. Select no
   production provider until its ADR is accepted.
8. Add authorization, privacy, RLS, idempotency, concurrency, outbox/audit, provider failure,
   migration, backup/restore, cache/export isolation, and append-only tests.
9. Validate against one real consumer contract. **bFleet is recommended first** because sites and
   depots exercise identity, address, point, containment, and privacy without requiring cadastral
   authority. PropTech is second and validates Document/Asset links.
10. Submit exact candidate evidence for independent EBIV review and separate operator disposition.

Deferred slices: PostGIS/spatial search, polygons/geofences, alternative CRS/JSON-FG, route/ETA,
telemetry, indoor positioning, automated provider acceptance, cadastral data, and product-specific
assignments.

## 12. Required invariants and defensive verification

| ID | Invariant | Required refusal/acceptance evidence |
| :--- | :--- | :--- |
| `LOC-INV-01` | Tenant isolation | Wrong/missing/inactive context cannot read, search, infer, export, relate, geocode, cache, or receive events for foreign locations |
| `LOC-INV-02` | Independent gates | Unauthenticated, unauthorized, missing-entitlement, disabled-module, expired-grant, and privacy-denied cases fail independently |
| `LOC-INV-03` | Immutable identity | Address, coordinate, provider ID, lifecycle, and tenant changes cannot replace/reuse Location ID |
| `LOC-INV-04` | Coordinate validity | NaN/infinity, longitude outside `[-180,180]`, latitude outside `[-90,90]`, reversed/ambiguous axis, unsupported CRS, and non-Point geometry are refused |
| `LOC-INV-05` | Accuracy/provenance | Observation missing required source/time/accuracy policy cannot become accepted current geometry |
| `LOC-INV-06` | Provider distrust | Malformed, stale, mismatched, low-confidence/ambiguous, cross-tenant, or unsolicited provider result is not silently accepted |
| `LOC-INV-07` | Address integrity | Invalid country/profile/components/effective interval and forbidden overlapping current version are refused while original input remains traceable |
| `LOC-INV-08` | Identifier integrity | Tenant-local live scheme/value collision is refused without revealing another tenant's identifier |
| `LOC-INV-09` | Relationship integrity | Cross-tenant target, self-link, duplicate live edge, invalid interval, and containment cycle are refused |
| `LOC-INV-10` | Lifecycle | Undefined transitions and reactivation after retirement are refused; history survives retirement |
| `LOC-INV-11` | Idempotency/concurrency | Retry creates no duplicate location/version/observation/event; stale expected revision is refused |
| `LOC-INV-12` | Append-only evidence | Direct update/delete and cascade deletion of accepted observation/history are refused |
| `LOC-INV-13` | Provider failure | Timeout/quota/outage/partial response cannot commit accepted data; bounded retry and reconciliation remain visible |
| `LOC-INV-14` | Privacy | Logs/errors/events/metrics/default exports omit precise or full sensitive data beyond their authorized audience |
| `LOC-INV-15` | Migration/recovery | Trial→paid copy, rollback/compensation, backup/restore, and cache rebuild preserve IDs/history and cross-tenant denial |

Each proposition must trace to a named executed test at an exact commit/tree. Live PostgreSQL is
required for RLS, foreign-key, append-only, cascade, and migration claims. Real provider behavior is
required before production provider qualification; fake adapter results prove only owned contract
logic. Unknown or untested cross-tenant behavior keeps the exit gate closed.

## 13. Risks and unresolved decisions

| ID | Decision/risk | Recommendation before authorization |
| :--- | :--- | :--- |
| `LOC-D-01` | Reference consumer | Select bFleet first; PropTech second |
| `LOC-D-02` | Initial Location type vocabulary | Keep small and product-neutral; version it rather than accept arbitrary strings |
| `LOC-D-03` | International address model | Adopt owned components informed by ISO 19160/UPU S42; prioritize Laos/Thailand profile and script tests without hard-coding one country |
| `LOC-D-04` | Point storage and precision | Decide database type/scale and prove round-trip; record accuracy separately from numeric precision |
| `LOC-D-05` | Relationship scope | First slice only `contains`; one active parent per declared hierarchy/namespace; refuse cycles |
| `LOC-D-06` | Precise-location privacy | Define classifications, field-level capabilities, coarsening, retention, export, support, and audit rules |
| `LOC-D-07` | Provider selection | Defer until ADR covers terms, residency, caching, quotas, cost, accuracy, secrets, failover, and replacement |
| `LOC-D-08` | Provider-result acceptance | Require explicit authorized acceptance; define confidence and stale-result policy |
| `LOC-D-09` | Search | Defer nearby/spatial query; decide bounded text/address search and tenant-safe indexing separately |
| `LOC-D-10` | PostGIS/geofence/alternate CRS | Later ADR and baseline; not implied by a Point field or approved capability-matrix direction |
| `LOC-D-11` | Jurisdiction references | Treat as external versioned references, not bOPEN legal truth; select code sources/profile |
| `LOC-D-12` | Deletion and referenced locations | Default to retirement/tombstone once referenced; define retention and exceptional purge authority |

## 14. Required successor artifacts and exit gates

Before implementation:

1. advisory review of this research closes without a blocking boundary defect;
2. operator records a bounded Location authorization in `DEC-P4-ENTRY` or its governed successor;
3. `LOC-D-01` through `LOC-D-12` are resolved or explicitly deferred without silent defaults;
4. `BOPEN-LOC-001`, API/error/event schemas, privacy model, provider adapter, threat model, migration
   and rollback/compensation plan, test matrix, and accepted work package are frozen;
5. any material change to storage/placement, PostGIS, trust boundary, or provider lock-in receives an
   ADR and, where required, an architecture baseline first;
6. maker, eligible independent verifier, evidence paths, candidate anchors, and stop conditions are
   named.

Implementation exit requires executed acceptance/refusal tests, live RLS/migration/recovery evidence,
provider conformance for the selected production adapter, repository/clean-room checks, traceability,
independent EBIV ballot, and operator disposition. Release and production activation remain separate.

## 15. Source register

Retrieved 2026-08-05. External standards are informative requirements sources unless a future
approved bOPEN artifact explicitly adopts a requirement.

| Source | Evidence class | Use in this research |
| :--- | :--- | :--- |
| [`CAPABILITY-MATRIX`](CAPABILITY-MATRIX.md) | Approved repository specification | Foundation purpose, dependency, and consumers |
| [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §9 | Repository authority record | Current Location gate status |
| [`REVIEW-MILE-4.2-DOCUMENT`](MILE-4.2-document-foundation-review.md) | Advisory repository review | Sequential research entry evidence only |
| [ISO 19160-1:2015 — Addressing conceptual model](https://www.iso.org/standard/61710.html) | Official standard | Address lifecycle, metadata, aliases, and implementation-independent model |
| [UPU Addressing Solutions / S42](https://www.upu.int/en/Postal-Solutions/Programmes-Services/Addressing-Solutions?cid=225&csid=20) | Official standards body guidance | International components and country-specific rendering templates |
| [RFC 7946 — GeoJSON](https://datatracker.ietf.org/doc/html/rfc7946) | IETF standard | First-slice WGS 84 Point interchange and longitude-latitude order |
| [OGC Features and Geometries JSON 1.0](https://docs.ogc.org/is/21-045r1/21-045r1.html) | OGC standard | Future alternate-CRS and temporal-geometry extension seam |

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
