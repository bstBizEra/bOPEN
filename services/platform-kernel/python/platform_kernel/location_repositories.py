"""Tenant-scoped Location Registry — MILE-4.2 Location foundation (BOPEN-LOC-001, DEC-P4-ENTRY §11).

A Location is a stable, immutable, tenant-owned identity for a named place/site. It is deliberately NOT
an address, a coordinate, or a provider id: identity is never derived from mutable external data
(LOC-INV-03). Around that identity the registry keeps versioned addresses, point geometry observations,
external identifiers, a bounded `contains` relationship, and an append-only history.

Every method runs through `db.tenant_session`, so isolation is the row-level-security policy's property
and this module's, and nothing else — the same contract as `party_repositories.py`. There is no unscoped
read of a location table, deliberately: an unscoped read of a tenant-owned table is the shape of a
cross-tenant disclosure even when the caller means well.

Two keystones live here rather than in the database, because the database cannot see them:

  Provider distrust (LOC-INV-05/06). A geometry observation is born a `candidate`. `accept` is a
  distinct, authorized action that requires an explicit actor AND the provenance an accepted point must
  carry (source, observed_at, confidence). "HTTP 200 does not mean accepted."

  Containment acyclicity (LOC-INV-09). A row CHECK cannot see a cycle; before inserting `from CONTAINS
  to`, a WITH RECURSIVE walk of the live `contains` graph asks whether `from` is already reachable FROM
  `to` — if it is, the new edge would close a cycle and is refused.

Precise coordinates are higher-sensitivity (LOC-D-06): the append-only history records only SAFE
metadata (ids, event types, states), never a longitude/latitude, and the API redacts coordinates from
every audit record.
"""

from __future__ import annotations

import json
import math
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Sequence

import psycopg

from . import db
from . import uom
from . import uom_repositories as uom_repo


class LocationError(RuntimeError):
    """Base for location-registry failures."""


class LocationNotFoundError(LocationError):
    """A location (or child row) does not exist in this tenant (indistinguishable from another's)."""


class LocationConflictError(LocationError):
    """A duplicate code, a stale revision, a live identifier collision, or a duplicate/second-parent
    relationship edge."""


class LocationValidationError(LocationError):
    """A governed vocabulary is violated, an accuracy unit is not a UOM length unit, or a lifecycle
    transition is undefined."""


class CoordinateValidityError(LocationError):
    """A NaN/∞, out-of-range, or otherwise invalid coordinate (LOC-INV-04)."""


class ProviderAcceptanceError(LocationError):
    """An observation cannot be accepted: it is not a candidate, lacks required provenance, or the
    acceptance carries no explicit actor (LOC-INV-05/06)."""


class RelationshipCycleError(LocationError):
    """A `contains` edge that would close a containment cycle, or a self-link (LOC-INV-09)."""


# location: proposed -> active <-> inactive -> retired (terminal). Every other move — including any
# reactivation after retirement — is undefined and refused (LOC-INV-10).
_ALLOWED_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    {
        ("proposed", "active"),
        ("active", "inactive"),
        ("inactive", "active"),
        ("active", "retired"),
        ("inactive", "retired"),
    }
)


# --------------------------------------------------------------------------------------
# Stored value types
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class StoredLocation:
    id: str
    tenant_id: str
    code: str
    name: str
    location_type: str
    lifecycle_state: str
    current_address_version_id: str | None
    current_geometry_observation_id: str | None
    revision: int


@dataclass(frozen=True)
class StoredAddressVersion:
    id: str
    tenant_id: str
    location_id: str
    version_number: int
    country_code: str
    premise: str | None
    thoroughfare: str | None
    locality: str | None
    admin_area: str | None
    postal_code: str | None
    recipient: str | None
    components: dict | None
    original_input: str
    rendered: str | None
    language_tag: str | None
    script_tag: str | None
    template_profile: str | None
    verification_state: str
    confidence: Decimal | None
    effective_from: datetime
    effective_to: datetime | None
    revision: int


