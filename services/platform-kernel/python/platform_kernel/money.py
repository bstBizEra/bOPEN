"""Money value type — MILE-4.2 Money & Currency foundation (independently designed).

`DEC-P4-ENTRY` MILE-4.2. Money is represented as **integer minor units** plus an ISO-4217 currency
code — `$10.50` is `Money(1050, "USD")`, `¥100` is `Money(100, "JPY")` (JPY has zero minor units).
This is a deliberate, stronger design than the float-with-precision model common to upstream ERP
systems: integer arithmetic cannot drift the way binary floating point does (`0.1 + 0.2 != 0.3`),
so a sum of monetary amounts is always exact.

Clean-room (`AGENTS.md` §6): this is an independent implementation of the well-established money
pattern (integer minor units, ISO-4217), not adopted from any upstream source.

What is refused, each because it is a money bug in waiting:

  - a float amount (`Money(10.5, ...)`) — the value would already have lost precision;
  - adding or subtracting across currencies without an explicit conversion;
  - a currency this module does not know the minor units of.

Conversion uses exact decimal arithmetic (`decimal.Decimal`, not `float`) and rounds the result to
the target currency's minor units with banker's rounding (`ROUND_HALF_EVEN`), which is deterministic
and unbiased.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN

#: ISO-4217 minor units (decimal places) for the currencies this foundation knows. Extend as
#: products require; kept as reference data in code rather than a table because it changes rarely
#: and a wrong value here is a correctness defect, not tenant data.
_MINOR_UNITS: dict[str, int] = {
    "USD": 2, "EUR": 2, "GBP": 2, "THB": 2, "CNY": 2, "SGD": 2, "HKD": 2, "AUD": 2,
    "CAD": 2, "CHF": 2, "INR": 2, "MYR": 2, "PHP": 2, "IDR": 2, "NZD": 2, "SEK": 2,
    "JPY": 0, "KRW": 0, "VND": 0, "CLP": 0, "ISK": 0,
    "BHD": 3, "KWD": 3, "OMR": 3, "JOD": 3, "TND": 3,
}


class MoneyError(Exception):
    """Base for money misuse — always a refusal, never a silent coercion."""


class UnknownCurrencyError(MoneyError):
    """A currency whose minor units this module does not know."""


class CurrencyMismatchError(MoneyError):
    """An attempt to combine two different currencies without an explicit conversion."""


def minor_units(currency: str) -> int:
    """Return the number of minor units (decimal places) for an ISO-4217 currency, or refuse."""
    try:
        return _MINOR_UNITS[currency]
    except KeyError:
        raise UnknownCurrencyError(f"unknown currency {currency!r}") from None


def _require_int(value: object, what: str) -> int:
    # bool is a subclass of int, and a True/False amount or factor is almost certainly a mistake.
    if not isinstance(value, int) or isinstance(value, bool):
        raise MoneyError(f"{what} must be an int (integer minor units), never a float or bool")
    return value


@dataclass(frozen=True)
class Money:
    """An exact monetary amount: integer minor units of an ISO-4217 currency."""

    amount_minor: int
    currency: str

    def __post_init__(self) -> None:
        _require_int(self.amount_minor, "amount_minor")
        minor_units(self.currency)  # validates the currency is known

    def _same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise CurrencyMismatchError(
                f"cannot combine {self.currency} and {other.currency}; convert first"
            )

    def add(self, other: "Money") -> "Money":
        self._same_currency(other)
        return Money(self.amount_minor + other.amount_minor, self.currency)

    def subtract(self, other: "Money") -> "Money":
        self._same_currency(other)
        return Money(self.amount_minor - other.amount_minor, self.currency)

    def times(self, factor: int) -> "Money":
        """Scale by an integer factor (e.g. a quantity). A fractional factor is a conversion, not a
        multiplication, and is refused so a caller does not silently lose precision here."""
        _require_int(factor, "factor")
        return Money(self.amount_minor * factor, self.currency)

    def convert(self, rate: "Decimal | str | int", to_currency: str) -> "Money":
        """Convert to another currency at an exact decimal `rate` (this currency -> to_currency).

        The rate is a ratio, not money, so it is exact-decimal; the result is rounded to the target
        currency's minor units with banker's rounding. Never touches `float`.
        """
        r = rate if isinstance(rate, Decimal) else Decimal(str(rate))
        from_mu = minor_units(self.currency)
        to_mu = minor_units(to_currency)
        major_from = Decimal(self.amount_minor) / (Decimal(10) ** from_mu)
        minor_to = (major_from * r * (Decimal(10) ** to_mu)).quantize(
            Decimal(1), rounding=ROUND_HALF_EVEN
        )
        return Money(int(minor_to), to_currency)
