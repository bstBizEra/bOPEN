"""Unit-of-Measure value type — MILE-4.2 UOM foundation.

Governed by DEC-P4-ENTRY §9, independently designed (AGENTS.md §6 clean-room — the dimension +
base-unit + factor model, implemented from first principles, not adopted from any upstream).

The one property everything here defends: **dimension safety** — `kg + m` cannot be expressed, and
`kilograms -> metres` is refused. Magnitudes are exact `Decimal`, never float; conversion goes through
a dimension's base unit and rounds deterministically. Temperature (affine) conversion is refused in
this slice rather than answered wrongly. These are unit tests — no database.
"""

from __future__ import annotations

import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))

from platform_kernel import uom  # noqa: E402


class TestQuantityValueType(unittest.TestCase):
    # -- the core property: exact decimal magnitude, never float ------------------------

    def test_a_quantity_holds_an_exact_decimal_magnitude(self):
        q = uom.Quantity("2.5", "kg")
        self.assertEqual(q.magnitude, Decimal("2.5"))
        self.assertEqual(q.unit, "kg")

    def test_a_float_magnitude_is_refused(self):
        with self.assertRaises(uom.UomError):
            uom.Quantity(2.5, "kg")  # a Python float has already drifted; refused at construction

    def test_a_bool_magnitude_is_refused(self):
        with self.assertRaises(uom.UomError):
            uom.Quantity(True, "kg")

    def test_an_int_or_decimal_or_string_magnitude_is_accepted(self):
        self.assertEqual(uom.Quantity(3, "kg").magnitude, Decimal(3))
        self.assertEqual(uom.Quantity(Decimal("3.14"), "m").magnitude, Decimal("3.14"))
        self.assertEqual(uom.Quantity("1600", "m2").magnitude, Decimal("1600"))

    # -- exact conversion within a dimension -------------------------------------------

    def test_conversion_within_a_dimension_is_exact(self):
        self.assertEqual(uom.STANDARD.convert(uom.Quantity(1, "kg"), "g").magnitude, Decimal("1000"))
        self.assertEqual(uom.STANDARD.convert(uom.Quantity("2.5", "kg"), "g").magnitude, Decimal("2500"))
        self.assertEqual(uom.STANDARD.convert(uom.Quantity(1, "km"), "m").magnitude, Decimal("1000"))

    def test_thai_land_units_convert_exactly(self):
        # 1 rai = 1600 m2, 1 ngan = 400 m2, 1 sq wah = 4 m2 — exact, no float.
        self.assertEqual(uom.STANDARD.convert(uom.Quantity(1, "rai"), "m2").magnitude, Decimal("1600"))
        self.assertEqual(uom.STANDARD.convert(uom.Quantity(1, "rai"), "ngan").magnitude, Decimal("4"))
        self.assertEqual(uom.STANDARD.convert(uom.Quantity(1, "ngan"), "wah2").magnitude, Decimal("100"))

    def test_imperial_conversion_is_exact_not_float(self):
        # 1 in = 0.0254 m exactly; 2 in = 0.0508 m, not 0.05080000000001 as a float would give.
        self.assertEqual(uom.STANDARD.convert(uom.Quantity(2, "in"), "m").magnitude, Decimal("0.0508"))
        self.assertEqual(uom.STANDARD.convert(uom.Quantity(1, "lb"), "g").magnitude, Decimal("453.59237"))

    def test_a_round_trip_conversion_returns_the_original(self):
        q = uom.Quantity("3", "kg")
        there = uom.STANDARD.convert(q, "lb")
        back = uom.STANDARD.convert(there, "kg")
        self.assertEqual(back.magnitude, Decimal("3"))

    # -- the keystone: dimension safety ------------------------------------------------

    def test_converting_across_dimensions_is_refused(self):
        with self.assertRaises(uom.DimensionMismatchError):
            uom.STANDARD.convert(uom.Quantity(1, "kg"), "m")  # mass -> length is a bug

    def test_adding_across_dimensions_is_refused(self):
        with self.assertRaises(uom.DimensionMismatchError):
            uom.STANDARD.add(uom.Quantity(1, "kg"), uom.Quantity(1, "m"))

    def test_adding_within_a_dimension_converts_and_sums(self):
        # 1 kg + 500 g = 1.5 kg (result in the first operand's unit).
        total = uom.STANDARD.add(uom.Quantity(1, "kg"), uom.Quantity(500, "g"))
        self.assertEqual(total.magnitude, Decimal("1.5"))
        self.assertEqual(total.unit, "kg")

    def test_subtracting_within_a_dimension(self):
        d = uom.STANDARD.subtract(uom.Quantity(1, "m"), uom.Quantity(30, "cm"))
        self.assertEqual(d.magnitude, Decimal("0.70"))

    # -- scaling ------------------------------------------------------------------------

    def test_scaling_by_a_scalar(self):
        self.assertEqual(uom.STANDARD.scale(uom.Quantity("2.5", "kg"), 4).magnitude, Decimal("10.0"))

    def test_scaling_by_a_float_is_refused(self):
        with self.assertRaises(uom.UomError):
            uom.STANDARD.scale(uom.Quantity(1, "kg"), 1.5)

    # -- unknown units and affine refusal ----------------------------------------------

    def test_an_unknown_unit_is_refused(self):
        with self.assertRaises(uom.UnknownUnitError):
            uom.STANDARD.convert(uom.Quantity(1, "smoot"), "m")

    def test_temperature_conversion_is_refused_loudly(self):
        # Affine units need an offset, not a factor; refused rather than mis-converted in this slice.
        with self.assertRaises(uom.AffineConversionNotSupportedError):
            uom.STANDARD.convert(uom.Quantity(100, "degC"), "degF")

    # -- tenant custom units through the shared base -----------------------------------

    def test_a_custom_unit_converts_through_the_base(self):
        # A tenant defines "pallet" = 48 each (count). It converts to dozen through the base "each".
        reg = uom.STANDARD.with_custom({"pallet": uom._UnitDef("count", Decimal("48"))})
        self.assertEqual(reg.convert(uom.Quantity(1, "pallet"), "each").magnitude, Decimal("48"))
        self.assertEqual(reg.convert(uom.Quantity(1, "pallet"), "dozen").magnitude, Decimal("4"))

    def test_a_custom_unit_of_another_dimension_is_still_dimension_safe(self):
        reg = uom.STANDARD.with_custom({"pallet": uom._UnitDef("count", Decimal("48"))})
        with self.assertRaises(uom.DimensionMismatchError):
            reg.convert(uom.Quantity(1, "pallet"), "kg")  # count -> mass still refused


if __name__ == "__main__":
    unittest.main()