@dataclass(frozen=True)
class StoredGeometryObservation:
    id: str
    tenant_id: str
    location_id: str
    longitude: Decimal
    latitude: Decimal
    crs: str
    accuracy_radius_value: Decimal | None
    accuracy_radius_unit: str | None
    capture_method: str | None
    source: str | None
    confidence: Decimal | None
    observed_at: datetime | None
    received_at: datetime
    acceptance_state: str
    accepted_by: str | None
    rejected_reason: str | None
    revision: int


@dataclass(frozen=True)
class StoredExternalIdentifier:
    id: str
    tenant_id: str
    location_id: str
    scheme: str
    value: str
    issuer: str | None
    effective_from: datetime
    effective_to: datetime | None
    is_primary: bool
    provenance: str | None


@dataclass(frozen=True)
class StoredRelationship:
    id: str
    tenant_id: str
    from_location_id: str
    to_location_id: str
    relationship_type: str
    effective_from: datetime
    effective_to: datetime | None


@dataclass(frozen=True)
class StoredHistoryEvent:
    id: str
    tenant_id: str
    location_id: str
    event_type: str
    detail: dict | None
    at: datetime


_LOCATION_COLUMNS = (
    "id, tenant_id, code, name, location_type, lifecycle_state, "
    "current_address_version_id, current_geometry_observation_id, revision"
)

_ADDR_COLUMNS = (
    "id, tenant_id, location_id, version_number, country_code, premise, thoroughfare, locality, "
    "admin_area, postal_code, recipient, components, original_input, rendered, language_tag, "
    "script_tag, template_profile, verification_state, confidence, effective_from, effective_to, "
    "revision"
)

_GEO_COLUMNS = (
    "id, tenant_id, location_id, longitude, latitude, crs, accuracy_radius_value, "
    "accuracy_radius_unit, capture_method, source, confidence, observed_at, received_at, "
    "acceptance_state, accepted_by, rejected_reason, revision"
)

_EXTID_COLUMNS = (
    "id, tenant_id, location_id, scheme, value, issuer, effective_from, effective_to, is_primary, "
    "provenance"
)

_REL_COLUMNS = (
    "id, tenant_id, from_location_id, to_location_id, relationship_type, effective_from, effective_to"
)


def _location(row) -> StoredLocation:
    return StoredLocation(
        id=str(row[0]),
        tenant_id=str(row[1]),
        code=row[2],
        name=row[3],
        location_type=row[4],
        lifecycle_state=row[5],
        current_address_version_id=str(row[6]) if row[6] is not None else None,
        current_geometry_observation_id=str(row[7]) if row[7] is not None else None,
        revision=row[8],
    )


def _address(row) -> StoredAddressVersion:
    return StoredAddressVersion(
        id=str(row[0]),
        tenant_id=str(row[1]),
        location_id=str(row[2]),
        version_number=row[3],
        country_code=row[4],
        premise=row[5],
        thoroughfare=row[6],
        locality=row[7],
        admin_area=row[8],
        postal_code=row[9],
        recipient=row[10],
        components=row[11],
        original_input=row[12],
        rendered=row[13],
        language_tag=row[14],
        script_tag=row[15],
        template_profile=row[16],
        verification_state=row[17],
        confidence=row[18],
        effective_from=row[19],
        effective_to=row[20],
        revision=row[21],
    )


def _geometry(row) -> StoredGeometryObservation:
    return StoredGeometryObservation(
        id=str(row[0]),
        tenant_id=str(row[1]),
        location_id=str(row[2]),
        longitude=row[3],
        latitude=row[4],
        crs=row[5],
        accuracy_radius_value=row[6],
        accuracy_radius_unit=row[7],
        capture_method=row[8],
        source=row[9],
        confidence=row[10],
        observed_at=row[11],
        received_at=row[12],
        acceptance_state=row[13],
        accepted_by=row[14],
        rejected_reason=row[15],
        revision=row[16],
    )


def _external_identifier(row) -> StoredExternalIdentifier:
    return StoredExternalIdentifier(
        id=str(row[0]),
        tenant_id=str(row[1]),
        location_id=str(row[2]),
        scheme=row[3],
        value=row[4],
        issuer=row[5],
        effective_from=row[6],
        effective_to=row[7],
        is_primary=row[8],
        provenance=row[9],
    )


