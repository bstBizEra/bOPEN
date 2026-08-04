"""Tenant-scoped Party ContactPoint registry — MILE-4.2 (BOPEN-PARTY-002, DEC-P4-ENTRY §10).

A contact point is a Party-owned, tenant-scoped, typed, purpose-classified, verifiable communication
endpoint (email or phone). It is the missing entity a future NotificationRecipientResolver resolves a
business recipient against, so a send never falls back to `principals.email`.

Every method runs through `db.tenant_session`, so isolation is the row-level-security policy's
property and this module's, and nothing else — the same contract as `party_repositories.py`. There is
no unscoped read of a contact point, deliberately: an unscoped read of a tenant-owned table is the
shape of a cross-tenant disclosure even when the caller means well.

The keystone (CP-INV-03): `resolve` yields a usable destination ONLY for a contact point that is
verified, of the authorized purpose, of the requested channel's type, currently effective, and
belonging to a Party of the caller's tenant (RLS). Unverified, failed, wrong-purpose, wrong-channel,
not-effective, cross-tenant, and `principals.email` are all refused — uniformly, as one
`RecipientUnresolved`, without revealing which rung failed (CP-INV-05).
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

import psycopg

from . import db


class ContactPointError(RuntimeError):
    """Base for contact-point failures."""


class ContactPointNotFoundError(ContactPointError):
    """A contact point does not exist in this tenant (indistinguishable from another tenant's)."""


class ContactPointConflictError(ContactPointError):
    """A duplicate endpoint for a Party, a stale revision, or a primary-flag conflict."""


class ContactPointValidationError(ContactPointError):
    """An endpoint value is malformed, or an endpoint type / purpose is not a governed vocabulary."""


class ContactPointPartyNotFoundError(ContactPointError):
    """The owning Party is not a Party of this tenant — the composite FK refuses the attachment."""


class RecipientUnresolved(ContactPointError):
    """The resolver could not produce a usable destination. Uniform and anti-enumerating: it does not
    reveal which keystone rung failed, nor whether the endpoint or Party exists in another tenant."""


# Administrative-assertion verify is the one governed, audited path that transitions to verified in
# this slice; the challenge ceremony (OTP/magic-link) is deferred (CP-D-05).
VERIFICATION_METHOD_ADMIN_ASSERTION = "administrative_assertion"

# channel -> endpoint_type (CP-D-06). A channel with no matching verified endpoint is a refusal, never
# a fallback to another channel or to principals.email.
_CHANNEL_TO_TYPE = {
    "email": "email",
    "sms": "phone",
    "voice": "phone",
}

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^\+?[0-9]{7,15}$")


@dataclass(frozen=True)
class StoredContactPoint:
    id: str
    tenant_id: str
    party_id: str
    endpoint_type: str
    endpoint_value: str
    purpose: str
    verification_state: str
    verification_method: str | None
    verified_at: datetime | None
    effective_from: datetime
    effective_to: datetime | None
    is_primary: bool
    provenance: str | None
    revision: int


@dataclass(frozen=True)
class RecipientSnapshot:
    """The minimal, frozen, verified endpoint returned for ONE send. Not a continuing consent, not a
    new contact master — evidence for a single resolve (§9.2)."""

    endpoint_type: str
    endpoint_value: str
    purpose: str
    party_id: str
    resolved_at: datetime


_COLUMNS = (
    "id, tenant_id, party_id, endpoint_type, endpoint_value, purpose, verification_state, "
    "verification_method, verified_at, effective_from, effective_to, is_primary, provenance, revision"
)


def _row(row) -> StoredContactPoint:
    return StoredContactPoint(
        id=str(row[0]),
        tenant_id=str(row[1]),
        party_id=str(row[2]),
        endpoint_type=row[3],
        endpoint_value=row[4],
        purpose=row[5],
        verification_state=row[6],
        verification_method=row[7],
        verified_at=row[8],
        effective_from=row[9],
        effective_to=row[10],
        is_primary=row[11],
        provenance=row[12],
        revision=row[13],
    )


def _validate_endpoint_form(endpoint_type: str, endpoint_value: str) -> None:
    """Reject an obviously invalid endpoint before it reaches the database. The CHECK constraint
    governs the type vocabulary; this governs the value form (RFC 5322-ish email, E.164-ish phone)."""
    value = (endpoint_value or "").strip()
    if endpoint_type == "email":
        if not _EMAIL_RE.match(value):
            raise ContactPointValidationError("email endpoint must be a valid address form")
    elif endpoint_type == "phone":
        if not _PHONE_RE.match(value):
            raise ContactPointValidationError(
                "phone endpoint must be E.164-ish: optional '+' and 7 to 15 digits"
            )
    else:
        # The database CHECK will refuse it too; failing here gives a clean 422 with a stable message.
        raise ContactPointValidationError("endpoint_type must be one of email, phone")


class ContactPointRepository:
    """Tenant-scoped. Every method runs under the tenant's own isolation policy."""

    def create(
        self,
        tenant_id: str,
        party_id: str,
        endpoint_type: str,
        endpoint_value: str,
        purpose: str,
        provenance: str | None = None,
    ) -> StoredContactPoint:
        # A new endpoint always starts unverified (CP-INV-04): the resolver refuses it until the
        # verification seam transitions it. No create path may mint a verified endpoint.
        _validate_endpoint_form(endpoint_type, endpoint_value)
        cp_id = str(uuid.uuid4())
        try:
            with db.tenant_session(tenant_id) as cur:
                cur.execute(
                    f"INSERT INTO party_contact_points "
                    f"(id, tenant_id, party_id, endpoint_type, endpoint_value, purpose, provenance) "
                    f"VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING {_COLUMNS}",
                    (cp_id, tenant_id, party_id, endpoint_type, endpoint_value, purpose, provenance),
                )
                row = cur.fetchone()
        except psycopg.errors.UniqueViolation:
            raise ContactPointConflictError(
                "this endpoint is already recorded for this party"
            ) from None
        except psycopg.errors.ForeignKeyViolation:
            # The composite FK to parties(tenant_id, id): the Party is not a Party of this tenant.
            raise ContactPointPartyNotFoundError(
                "party not found in this tenant"
            ) from None
        except psycopg.errors.CheckViolation as exc:
            # chk_cp_endpoint_type or chk_cp_purpose.
            raise ContactPointValidationError(
                "endpoint_type must be one of email, phone and purpose must be one of "
                "security_operational, transactional, billing, general"
            ) from exc
        return _row(row)

    def get(self, tenant_id: str, contact_point_id: str) -> StoredContactPoint:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                f"SELECT {_COLUMNS} FROM party_contact_points WHERE id = %s", (contact_point_id,)
            )
            row = cur.fetchone()
        if row is None:
            raise ContactPointNotFoundError(
                f"contact point {contact_point_id} not found in this tenant"
            )
        return _row(row)

    def list(self, tenant_id: str, party_id: str, limit: int = 500) -> Sequence[StoredContactPoint]:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                f"SELECT {_COLUMNS} FROM party_contact_points WHERE party_id = %s "
                f"ORDER BY created_at LIMIT %s",
                (party_id, limit),
            )
            rows = cur.fetchall()
        return [_row(r) for r in rows]

    def update(
        self,
        tenant_id: str,
        contact_point_id: str,
        expected_revision: int,
        endpoint_value: str | None = None,
        purpose: str | None = None,
        effective_to: datetime | None = None,
    ) -> StoredContactPoint:
        """Update value / purpose / effective interval under an optimistic revision check.

        Changing the endpoint VALUE re-opens the trust question, so it resets verification to
        `unverified` — a changed address has not been verified (CP-INV-04). The whole operation, read
        and write, is one transaction, so a stale revision is refused before any row changes.
        """
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                f"SELECT {_COLUMNS} FROM party_contact_points WHERE id = %s FOR UPDATE",
                (contact_point_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise ContactPointNotFoundError(
                    f"contact point {contact_point_id} not found in this tenant"
                )
            current = _row(row)
            if current.revision != expected_revision:
                raise ContactPointConflictError(
                    f"stale revision: expected {current.revision}, got {expected_revision}"
                )

            new_value = current.endpoint_value if endpoint_value is None else endpoint_value
            new_purpose = current.purpose if purpose is None else purpose
            if endpoint_value is not None:
                _validate_endpoint_form(current.endpoint_type, endpoint_value)
            # A value change invalidates verification; a purpose-only change preserves it.
            value_changed = endpoint_value is not None and endpoint_value != current.endpoint_value
            new_state = "unverified" if value_changed else current.verification_state
            new_method = None if value_changed else current.verification_method
            new_verified_at = None if value_changed else current.verified_at

            try:
                cur.execute(
                    f"UPDATE party_contact_points SET "
                    f"endpoint_value = %s, purpose = %s, effective_to = %s, "
                    f"verification_state = %s, verification_method = %s, verified_at = %s, "
                    f"revision = revision + 1, updated_at = CURRENT_TIMESTAMP "
                    f"WHERE id = %s RETURNING {_COLUMNS}",
                    (
                        new_value, new_purpose, effective_to,
                        new_state, new_method, new_verified_at,
                        contact_point_id,
                    ),
                )
                updated = cur.fetchone()
            except psycopg.errors.UniqueViolation:
                raise ContactPointConflictError(
                    "this endpoint is already recorded for this party"
                ) from None
            except psycopg.errors.CheckViolation as exc:
                raise ContactPointValidationError(
                    "purpose must be one of security_operational, transactional, billing, general"
                ) from exc
        return _row(updated)

    def retire(self, tenant_id: str, contact_point_id: str) -> StoredContactPoint:
        """Retire a contact point — set `effective_to = now` and clear the primary flag. NOT a hard
        delete: a verified/referenced endpoint keeps its row and its append-only verification history
        (CP-D-03). A retired endpoint is no longer effective, so the resolver will not return it, and
        clearing is_primary frees the one-live-primary slot for a replacement."""
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                f"UPDATE party_contact_points "
                f"SET effective_to = CURRENT_TIMESTAMP, is_primary = false, "
                f"    revision = revision + 1, updated_at = CURRENT_TIMESTAMP "
                f"WHERE id = %s AND (effective_to IS NULL OR effective_to > CURRENT_TIMESTAMP) "
                f"RETURNING {_COLUMNS}",
                (contact_point_id,),
            )
            row = cur.fetchone()
        if row is None:
            # Either it does not exist in this tenant, or it is already retired. Both read as
            # not-found to the caller — an already-retired endpoint has no live thing to retire.
            raise ContactPointNotFoundError(
                f"contact point {contact_point_id} not found (or already retired) in this tenant"
            )
        return _row(row)

    def set_primary(self, tenant_id: str, contact_point_id: str) -> StoredContactPoint:
        """Make this the primary contact point for its (party, type). At most one live primary per
        (party, type) — the partial unique index enforces it (CP-INV-08). The existing primary of the
        same scope is demoted first, in the same transaction, so the switch is atomic."""
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT party_id, endpoint_type FROM party_contact_points WHERE id = %s FOR UPDATE",
                (contact_point_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise ContactPointNotFoundError(
                    f"contact point {contact_point_id} not found in this tenant"
                )
            party_id, endpoint_type = str(row[0]), row[1]
            # Demote the current primary of this (party, type), if any, then promote the target.
            cur.execute(
                "UPDATE party_contact_points SET is_primary = false, updated_at = CURRENT_TIMESTAMP "
                "WHERE party_id = %s AND endpoint_type = %s AND is_primary AND id <> %s",
                (party_id, endpoint_type, contact_point_id),
            )
            cur.execute(
                f"UPDATE party_contact_points "
                f"SET is_primary = true, revision = revision + 1, updated_at = CURRENT_TIMESTAMP "
                f"WHERE id = %s RETURNING {_COLUMNS}",
                (contact_point_id,),
            )
            updated = cur.fetchone()
        return _row(updated)

    def verify_by_assertion(
        self, tenant_id: str, contact_point_id: str, actor_principal_id: str | None
    ) -> StoredContactPoint:
        """Transition unverified/failed -> verified by governed administrative assertion — the one
        audited verify path that ships in this slice; the challenge ceremony is deferred (CP-D-05).

        The state change and the append-only verification-event row are ONE transaction: either both
        happen or neither does. The event records the from_state, to_state, method and actor so the
        transition is evidenced (CP-INV-07) — and the event carries no endpoint value (CP-INV-06).
        """
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT verification_state FROM party_contact_points WHERE id = %s FOR UPDATE",
                (contact_point_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise ContactPointNotFoundError(
                    f"contact point {contact_point_id} not found in this tenant"
                )
            from_state = row[0]

            cur.execute(
                f"UPDATE party_contact_points SET "
                f"verification_state = 'verified', verification_method = %s, "
                f"verified_at = CURRENT_TIMESTAMP, revision = revision + 1, "
                f"updated_at = CURRENT_TIMESTAMP "
                f"WHERE id = %s RETURNING {_COLUMNS}",
                (VERIFICATION_METHOD_ADMIN_ASSERTION, contact_point_id),
            )
            updated = cur.fetchone()

            cur.execute(
                "INSERT INTO party_contact_point_verification_events "
                "(id, tenant_id, contact_point_id, from_state, to_state, method, actor_principal_id) "
                "VALUES (%s, %s, %s, %s, 'verified', %s, %s)",
                (
                    str(uuid.uuid4()), tenant_id, contact_point_id, from_state,
                    VERIFICATION_METHOD_ADMIN_ASSERTION, actor_principal_id,
                ),
            )
        return _row(updated)

    def resolve(
        self, tenant_id: str, party_id: str, purpose: str, channel: str
    ) -> RecipientSnapshot:
        """The NotificationRecipientResolver keystone (CP-INV-03). Resolve a business recipient
        (party_id + purpose + channel) to a verified, purpose-authorized, currently-effective
        destination of the requested channel's type, for a Party of the caller's tenant (RLS scopes
        the tenant). NEVER reads principals.email. Any failure is a single uniform RecipientUnresolved
        — the reasons are distinct internally but not revealed externally (CP-INV-05).

        A primary endpoint is preferred over a non-primary one of the same scope, then the most
        recently effective, so resolution is deterministic when several candidates qualify.
        """
        endpoint_type = _CHANNEL_TO_TYPE.get(channel)
        if endpoint_type is None:
            # An unknown channel maps to no type — a uniform refusal, not a distinct error surface.
            raise RecipientUnresolved("no usable destination for this recipient")

        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT endpoint_type, endpoint_value, purpose, party_id "
                "FROM party_contact_points "
                "WHERE party_id = %s AND endpoint_type = %s AND purpose = %s "
                "  AND verification_state = 'verified' "
                "  AND effective_from <= CURRENT_TIMESTAMP "
                "  AND (effective_to IS NULL OR effective_to > CURRENT_TIMESTAMP) "
                "ORDER BY is_primary DESC, effective_from DESC "
                "LIMIT 1",
                (party_id, endpoint_type, purpose),
            )
            row = cur.fetchone()

        if row is None:
            raise RecipientUnresolved("no usable destination for this recipient")
        return RecipientSnapshot(
            endpoint_type=row[0],
            endpoint_value=row[1],
            purpose=row[2],
            party_id=str(row[3]),
            resolved_at=datetime.now(timezone.utc),
        )
