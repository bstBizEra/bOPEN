# EVD-MILE-4.2-MONEY-MAKER — Money & Currency foundation

**Document ID:** `EVD-MILE-4.2-MONEY-MAKER`
**Version:** `1.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision
**Issued:** 2026-08-03
**Implements:** [`DEC-P4-ENTRY`](../../decisions/DEC-P4-ENTRY.md) MILE-4.2 (Money & Currency)
**Candidate:** the commit carrying this submission (value type at `20eeb0f`, rates+HTTP at `2ef46fe`)
**Blob — `money.py`:** `c5369ea7b2c34fa11de3a742bacd85115d6a1eb2`
**Blob — `money_repositories.py`:** `51273899a2ad9ddedab871ab8291556c98e16b79`
**Blob — `api.py`:** `68c3987949e5967d172f91c8bd221ae4fbbcaeba`
**Blob — `012_exchange_rates.sql`:** `a70b8e815849321822194a7509d93ffcbaeffb0c`
**Blob — `invariant-traceability.csv`:** `a820e9c4d95a39749c3ffed1843467713b3fc734`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifier:** Codex
**Suites:** canonical **521/521** against PostgreSQL

---

## 1. What this is — and the one property it defends

The Money & Currency foundation. Its point is a **money value type that is integer minor units, never
a float**: `$10.50` is `Money(1050, "USD")`, `¥100` is `Money(100, "JPY")` (JPY has zero minor
units). Integer arithmetic cannot drift the way binary floating point does (`0.1 + 0.2 != 0.3`), so a
sum of monetary amounts is always exact. Conversion uses exact `decimal.Decimal` (not `float`) and
rounds to the target currency's minor units with banker's rounding.

**Clean-room (`AGENTS.md` §6):** independently designed. This is the well-established integer
minor-units money pattern, deliberately **not** the float-with-precision model of upstream ERP
systems — that model is what integer minor units exists to avoid.

## 2. Defensive verification

Every proposition asserts the platform **refuses** an operation that would lose precision or cross a
tenant boundary, and **admits** a valid one. No offensive objective.

## 3. Propositions (traced in `invariant-traceability.csv`)

**Group A — money value type** (`tests/unit/test_money.py`, executed Python):

| ID | Money must… | Test |
| :--- | :--- | :--- |
| `P4-MONEY-01` | refuse a float amount (integer minor units only) | `test_a_float_amount_is_refused` |
| `P4-MONEY-02` | refuse an unknown currency | `test_an_unknown_currency_is_refused` |
| `P4-MONEY-03` | add two amounts of one currency exactly | `test_addition_within_a_currency` |
| `P4-MONEY-04` | refuse adding two different currencies | `test_addition_across_currencies_is_refused` |
| `P4-MONEY-05` | refuse scaling by a float | `test_multiplication_by_a_float_is_refused` |
| `P4-MONEY-06` | round a conversion to the target minor units | `test_conversion_respects_the_target_minor_units` |
| `P4-MONEY-07` | round a conversion half-to-even deterministically | `test_conversion_rounds_half_to_even_deterministically` |

**Group B — HTTP layer** (`tests/integration/test_money_http.py`, executed HTTP, bearer-gated):

| ID | The kernel must… | Test |
| :--- | :--- | :--- |
| `P4-MONEY-HTTP-01` | let a tenant set and read its exchange rate | `test_set_and_get_a_rate` |
| `P4-MONEY-HTTP-02` | convert using the tenant's rate exactly | `test_convert_uses_the_tenants_rate_exactly` |
| `P4-MONEY-HTTP-03` | keep a rate private to its tenant (B gets 404) | `test_a_rate_is_private_to_its_tenant` |
| `P4-MONEY-HTTP-04` | refuse a convert with no rate set (404) | `test_convert_without_a_rate_is_refused` |
| `P4-MONEY-HTTP-05` | refuse an unknown currency (422) | `test_an_unknown_currency_is_refused` |
| `P4-MONEY-HTTP-06` | require a bearer to set a rate (401 without) | `test_setting_a_rate_requires_a_bearer` |

**Attack angle for the verifier:** send `"rate": 33.5` as a JSON **number** rather than a string — the
request model refuses it, so a float cannot enter the arithmetic; try to read tenant A's rate with
tenant B's bearer (must be 404); check that `Money(1050,"USD").convert(33.00,"THB")` is exactly
`34650` minor units, not `34649` or `34651`.

## 4. Execution

```text
python tools/run_tests.py     521/521 OK   (live PostgreSQL)
```

Migration 012 adds `exchange_rates`, tenant-scoped by RLS, `rate NUMERIC` (exact, positive,
currencies differ). The rate crosses the HTTP boundary as a decimal **string**, never a JSON number.
Mutation intuition: change `Money.amount_minor` to accept a float and `P4-MONEY-01` breaks; change
`convert` to use `float()` and `P4-MONEY-07` drifts.

## 5. What this does NOT establish (disclosed)

1. **No ledger, no accounting, no payment** — this is the money *type* and per-tenant rates, not a
   general ledger. bERP will build those on this base (studying upstream ERP as a requirements source
   under `AGENTS.md` §6, independently implemented).
2. **Rates are a single current value per pair**, not a time series; historical-rate lookup is a
   later slice.
3. **The currency table is a code constant** (ISO-4217 subset), extended as products require; it is
   reference data, not tenant data.
4. **No cross-currency allocation/splitting** (Fowler's `allocate`) yet.

## 6. Authority

A maker's submission. `EBIV` §8: a passing suite carries no verdict weight.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