def _relationship(row) -> StoredRelationship:
    return StoredRelationship(
        id=str(row[0]),
        tenant_id=str(row[1]),
        from_location_id=str(row[2]),
        to_location_id=str(row[3]),
        relationship_type=row[4],
        effective_from=row[5],
        effective_to=row[6],
    )


def _coordinate(value: object, low: Decimal, high: Decimal, what: str) -> Decimal:
    """Validate one coordinate to an exact Decimal in [low, high], refusing NaN/∞ loudly.

    This is belt-and-braces with the chk_geo_lon/chk_geo_lat database constraints (LOC-INV-04): a bad
    coordinate is refused before the insert with a clean CoordinateValidityError, and the constraint
    still holds if this check is ever bypassed. A float is accepted from the boundary (the API may pass
    a bounded float), but is screened for NaN/∞ first and then converted through its string form so no
    binary-float noise is stored.
    """
    if isinstance(value, bool):
        raise CoordinateValidityError(f"{what} must be a number, not a bool")
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise CoordinateValidityError(f"{what} must be a finite number, not NaN or infinity")
        candidate = Decimal(str(value))
    elif isinstance(value, (int, Decimal)):
        candidate = Decimal(value)
    elif isinstance(value, str):
        try:
            candidate = Decimal(value)
        except InvalidOperation:
            raise CoordinateValidityError(f"{what} {value!r} is not a valid decimal") from None
    else:
        raise CoordinateValidityError(f"{what} must be a number or decimal string")
    if candidate.is_nan() or not candidate.is_finite():
        raise CoordinateValidityError(f"{what} must be a finite number, not NaN or infinity")
    if candidate < low or candidate > high:
        raise CoordinateValidityError(
            f"{what} {candidate} is out of range [{low}, {high}]"
        )
    return candidate


def _append_history(cur, tenant_id: str, location_id: str, event_type: str, detail: dict | None) -> None:
    """Append one SAFE-metadata event. detail must never carry precise coordinates (LOC-INV-14)."""
    cur.execute(
        "INSERT INTO location_history (id, tenant_id, location_id, event_type, detail) "
        "VALUES (%s, %s, %s, %s, %s::jsonb)",
        (
            str(uuid.uuid4()),
            tenant_id,
            location_id,
            event_type,
            json.dumps(detail) if detail is not None else None,
        ),
    )


