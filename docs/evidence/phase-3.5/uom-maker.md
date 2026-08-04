# EVD-UOM-MAKER — Unit-of-Measure foundation

**Document ID:** `EVD-UOM-MAKER`
**Version:** `1.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision
**Issued:** 2026-08-05
**Implements:** [`DEC-P4-ENTRY`](../../decisions/DEC-P4-ENTRY.md) §9 (authorized); [`RESEARCH-MILE-4.2-UOM`](../../01-product/MILE-4.2-uom-foundation-research.md)
**Candidate:** `9ea765c`
**Blob — `uom.py`:** `37ec24057a35c9acf5f4b9a6da59dd8bd14a9d1d`
**Blob — `uom_repositories.py`:** `40d341bf50c8cf00fdcf129565e74b04c8789403`
**Blob — `018_uom_custom_units.sql`:** `a9bab5c682a4ecc3ccad90e23587293afdac45a5`
**Blob — `test_uom.py`:** `0e9b7fb7b8bbf39b290d9b4ac34c0ef5b371d1cd`
**Blob — `invariant-traceability.csv`:** `f7315f860bd225c6a20613ec73c01447c579320a`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifier:** Codex
**Suites:** canonical **589/589** against PostgreSQL

---

## 1. What this is — and the one property it defends

The Unit-of-Measure foundation, Money's sibling. A physical quantity is `Quantity(magnitude: Decimal,
unit: str)` — `2.5 kg`, `1 rai` — with **exact decimal** arithmetic and banker's rounding, **never a
float**. The defended property is **dimension safety**: just as Money refuses `USD + EUR`, this
refuses `kg + m` and refuses converting `kilograms → metres`. A UOM foundation whose whole value is
that it makes that mistake unrepresentable.

Every unit belongs to a **dimension** (mass, length, area, volume, time, count, temperature) and
converts through that dimension's **base unit** by an **exact factor**. Standard units are a code
constant; a tenant's **custom units** are tenant-scoped with **full CRUD**.

**Clean-room (`AGENTS.md` §6):** independently implemented from the settled industry model
(dimension + base-unit + factor), studied from SI/ISO 80000, UCUM and ERP UOM models, adopted from
none.

## 2. Defensive verification

Every proposition asserts the foundation **refuses** an operation that would be meaningless or lose
precision — a cross-dimension conversion, a temperature (affine) conversion, a float magnitude, a
custom unit shadowing a standard one, a cross-tenant read — and **admits** a valid one exactly.

## 3. Propositions (traced in `invariant-traceability.csv`)

**Group A — value type** (`tests/unit/test_uom.py`, executed Python):

| ID | The quantity type must… | Test |
| :--- | :--- | :--- |
| `P4-UOM-01` | refuse a float magnitude | `test_a_float_magnitude_is_refused` |
| `P4-UOM-02` | convert within a dimension exactly (through the base) | `test_conversion_within_a_dimension_is_exact` |
| `P4-UOM-03` | **refuse converting across dimensions** (keystone) | `test_converting_across_dimensions_is_refused` |
| `P4-UOM-04` | refuse adding across dimensions | `test_adding_across_dimensions_is_refused` |
| `P4-UOM-05` | refuse a temperature (affine) conversion loudly | `test_temperature_conversion_is_refused_loudly` |
| `P4-UOM-06` | convert a tenant custom unit through the shared base | `test_a_custom_unit_converts_through_the_base` |
| `P4-UOM-07` | convert Thai land units (rai/ngan/wah²) exactly | `test_thai_land_units_convert_exactly` |
| `P4-UOM-08` | refuse scaling by a float | `test_scaling_by_a_float_is_refused` |

**Group B — HTTP** (`tests/integration/test_uom_http.py`, executed HTTP, bearer-gated):

| ID | The kernel must… | Test |
| :--- | :--- | :--- |
| `P4-UOM-HTTP-01` | convert exactly over HTTP | `test_convert_standard_units_exactly` |
| `P4-UOM-HTTP-02` | refuse a cross-dimension conversion (422) | `test_a_cross_dimension_conversion_is_refused` |
| `P4-UOM-HTTP-03` | refuse a temperature conversion (422) | `test_a_temperature_conversion_is_refused` |
| `P4-UOM-HTTP-04` | support full CRUD on a custom unit | `test_create_read_update_delete_a_custom_unit` |
| `P4-UOM-HTTP-05` | refuse a custom unit that shadows a standard one (409) | `test_a_custom_unit_cannot_shadow_a_standard_unit` |
| `P4-UOM-HTTP-06` | keep a custom unit private to its tenant (404) | `test_a_custom_unit_is_private_to_its_tenant` |
| `P4-UOM-HTTP-07` | require a bearer to create a custom unit (401) | `test_creating_a_custom_unit_requires_a_bearer` |

**Attack angle for the verifier:** ask to convert `1 kg` to `m` (must be 422); convert `100 degC` to
`degF` (must be 422 — affine, refused not mis-answered); confirm `1 rai → 1600 m²` and `2 in →
0.0508 m` **exactly** (not a float approximation); create a custom `pallet = 48 each` and convert
`1 pallet → 4 dozen`; try to redefine `kg` as a custom unit (must be 409); read tenant A's custom unit
as tenant B (must be 404).

## 4. Execution

```text
python tools/run_tests.py     589/589 OK   (live PostgreSQL)
```

- `platform_kernel/uom.py` — the `Quantity` value type, the `STANDARD_UNITS` constant (SI + common +
  imperial + Thai `rai`/`ngan`/`wah²`), and a `UnitRegistry` performing dimension-safe convert / add /
  subtract / scale with exact `Decimal` and `ROUND_HALF_EVEN`. Affine units (temperature) carry a
  `None` factor and are refused.
- Migration 018 adds `uom_custom_units`, tenant-scoped by RLS (mirrors `exchange_rates`), factor
  `NUMERIC` (exact, positive), dimension constrained to the multiplicative set.
- `uom_repositories.py` (full CRUD; refuses shadowing a standard unit) + bearer-gated endpoints
  (`POST/GET/PUT/DELETE /v1/uom/units`, `POST /v1/uom/convert`, `GET /v1/uom/standard-units`). The
  magnitude and factor cross the boundary as decimal **strings**, never JSON numbers.
- **Cross-slice, caught by a control:** adding `uom_custom_units` to the tenant-scoped classification
  made the trial→paid migration's coverage test (`INV-MIGRATE-COVERAGE-01`) fail until the table was
  also added to the migrate tool's `COPY_ORDER` — otherwise a trial→paid migration would silently
  leave a tenant's custom units behind. The enumerate-don't-miss control did its job; the tool now
  copies `uom_custom_units` too.

## 5. What this does NOT establish (disclosed)

1. **Multiplicative units only.** Temperature and any **affine** unit are refused, not converted —
   deferred to a follow-up (needs an offset model).
2. **No compound / derived units** (`km/h`, `L/100km`, price-per-unit where UOM meets Money). Single
   dimension per unit; compound units are a later slice.
3. **No per-tenant unit-system defaults** (metric vs imperial display) — presentation, later.
4. **The dimension of a custom unit is not editable** (a dimension change is delete-and-recreate),
   deliberately, so a recorded quantity is never silently reinterpreted.
5. **One verifier, not two** (two-agent profile).

## 6. Authority

A maker's submission. `EBIV` §8: a passing suite carries no verdict weight.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
