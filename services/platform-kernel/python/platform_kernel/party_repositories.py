"""Tenant-scoped party graph — MILE-4.1 (BOPEN-PARTY-001).

Every method runs through `db.tenant_session`, so isolation is the row-level security policy's
property and this module's, and nothing else — the same contract as `repositories.py`. A party is a
business entity (person or organization) owned by a tenant, distinct from a principal (an
authentication identity).

There is no `get(party_id)` without a tenant, deliberately: an unscoped read of a tenant-owned table
is the shape of a cross-tenant disclosure even when the caller means well.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Sequence

import psycopg

from . import db


class PartyRepositoryError(RuntimeError):
    """Base for party repository failures."""


class PartyNotFoundError(PartyRepositoryError):
    """A party does not exist in this tenant (indistinguishable from belonging to another)."""


class PartyRelationshipError(PartyRepositoryError):
    """A relationship could not be formed — a self-relationship, or an endpoint that is not a
    party of this tenant. The database refuses both; this translates the refusal for the caller."""


@dataclass(frozen=True)
class StoredParty:
    id: str
    tenant_id: str
    party_type: str
    display_name: str
    status: str


@dataclass(frozen=True)
class StoredPartyRelationship:
    id: str
    tenant_id: str
    from_party_id: str
    to_party_id: str
    relationship_type: str


def _party(row) -> StoredParty:
    return StoredParty(
        id=str(row[0]),
        tenant_id=str(row[1]),
        party_type=row[2],
        display_name=row[3],
        status=row[4],
    )


class PartyRepository:
    """Tenant-scoped. Every method runs under the tenant's own isolation policy."""

    _COLUMNS = "id, tenant_id, party_type, display_name, status"

    def create(self, tenant_id: str, party_type: str, display_name: str) -> StoredParty:
        party_id = str(uuid.uuid4())
        try:
            with db.tenant_session(tenant_id) as cur:
                cur.execute(
                    f"INSERT INTO parties (id, tenant_id, party_type, display_name) "
                    f"VALUES (%s, %s, %s, %s) RETURNING {self._COLUMNS}",
                    (party_id, tenant_id, party_type, display_name),
                )
                row = cur.fetchone()
        except psycopg.errors.CheckViolation as exc:
            # chk_party_type: an unrecognised party_type. Translated so the endpoint returns 422,
            # not a 500 that leaks the constraint name.
            raise PartyRepositoryError("party_type is not one of person, organization") from exc
        return _party(row)

    def get(self, tenant_id: str, party_id: str) -> StoredParty:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(f"SELECT {self._COLUMNS} FROM parties WHERE id = %s", (party_id,))
            row = cur.fetchone()
        if row is None:
            raise PartyNotFoundError(f"party {party_id} not found in this tenant")
        return _party(row)

    def list(self, tenant_id: str, limit: int = 100) -> Sequence[StoredParty]:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                f"SELECT {self._COLUMNS} FROM parties ORDER BY created_at LIMIT %s", (limit,)
            )
            rows = cur.fetchall()
        return [_party(row) for row in rows]

    def create_relationship(
        self, tenant_id: str, from_party_id: str, to_party_id: str, relationship_type: str
    ) -> StoredPartyRelationship:
        rel_id = str(uuid.uuid4())
        try:
            with db.tenant_session(tenant_id) as cur:
                cur.execute(
                    "INSERT INTO party_relationships "
                    "(id, tenant_id, from_party_id, to_party_id, relationship_type) "
                    "VALUES (%s, %s, %s, %s, %s) "
                    "RETURNING id, tenant_id, from_party_id, to_party_id, relationship_type",
                    (rel_id, tenant_id, from_party_id, to_party_id, relationship_type),
                )
                row = cur.fetchone()
        except psycopg.errors.CheckViolation as exc:
            # chk_no_self_relationship or chk_relationship_type.
            raise PartyRelationshipError(
                "a party cannot relate to itself, and the type must be a known relationship type"
            ) from exc
        except psycopg.errors.ForeignKeyViolation as exc:
            # The composite FK to parties(tenant_id, id): an endpoint that is not a party of this
            # tenant. A cross-tenant relationship is refused here at the database.
            raise PartyRelationshipError(
                "both parties must exist in this tenant"
            ) from exc
        return StoredPartyRelationship(
            id=str(row[0]),
            tenant_id=str(row[1]),
            from_party_id=str(row[2]),
            to_party_id=str(row[3]),
            relationship_type=row[4],
        )
