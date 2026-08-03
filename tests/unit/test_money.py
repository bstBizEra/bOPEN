"""Money value type — MILE-4.2 Money & Currency foundation.

Governed by DEC-P4-ENTRY (MILE-4.2), independently designed (AGENTS.md §6 clean-room — not
adopted from any upstream ERP, which store money as floats; integer minor units is a distinct and
stronger design).

The one property everything here defends: **money is integer minor units, never a float.** $10.50
is `Money(1050, "USD")`, ¥100 is `Money(100, "JPY")` (JPY has zero minor units). Arithmetic is
integer arithmetic, so it cannot drift the way `0.1 + 0.2` does. Conversion uses exact decimal
(not binary float) and rounds deterministically. These are unit tests — no database.
"""

from __future__ import annotations

import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))

from platform_kernel import money  # noqa: E402


class TestMoneyValueType(unittest.TestCase):
    # -- the core property: integer minor units, never float --------------------------

    def test_a_money_is_integer_minor_units(self):
        m = money.Money(1050, "USD")
        self.assertEqual(m.amount_minor, 1050)
        self.assertEqual(m.currency, "USD")

    def test_a_float_amount_is_refused(self):
        with self.assertRaises(money.MoneyError):
            money.Money(10.50, "USD")  # the classic money bug, refused at construction

    def test_a_bool_amount_is_refused(self):
        # bool is a subclass of int; a True/False amount is almost certainly a mistake.
        with self.assertRaises(money.MoneyError):
            money.Money(True, "USD")

    def test_an_unknown_currency_is_refused(self):
        with self.assertRaises(money.UnknownCurrencyError):
            money.Money(1000, "XYZ")

    # -- arithmetic -------------------------------------------------------------------

    def test_addition_within_a_currency(self):
        self.assertEqual(
            money.Money(1050, "USD").add(money.Money(295, "USD")),
            money.Money(1345, "USD"),
        )

    def test_addition_across_currencies_is_refused(self):
        with self.assertRaises(money.CurrencyMismatchError):
            money.Money(1050, "USD").add(money.Money(1000, "THB"))

    def test_subtraction_within_a_currency(self):
        self.assertEqual(
            money.Money(1050, "USD").subtract(money.Money(50, "USD")),
            money.Money(1000, "USD"),
        )

    def test_multiplication_by_an_integer_factor(self):
        self.assertEqual(money.Money(1050, "USD").times(3), money.Money(3150, "USD"))

    def test_multiplication_by_a_float_is_refused(self):
        with self.assertRaises(money.MoneyError):
            money.Money(1050, "USD").times(1.5)

    # -- conversion: exact decimal, deterministic rounding, minor-units-aware ---------

    def test_conversion_respects_the_target_minor_units(self):
        # USD 10.50 at 33.00 THB/USD -> THB 346.50 -> 34650 minor units (THB has 2)
        result = money.Money(1050, "USD").convert(Decimal("33.00"), "THB")
        self.assertEqual(result, money.Money(34650, "THB"))

    def test_conversion_into_a_zero_minor_unit_currency(self):
        # USD 10.50 at 150 JPY/USD -> JPY 1575 -> 1575 minor units (JPY has 0)
        result = money.Money(1050, "USD").convert(Decimal("150"), "JPY")
        self.assertEqual(result, money.Money(1575, "JPY"))

    def test_conversion_rounds_half_to_even_deterministically(self):
        # Construct results landing EXACTLY on a half minor unit and assert banker's rounding.
        # USD 0.04 (4 minor) at 0.125 -> 0.005 major THB -> 0.5 minor -> HALF_EVEN -> 0 (even)
        self.assertEqual(money.Money(4, "USD").convert(Decimal("0.125"), "THB").amount_minor, 0)
        # USD 0.12 (12 minor) at 0.125 -> 0.015 major THB -> 1.5 minor -> HALF_EVEN -> 2 (even)
        self.assertEqual(money.Money(12, "USD").convert(Decimal("0.125"), "THB").amount_minor, 2)

    def test_conversion_to_an_unknown_currency_is_refused(self):
        with self.assertRaises(money.UnknownCurrencyError):
            money.Money(1000, "USD").convert(Decimal("1"), "XYZ")

    def test_equality_and_immutability(self):
        self.assertEqual(money.Money(100, "USD"), money.Money(100, "USD"))
        self.assertNotEqual(money.Money(100, "USD"), money.Money(100, "EUR"))
        with self.assertRaises(Exception):
            money.Money(100, "USD").amount_minor = 200  # frozen


if __name__ == "__main__":
    unittest.main()
