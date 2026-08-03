"""Test fixture helper — provision a tenant's registry row.

`DEC-P35-TENANCY-MODEL` §9.3 (Option C): every tenant with tenant-scoped data must have a `tenants`
registry row, so the strict placement resolver (`WP-P35-06`) routes it fail-closed rather than
refusing it. The entitlement/metering tables (migration 002) carry no foreign key to `tenants`, so
several suites once minted a tenant_id without a registry row; this helper provisions it.

Idempotent, so a tenant reused across several writes is provisioned once.
"""

from __future__ import annotations


def register_tenant(tenant_id: str, *, name: str | None = None) -> str:
    """Insert the tenant into the registry if absent. Returns the tenant_id for convenience."""
    from platform_kernel import db

    with db.system_session() as cur:
        cur.execute(
            "INSERT INTO tenants (id, name, status) VALUES (%s, %s, 'active') "
            "ON CONFLICT (id) DO NOTHING",
            (tenant_id, name or f"test-tenant-{str(tenant_id)[:8]}"),
        )
    return tenant_id
