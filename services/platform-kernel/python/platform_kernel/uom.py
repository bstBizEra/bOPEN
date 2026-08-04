"""Unit-of-Measure value type — MILE-4.2 UOM foundation (independently designed).

`DEC-P4-ENTRY` §9. A physical quantity is represented as an exact `decimal.Decimal` magnitude plus a
unit code — `2.5 kg` is `Quantity("2.5", "kg")`, `1 rai` is `Quantity(1, "rai")`. This is UOM's
sibling to the Money foundation, and it carries Money's discipline: **never a float**, exact decimal
arithmetic, banker's rounding (`ROUND_HALF_EVEN`).

Clean-room (`AGENTS.md` §6): an independent implementation of the settled industry model
(dimension + base-unit + conversion factor), studied from SI/ISO 80000, UCUM and ERP UOM models but
adopted from none of them.

The one property it defends — **dimension safety**. Just as Money refuses to add `USD` to `EUR`, this
refuses to add or convert across dimensions: `kg + m` is meaningless and `kilograms -> metres` is a
bug, not a rounding question. Every unit belongs to a dimension, and two units are convertible iff
they share one, converting through the dimension's base unit.

What is refused, each because it is a quantity bug in waiting:

  - a float magnitude (`Quantity(2.5, ...)` with a Python float) — the value would already have drifted;
  - adding, subtracting or converting across dimensions;
  - a unit this registry does not know;
  - converting an **affine** unit (temperature: degC/degF/K need an offset, not a factor). This first
    slice is multiplicative-only and refuses affine conversion loudly rather than answering wrongly.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN, localcontext


class UomError(Exception):
    """Base for unit-of-measure misuse — always a refusal, never a silent coercion."""


class UnknownUnitError(UomError):
    """A unit this registry does not know."""


class DimensionMismatchError(UomError):
    """An attempt to combine or convert quantities of different dimensions."""


class AffineConversionNotSupportedError(UomError):
    """A conversion involving an affine unit (e.g. temperature), which needs an offset, not a factor.

    Deliberately refused in this slice rather than mis-converted. Affine units are a later slice."""


def _to_decimal(value: object, what: str) -> Decimal:
    # bool is a subclass of int; a True/False magnitude is almost certainly a mistake.
    if isinstance(value, bool):
        raise UomError(f"{what} must be a number, never a bool")
    # A Python float has already lost precision by the time it reaches here; refuse it as Money does.
    if isinstance(value, float):
        raise UomError(
            f"{what} must not be a float (binary floating point drifts); pass an int, a Decimal, "
            f"or a decimal string"
        )
    if isinstance(value, (int, Decimal)):
        return Decimal(value)
    if isinstance(value, str):
        try:
            return Decimal(value)
        except Exception:
            raise UomError(f"{what} {value!r} is not a valid decimal") from None
    raise UomError(f"{what} must be an int, a Decimal, or a decimal string")


@dataclass(frozen=True)
class _UnitDef:
    """A unit's dimension and its exact factor to that dimension's base unit. `factor is None` marks
    an affine unit (temperature), which cannot be converted by a factor and is refused."""

    dimension: str
    factor: Decimal | None


def _u(dimension: str, factor: "Decimal | str | int | None") -> _UnitDef:
    return _UnitDef(dimension, None if factor is None else _to_decimal(factor, "factor"))


#: Standard units as reference data in code (not tenant data): the base unit of each dimension has
#: factor 1, every other unit its exact factor to that base. Extend as products require; a wrong
#: factor here is a correctness defect. Affine units (temperature) carry `None` and are refused.
STANDARD_UNITS: dict[str, _UnitDef] = {
    # mass — base gram
    "g": _u("mass", 1), "kg": _u("mass", 1000), "mg": _u("mass", "0.001"),
    "t": _u("mass", 1_000_000), "lb": _u("mass", "453.59237"), "oz": _u("mass", "28.349523125"),
    # length — base metre
    "m": _u("length", 1), "km": _u("length", 1000), "cm": _u("length", "0.01"),
    "mm": _u("length", "0.001"), "in": _u("length", "0.0254"), "ft": _u("length", "0.3048"),
    "yd": _u("length", "0.9144"), "mi": _u("length", "1609.344"),
    # area — base square metre (incl. Thai land units, exact)
    "m2": _u("area", 1), "cm2": _u("area", "0.0001"), "km2": _u("area", 1_000_000),
    "ha": _u("area", 10_000), "ft2": _u("area", "0.09290304"),
    "rai": _u("area", 1600), "ngan": _u("area", 400), "wah2": _u("area", 4),
    # volume — base litre
    "L": _u("volume", 1), "mL": _u("volume", "0.001"), "m3": _u("volume", 1000),
    "gal_us": _u("volume", "3.785411784"),
    # time — base second
    "s": _u("time", 1), "min": _u("time", 60), "h": _u("time", 3600), "day": _u("time", 86400),
    # count (dimensionless) — base each
    "each": _u("count", 1), "pair": _u("count", 2), "dozen": _u("count", 12),
    # temperature — affine; conversion refused in this slice
    "degC": _u("temperature", None), "degF": _u("temperature", None), "K": _u("temperature", None),
}


@dataclass(frozen=True)
class Quantity:
    """An exact physical quantity: a decimal magnitude of a unit."""

    magnitude: Decimal
    unit: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "magnitude", _to_decimal(self.magnitude, "magnitude"))


class UnitRegistry:
    """Knows a set of units and performs dimension-safe operations on quantities.

    The standard registry is a constant; a tenant's custom units extend it via `with_custom`, so a
    conversion involving a tenant-defined unit works exactly like a standard one — through the shared
    base unit of its dimension.
    """

    def __init__(self, units: "dict[str, _UnitDef]"):
        self._units = dict(units)

    def with_custom(self, custom: "dict[str, _UnitDef]") -> "UnitRegistry":
        """Return a registry that is the standard units plus these custom ones (custom win on clash)."""
        return UnitRegistry({**self._units, **custom})

    def _def(self, unit: str) -> _UnitDef:
        try:
            return self._units[unit]
        except KeyError:
            raise UnknownUnitError(f"unknown unit {unit!r}") from None

    def dimension_of(self, unit: str) -> str:
        return self._def(unit).dimension

    def convert(self, quantity: Quantity, to_unit: str) -> Quantity:
        """Convert a quantity to another unit of the SAME dimension, exactly, refusing anything else."""
        src = self._def(quantity.unit)
        dst = self._def(to_unit)
        if src.dimension != dst.dimension:
            raise DimensionMismatchError(
                f"cannot convert {quantity.unit!r} ({src.dimension}) to {to_unit!r} "
                f"({dst.dimension}); different dimensions"
            )
        if src.factor is None or dst.factor is None:
            raise AffineConversionNotSupportedError(
                f"conversion involving an affine unit ({quantity.unit!r} or {to_unit!r}, dimension "
                f"{src.dimension}) is not supported in this slice; it needs an offset, not a factor"
            )
        # Convert through the dimension's base unit, then a single deterministic rounding.
        with localcontext() as ctx:
            ctx.prec = 34
            ctx.rounding = ROUND_HALF_EVEN
            base = quantity.magnitude * src.factor
            result = base / dst.factor
            result = +result  # apply the context (precision/rounding) to the result
        return Quantity(result, to_unit)

    def add(self, a: Quantity, b: Quantity) -> Quantity:
        """Add two quantities of the same dimension; the result is in `a`'s unit. Refuses across
        dimensions — the keystone: `kg + m` cannot be expressed."""
        b_in_a = self.convert(b, a.unit)  # raises DimensionMismatchError / affine as needed
        return Quantity(a.magnitude + b_in_a.magnitude, a.unit)

    def subtract(self, a: Quantity, b: Quantity) -> Quantity:
        b_in_a = self.convert(b, a.unit)
        return Quantity(a.magnitude - b_in_a.magnitude, a.unit)

    def scale(self, a: Quantity, factor: "Decimal | str | int") -> Quantity:
        """Scale a quantity by a dimensionless scalar (never a float)."""
        return Quantity(a.magnitude * _to_decimal(factor, "factor"), a.unit)


#: The standard registry — the constant every caller starts from.
STANDARD = UnitRegistry(STANDARD_UNITS)


def known_dimensions() -> "frozenset[str]":
    """The dimensions the standard registry defines — used to validate a custom unit's dimension."""
    return frozenset(u.dimension for u in STANDARD_UNITS.values())
