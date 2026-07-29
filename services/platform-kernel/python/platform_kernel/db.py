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
    """
    owns_connection = connection is None
    conn = connection or connect()
    try:
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
