"""
bOPEN tenant-scoped PostgreSQL session layer.

Work package: BOPEN-P35-001 (WP-P35-01, deliverable D-02)
Governing artifacts: BOPEN-TENANT-001, AGENTS.md section 8, BOPEN-ARCH-PLAN-001 section 3

Every tenant-scoped read or write in the kernel passes through `tenant_session`. The
session sets `app.current_tenant_id` for the duration of one transaction, which is the
variable the Row-Level Security policies in `infrastructure/database/` compare against.

The isolation guarantee is therefore a property of this module plus those policies, and of
nothing else. No caller filters by tenant. If a query in kernel code contains
`WHERE tenant_id = ...` written by hand, that is a defect: it means the caller believes it
is responsible for isolation, and a caller that believes that will eventually forget.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

try:
    import psycopg
except ImportError as exc:  # pragma: no cover - environment guard
    raise ImportError(
        "psycopg is required by the bOPEN kernel persistence layer.\n"
        "Install it with:  python -m pip install -r requirements.txt\n"
        "The kernel has no in-memory fallback by design: a fallback would let tenant "
        "isolation appear to work while no policy is enforcing it."
    ) from exc


ENV_DATABASE_URL = "BOPEN_DATABASE_URL"
TENANT_SETTING = "app.current_tenant_id"


class DatabaseNotConfiguredError(RuntimeError):
    """Raised when no connection target is configured.

    This is deliberately an error and never a silent no-op. Under BOPEN-GOV-EBIV-001 R5 a
    check that cannot run must report failure; a persistence layer that quietly degrades to
    doing nothing is indistinguishable from one that is working.
    """


class TenantContextError(RuntimeError):
    """Raised when a tenant-scoped session is opened without a usable tenant identifier."""


class TenantScopeReentryError(RuntimeError):
    """Raised when a session is nested inside another with a different scope in force.

    This closes a complete isolation bypass, found by security review on 2026-07-30 and
    reproduced end to end.

    `set_config(..., is_local => true)` is discarded when the transaction it belongs to ends.
    But psycopg3's `conn.transaction()`, entered on a connection that is *already* inside a
    transaction, emits a SAVEPOINT rather than opening a new one — and PostgreSQL reverts a
    `SET LOCAL` on savepoint ROLLBACK but **not** on savepoint RELEASE.

    So a nested `tenant_session` that exits *cleanly* left the inner tenant in force in the
    enclosing block. Measured, with real rows:

        outer opened for B, reads          -> 0 rows          (correct)
        nested session for A, exits cleanly
        outer, same block, reads           -> ['A-SECRET']    (tenant A's row)
        tenant in force in the outer block -> A

    Cross-tenant read and write, in both directions, with row-level security fully enabled and
    fully intact — because the policy was being told the wrong tenant. That is precisely the
    failure this module's docstring calls void-if-broken.

    The inner-raises path was already correct: savepoint ROLLBACK does revert the setting. Only
    the clean exit leaked, which is why no test caught it.

    Re-entry with the *same* scope is permitted, because composing several same-tenant
    operations onto one connection is the reason the `connection=` parameter exists and it
    cannot produce a mismatch. Anything else is refused rather than repaired: restoring the
    outer value on exit would work, but it would leave nesting looking safe and make the next
    variant of this bug quiet again.
    """


def database_url() -> str:
    """Return the configured connection URL, or raise with actionable remediation."""
    url = os.environ.get(ENV_DATABASE_URL, "").strip()
    if not url:
        raise DatabaseNotConfiguredError(
            f"{ENV_DATABASE_URL} is not set.\n"
            f"Provision a local verification database with:\n"
            f"    python tools/db_bootstrap.py --apply\n"
            f"then export the URL it prints, for example:\n"
            f"    export {ENV_DATABASE_URL}="
            f"postgresql://bopen_app:<password>@127.0.0.1:5432/bopen_dev"
        )
    return url


def connect(url: str | None = None, *, autocommit: bool = False) -> "psycopg.Connection":
    """Open a connection. Callers should prefer `tenant_session` or `system_session`."""
    return psycopg.connect(url or database_url(), autocommit=autocommit)


def _reject_conflicting_scope(conn: "psycopg.Connection", desired: str) -> None:
    """Refuse to nest a session inside another with a different scope in force.

    Only relevant when the connection is already inside a transaction — that is exactly when
    `conn.transaction()` becomes a savepoint, and a savepoint RELEASE does not revert
    `set_config(..., true)`. Outside a transaction there is nothing to conflict with.

    The comparison is against what PostgreSQL currently holds rather than against anything this
    module tracks, so it cannot drift from reality.
    """
    if conn.info.transaction_status == psycopg.pq.TransactionStatus.IDLE:
        return

    with conn.cursor() as cursor:
        cursor.execute("SELECT COALESCE(current_setting(%s, true), '')", (TENANT_SETTING,))
        row = cursor.fetchone()
    current = (row[0] if row else "") or ""

    if current == desired:
        return

    raise TenantScopeReentryError(
        f"refusing to open a session for {desired or '<system>'!r} inside one already scoped to "
        f"{current or '<system>'!r} on the same connection.\n"
        f"\n"
        f"A nested session that exits cleanly does NOT restore the enclosing scope: psycopg "
        f"emits a SAVEPOINT, and PostgreSQL reverts SET LOCAL on savepoint rollback but not on "
        f"release. The enclosing block would continue with the inner tenant in force and read "
        f"and write that tenant's rows while believing it was scoped to its own.\n"
        f"\n"
        f"Restructure so the two scopes do not overlap, or pass no `connection=` so each opens "
        f"its own. Re-entry with the same scope is allowed."
    )


@contextmanager
def tenant_session(
    tenant_id: str, *, connection: "psycopg.Connection | None" = None
) -> Iterator["psycopg.Cursor"]:
    """Yield a cursor bound to one tenant for the duration of one transaction.

    The tenant identifier is applied with `set_config(..., is_local => true)` rather than
    `SET LOCAL`, for two reasons that both matter:

    1. `SET LOCAL` takes a literal, not a bind parameter. Building it by string
       interpolation would place a caller-supplied value directly into SQL. Tenant
       identifiers arrive from request headers and tokens, so that is an injection point on
       the exact variable the whole isolation model depends on. `set_config` accepts a bind
       parameter and closes it.

    2. `is_local => true` scopes the setting to the current transaction. It is discarded on
       commit or rollback, so a pooled connection cannot carry one tenant's context into the
       next tenant's transaction. Session-scoped settings leak across checkouts; that leak
       is silent and grants cross-tenant read access.

    Point 2 holds for the *outermost* transaction and, as originally written, was relied on for
    a case where it does not hold. See `_reject_conflicting_scope` — nesting is now refused.

    The transaction commits on clean exit and rolls back on any exception.
    """
    if not tenant_id or not str(tenant_id).strip():
        raise TenantContextError(
            "tenant_session requires a non-empty tenant identifier. Refusing to open a "
            "session with an unset tenant: the RLS policies would then match no rows and "
            "the caller would read that as 'this tenant has no data' rather than as an "
            "error."
        )

    owns_connection = connection is None
    conn = connection or connect()
    try:
        _reject_conflicting_scope(conn, str(tenant_id))
        with conn.transaction():
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT set_config(%s, %s, true)",
                    (TENANT_SETTING, str(tenant_id)),
                )
                yield cursor
    finally:
        if owns_connection:
            conn.close()


@contextmanager
def system_session(
    *, connection: "psycopg.Connection | None" = None
) -> Iterator["psycopg.Cursor"]:
    """Yield a cursor with no tenant context set.

    Used for migrations, for tenant provisioning, and for the deny-by-default probe. Under
    the policies in `infrastructure/database/`, tenant-scoped tables return zero rows in
    this state. That is the intended behaviour and is asserted by the isolation suite: an
    unset context must read as "no access", never as "all access".

    Nesting is refused here for the same reason as in `tenant_session`, and the direction of
    the failure differs in a way worth naming. A system session nested inside a tenant session
    fails *closed* — it clears the setting, so the enclosing block afterwards sees nothing and
    reads it as "this tenant has no data". A tenant session nested inside a system session
    fails *open* — the tenant stays in force and the enclosing block reads that tenant's rows
    while believing it is unscoped. One is a correctness bug and the other is a disclosure, and
    both are refused rather than only the second, because a rule with an exception is a rule
    somebody has to remember.
    """
    owns_connection = connection is None
    conn = connection or connect()
    try:
        _reject_conflicting_scope(conn, "")
        with conn.transaction():
            with conn.cursor() as cursor:
                cursor.execute("SELECT set_config(%s, '', true)", (TENANT_SETTING,))
                yield cursor
    finally:
        if owns_connection:
            conn.close()


def current_tenant(cursor: "psycopg.Cursor") -> str | None:
    """Return the tenant identifier in force on this cursor's transaction, if any."""
    cursor.execute("SELECT NULLIF(current_setting(%s, true), '')", (TENANT_SETTING,))
    row = cursor.fetchone()
    return row[0] if row else None


def rls_is_active(cursor: "psycopg.Cursor", table_name: str) -> tuple[bool, bool]:
    """Return (row_security_enabled, row_security_forced) for a table.

    `FORCE ROW LEVEL SECURITY` matters independently of `ENABLE`: without it, the table
    owner bypasses every policy. Kernel services frequently connect as the owner in
    development, so a suite that only checks `ENABLE` can pass while the policies are inert
    for the role actually running the queries.
    """
    cursor.execute(
        """
        SELECT c.relrowsecurity, c.relforcerowsecurity
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = %s AND n.nspname = current_schema()
        """,
        (table_name,),
    )
    row = cursor.fetchone()
    if row is None:
        raise LookupError(f"table {table_name!r} does not exist in the current schema")
    return bool(row[0]), bool(row[1])
