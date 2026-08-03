"""Tenant placement resolution — WP-P35-06 seam (DEC-P35-TENANCY-MODEL Option D).

Resolves a tenant to the database that holds its data: the shared RLS pool (default) or a
dedicated database (paying/production tenants). This is the seam that makes "one tenant, one
database" possible without assuming a single instance — and it is the correctness-critical part of
hybrid placement, because a mis-resolution is a tenant-isolation failure that row-level security
cannot catch (within the wrong database the session is correctly scoped to a tenant that has no
data there, so the caller reads "no data" rather than a refusal).

Two properties make that failure impossible rather than unlikely:

  1. **Fail-closed (A-09).** A tenant with no registry row, an unknown placement kind, or a
     dedicated placement whose connection is not configured is REFUSED. It is never defaulted into
     the shared pool — a wrong default would route a private tenant's requests into a database that
     is not theirs.
  2. **Identity is verifiable.** `verify_connection_serves` lets a caller assert, after connecting,
     that the database actually belongs to the tenant it resolved for, so a mis-configured ref is
     caught loudly. Dedicated databases carry that identity; the shared pool is verified by the
     row-level-security scope it is used under.

The tenant registry (and this placement column) always lives in the control connection
(`BOPEN_DATABASE_URL`). Only tenant *data* moves to a dedicated database.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from . import db

SHARED_POOL = "shared_pool"
DEDICATED = "dedicated"

#: A dedicated tenant's database URL is read from `BOPEN_DEDICATED_DB__<ref>`. Keeping the URL in
#: the environment rather than the registry means the connection secret never sits in a table.
DEDICATED_ENV_PREFIX = "BOPEN_DEDICATED_DB__"


class PlacementUnresolved(Exception):
    """A tenant could not be resolved to a database. Always a refusal, never a fallback."""


@dataclass(frozen=True)
class Placement:
    tenant_id: str
    kind: str
    connection_url: str


def _dedicated_url(tenant_id: str, ref: str) -> str:
    url = os.environ.get(f"{DEDICATED_ENV_PREFIX}{ref}", "").strip()
    if not url:
        raise PlacementUnresolved(
            f"tenant {tenant_id} is placed on dedicated database '{ref}', but no connection is "
            f"configured ({DEDICATED_ENV_PREFIX}{ref} is unset). Refusing rather than falling back "
            f"to the shared pool, which would route this tenant's requests into a database that is "
            f"not theirs."
        )
    return url


def resolve_placement(tenant_id: str, *, control_connection=None) -> Placement:
    """Resolve a tenant to the database that holds its data. Fail-closed on anything unexpected."""
    tid = str(tenant_id).strip()
    if not tid:
        raise PlacementUnresolved("placement resolution requires a non-empty tenant identifier")

    with db.system_session(connection=control_connection) as cur:
        cur.execute(
            "SELECT placement_kind, placement_ref FROM tenants WHERE id = %s", (tid,)
        )
        row = cur.fetchone()

    if row is None:
        raise PlacementUnresolved(
            f"tenant {tid} has no placement — no such tenant, or its registry row is missing. "
            f"Refusing: an unresolvable tenant is never defaulted into a placement."
        )

    kind, ref = row[0], row[1]
    if kind == SHARED_POOL:
        return Placement(tid, SHARED_POOL, db.database_url())
    if kind == DEDICATED:
        return Placement(tid, DEDICATED, _dedicated_url(tid, ref))
    raise PlacementUnresolved(f"tenant {tid} has an unrecognised placement kind {kind!r}")


def verify_connection_serves(cursor, tenant_id: str, placement: Placement) -> None:
    """Assert the connection actually serves the tenant it was resolved for.

    The shared pool serves every tenant and is scoped by row-level security, so there is nothing
    to cross-check here beyond the resolution itself. A dedicated database declares the single
    tenant it serves in `placement_identity`; if that declaration is absent or names a different
    tenant, the connection is refused rather than used — turning a mis-configured ref from a silent
    wrong answer into a loud failure.
    """
    if placement.kind == SHARED_POOL:
        return
    cursor.execute("SELECT tenant_id FROM placement_identity LIMIT 2")
    rows = cursor.fetchall()
    if len(rows) != 1 or str(rows[0][0]) != str(tenant_id):
        raise PlacementUnresolved(
            f"the dedicated database resolved for tenant {tenant_id} does not declare that it "
            f"serves exactly that tenant. Refusing the connection rather than trusting the route."
        )
