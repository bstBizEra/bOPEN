# EVD-LOCATION-DISPOSITION — Location foundation, §6.5 disposition surface

**Document ID:** `EVD-LOCATION-DISPOSITION`
**Version:** `1.0.0`
**Status:** **DISPOSED 2026-08-05 — `CONFIRMED_UNDER_TWO_AGENT_PROFILE`.** Operator (`BizEra`, Completion Authority) disposed the verdict and acknowledged the disclosed-risk record. Transcribed by Claude (Motor); not a maker approval.
**Issued:** 2026-08-05
**Maker/Recorder:** Claude (agent, Motor role) — `claude@bst.local`, advisory only
**Governing:** [`BOPEN-GOV-EBIV-001`](../../00-governance/BOPEN-GOV-EBIV-001.md) §6.5; [`DEC-P35-TWO-AGENT-QUORUM`](../../decisions/DEC-P35-TWO-AGENT-QUORUM.md)
**Subject:** [`EVD-LOCATION-MAKER`](location-maker.md); [`DEC-P4-ENTRY`](../../decisions/DEC-P4-ENTRY.md) §11

---

## 1. The verifier verdict — confirmed from repository objects

Confirmed against `ballots.jsonl` and `git`:

| Field | Value |
| :--- | :--- |
| Candidate | `1cde994` (tree `dfc5d22`) |
| Ballot commit | `b524846` — the ballots are the independent verifier's (`verifier_id=codex`, `independent_of_maker=true`); the verifier run left `ballots.jsonl` uncommitted, so the Motor persisted them (additions only, no existing ballot altered) |
| Verdicts | **31/31 `CONFIRMED`** (`LOC-INV-*`), 0 `REFUTED` — a clean first pass, no refutation |
| Admissibility | R1–R5 true on every ballot; verifier `codex`, distinct from the maker (Claude) |
| Suite | canonical 649/649 against PostgreSQL |

The verifier's independent probe confirmed the two keystones and the integrity refusals: a coordinate
is refused for an out-of-range longitude/latitude and for `NaN` at **both** the database CHECK and the
repository screen; a geometry observation is a **`candidate`** on creation and is accepted only by an
explicit actor with full provenance (source/observed_at/confidence), updating the location's current
pointer — never on HTTP success alone; a containment **cycle** (`A⊃B⊃C` then `C⊃A`) is refused by the
`WITH RECURSIVE` walk, as are a self-link and a second live parent; a child cannot attach to another
tenant's location (composite FK); append-only history resists UPDATE/DELETE and survives a location
delete (`ON DELETE RESTRICT`); an accuracy radius must be a UOM `length` unit (`kg` refused, `5 m`
admitted exactly); and precise coordinates never appear in an audit record. It also confirmed
`INV-MIGRATE-COVERAGE-01` stays green with the six tables in both the RLS classification and the
migrate tool's `COPY_ORDER`.

## 2. What the verdict closes

The Location foundation — a tenant-scoped Location Registry (`BOPEN-LOC-001`): a stable, immutable place
identity separated from its versioned addresses, point geometry observations (each an explicit
candidate that must be accepted, never auto-accepted from an HTTP 200), external identifiers, and a
bounded `contains` relationship. Identity is never derived from a formatted address, coordinate, or
provider id. It joins Party, Money, Workflow, UOM, and the Party ContactPoint extension as a ratified
MILE-4.2 foundation, and it clears the address/place dependency for its consumers (PropTech, bFleet,
Asset, Document) and the ContactPoint `postal` endpoint type deferred under `CP-D-02`.

## 3. The disclosed-risk record (acknowledged by the operator)

- **No production geocoding provider (`LOC-D-07`).** Provider distrust is proven at the observation
  level (candidate → explicit accept with provenance); the live `geocode.request` adapter and any real
  provider ship with the provider ADR. The first slice is the owned registry.
- **Point geometry only.** No polygon/geofence, PostGIS, alternative CRS, or spatial/nearby/autocomplete
  search (`LOC-D-09`/`10`) — deferred so no field becomes a cross-tenant existence oracle.
- **The containment-cycle check is transactional, not serialized.** The `WITH RECURSIVE` walk and the
  insert run in one transaction and the one-active-parent index keeps the graph a forest, but under
  `READ COMMITTED` two concurrent inserts could each pass the check and together form a cycle. A
  `SELECT … FOR UPDATE` lock on the involved locations or `SERIALIZABLE` isolation would close that
  window — a tracked refinement.
- **Address components are owned and flexible, not certified** (no postal-authority validation);
  `original_input` is preserved separately from normalized/rendered forms.
- **Retire, not delete** — a referenced location is retired (tombstone); its versions, geometry,
  identifiers, relationships, and history are preserved (`LOC-D-12`).
- **One verifier, not two** (two-agent profile).

## 4. Disposition — RESERVED TO THE OPERATOR (Completion Authority)

```yaml
disposition:
  verdict_basis: one_verifier_plus_operator            # EBIV §6.5 two-agent profile
  candidate_commit: 1cde994
  ballot_commit: b524846   # Codex, 31/31 CONFIRMED, verified from ballots.jsonl
  decision: CONFIRMED_UNDER_TWO_AGENT_PROFILE
  disclosed_risk_acknowledged: true                    # the items in §3 are read and accepted
  approver: "Operator: BizEra <ounkhamvilay@gmail.com>, Completion Authority"
  decision_timestamp: 2026-08-05
  recorded_by: Claude (Motor), transcribing — execution_authority:false approval_authority:false
```

**Recorded follow-through:** the profile verdict is noted in [`manifest.json`](manifest.json); the
Location foundation is verified-and-disposed. Notification and the other gated foundations (Document,
Calendar, Asset) enter on their own operator dispositions.

## 5. Authority

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
