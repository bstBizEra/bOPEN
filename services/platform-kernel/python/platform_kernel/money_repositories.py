"""Tenant-scoped exchange rates — MILE-4.2 Money & Currency.

Every method runs through `db.tenant_session`, so a tenant's rates are isolated by the row-level
security policy on `exchange_rates` and nothing else — the same contract as the other repositories.
Rates are read and written as `decimal.Decimal` (exact), never `float`, matching the money value
type's discipline.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import psycopg

from . import db


class ExchangeRateError(RuntimeError):
    """Base for exchange-rate failures."""


class ExchangeRateNotFoundError(ExchangeRateError):
    """No rate is set for this currency pair in this tenant."""


@dataclass(frozen=True)
class StoredRate:
    tenant_id: str
    from_currency: str
    to_currency: str
    rate: Decimal


def _rate(row) -> StoredRate:
    return StoredRate(
        tenant_id=str(row[0]),
        from_currency=row[1],
        to_currency=row[2],
        rate=Decimal(str(row[3])),
    )


class ExchangeRateRepository:
    """Tenant-scoped. A tenant sets and reads its own booking rates."""

    def set(self, tenant_id: str, from_currency: str, to_currency: str, rate: Decimal) -> StoredRate:
        try:
            with db.tenant_session(tenant_id) as cur:
                cur.execute(
                    "INSERT INTO exchange_rates (tenant_id, from_currency, to_currency, rate) "
                    "VALUES (%s, %s, %s, %s) "
                    "ON CONFLICT (tenant_id, from_currency, to_currency) "
                    "DO UPDATE SET rate = EXCLUDED.rate, updated_at = CURRENT_TIMESTAMP "
                    "RETURNING tenant_id, from_currency, to_currency, rate",
                    (tenant_id, from_currency, to_currency, str(rate)),
                )
                row = cur.fetchone()
        except psycopg.errors.CheckViolation as exc:
            # chk_rate_positive or chk_currencies_differ.
            raise ExchangeRateError(
                "a rate must be positive and convert between two different currencies"
            ) from exc
        return _rate(row)

    def get(self, tenant_id: str, from_currency: str, to_currency: str) -> StoredRate:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT tenant_id, from_currency, to_currency, rate FROM exchange_rates "
                "WHERE from_currency = %s AND to_currency = %s",
                (from_currency, to_currency),
            )
            row = cur.fetchone()
        if row is None:
            raise ExchangeRateNotFoundError(
                f"no {from_currency}->{to_currency} rate is set in this tenant"
            )
        return _rate(row)
