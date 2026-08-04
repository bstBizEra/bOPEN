# MILE-4.2 — Unit-of-Measure (UOM) foundation, research & design

**Document ID:** `RESEARCH-MILE-4.2-UOM`
**Version:** `1.0.0`
**Status:** **Research — advisory. A future slice; buildable only on operator authorization.** One of the gated MILE-4.2 foundations ([`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §7 lists UOM as gated).
**Issued:** 2026-08-05
**Raised by:** Claude (agent, Motor role) — advisory research, no approval authority
**Clean-room:** `AGENTS.md` §6 — standards and prior art below are studied as *requirements sources*; any implementation is designed independently, not copied.

---

## 1. What UOM is, and why it is Money's sibling

A unit-of-measure foundation lets the platform represent a **physical quantity** — `2.5 kg`,
`3 boxes`, `120 km`, `48 m²` — as a value it can convert and compute with **safely**. It is the
quantity analogue of the Money foundation (MILE-4.2), and the parallel is close enough that UOM should
reuse Money's shape and its hard-won lessons.

| | **Money** (built) | **UOM** (this research) |
| :--- | :--- | :--- |
| Value | `Money(amount_minor: int, currency: str)` | `Quantity(magnitude: Decimal, unit: str)` |
| "never a float" | integer minor units | exact `Decimal` magnitude **and** exact conversion factors |
| compatibility rule | same **currency** to add | same **dimension** to add |
| conversion | exchange rate | conversion factor |
| reference data (constant) | currency table (ISO-4217 subset) | standard units (SI + common) |
| tenant data (RLS) | exchange rates | tenant **custom units / conversions** |
| rounding | `ROUND_HALF_EVEN` | `ROUND_HALF_EVEN` |
| its own hard edge | JPY has 0 minor units | **affine** units (°C↔°F) and **compound** units (km/h) |

The operator's instinct — "usable for many things" — is exactly why it is a *foundation* and not a
product feature: nearly every satellite product measures something (see §8).

## 2. The one property it defends — dimension safety

Just as Money refuses to add `USD` to `EUR` without a rate, UOM must **refuse to add or convert across
dimensions**: `kg + m` is meaningless, and converting `kilograms → metres` is a bug, not a rounding
question. A UOM foundation whose whole value is that it makes that mistake *unrepresentable*. This is
the keystone invariant, the direct analogue of Money's `CurrencyMismatchError`.

Concretely, every unit belongs to a **dimension** (a.k.a. quantity kind): mass, length, time, volume,
area, plane-angle, temperature, and the special dimensionless **count** (each, dozen, box). Two units
are convertible **iff** they share a dimension.

## 3. Core model

Four concepts, mirroring how `_MINOR_UNITS` underpins Money:

1. **Dimension** — `mass`, `length`, `time`, `volume`, `area`, `temperature`, `count`, … Each has one
   **base unit** through which all its units convert (the analogue of a currency's minor-unit scale):
   gram for mass, metre for length, litre for volume, and so on.
2. **Unit** — a code (`kg`, `g`, `lb`, `m`, `cm`, `ft`, `L`, `mL`) belonging to a dimension, with a
   **conversion factor** to the dimension's base unit, held as an **exact** value (`1 kg = 1000 g`,
   `1 in = 0.0254 m` exactly, `1 lb = 453.592 37 g` exactly).
3. **Quantity** — the value type `Quantity(magnitude: Decimal, unit)`, with:
   - `add` / `subtract` — same **dimension** only (convert the operand to the receiver's unit first),
   - `scale(k)` — multiply the magnitude by a dimensionless scalar,
   - `convert(to_unit)` — same dimension only; `magnitude × (from_factor / to_factor)` quantized with
     banker's rounding.
4. **Conversion** — derived from the two units' factors to the common base. No pairwise conversion
   table is stored for standard units (that is the mistake that makes unit tables drift); everything
   goes **through the base unit**, exactly as Money would round-trip through a base if it converted
   within a currency.

## 4. Precision — carry the Money lesson, do not repeat float

Money banned `float` and used integer minor units. UOM cannot use integers (quantities are `2.5 kg`,
`0.333 L`), so it uses **`decimal.Decimal` for the magnitude and exact factors for units**, with
`ROUND_HALF_EVEN` — never binary `float`. Two rules keep conversions exact:

- **Factors are exact.** Store `0.0254` (inch→metre) and `453.59237` (pound→gram) as exact `Decimal`s
  (or integer numerator/denominator rationals), not `float`. A chain `in → m → ft` must not accumulate
  representation error.
- **Convert through the base once**, then quantize once at the end, so a single rounding happens at
  the boundary — the same discipline as `Money.convert`.

## 5. Standards and prior art researched (requirements sources, not code to copy)

- **SI / ISO 80000** — the authority for base units and dimensions. Defines the seven SI base
  quantities and coherent derived units; the source of truth for `metre`, `kilogram`, `second`, etc.
- **UCUM (Unified Code for Units of Measure)** — a machine-readable unit-code system (used in HL7/
  healthcare). Valuable as a *code vocabulary* (`kg`, `m`, `L`, `Cel`, `[lb_av]`) and for how it
  separates the unit atom from its scale — worth adopting the *idea* of stable string codes.
- **ERP UOM models (ERPNext "UOM" + "UOM Conversion Factor"; Odoo `uom.uom` with category + factor +
  reference unit; SAP unit conversion).** These confirm the ubiquitous industry shape: **a category
  (our dimension), a reference/base unit per category, and a factor per unit.** Studied as the pattern
  the whole industry converges on — implemented here independently, not ported (`AGENTS.md` §6).
- **Libraries — Pint (Python), QUDT ontology, `units`.** Pint's registry + dimensionality-checking is
  the reference for *dimension safety* and *compound units*; QUDT for a formal quantity/unit ontology.
  Pattern references; the kernel writes its own small, auditable value type rather than taking a
  dependency, matching how Money was built from first principles.

**Conclusion of the survey:** every serious model is *dimension + base-unit + factor*, with the hard
parts being affine units and compound units. That convergence is why UOM is safe to design now — the
shape is settled; only the scope of the first slice is a choice.

## 6. Tenant model — reference constant + tenant custom, exactly like Money

- **Standard units are a code constant**, like Money's currency table: SI plus the common
  imperial/US and business units (`kg g mg t`, `m cm mm km`, `L mL`, `m² ha`, `each dozen`), extended
  as products need. Reference data, not tenant data — no RLS, versioned in code.
- **Tenant custom units and conversions are tenant-scoped** (RLS), the analogue of exchange rates: a
  tenant defines `1 pallet = 48 boxes` or a product-specific packaging unit private to it. This reuses
  the exact tenancy machinery already verified for `exchange_rates` (migration 012).
- **Local relevance:** the standard set should include Thai business units the products will need —
  **`rai`, `ngan`, `wah²`** for land area (PropTech), which convert exactly to m² (`1 rai = 1600 m²`).

## 7. The hard edges — what a first slice should defer, disclosed early

1. **Affine units (temperature).** `°C ↔ °F ↔ K` need an **offset**, not just a factor
   (`°F = °C × 9/5 + 32`). A factor-only model gets these wrong. Recommendation: the first slice is
   **multiplicative (factor) units only**, and **refuses** temperature conversion loudly rather than
   doing it wrong — then affine units are a clean follow-up. (Refusing is the Money/EBIV discipline:
   better a loud "not supported" than a silent wrong answer.)
2. **Compound / derived units** (`km/h`, `kg·m/s²`, `L/100km` fuel economy, price-per-unit). These
   compose dimensions. Defer; the first slice handles single-dimension units. Money-per-unit
   (price × quantity) is where UOM and Money meet and is its own later slice.
3. **Unit systems / display preferences** per tenant (metric vs imperial defaults) — presentation,
   later.

## 8. Consumers across bOPEN (why the breadth is real)

| Product | Uses UOM for |
| :--- | :--- |
| **bERP / inventory** | stock in each/box/kg; purchase-UOM ↔ stock-UOM conversion; the classic ERP need |
| **bFleet** | fuel (L/gal), distance (km/mi), payload weight/volume capacity |
| **PropTech** | area (m²/ft²/**rai/ngan**), land measurement |
| **Manufacturing / recipe** | ingredient quantities and yields |
| **Shipping / logistics** | package weight + dimensions, volumetric weight |
| **bPro (services)** | billable quantities (hours, units of work) — meets Money as price-per-unit |

## 9. Recommended first slice (mirrors the Money slice exactly)

Buildable as one governed cycle, structurally a copy of how Money was built:

- `uom.py` — `Quantity` value type + `Dimension`/unit registry constant + `convert`/`add`/`subtract`/
  `scale`, dimension-checked, exact `Decimal`, `ROUND_HALF_EVEN`; `DimensionMismatchError`,
  `UnknownUnitError`. (Sibling of `money.py`.)
- A migration for **tenant custom units / conversions**, tenant-scoped by RLS (sibling of migration
  012 `exchange_rates`); the standard units stay a code constant.
- `uom_repositories.py` + bearer-gated HTTP endpoints (create/read custom unit, convert a quantity),
  reusing `resolve_context` and the placement/tenancy machinery already verified.
- Invariants to trace (R2), the keystone being **`kg + m` refused** and **exact conversion through the
  base**, with the temperature refusal as a named negative.

## 10. Open decisions for the operator (before any build authorization)

1. **First-slice scope:** multiplicative units only, temperature refused (recommended) — or include
   affine units in the first slice?
2. **Standard unit set:** confirm the initial vocabulary, including the **Thai land units** for
   PropTech relevance.
3. **Sequencing:** build UOM next as a standalone foundation, or defer until a specific product
   (bERP / PropTech / bFleet) pulls it — so its unit set is driven by that product's real needs.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
