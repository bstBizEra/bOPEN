# MILE-4.2 — Asset foundation, research & design

**Document ID:** `RESEARCH-MILE-4.2-ASSET`  
**Version:** `1.0.0`  
**Status:** **Research — advisory. A future slice; buildable only on operator authorization.** Asset remains gated by [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §9.  
**Issued:** 2026-08-05  
**Owner:** Architecture & Engineering Authority  
**Raised by:** Codex (agent, advisory role) — research and planning only; no approval authority  
**Governing:** `AGENTS.md` §§2, 7–12, 20.2; [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md); [`CAPABILITY-MATRIX`](CAPABILITY-MATRIX.md)  
**Dependent artifacts:** Future `BOPEN-ASSET-001`, accepted Asset work package, contracts, threat model, test matrix, and EBIV evidence  
**Clean-room:** External standards and products below are requirements sources only. No upstream code, schema, migration, or tests are copied into bOPEN.

---

## 1. Executive summary

The recommended bOPEN Asset foundation is a **thin, tenant-scoped Asset Registry with extension
contracts**. It provides one stable identity and generic lifecycle for physical, digital, and hybrid
assets shared by bFleet, PropTech, and bERP integrations. It does **not** become a full enterprise
asset-management, accounting, inventory, maintenance, fleet, or property system.

This boundary prevents two opposite failures:

1. every product inventing an incompatible asset identity and lifecycle; and
2. bOPEN absorbing product and ERP semantics that belong outside the platform foundation.

The first implementation slice should be pulled by one reference consumer. **bFleet is the
recommended first validation consumer** because it exercises identity, custody, movement references,
and component relationships without requiring bOPEN to own accounting. PropTech is the recommended
second consumer. bERP should treat ERPNext as the source of truth for financial fixed-asset behavior
and link it to the bOPEN asset identity through versioned APIs and events.

This document records research and a proposed plan. It grants no implementation, merge, release,
deployment, production, or gate authority.

## 2. Research question and scope

### 2.1 Research question

What is the smallest reusable Asset foundation that gives bOPEN products a common asset identity,
classification, lifecycle, and relationship surface without importing ERP, fleet, property, or
maintenance semantics into the platform kernel?

### 2.2 In scope

- tenant-scoped asset instance identity and human-readable asset code;
- asset class/type reference;
- physical, digital, or hybrid asset nature;
- multiple identifiers and identifier schemes, including external-system identifiers;
- generic lifecycle state and explicitly authorized transitions;
- effective-dated party roles such as owner, custodian, and operator;
- append-only lifecycle and assignment history;
- domain events and correlated audit records;
- optional future references to Location and Document foundations;
- tenant isolation, authorization, concurrency, idempotency, retention, and evidence controls;
- extension seams for product-owned attributes and relationships.

### 2.3 Out of scope

- general ledger, capitalization, book value, depreciation, revaluation, tax, sale proceeds, and
  other financial fixed-asset accounting;
- preventive maintenance, repair, service schedules, work orders, parts, and downtime management;
- stock quantities, warehouses, batches, serial-stock rules, and inventory valuation;
- vehicle telemetry, mileage, fuel, driver, route, and regulatory fleet semantics;
- cadastral parcels, title, appraisal, lease, occupancy, and property valuation semantics;
- insurance policy, claim, coverage, and loss-adjustment semantics;
- product-specific lifecycle states such as `under_maintenance`, `leased`, or `awaiting_appraisal`;
- binary document storage, address/geospatial implementation, workflow orchestration, and
  notifications themselves;
- BPMN, timers, branching, or automation behavior;
- any implementation before a separate operator authorization.

### 2.4 Assumptions

- Tenant remains the commercial, policy, security, and isolation boundary.
- Party represents real-world persons and organizations; Principal remains the actor/authentication
  concept. Asset ownership therefore references Party, not Principal.
- Workflow may orchestrate an approved asset transition but cannot override the Asset foundation's
  lifecycle invariants or authorization decision.
- Asset data will begin in pooled PostgreSQL storage with tenant ownership and forced RLS, while
  preserving contracts that can survive hybrid placement.
- A product may extend an asset, but it must not redefine or reuse the foundation's immutable asset
  identity.

## 3. Facts, interpretations, and recommendation

| Class | Statement |
| :--- | :--- |
| **Repository fact** | `CAPABILITY-MATRIX` defines Asset Baseline as generic physical/digital asset lifecycle tracking, with bFleet, PropTech, and bERP as primary consumers. |
| **Repository fact** | `DEC-P4-ENTRY` §9 leaves Asset gated; UOM authorization does not authorize Asset. |
| **External fact** | ISO 55000/55001 describe asset management across the lifecycle and balance value, performance, risk, and expenditure. |
| **External fact** | GS1 provides distinct keys for individual assets (GIAI) and returnable assets (GRAI), supporting identifier schemes rather than a single overloaded serial field. |
| **External fact** | The Asset Administration Shell metamodel separates globally unique asset identity from specific identifiers and distinguishes asset type from asset instance. |
| **External fact** | ERPNext Asset combines purchase, depreciation, maintenance, movement, sale, and scrapping. |
| **Architecture interpretation** | Those ERP functions demonstrate why bOPEN should expose an integration identity and generic lifecycle, not duplicate ERPNext's financial and operational asset module. |
| **Recommendation** | Adopt a thin Asset Registry plus product extension contracts, pulled first by a reference product. |

## 4. Boundary decision matrix

| Option | Boundary integrity | Reuse | ERP/product overlap | P0 complexity | Reversibility | Disposition |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| Full EAM/fixed-asset suite in bOPEN | 1 | 5 | 1 | 1 | 2 | **Reject** — duplicates ERPNext and absorbs industry behavior |
| Separate asset model in every product | 2 | 1 | 3 | 4 | 2 | **Reject** — identity, lifecycle, and integrations drift |
| Thin Asset Registry + extension contracts | 5 | 5 | 5 | 4 | 5 | **Recommend** — shared identity with bounded semantics |

Scores are directional (1 weak, 5 strong) and support the boundary judgment; they do not replace an
operator decision.

## 5. Domain distinctions

| Concept | Meaning | Must not be confused with |
| :--- | :--- | :--- |
| `AssetClass` | Reusable classification/model describing a kind of asset | Product SKU, inventory item, or one asset instance |
| `Asset` | One tenant-owned, trackable physical/digital/hybrid instance | Authorization `Resource`, accounting ledger entry, or stock quantity |
| `AssetIdentifier` | Scheme-qualified identifier for resolving the asset | The immutable internal asset ID |
| `AssetPartyAssignment` | Effective-dated Party relationship such as owner/custodian/operator | Principal membership, role grant, or authorization permission |
| `AssetLifecycleHistory` | Append-only record of accepted lifecycle changes | Mutable current-state column or general audit log |
| Financial fixed asset | ERP/accounting representation used for capitalization and depreciation | bOPEN Asset identity |
| Product extension | Product-owned data keyed by `asset_id` | A second competing asset master |

An asset may have a bOPEN internal ID, tenant asset code, manufacturer serial number, VIN, GIAI,
GRAI, and ERPNext ID simultaneously. The internal ID remains immutable; identifiers are stored as
scheme/value records with provenance and lifecycle rather than overloaded into one field.

## 6. Proposed core model

```text
AssetClass
  └─ Asset instance
      ├─ AssetIdentifier[]
      ├─ AssetPartyAssignment[]
      └─ AssetLifecycleHistory[]

Product extension ── asset_id ──> Asset
Optional Location/Document references ──> Asset
ERPNext fixed asset ── external identifier/event ──> Asset
```

### 6.1 `AssetClass`

Minimum proposed fields: `id`, `tenant_id`, `code`, `name`, `asset_nature`, `status`, `revision`,
`created_at`, `updated_at`. A class describes a reusable kind; it is not a tenant-independent global
taxonomy in the first slice.

### 6.2 `Asset`

Minimum proposed fields: `id`, `tenant_id`, `asset_class_id`, `asset_code`, `name`,
`lifecycle_state`, `revision`, `registered_at`, `retired_at`, `retirement_reason`, `created_at`, and
`updated_at`.

### 6.3 `AssetIdentifier`

Minimum proposed fields: `id`, `tenant_id`, `asset_id`, `scheme`, `value`, `issuer`, `is_primary`,
`effective_from`, `effective_to`, and provenance metadata. Scheme vocabulary is governed and
extensible; identifiers never replace the internal UUID.

### 6.4 `AssetPartyAssignment`

Minimum proposed fields: `id`, `tenant_id`, `asset_id`, `party_id`, `relationship_type`,
`effective_from`, `effective_to`, `revision`, and audit correlation. The first vocabulary may include
`owner`, `custodian`, and `operator`, subject to operator scope decision.

### 6.5 `AssetLifecycleHistory`

Minimum proposed fields: `id`, `tenant_id`, `asset_id`, `from_state`, `to_state`, `reason_code`,
`effective_at`, `actor_principal_id`, `correlation_id`, and `recorded_at`. Rows are append-only and
remain after the asset is retired.

## 7. Generic lifecycle

```text
registered ──> active <──> inactive
     │            │            │
     └────────────┴────────────┴──> retired (terminal)
```

- `registered`: identity exists but the asset is not yet active for product operations;
- `active`: available for eligible product-owned operations;
- `inactive`: temporarily not active while retaining identity and history;
- `retired`: terminal generic state; no return to active.

`sold`, `scrapped`, `lost`, and `disposed` should be retirement reasons or external ERP/product
transactions unless later evidence proves one must be a shared state. `under_maintenance`, `leased`,
`in_service`, and property-specific states remain product-owned. A generic transition is accepted
only when the state machine, authorization, current revision, and tenant context all allow it.

## 8. Dependency plan

| Dependency | First-slice posture | Reason |
| :--- | :--- | :--- |
| Tenant/context/authz/audit/events | **Hard dependency** | Ownership, isolation, decision, and evidence boundary |
| Party | **Hard for party assignments** | Owner/custodian/operator are business parties, not principals |
| Workflow | Optional orchestrator | May request transitions; Asset invariants remain authoritative |
| Location | **Deferred optional reference** | Do not block Asset identity on a foundation that is still gated |
| Document | **Deferred optional reference** | Attachments are useful but storage/access control is its own slice |
| UOM | Optional product extension | Capacity, weight, and dimensions are not required for core identity |
| Money/ERPNext | Integration only | Accounting valuation and depreciation remain outside core |
| Notification | Downstream event consumer | Asset must not synchronously depend on delivery providers |

The existing capability matrix lists Location as an Asset dependency. This plan narrows that to an
optional extension so the first slice does not silently authorize or require the still-gated
Location foundation. Changing the approved matrix itself would require the designated authority.

## 9. Proposed contracts

### 9.1 Capabilities

- `asset.class.create`, `asset.class.read`, `asset.class.update`;
- `asset.create`, `asset.read`, `asset.list`, `asset.update`;
- `asset.transition`;
- `asset.identifier.manage`;
- `asset.party_assignment.manage`.

Each decision remains deny-by-default and includes principal, tenant context, action, resource,
scope, lifecycle state, entitlement/module state where applicable, reason code, and correlation data.

### 9.2 Events

- `asset.registered.v1`;
- `asset.updated.v1`;
- `asset.lifecycle_changed.v1`;
- `asset.identifier_added.v1`;
- `asset.party_assignment_changed.v1`.

Events use the bOPEN envelope and transactional outbox. Consumers must deduplicate by event ID.
Ordering is guaranteed only to the level defined in the future event contract; consumers must not
infer global ordering.

### 9.3 API behavior

- externally observable schemas and error codes are frozen before implementation;
- writes carry an idempotency key and expected revision where applicable;
- stale revisions are refused rather than silently overwriting concurrent changes;
- cross-tenant existence is not disclosed through response differences;
- retiring an asset replaces hard deletion once history or external references exist.

## 10. First implementation slice (proposed, not authorized)

1. Freeze `BOPEN-ASSET-001`, API/event schemas, lifecycle, identifier vocabulary, and errors.
2. Add tenant-scoped `AssetClass`, `Asset`, `AssetIdentifier`, `AssetPartyAssignment`, and
   `AssetLifecycleHistory` storage with foreign keys, tenant-inclusive uniqueness, forced RLS, and a
   compensating/rollback plan.
3. Implement class create/read/update and asset create/read/update/list.
4. Implement identifier management without changing the immutable asset ID.
5. Implement generic lifecycle transitions with optimistic concurrency.
6. Implement effective-dated party assignments if included by operator scope decision.
7. Record append-only history and publish domain events through the transactional outbox.
8. Add authorization allow/deny, tenant isolation, idempotency, concurrency, retention, migration,
   backup/restore, event replay, and audit-integrity tests.
9. Validate the slice through the selected reference consumer contract; do not build the product
   module as part of the foundation work package.
10. Submit maker evidence for an independent EBIV ballot and separate operator disposition.

## 11. Required invariants and refusal tests

| Invariant | Defensive test expectation |
| :--- | :--- |
| Tenant ownership | Missing or wrong tenant context is refused; direct IDs, list, search, joins, exports, events, and caches disclose zero foreign-tenant data |
| Authorization | Unauthenticated, unauthorized, expired-grant, inactive-membership, and missing-entitlement requests are refused independently |
| Immutable identity | Internal asset ID cannot be changed or reused |
| Identifier uniqueness | A live `(tenant_id, scheme, value)` collision is refused without revealing collisions in another tenant |
| Lifecycle | Undefined transitions are refused; `retired` is terminal |
| History integrity | Update/delete of lifecycle history is refused; retirement preserves history |
| Party integrity | Assignment to a Party outside the active tenant is refused |
| Idempotency | Retrying the same mutation does not create duplicate assets, assignments, history, or events |
| Concurrency | A stale expected revision is refused; no lost update is accepted |
| Deletion | Hard delete is refused after history or external reference; retirement is used instead |
| Placement | Pooled and future dedicated placement preserve the same API/domain contract and tenant denial behavior |
| Event/audit | Every accepted mutation has correlated domain-event/outbox and audit evidence; refused mutations are auditable without leaking tenant data |

The future traceability matrix must bind each proposition to a named test and exact candidate object.
Green maker tests do not authorize, confirm, or activate the foundation.

## 12. Consumer sequencing

| Sequence | Consumer | What it validates | Boundary it must not pull into core |
| :---: | :--- | :--- | :--- |
| 1 | **bFleet (recommended)** | shared identity, serial/VIN schemes, custody, optional location, component extension | telemetry, fuel, driver, maintenance, route |
| 2 | PropTech | physical property identity, ownership reference, document/location links | title, appraisal, lease, cadastral rules |
| 3 | bERP/ERPNext integration | stable cross-system identity and lifecycle events | depreciation, capitalization, inventory, GL |

Research may proceed now. Build begins only after the operator authorizes a bounded Asset slice and
names the reference consumer contract; MILE-4.3 itself remains separately gated.

## 13. Risks and unresolved questions

| ID | Risk/question | Recommended posture before authorization |
| :--- | :--- | :--- |
| `ASSET-D-01` | Which reference consumer drives the first contract? | Select bFleet unless product sequencing changes |
| `ASSET-D-02` | Are party assignments in the first slice? | Include owner/custodian/operator only if Party contract is stable |
| `ASSET-D-03` | Are parent/component relationships in the first slice? | Defer storage; reserve an extension contract and validate with bFleet |
| `ASSET-D-04` | Which identifier schemes are initially governed? | Internal, serial, VIN, GIAI, GRAI, and `external_system`; reject free-form ambiguous schemes |
| `ASSET-D-05` | Is Location required at create time? | No; add an optional reference only after Location is authorized |
| `ASSET-D-06` | Is the nature vocabulary physical/digital/hybrid sufficient? | Confirm from the first consumer; version the vocabulary |
| `ASSET-D-07` | What retirement reasons are shared? | Start narrow and extensible; do not turn product events into core states |
| `ASSET-D-08` | How are identifier reassignment and reuse governed? | Default to non-reuse; require a separate policy and audit evidence for exceptions |

## 14. Required decisions and successor artifacts

Before implementation:

1. operator authorization recorded as an extend-only amendment to `DEC-P4-ENTRY` or its governed
   successor, with exact first-slice scope;
2. reference consumer and dependency posture selected;
3. `ASSET-D-01` through `ASSET-D-08` resolved or explicitly deferred without silent defaults;
4. normative Asset contract/specification (`BOPEN-ASSET-001`) accepted;
5. accepted work package naming maker, eligible independent verifier, evidence, and stop conditions;
6. API/event/error contracts, migrations, rollback/compensation, threat model, and test matrix frozen;
7. baseline captured first if the selected design changes an existing architecture boundary.

After implementation, maker evidence, an independent verifier ballot, and operator disposition are
three distinct acts. None alone grants production activation.

## 15. Source register

Retrieved 2026-08-05. External sources are informative requirements inputs unless an approved bOPEN
artifact adopts a requirement explicitly.

| Source | Evidence class | Use in this research |
| :--- | :--- | :--- |
| [`CAPABILITY-MATRIX`](CAPABILITY-MATRIX.md) | Approved repository specification | Asset purpose, dependencies, and consumers |
| [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §9 | Repository authority record | Current Asset gate status |
| [ISO 55000:2024](https://www.iso.org/standard/83053.html) | Official standard overview | Lifecycle/value framing |
| [ISO 55001:2024](https://www.iso.org/standard/83054.html) | Official standard overview | Performance/risk/expenditure lifecycle framing |
| [GS1 Identification Keys](https://www.gs1.org/standards/id-keys) | Official standard body guidance | Multiple scheme-qualified identifiers |
| [GS1 GRAI](https://www.gs1.org/standards/id-keys/grai) | Official standard body guidance | Returnable-asset identifier example |
| [IDTA Asset Administration Shell Part 1, v3.0](https://industrialdigitaltwin.org/wp-content/uploads/2023/04/IDTA-01001-3-0_SpecificationAssetAdministrationShell_Part1_Metamodel.pdf) | Official specification | Global/specific identity and type/instance separation |
| [ERPNext Asset documentation](https://docs.frappe.io/erpnext/asset) | Official vendor documentation | ERP scope comparison and integration boundary |

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
