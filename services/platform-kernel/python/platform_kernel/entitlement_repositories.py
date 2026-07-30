"""
bOPEN Phase 3 entitlement / metering persistence repositories.

Work package: BOPEN-P35-001
Governing artifacts: BOPEN-TENANT-001, BOPEN-ENT-001, AGENTS.md section 8
Governing findings: F-3 (the outbox was a Python list), F-2 residue (quota reservations held
                    nothing, and expiry was never compared to the present instant)

Backs the five tables created by `infrastructure/database/002_phase3_entitlement_metering.sql`,
whose isolation policies were corrected by `004_tenant_identity_policy_alignment.sql`. Before
this module those tables existed, carried row-level security, carried CHECK constraints added
by migration 003, and were read and written by nothing at all.

The two rules from `platform_kernel.repositories` hold here unchanged and are not repeated at
each call site:

1. **Tenant-scoped reads and writes go through `db.tenant_session`.** No statement in this
   module appends `WHERE tenant_id = ...` by hand. Isolation is the database's job via the
   policies in `infrastructure/database/`; a hand-written filter would mean the caller
   believes isolation is its responsibility, and a caller that believes that will eventually
   forget. The one place `tenant_id` appears in a statement is the INSERT column list, where
   it is the value being stored and the policy's WITH CHECK is what validates it.

2. **Identifiers are passed through unchanged.** The 002 tables store `tenant_id` as
   `VARCHAR(64)`, constrained by migration 004 to canonical lowercase UUID text. This module
   does not normalise, prefix or reshape it. Normalising here would hide a caller that is
   holding an identifier in the wrong form, and the CHECK constraint exists precisely so that
   such a caller is refused rather than quietly accommodated.

WHAT THESE TABLES CANNOT STORE
------------------------------
Three contract-required values have no column, and this module does not invent one:

* `usage_outbox` has no `context_id`, while
  `contracts/schemas/usage-metered-event.schema.json` requires `context_id` with
  `minLength: 1`. A stored outbox row therefore cannot reproduce the context a replayed
  event was first recorded under. See `UsageOutboxRepository.record`.

* `quota_reservations` has no `quota_window`, `window_starts_at`, `window_ends_at` or
  `idempotency_key`, while `contracts/schemas/quota-reservation.schema.json` requires all
  four. A reservation identifier alone is therefore not enough to rebuild a contract-valid
  record, which is why the transition methods below take the values from the caller's own
  record and verify the rest against the stored row rather than fabricating them.

Both gaps need a migration to close and migrations are append-only after merge
(AGENTS.md section 14), so they are recorded here rather than papered over.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence

import psycopg

from platform_kernel import db


# ---------------------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------------------
# These live here rather than in `metering.py` because the repository raises them and
# `metering.py` imports this module. `metering.py` re-exports every name below, so
# `from platform_kernel.metering import QuotaReservationError` keeps working.


class EntitlementRepositoryError(RuntimeError):
    """Base class for entitlement/metering persistence refusals."""


class InvalidQuantityError(EntitlementRepositoryError):
    """Raised when a metered quantity or reserved quantity is not a positive integer.

    The database also refuses this (`chk_outbox_quantity_positive`,
    `chk_reservation_quantity_positive`). The application check is retained so callers get a
    typed error rather than a driver exception, not because it is the enforcement.
    """


class CrossTenantIdempotencyViolationError(EntitlementRepositoryError):
    """Retained for callers that catch it. Nothing raises this class directly any more.

    It previously covered two unrelated situations. One of them — a second tenant reusing an
    idempotency key a first tenant had used — is no longer an error and cannot be observed:
    `usage_outbox` is unique on `(tenant_id, idempotency_key)`, not on `idempotency_key`, and
    row-level security means one tenant cannot see whether another holds a key. The old guard
    also named the owning tenant in its message, which disclosed the existence and identity of
    another tenant to the caller.

    The situation that remains an error — one tenant replaying its own key with a different
    payload — is `IdempotencyPayloadConflictError`, which subclasses this so existing
    `except` and `assertRaises` clauses still catch it.
    """


class IdempotencyPayloadConflictError(CrossTenantIdempotencyViolationError):
    """Raised when a tenant reuses one of its own idempotency keys with a different payload."""


class OutboxRecordMissingError(EntitlementRepositoryError):
    """Raised when an outbox insert conflicted but the conflicting row is not readable."""


class QuotaReservationError(EntitlementRepositoryError):
    """Base class for quota reservation refusals."""


class QuotaBalanceNotProvisionedError(QuotaReservationError):
    """Raised when no `usage_meter_balances` row covers the present instant.

    Refusing is deliberate. A reservation exists to hold quota; with no balance row there is
    no quota to hold and nothing to refuse an over-consumption against. Allowing the
    reservation would produce a hold that constrains nothing, which reads as success.
    """


class AmbiguousQuotaWindowError(QuotaReservationError):
    """Raised when more than one balance row covers the present instant for a capability.

    `uq_tenant_capability_window` is unique on `(tenant_id, capability_id, window_start)`, so
    two rows with overlapping windows and different starts are admissible. Which one a
    reservation holds against would then decide whether it fits, so the ambiguity is refused
    rather than resolved by row order.
    """


class QuotaExceededError(QuotaReservationError):
    """Raised when a hold would push `used_quantity` past `quota_limit`.

    This is a translation of `chk_balance_within_quota`, not an application-level check. The
    refusal happens in the database and would happen to any writer, including one that never
    called this module.
    """


class ReservationNotFoundError(QuotaReservationError):
    """Raised when no reservation with that identifier is visible to this tenant.

    Indistinguishable from "exists but belongs to another tenant", which is the correct
    externally observable behaviour.
    """


class ReservationNotPendingError(QuotaReservationError):
    """Raised when a reservation is transitioned out of a status that is not `pending`."""


class ReservationExpiredError(QuotaReservationError):
    """Raised when a reservation is committed after its `expires_at` has passed.

    `chk_reservation_expiry_future` compares `expires_at` to `created_at`. Both are fixed at
    insert, so the constraint can only reject a reservation that was born expired; it cannot
    reject one that has since expired. Only a comparison against the present instant can, and
    that comparison is made in `QuotaReservationRepository.commit`.
    """


class ReservationRecordMismatchError(QuotaReservationError):
    """Raised when a presented reservation record disagrees with the stored row.

    The transition methods accept the caller's record because four contract-required fields
    have no column (see the module docstring). Accepting a record without checking it would
    let a caller supply a larger `reserved_quantity` or a later `expires_at` than the one the
    database actually holds, and the transition would then act on the caller's numbers. Every
    field that does have a column is compared against the stored row.
    """


class BalanceRowMissingError(QuotaReservationError):
    """Raised when the balance row a reservation held against can no longer be found."""


# ---------------------------------------------------------------------------------------
# Stored row shapes
# ---------------------------------------------------------------------------------------
# Each dataclass mirrors the columns that exist, and only those. The absence of
# `context_id` on the outbox record and of the four window/idempotency fields on the
# reservation record is the schema gap made visible in the type system instead of in prose.


@dataclass(frozen=True)
class StoredOutboxRecord:
    outbox_id: str
    event_id: str
    tenant_id: str
    principal_id: str
    capability_id: str
    quantity: int
    unit: str
    correlation_id: str
    idempotency_key: str
    created_at: datetime
    dispatched_at: Optional[datetime]

    @property
    def is_dispatched(self) -> bool:
        return self.dispatched_at is not None


@dataclass(frozen=True)
class StoredReservation:
    reservation_id: str
    tenant_id: str
    capability_id: str
    reserved_quantity: int
    expires_at: datetime
    status: str
    correlation_id: str
    created_at: datetime


@dataclass(frozen=True)
class StoredBalance:
    balance_id: str
    tenant_id: str
    capability_id: str
    used_quantity: int
    quota_limit: int
    window_start: datetime
    window_end: datetime


_OUTBOX_COLUMNS = (
    "outbox_id, event_id, tenant_id, principal_id, capability_id, quantity, unit, "
    "correlation_id, idempotency_key, created_at, dispatched_at"
)

_RESERVATION_COLUMNS = (
    "reservation_id, tenant_id, capability_id, reserved_quantity, expires_at, status, "
    "correlation_id, created_at"
)

_BALANCE_COLUMNS = (
    "balance_id, tenant_id, capability_id, used_quantity, quota_limit, window_start, "
    "window_end"
)


def _row_to_outbox(row) -> StoredOutboxRecord:
    return StoredOutboxRecord(
        outbox_id=row[0],
        event_id=row[1],
        tenant_id=row[2],
        principal_id=row[3],
        capability_id=row[4],
        quantity=int(row[5]),
        unit=row[6],
        correlation_id=row[7],
        idempotency_key=row[8],
        created_at=row[9],
        dispatched_at=row[10],
    )


def _row_to_reservation(row) -> StoredReservation:
    return StoredReservation(
        reservation_id=row[0],
        tenant_id=row[1],
        capability_id=row[2],
        reserved_quantity=int(row[3]),
        expires_at=row[4],
        status=row[5],
        correlation_id=row[6],
        created_at=row[7],
    )


def _row_to_balance(row) -> StoredBalance:
    return StoredBalance(
        balance_id=row[0],
        tenant_id=row[1],
        capability_id=row[2],
        used_quantity=int(row[3]),
        quota_limit=int(row[4]),
        window_start=row[5],
        window_end=row[6],
    )


def _constraint_of(exc: psycopg.errors.Error) -> str:
    """Return the violated constraint name, or '' when the driver did not report one."""
    diag = getattr(exc, "diag", None)
    return getattr(diag, "constraint_name", None) or ""


# ---------------------------------------------------------------------------------------
# Transactional outbox
# ---------------------------------------------------------------------------------------


class UsageOutboxRepository:
    """`usage_outbox` — the transactional outbox that finding F-3 recorded as absent.

    The table already had everything an outbox needs: `event_id UNIQUE`,
    `UNIQUE (tenant_id, idempotency_key)`, and a nullable `dispatched_at`. What it did not
    have was a writer.
    """

    def record(
        self,
        tenant_id: str,
        principal_id: str,
        capability_id: str,
        quantity: int,
        unit: str,
        correlation_id: str,
        idempotency_key: str,
        *,
        connection: "psycopg.Connection | None" = None,
    ) -> tuple[StoredOutboxRecord, bool]:
        """Append one usage event. Returns `(record, created)`.

        `created` is False when the row already existed, in which case the returned record is
        the stored one — the same `event_id`, the same `created_at`. A replay must return what
        was recorded, not a fresh event that happens to carry the caller's key.

        `INSERT ... ON CONFLICT (tenant_id, idempotency_key) DO NOTHING` followed by a
        re-SELECT is the whole replay guard. It is one round trip in the common case and it
        holds under concurrency, because the uniqueness is the database's and not a Python
        dictionary's. A read-then-write guard would have a window between the two.

        The conflict target is `(tenant_id, idempotency_key)`. A second tenant using the same
        key does not conflict and gets its own row — correct, and unobservable to the first
        tenant under the isolation policy.

        `context_id` is not a parameter because `usage_outbox` has no column for it. See the
        module docstring.
        """
        if quantity <= 0:
            raise InvalidQuantityError(
                f"quantity must be a positive integer, got {quantity}"
            )

        with db.tenant_session(tenant_id, connection=connection) as cur:
            cur.execute(
                f"INSERT INTO usage_outbox "
                f"(outbox_id, event_id, tenant_id, principal_id, capability_id, quantity, "
                f" unit, correlation_id, idempotency_key) "
                f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
                f"ON CONFLICT (tenant_id, idempotency_key) DO NOTHING "
                f"RETURNING {_OUTBOX_COLUMNS}",
                (
                    str(uuid.uuid4()),
                    f"evt_mtr_{uuid.uuid4().hex[:12]}",
                    tenant_id,
                    principal_id,
                    capability_id,
                    quantity,
                    unit,
                    correlation_id,
                    idempotency_key,
                ),
            )
            row = cur.fetchone()
            if row is not None:
                return _row_to_outbox(row), True

            cur.execute(
                f"SELECT {_OUTBOX_COLUMNS} FROM usage_outbox WHERE idempotency_key = %s",
                (idempotency_key,),
            )
            replayed = cur.fetchone()

        if replayed is None:
            raise OutboxRecordMissingError(
                f"insert of idempotency key {idempotency_key!r} conflicted, but the "
                f"conflicting row is not readable in this tenant's session. This should be "
                f"unreachable: the conflict target is (tenant_id, idempotency_key) and the "
                f"session is scoped to this tenant."
            )
        return _row_to_outbox(replayed), False

    def get_by_idempotency_key(
        self,
        tenant_id: str,
        idempotency_key: str,
        *,
        connection: "psycopg.Connection | None" = None,
    ) -> Optional[StoredOutboxRecord]:
        with db.tenant_session(tenant_id, connection=connection) as cur:
            cur.execute(
                f"SELECT {_OUTBOX_COLUMNS} FROM usage_outbox WHERE idempotency_key = %s",
                (idempotency_key,),
            )
            row = cur.fetchone()
        return _row_to_outbox(row) if row else None

    def list_all(
        self, tenant_id: str, *, connection: "psycopg.Connection | None" = None
    ) -> Sequence[StoredOutboxRecord]:
        """Every outbox row for this tenant, dispatched or not.

        Dispatch marks; it does not delete. So this list only grows, and its length is not a
        measure of pending work — `list_pending` is.
        """
        with db.tenant_session(tenant_id, connection=connection) as cur:
            cur.execute(
                f"SELECT {_OUTBOX_COLUMNS} FROM usage_outbox ORDER BY created_at, outbox_id"
            )
            rows = cur.fetchall()
        return [_row_to_outbox(r) for r in rows]

    def list_pending(
        self, tenant_id: str, *, connection: "psycopg.Connection | None" = None
    ) -> Sequence[StoredOutboxRecord]:
        with db.tenant_session(tenant_id, connection=connection) as cur:
            cur.execute(
                f"SELECT {_OUTBOX_COLUMNS} FROM usage_outbox WHERE dispatched_at IS NULL "
                f"ORDER BY created_at, outbox_id"
            )
            rows = cur.fetchall()
        return [_row_to_outbox(r) for r in rows]

    def mark_dispatched(
        self,
        tenant_id: str,
        *,
        sink=None,
        connection: "psycopg.Connection | None" = None,
    ) -> Sequence[StoredOutboxRecord]:
        """Stamp `dispatched_at` on every undispatched row and return the rows stamped.

        Nothing is deleted, which is the point of the change. An outbox that empties itself on
        dispatch has destroyed the only record of what it sent, so a redelivery question after
        the fact has no answer, and a consumer that never received the message leaves no trace.

        `sink` is invoked inside the same transaction as the UPDATE. If the sink raises, the
        stamping rolls back with it and the rows stay pending — at-least-once delivery. The
        reverse order (send, then stamp in a new transaction) loses events whenever the process
        dies between the two.
        """
        with db.tenant_session(tenant_id, connection=connection) as cur:
            cur.execute(
                f"UPDATE usage_outbox SET dispatched_at = now() "
                f"WHERE dispatched_at IS NULL "
                f"RETURNING {_OUTBOX_COLUMNS}"
            )
            records = [_row_to_outbox(r) for r in cur.fetchall()]
            if sink is not None and records:
                sink(records)
        return records


# ---------------------------------------------------------------------------------------
# Meter balances
# ---------------------------------------------------------------------------------------


class MeterBalanceRepository:
    """`usage_meter_balances` — the quota a reservation is held against.

    A balance row is the database expression of an entitled allowance: `quota_limit` is what
    the plan grants and `used_quantity` is what has been consumed or held.
    `chk_balance_within_quota` makes over-consumption unrepresentable, so the quota guarantee
    does not depend on any service remembering to check it.
    """

    def provision(
        self,
        tenant_id: str,
        capability_id: str,
        quota_limit: int,
        window_start: datetime,
        window_end: datetime,
        *,
        connection: "psycopg.Connection | None" = None,
    ) -> StoredBalance:
        """Create the balance row for a window if it is absent, and return it either way.

        Idempotent on `(tenant_id, capability_id, window_start)`. This deliberately does not
        update `quota_limit` on an existing row: raising a limit mid-window is a commercial
        decision with billing consequences, not a side effect of a metered call arriving.
        """
        if quota_limit <= 0:
            raise InvalidQuantityError(
                f"quota_limit must be a positive integer, got {quota_limit}"
            )
        with db.tenant_session(tenant_id, connection=connection) as cur:
            cur.execute(
                f"INSERT INTO usage_meter_balances "
                f"(balance_id, tenant_id, capability_id, used_quantity, quota_limit, "
                f" window_start, window_end) "
                f"VALUES (%s, %s, %s, 0, %s, %s, %s) "
                f"ON CONFLICT (tenant_id, capability_id, window_start) DO NOTHING "
                f"RETURNING {_BALANCE_COLUMNS}",
                (
                    str(uuid.uuid4()),
                    tenant_id,
                    capability_id,
                    quota_limit,
                    window_start,
                    window_end,
                ),
            )
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    f"SELECT {_BALANCE_COLUMNS} FROM usage_meter_balances "
                    f"WHERE capability_id = %s AND window_start = %s",
                    (capability_id, window_start),
                )
                row = cur.fetchone()
        if row is None:
            raise BalanceRowMissingError(
                f"balance for {capability_id!r} at {window_start.isoformat()} conflicted on "
                f"insert but is not readable in this tenant's session"
            )
        return _row_to_balance(row)

    def get(
        self,
        tenant_id: str,
        capability_id: str,
        window_start: datetime,
        *,
        connection: "psycopg.Connection | None" = None,
    ) -> Optional[StoredBalance]:
        with db.tenant_session(tenant_id, connection=connection) as cur:
            cur.execute(
                f"SELECT {_BALANCE_COLUMNS} FROM usage_meter_balances "
                f"WHERE capability_id = %s AND window_start = %s",
                (capability_id, window_start),
            )
            row = cur.fetchone()
        return _row_to_balance(row) if row else None


# ---------------------------------------------------------------------------------------
# Quota reservations
# ---------------------------------------------------------------------------------------


class QuotaReservationRepository:
    """`quota_reservations` — an atomic hold against a `usage_meter_balances` row."""

    def create(
        self,
        tenant_id: str,
        capability_id: str,
        reserved_quantity: int,
        expires_at: datetime,
        correlation_id: str,
        *,
        connection: "psycopg.Connection | None" = None,
    ) -> tuple[StoredReservation, StoredBalance]:
        """Take the hold and write the reservation in one transaction.

        The order matters: the balance is incremented first, so a hold that would exceed the
        quota is refused by `chk_balance_within_quota` before any reservation row exists. If
        the insert then fails for any reason the increment rolls back with it, so there is no
        state in which quota is held by nothing.

        The balance row is located by the window containing the present instant rather than by
        a window the caller computed. A caller-computed window is a second opinion about which
        allowance is in force, and the two can disagree at a boundary; the row that exists is
        the allowance that exists.

        Returns the reservation and the balance row it holds against. The balance row carries
        the only authoritative window bounds for this reservation — `quota_reservations` has no
        window columns.
        """
        if reserved_quantity <= 0:
            raise InvalidQuantityError(
                f"reserved_quantity must be a positive integer, got {reserved_quantity}"
            )

        reservation_id = f"res_{uuid.uuid4().hex[:12]}"
        with db.tenant_session(tenant_id, connection=connection) as cur:
            try:
                cur.execute(
                    f"UPDATE usage_meter_balances "
                    f"SET used_quantity = used_quantity + %s "
                    f"WHERE capability_id = %s "
                    f"  AND window_start <= now() AND window_end > now() "
                    f"RETURNING {_BALANCE_COLUMNS}",
                    (reserved_quantity, capability_id),
                )
            except psycopg.errors.CheckViolation as exc:
                # chk_balance_within_quota. Raising here propagates out of tenant_session,
                # which rolls the transaction back, so the hold is not left applied.
                raise QuotaExceededError(
                    f"holding {reserved_quantity} against {capability_id!r} would exceed the "
                    f"entitled quota for this window "
                    f"(constraint {_constraint_of(exc) or 'chk_balance_within_quota'})"
                ) from exc

            balances = cur.fetchall()
            if not balances:
                raise QuotaBalanceNotProvisionedError(
                    f"no usage_meter_balances row covers the present instant for "
                    f"{capability_id!r} in this tenant. A reservation with nothing to hold "
                    f"against would constrain nothing, so it is refused rather than created."
                )
            if len(balances) > 1:
                raise AmbiguousQuotaWindowError(
                    f"{len(balances)} balance rows cover the present instant for "
                    f"{capability_id!r}; which allowance is in force is undecidable"
                )
            balance = _row_to_balance(balances[0])

            try:
                cur.execute(
                    f"INSERT INTO quota_reservations "
                    f"(reservation_id, tenant_id, capability_id, reserved_quantity, "
                    f" expires_at, status, correlation_id) "
                    f"VALUES (%s, %s, %s, %s, %s, 'pending', %s) "
                    f"RETURNING {_RESERVATION_COLUMNS}",
                    (
                        reservation_id,
                        tenant_id,
                        capability_id,
                        reserved_quantity,
                        expires_at,
                        correlation_id,
                    ),
                )
            except psycopg.errors.CheckViolation as exc:
                constraint = _constraint_of(exc)
                if constraint == "chk_reservation_expiry_future":
                    raise ReservationExpiredError(
                        f"expires_at {expires_at.isoformat()} is not later than the moment "
                        f"the reservation would be created; it would be born expired"
                    ) from exc
                raise QuotaReservationError(
                    f"quota_reservations refused the row (constraint {constraint!r})"
                ) from exc

            reservation = _row_to_reservation(cur.fetchone())

        return reservation, balance

    def get(
        self,
        tenant_id: str,
        reservation_id: str,
        *,
        connection: "psycopg.Connection | None" = None,
    ) -> StoredReservation:
        with db.tenant_session(tenant_id, connection=connection) as cur:
            cur.execute(
                f"SELECT {_RESERVATION_COLUMNS} FROM quota_reservations "
                f"WHERE reservation_id = %s",
                (reservation_id,),
            )
            row = cur.fetchone()
        if row is None:
            raise ReservationNotFoundError(
                f"reservation {reservation_id} not found in this tenant"
            )
        return _row_to_reservation(row)

    def commit(
        self,
        tenant_id: str,
        reservation_id: str,
        *,
        window_start: datetime,
        expect_capability_id: str,
        expect_reserved_quantity: int,
        expect_correlation_id: str,
        expect_expires_at: datetime,
        connection: "psycopg.Connection | None" = None,
    ) -> StoredReservation:
        """Turn a pending hold into consumption, refusing one that has since expired.

        The expiry comparison is the reason this method cannot be a bare UPDATE.
        `chk_reservation_expiry_future` compares `expires_at` to `created_at` — two values
        fixed when the row was written — so the database will happily accept a commit hours
        after the hold lapsed. The comparison that matters is `expires_at` against `now()`,
        and only application logic can make it.

        `now()` is the transaction timestamp, so the same instant governs the read, the
        decision and the write. Reading the row `FOR UPDATE` first means a concurrent commit of
        the same reservation waits rather than double-consuming.

        A reservation found expired is transitioned to `expired` and its hold is returned to
        the balance before the refusal is raised. Leaving it `pending` would leave the quota
        held forever by a reservation that can never be committed.
        """
        return self._transition(
            tenant_id,
            reservation_id,
            target_status="committed",
            release_hold=False,
            check_expiry=True,
            window_start=window_start,
            expect_capability_id=expect_capability_id,
            expect_reserved_quantity=expect_reserved_quantity,
            expect_correlation_id=expect_correlation_id,
            expect_expires_at=expect_expires_at,
            connection=connection,
        )

    def release(
        self,
        tenant_id: str,
        reservation_id: str,
        *,
        window_start: datetime,
        expect_capability_id: str,
        expect_reserved_quantity: int,
        expect_correlation_id: str,
        expect_expires_at: datetime,
        connection: "psycopg.Connection | None" = None,
    ) -> StoredReservation:
        """Return a pending hold to the balance.

        Expiry is not checked: releasing an expired hold is exactly what should happen to it.
        Only `pending` may be released, so a second release cannot decrement the balance twice.
        """
        return self._transition(
            tenant_id,
            reservation_id,
            target_status="released",
            release_hold=True,
            check_expiry=False,
            window_start=window_start,
            expect_capability_id=expect_capability_id,
            expect_reserved_quantity=expect_reserved_quantity,
            expect_correlation_id=expect_correlation_id,
            expect_expires_at=expect_expires_at,
            connection=connection,
        )

    # -- internals ------------------------------------------------------------------------

    def _transition(
        self,
        tenant_id: str,
        reservation_id: str,
        *,
        target_status: str,
        release_hold: bool,
        check_expiry: bool,
        window_start: datetime,
        expect_capability_id: str,
        expect_reserved_quantity: int,
        expect_correlation_id: str,
        expect_expires_at: datetime,
        connection: "psycopg.Connection | None" = None,
    ) -> StoredReservation:
        expired_record: Optional[StoredReservation] = None
        result: Optional[StoredReservation] = None

        with db.tenant_session(tenant_id, connection=connection) as cur:
            cur.execute(
                f"SELECT {_RESERVATION_COLUMNS}, (expires_at <= now()) AS has_expired "
                f"FROM quota_reservations WHERE reservation_id = %s FOR UPDATE",
                (reservation_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise ReservationNotFoundError(
                    f"reservation {reservation_id} not found in this tenant"
                )
            stored = _row_to_reservation(row)
            has_expired = bool(row[8])

            self._assert_matches(
                stored,
                expect_capability_id=expect_capability_id,
                expect_reserved_quantity=expect_reserved_quantity,
                expect_correlation_id=expect_correlation_id,
                expect_expires_at=expect_expires_at,
            )

            if stored.status != "pending":
                raise ReservationNotPendingError(
                    f"reservation {reservation_id} is {stored.status!r}; only a pending "
                    f"reservation may become {target_status!r}"
                )

            if check_expiry and has_expired:
                # Return the hold first: if the balance row is gone the whole transaction
                # rolls back and the reservation stays pending, which is recoverable. Marking
                # it expired without returning the hold is not.
                self._adjust_balance(
                    cur, stored.capability_id, window_start, -stored.reserved_quantity
                )
                cur.execute(
                    f"UPDATE quota_reservations SET status = 'expired' "
                    f"WHERE reservation_id = %s RETURNING {_RESERVATION_COLUMNS}",
                    (reservation_id,),
                )
                expired_record = _row_to_reservation(cur.fetchone())
            else:
                if release_hold:
                    self._adjust_balance(
                        cur, stored.capability_id, window_start, -stored.reserved_quantity
                    )
                cur.execute(
                    f"UPDATE quota_reservations SET status = %s "
                    f"WHERE reservation_id = %s RETURNING {_RESERVATION_COLUMNS}",
                    (target_status, reservation_id),
                )
                result = _row_to_reservation(cur.fetchone())

        # Raised after the transaction commits, so the `expired` transition and the returned
        # hold survive the refusal. Raising inside would roll both back and leave the quota
        # held by a reservation that can never be committed.
        if expired_record is not None:
            raise ReservationExpiredError(
                f"reservation {reservation_id} expired at "
                f"{expired_record.expires_at.isoformat()}; it has been marked expired and its "
                f"hold of {expired_record.reserved_quantity} returned to the balance. "
                f"chk_reservation_expiry_future could not refuse this: it compares expires_at "
                f"to created_at, both fixed at insert."
            )
        if result is None:
            # Unreachable: the branch above sets either `expired_record` or `result`. Stated
            # as a raise rather than an `assert`, which `python -O` removes — and this would
            # then return None into a caller that is about to read `.status` off it.
            raise QuotaReservationError(
                f"reservation {reservation_id} produced neither a transition nor an expiry"
            )
        return result

    @staticmethod
    def _assert_matches(
        stored: StoredReservation,
        *,
        expect_capability_id: str,
        expect_reserved_quantity: int,
        expect_correlation_id: str,
        expect_expires_at: datetime,
    ) -> None:
        differences = []
        if stored.capability_id != expect_capability_id:
            differences.append(
                f"capability_id stored={stored.capability_id!r} "
                f"presented={expect_capability_id!r}"
            )
        if stored.reserved_quantity != expect_reserved_quantity:
            differences.append(
                f"reserved_quantity stored={stored.reserved_quantity} "
                f"presented={expect_reserved_quantity}"
            )
        if stored.correlation_id != expect_correlation_id:
            differences.append(
                f"correlation_id stored={stored.correlation_id!r} "
                f"presented={expect_correlation_id!r}"
            )
        if stored.expires_at != expect_expires_at:
            differences.append(
                f"expires_at stored={stored.expires_at.isoformat()} "
                f"presented={expect_expires_at.isoformat()}"
            )
        if differences:
            raise ReservationRecordMismatchError(
                f"presented reservation {stored.reservation_id} disagrees with the stored "
                f"row: " + "; ".join(differences)
            )

    @staticmethod
    def _adjust_balance(
        cur, capability_id: str, window_start: datetime, delta: int
    ) -> None:
        cur.execute(
            "UPDATE usage_meter_balances SET used_quantity = used_quantity + %s "
            "WHERE capability_id = %s AND window_start = %s "
            "RETURNING balance_id",
            (delta, capability_id, window_start),
        )
        if cur.fetchone() is None:
            raise BalanceRowMissingError(
                f"the balance row for {capability_id!r} at {window_start.isoformat()} is no "
                f"longer readable in this tenant, so the hold cannot be accounted for"
            )
