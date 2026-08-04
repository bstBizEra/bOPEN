"""Tenant custom units of measure — MILE-4.2 UOM (DEC-P4-ENTRY §9).

Every method runs through `db.tenant_session`, so isolation is the row-level-security policy's
property and this module's, and nothing else — the same contract as `repositories.py`. Standard units
are the code constant in `uom.py`; this is the tenant-scoped half, with full CRUD.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

import psycopg

from . import db
from . import uom


class CustomUnitError(RuntimeError):
    """Base for custom-unit failures."""


class CustomUnitNotFoundError(CustomUnitError):
    """A custom unit does not exist in this tenant (indistinguishable from another tenant's)."""


class CustomUnitConflictError(CustomUnitError):
    """A custom unit code that already exists for this tenant, or that shadows a standard unit."""


@dataclass(frozen=True)
class StoredCustomUnit:
    tenant_id: str
    unit_code: str
    dimension: str
    factor_to_base: Decimal
    display_name: str


def _row(row) -> StoredCustomUnit:
    return StoredCustomUnit(
        tenant_id=str(row[0]),
        unit_code=row[1],
        dimension=row[2],
        factor_to_base=row[3],
        display_name=row[4],
    )


_COLUMNS = "tenant_id, unit_code, dimension, factor_to_base, display_name"


class CustomUnitRepository:
    """Tenant-scoped. Every method runs under the tenant's own isolation policy."""

    def _reject_shadowing_a_standard_unit(self, unit_code: str) -> None:
        # A custom unit must not redefine a standard one — that would let a tenant quietly change what
        # `kg` means for itself, which is a correctness trap, not a feature.
        if unit_code in uom.STANDARD_UNITS:
            raise CustomUnitConflictError(
                f"{unit_code!r} is a standard unit and cannot be redefined as a custom unit"
            )

    def create(
        self, tenant_id: str, unit_code: str, dimension: str, factor_to_base: Decimal, display_name: str
    ) -> StoredCustomUnit:
        self._reject_shadowing_a_standard_unit(unit_code)
        try:
            with db.tenant_session(tenant_id) as cur:
                cur.execute(
                    f"INSERT INTO uom_custom_units "
                    f"(tenant_id, unit_code, dimension, factor_to_base, display_name) "
                    f"VALUES (%s, %s, %s, %s, %s) RETURNING {_COLUMNS}",
                    (tenant_id, unit_code, dimension, factor_to_base, display_name),
                )
                row = cur.fetchone()
        except psycopg.errors.UniqueViolation:
            raise CustomUnitConflictError(
                f"custom unit {unit_code!r} already exists for this tenant"
            ) from None
        except psycopg.errors.CheckViolation as exc:
            # chk_uom_factor_positive or chk_uom_dimension.
            raise CustomUnitError(
                "factor must be positive and dimension must be one of mass, length, area, volume, "
                "time, count (temperature is affine and not supported)"
            ) from exc
        return _row(row)

    def get(self, tenant_id: str, unit_code: str) -> StoredCustomUnit:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                f"SELECT {_COLUMNS} FROM uom_custom_units WHERE unit_code = %s", (unit_code,)
            )
            row = cur.fetchone()
        if row is None:
            raise CustomUnitNotFoundError(f"custom unit {unit_code!r} not found in this tenant")
        return _row(row)

    def list(self, tenant_id: str, limit: int = 500) -> Sequence[StoredCustomUnit]:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                f"SELECT {_COLUMNS} FROM uom_custom_units ORDER BY unit_code LIMIT %s", (limit,)
            )
            rows = cur.fetchall()
        return [_row(r) for r in rows]

    def update(
        self, tenant_id: str, unit_code: str, factor_to_base: Decimal, display_name: str
    ) -> StoredCustomUnit:
        # The dimension is not editable: changing a unit's dimension would silently reinterpret every
        # quantity recorded in it. A dimension change is a delete-and-recreate, deliberately.
        try:
            with db.tenant_session(tenant_id) as cur:
                cur.execute(
                    f"UPDATE uom_custom_units "
                    f"SET factor_to_base = %s, display_name = %s, updated_at = CURRENT_TIMESTAMP "
                    f"WHERE unit_code = %s RETURNING {_COLUMNS}",
                    (factor_to_base, display_name, unit_code),
                )
                row = cur.fetchone()
        except psycopg.errors.CheckViolation as exc:
            raise CustomUnitError("factor must be positive") from exc
        if row is None:
            raise CustomUnitNotFoundError(f"custom unit {unit_code!r} not found in this tenant")
        return _row(row)

    def delete(self, tenant_id: str, unit_code: str) -> None:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "DELETE FROM uom_custom_units WHERE unit_code = %s RETURNING unit_code", (unit_code,)
            )
            row = cur.fetchone()
        if row is None:
            raise CustomUnitNotFoundError(f"custom unit {unit_code!r} not found in this tenant")

    def registry_for(self, tenant_id: str) -> "uom.UnitRegistry":
        """Build this tenant's unit registry: the standard units plus its custom ones, so a conversion
        involving a custom unit works exactly like a standard one — through the shared base."""
        custom = {
            u.unit_code: uom._UnitDef(u.dimension, u.factor_to_base) for u in self.list(tenant_id)
        }
        return uom.STANDARD.with_custom(custom)