class LocationRepository:
    """Tenant-scoped. Every method runs under the tenant's own isolation policy."""

    # -- Location identity & lifecycle -------------------------------------------------

    def create(
        self, tenant_id: str, code: str, name: str, location_type: str
    ) -> StoredLocation:
        location_id = str(uuid.uuid4())
        try:
            with db.tenant_session(tenant_id) as cur:
                cur.execute(
                    f"INSERT INTO locations (id, tenant_id, code, name, location_type) "
                    f"VALUES (%s, %s, %s, %s, %s) RETURNING {_LOCATION_COLUMNS}",
                    (location_id, tenant_id, code, name, location_type),
                )
                row = cur.fetchone()
                _append_history(
                    cur, tenant_id, location_id, "location.registered",
                    {"code": code, "location_type": location_type},
                )
        except psycopg.errors.UniqueViolation:
            raise LocationConflictError(f"a location with code {code!r} already exists") from None
        except psycopg.errors.CheckViolation as exc:
            raise LocationValidationError(
                "location_type must be one of site, building, depot, office, warehouse, other"
            ) from exc
        return _location(row)

    def get(self, tenant_id: str, location_id: str) -> StoredLocation:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                f"SELECT {_LOCATION_COLUMNS} FROM locations WHERE id = %s", (location_id,)
            )
            row = cur.fetchone()
        if row is None:
            raise LocationNotFoundError(f"location {location_id} not found in this tenant")
        return _location(row)

    def list(self, tenant_id: str, limit: int = 500) -> Sequence[StoredLocation]:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                f"SELECT {_LOCATION_COLUMNS} FROM locations ORDER BY created_at LIMIT %s", (limit,)
            )
            rows = cur.fetchall()
        return [_location(r) for r in rows]

    def update(
        self,
        tenant_id: str,
        location_id: str,
        expected_revision: int,
        name: str | None = None,
        code: str | None = None,
    ) -> StoredLocation:
        """Rename / re-code a location under an optimistic revision check. Identity (id) never changes
        (LOC-INV-03); the read and write are one transaction, so a stale revision is refused before any
        row changes."""
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                f"SELECT {_LOCATION_COLUMNS} FROM locations WHERE id = %s FOR UPDATE",
                (location_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise LocationNotFoundError(f"location {location_id} not found in this tenant")
            current = _location(row)
            if current.revision != expected_revision:
                raise LocationConflictError(
                    f"stale revision: expected {current.revision}, got {expected_revision}"
                )
            new_name = current.name if name is None else name
            new_code = current.code if code is None else code
            try:
                cur.execute(
                    f"UPDATE locations SET name = %s, code = %s, revision = revision + 1, "
                    f"updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING {_LOCATION_COLUMNS}",
                    (new_name, new_code, location_id),
                )
                updated = cur.fetchone()
            except psycopg.errors.UniqueViolation:
                raise LocationConflictError(
                    f"a location with code {new_code!r} already exists"
                ) from None
            _append_history(cur, tenant_id, location_id, "location.updated", {"code": new_code})
        return _location(updated)

    def transition(
        self, tenant_id: str, location_id: str, to_state: str, actor: str | None = None
    ) -> StoredLocation:
        """Move a location along the lifecycle, but only along a defined edge. An undefined transition
        or a reactivation after retirement is refused (LOC-INV-10). The read, check, update and history
        append are one transaction."""
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT lifecycle_state FROM locations WHERE id = %s FOR UPDATE", (location_id,)
            )
            row = cur.fetchone()
            if row is None:
                raise LocationNotFoundError(f"location {location_id} not found in this tenant")
            from_state = row[0]
            if (from_state, to_state) not in _ALLOWED_TRANSITIONS:
                raise LocationValidationError(
                    f"transition {from_state!r} -> {to_state!r} is not a defined lifecycle move"
                )
            cur.execute(
                f"UPDATE locations SET lifecycle_state = %s, revision = revision + 1, "
                f"updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING {_LOCATION_COLUMNS}",
                (to_state, location_id),
            )
            updated = cur.fetchone()
            _append_history(
                cur, tenant_id, location_id, "location.lifecycle_changed",
                {"from": from_state, "to": to_state, "actor": actor},
            )
        return _location(updated)

    # -- Address versions --------------------------------------------------------------

    def add_address_version(
        self,
        tenant_id: str,
        location_id: str,
        *,
        country_code: str,
        original_input: str,
        premise: str | None = None,
        thoroughfare: str | None = None,
        locality: str | None = None,
        admin_area: str | None = None,
        postal_code: str | None = None,
        recipient: str | None = None,
        components: dict | None = None,
        rendered: str | None = None,
        language_tag: str | None = None,
        script_tag: str | None = None,
        template_profile: str | None = None,
    ) -> StoredAddressVersion:
        """Add a new address version and make it the current one. The prior current version's
        effective_to is set in the SAME transaction, so the partial unique index unq_addr_current
        (at most one current version per location — LOC-INV-07) always holds."""
        version_id = str(uuid.uuid4())
        with db.tenant_session(tenant_id) as cur:
            # The location must exist in this tenant (also the composite FK, but this gives a clean 404).
            cur.execute("SELECT 1 FROM locations WHERE id = %s FOR UPDATE", (location_id,))
            if cur.fetchone() is None:
                raise LocationNotFoundError(f"location {location_id} not found in this tenant")
            # Close the current version first, then insert the new current — never two NULLs at once.
            cur.execute(
                "UPDATE location_address_versions SET effective_to = CURRENT_TIMESTAMP "
                "WHERE location_id = %s AND effective_to IS NULL",
                (location_id,),
            )
            cur.execute(
                "SELECT COALESCE(MAX(version_number), 0) + 1 FROM location_address_versions "
                "WHERE location_id = %s",
                (location_id,),
            )
            version_number = cur.fetchone()[0]
            try:
                cur.execute(
                    f"INSERT INTO location_address_versions "
                    f"(id, tenant_id, location_id, version_number, country_code, premise, "
                    f" thoroughfare, locality, admin_area, postal_code, recipient, components, "
                    f" original_input, rendered, language_tag, script_tag, template_profile) "
                    f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s) "
                    f"RETURNING {_ADDR_COLUMNS}",
                    (
                        version_id, tenant_id, location_id, version_number, country_code, premise,
                        thoroughfare, locality, admin_area, postal_code, recipient,
                        json.dumps(components) if components is not None else None,
                        original_input, rendered, language_tag, script_tag, template_profile,
                    ),
                )
                row = cur.fetchone()
            except psycopg.errors.CheckViolation as exc:
                raise LocationValidationError("invalid address version fields") from exc
            cur.execute(
                "UPDATE locations SET current_address_version_id = %s, revision = revision + 1, "
                "updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (version_id, location_id),
            )
            _append_history(
                cur, tenant_id, location_id, "location.address_changed",
                {"version_number": version_number, "country_code": country_code},
            )
        return _address(row)

    def list_address_versions(
        self, tenant_id: str, location_id: str, limit: int = 500
    ) -> Sequence[StoredAddressVersion]:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                f"SELECT {_ADDR_COLUMNS} FROM location_address_versions WHERE location_id = %s "
                f"ORDER BY version_number LIMIT %s",
                (location_id, limit),
            )
            rows = cur.fetchall()
        return [_address(r) for r in rows]

    def set_current_address_version(
        self, tenant_id: str, location_id: str, version_id: str
    ) -> StoredAddressVersion:
        """Make a specific (possibly older) address version current — close whatever is current, then
        reopen the target — one transaction, so unq_addr_current holds throughout (LOC-INV-07)."""
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT id FROM location_address_versions WHERE id = %s AND location_id = %s "
                "FOR UPDATE",
                (version_id, location_id),
            )
            if cur.fetchone() is None:
                raise LocationNotFoundError(
                    f"address version {version_id} not found for this location in this tenant"
                )
            cur.execute(
                "UPDATE location_address_versions SET effective_to = CURRENT_TIMESTAMP "
                "WHERE location_id = %s AND effective_to IS NULL AND id <> %s",
                (location_id, version_id),
            )
            cur.execute(
                f"UPDATE location_address_versions SET effective_to = NULL, "
                f"effective_from = CURRENT_TIMESTAMP, revision = revision + 1 "
                f"WHERE id = %s RETURNING {_ADDR_COLUMNS}",
                (version_id,),
            )
            row = cur.fetchone()
            cur.execute(
                "UPDATE locations SET current_address_version_id = %s, revision = revision + 1, "
                "updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (version_id, location_id),
            )
            _append_history(
                cur, tenant_id, location_id, "location.address_changed",
                {"set_current": True},
            )
        return _address(row)

    # -- Geometry observations ---------------------------------------------------------

    def observe(
        self,
        tenant_id: str,
        location_id: str,
        longitude: object,
        latitude: object,
        *,
        crs: str = "OGC:CRS84",
        accuracy_radius_value: object | None = None,
        accuracy_radius_unit: str | None = None,
        capture_method: str | None = None,
        source: str | None = None,
        confidence: object | None = None,
        observed_at: datetime | None = None,
    ) -> StoredGeometryObservation:
        """Record a point observation as a CANDIDATE (never accepted on creation — LOC-INV-06).

        Coordinate validity (LOC-INV-04) is checked BEFORE the insert (NaN/∞/range) as belt-and-braces
        with the database CHECK constraints. If an accuracy radius is given, its unit must be a UOM
        `length` unit in the tenant's registry (standard + custom); a non-length or unknown unit is
        refused, and the magnitude is stored as an exact Decimal, never a float (LOC-D-04).
        """
        if crs != "OGC:CRS84":
            raise CoordinateValidityError(f"unsupported CRS {crs!r}; only OGC:CRS84 is supported")
        lon = _coordinate(longitude, Decimal(-180), Decimal(180), "longitude")
        lat = _coordinate(latitude, Decimal(-90), Decimal(90), "latitude")

        acc_value: Decimal | None = None
        if accuracy_radius_value is not None or accuracy_radius_unit is not None:
            if accuracy_radius_value is None or accuracy_radius_unit is None:
                raise LocationValidationError(
                    "accuracy radius needs both a value and a length unit, or neither"
                )
            # Validate the unit is a known length-dimension unit via the tenant's UOM registry, and the
            # magnitude an exact Decimal (uom rejects a float outright).
            registry = uom_repo.CustomUnitRepository().registry_for(tenant_id)
            try:
                dimension = registry.dimension_of(accuracy_radius_unit)
            except uom.UnknownUnitError:
                raise LocationValidationError(
                    f"accuracy_radius_unit {accuracy_radius_unit!r} is not a known unit"
                ) from None
            if dimension != "length":
                raise LocationValidationError(
                    f"accuracy_radius_unit {accuracy_radius_unit!r} is a {dimension} unit, not length"
                )
            try:
                acc_value = uom.Quantity(accuracy_radius_value, accuracy_radius_unit).magnitude
            except uom.UomError as exc:
                raise LocationValidationError(str(exc)) from exc

        observation_id = str(uuid.uuid4())
        try:
            with db.tenant_session(tenant_id) as cur:
                cur.execute("SELECT 1 FROM locations WHERE id = %s", (location_id,))
                if cur.fetchone() is None:
                    raise LocationNotFoundError(f"location {location_id} not found in this tenant")
                cur.execute(
                    f"INSERT INTO location_geometry_observations "
                    f"(id, tenant_id, location_id, longitude, latitude, crs, accuracy_radius_value, "
                    f" accuracy_radius_unit, capture_method, source, confidence, observed_at) "
                    f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
                    f"RETURNING {_GEO_COLUMNS}",
                    (
                        observation_id, tenant_id, location_id, lon, lat, crs, acc_value,
                        accuracy_radius_unit, capture_method, source, confidence, observed_at,
                    ),
                )
                row = cur.fetchone()
                # SAFE metadata only — never the coordinates (LOC-INV-14).
                _append_history(
                    cur, tenant_id, location_id, "location.geometry_observed",
                    {"observation_id": observation_id, "acceptance_state": "candidate"},
                )
        except psycopg.errors.CheckViolation as exc:
            # The coordinate CHECK is the database keystone if the pre-check is ever bypassed.
            raise CoordinateValidityError("coordinate failed a database validity constraint") from exc
        return _geometry(row)

    def get_observation(
        self, tenant_id: str, observation_id: str
    ) -> StoredGeometryObservation:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                f"SELECT {_GEO_COLUMNS} FROM location_geometry_observations WHERE id = %s",
                (observation_id,),
            )
            row = cur.fetchone()
        if row is None:
            raise LocationNotFoundError(f"observation {observation_id} not found in this tenant")
        return _geometry(row)

    def list_observations(
        self, tenant_id: str, location_id: str, limit: int = 500
    ) -> Sequence[StoredGeometryObservation]:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                f"SELECT {_GEO_COLUMNS} FROM location_geometry_observations WHERE location_id = %s "
                f"ORDER BY received_at LIMIT %s",
                (location_id, limit),
            )
            rows = cur.fetchall()
        return [_geometry(r) for r in rows]

    def accept_observation(
        self, tenant_id: str, observation_id: str, actor: str | None
    ) -> StoredGeometryObservation:
        """Accept a candidate observation — a distinct, authorized action (LOC-INV-06). Requires an
        explicit actor AND the provenance an accepted point must carry: source, observed_at, confidence
        (LOC-INV-05). On success the observation becomes `accepted` and the location's current geometry
        pointer is updated, atomically. An HTTP 200 on `observe` never reaches this state."""
        if not actor:
            raise ProviderAcceptanceError("acceptance requires an explicit authorized actor")
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT location_id, acceptance_state, source, observed_at, confidence "
                "FROM location_geometry_observations WHERE id = %s FOR UPDATE",
                (observation_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise LocationNotFoundError(
                    f"observation {observation_id} not found in this tenant"
                )
            location_id, state, source, observed_at, confidence = (
                str(row[0]), row[1], row[2], row[3], row[4],
            )
            if state not in ("received", "candidate"):
                raise ProviderAcceptanceError(
                    f"observation is {state!r}, not a candidate that can be accepted"
                )
            if source is None or observed_at is None or confidence is None:
                raise ProviderAcceptanceError(
                    "an observation missing source, observed_at, or confidence cannot be accepted"
                )
            cur.execute(
                f"UPDATE location_geometry_observations SET acceptance_state = 'accepted', "
                f"accepted_by = %s, revision = revision + 1 WHERE id = %s RETURNING {_GEO_COLUMNS}",
                (actor, observation_id),
            )
            updated = cur.fetchone()
            cur.execute(
                "UPDATE locations SET current_geometry_observation_id = %s, revision = revision + 1, "
                "updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (observation_id, location_id),
            )
            _append_history(
                cur, tenant_id, location_id, "location.geometry_accepted",
                {"observation_id": observation_id, "actor": actor},
            )
        return _geometry(updated)

    def reject_observation(
        self, tenant_id: str, observation_id: str, reason: str | None = None
    ) -> StoredGeometryObservation:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT location_id, acceptance_state FROM location_geometry_observations "
                "WHERE id = %s FOR UPDATE",
                (observation_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise LocationNotFoundError(
                    f"observation {observation_id} not found in this tenant"
                )
            location_id, state = str(row[0]), row[1]
            if state not in ("received", "candidate"):
                raise ProviderAcceptanceError(
                    f"observation is {state!r}, not a candidate that can be rejected"
                )
            cur.execute(
                f"UPDATE location_geometry_observations SET acceptance_state = 'rejected', "
                f"rejected_reason = %s, revision = revision + 1 WHERE id = %s RETURNING {_GEO_COLUMNS}",
                (reason, observation_id),
            )
            updated = cur.fetchone()
            _append_history(
                cur, tenant_id, location_id, "location.geometry_rejected",
                {"observation_id": observation_id},
            )
        return _geometry(updated)

    # -- External identifiers ----------------------------------------------------------

    def add_external_identifier(
        self,
        tenant_id: str,
        location_id: str,
        scheme: str,
        value: str,
        *,
        issuer: str | None = None,
        is_primary: bool = False,
        provenance: str | None = None,
    ) -> StoredExternalIdentifier:
        """Add an external identifier. A live (effective_to IS NULL) scheme/value collision within the
        tenant is refused (LOC-INV-08)."""
        extid_id = str(uuid.uuid4())
        try:
            with db.tenant_session(tenant_id) as cur:
                cur.execute(
                    f"INSERT INTO location_external_identifiers "
                    f"(id, tenant_id, location_id, scheme, value, issuer, is_primary, provenance) "
                    f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING {_EXTID_COLUMNS}",
                    (extid_id, tenant_id, location_id, scheme, value, issuer, is_primary, provenance),
                )
                row = cur.fetchone()
                _append_history(
                    cur, tenant_id, location_id, "location.external_identifier_changed",
                    {"scheme": scheme},
                )
        except psycopg.errors.UniqueViolation:
            raise LocationConflictError(
                f"a live external identifier {scheme!r} = {value!r} already exists"
            ) from None
        except psycopg.errors.ForeignKeyViolation:
            raise LocationNotFoundError(f"location {location_id} not found in this tenant") from None
        return _external_identifier(row)

    def list_external_identifiers(
        self, tenant_id: str, location_id: str, limit: int = 500
    ) -> Sequence[StoredExternalIdentifier]:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                f"SELECT {_EXTID_COLUMNS} FROM location_external_identifiers WHERE location_id = %s "
                f"ORDER BY created_at LIMIT %s",
                (location_id, limit),
            )
            rows = cur.fetchall()
        return [_external_identifier(r) for r in rows]

    # -- Relationships -----------------------------------------------------------------

    def add_contains(
        self, tenant_id: str, from_location_id: str, to_location_id: str
    ) -> StoredRelationship:
        """Add a live `contains` edge `from CONTAINS to`, refusing: a self-link; a cross-tenant/absent
        endpoint; a duplicate live edge; a second live parent for the child; and a containment CYCLE.

        The cycle check is a real WITH RECURSIVE walk (LOC-INV-09), because a row CHECK cannot see a
        cycle: adding `from CONTAINS to` closes a cycle iff `from` is already reachable FROM `to` via
        existing live `contains` edges (i.e. `to` transitively contains `from`). The walk and the insert
        run in one transaction so no concurrent edge can slip a cycle past the check.
        """
        if from_location_id == to_location_id:
            raise RelationshipCycleError("a location cannot contain itself")
        rel_id = str(uuid.uuid4())
        try:
            with db.tenant_session(tenant_id) as cur:
                cur.execute(
                    "WITH RECURSIVE reach AS ("
                    "  SELECT to_location_id AS n FROM location_relationships "
                    "  WHERE from_location_id = %(to)s AND relationship_type = 'contains' "
                    "    AND effective_to IS NULL "
                    "  UNION "
                    "  SELECT lr.to_location_id FROM location_relationships lr "
                    "  JOIN reach ON lr.from_location_id = reach.n "
                    "  WHERE lr.relationship_type = 'contains' AND lr.effective_to IS NULL"
                    ") SELECT 1 FROM reach WHERE n = %(from)s LIMIT 1",
                    {"to": to_location_id, "from": from_location_id},
                )
                if cur.fetchone() is not None:
                    raise RelationshipCycleError(
                        "this containment edge would close a cycle"
                    )
                cur.execute(
                    f"INSERT INTO location_relationships "
                    f"(id, tenant_id, from_location_id, to_location_id, relationship_type) "
                    f"VALUES (%s, %s, %s, %s, 'contains') RETURNING {_REL_COLUMNS}",
                    (rel_id, tenant_id, from_location_id, to_location_id),
                )
                row = cur.fetchone()
                _append_history(
                    cur, tenant_id, from_location_id, "location.relationship_changed",
                    {"to_location_id": to_location_id, "relationship_type": "contains"},
                )
        except psycopg.errors.UniqueViolation:
            # A duplicate live edge (unq_rel_live_edge) or a second live parent (unq_rel_one_active_parent).
            raise LocationConflictError(
                "a live containment edge already exists, or the child already has an active parent"
            ) from None
        except psycopg.errors.CheckViolation:
            # chk_rel_no_self, if a self-link ever reaches the database.
            raise RelationshipCycleError("a location cannot contain itself") from None
        except psycopg.errors.ForeignKeyViolation:
            raise LocationNotFoundError(
                "a location in this relationship is not a location of this tenant"
            ) from None
        return _relationship(row)

    def list_relationships(
        self, tenant_id: str, location_id: str, limit: int = 500
    ) -> Sequence[StoredRelationship]:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                f"SELECT {_REL_COLUMNS} FROM location_relationships "
                f"WHERE from_location_id = %s OR to_location_id = %s "
                f"ORDER BY created_at LIMIT %s",
                (location_id, location_id, limit),
            )
            rows = cur.fetchall()
        return [_relationship(r) for r in rows]

    # -- History -----------------------------------------------------------------------

    def list_history(
        self, tenant_id: str, location_id: str, limit: int = 500
    ) -> Sequence[StoredHistoryEvent]:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT id, tenant_id, location_id, event_type, detail, at "
                "FROM location_history WHERE location_id = %s ORDER BY at LIMIT %s",
                (location_id, limit),
            )
            rows = cur.fetchall()
        return [
            StoredHistoryEvent(
                id=str(r[0]),
                tenant_id=str(r[1]),
                location_id=str(r[2]),
                event_type=r[3],
                detail=r[4],
                at=r[5],
            )
            for r in rows
        ]
