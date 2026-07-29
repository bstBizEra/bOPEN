"""
bOPEN Phase 1 persistence repositories.

Work package: BOPEN-P35-001 (WP-P35-01, deliverable D-06)
Governing artifacts: BOPEN-TENANT-001, BOPEN-AUTHZ-001, AGENTS.md section 3 and section 8

Persists the Phase 1 entities that `AGENTS.md` section 3 authorizes: principal, tenant,
membership, active context, authorization decision and audit event.

Two rules hold throughout this module and are worth stating once rather than repeating at
every call site:

1. **Tenant-scoped reads and writes go through `db.tenant_session`.** No function here
   appends `WHERE tenant_id = ...` by hand. Isolation is the database's job via the policies
   in `infrastructure/database/`; a hand-written filter would mean the caller believes
   isolation is its responsibility, and a caller that believes that will eventually forget.

2. **Global registries use `db.system_session`.** `tenants` and `principals` are not
   tenant-owned — a tenant row cannot be scoped to itself, and a principal exists before it
   has any membership. Both tables therefore carry no row-level security policy by design,
   which is why writing to them needs an unscoped session.

Identifiers are bare UUIDs. `contracts/schemas/tenant-context.json` constrains
`principal_id`, `tenant_id` and `active_membership_id` only as `string`, so the `usr_`/`tnt_`/
`mem_` prefixes emitted by the in-memory `PlatformKernelService` were never contract-required.
They are also unstorable: migration 001 declares those columns `UUID`, and `tnt_<uuid>` does
not cast. Bare UUIDs keep the foreign keys, the indexes, and the `::uuid` cast in the
isolation policies working.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

from platform_kernel import db

# A context is short-lived by design. BOPEN-TENANT-001 requires active context to be
# explicit and validated; an unbounded context is neither, because nothing forces
# revalidation after the membership that justified it changes.
DEFAULT_CONTEXT_TTL = timedelta(hours=1)


class RepositoryError(RuntimeError):
    """Base class for persistence-layer refusals."""


class PrincipalNotFoundError(RepositoryError):
    pass


class MembershipNotFoundError(RepositoryError):
    pass


class ContextNotFoundError(RepositoryError):
    pass


@dataclass(frozen=True)
class StoredPrincipal:
    id: str
    type: str
    email: str
    status: str


@dataclass(frozen=True)
class StoredTenant:
    id: str
    name: str
    status: str


@dataclass(frozen=True)
class StoredMembership:
    id: str
    tenant_id: str
    principal_id: str
    state: str
    role: str


@dataclass(frozen=True)
class StoredContext:
    id: str
    tenant_id: str
    principal_id: str
    membership_id: str
    correlation_id: str
    established_at: datetime
    expires_at: datetime
    revoked_at: Optional[datetime]

    @property
    def is_live(self) -> bool:
        return self.revoked_at is None and self.expires_at > datetime.now(timezone.utc)


class PrincipalRepository:
    """Global principal registry. Not tenant-scoped: a principal precedes membership."""

    def create(self, email: str, principal_type: str = "human") -> StoredPrincipal:
        principal_id = str(uuid.uuid4())
        with db.system_session() as cur:
            cur.execute(
                "INSERT INTO principals (id, type, email, status) "
                "VALUES (%s, %s, %s, 'active') RETURNING id, type, email, status",
                (principal_id, principal_type, email),
            )
            row = cur.fetchone()
        return StoredPrincipal(id=str(row[0]), type=row[1], email=row[2], status=row[3])

    def get(self, principal_id: str) -> StoredPrincipal:
        with db.system_session() as cur:
            cur.execute(
                "SELECT id, type, email, status FROM principals WHERE id = %s",
                (principal_id,),
            )
            row = cur.fetchone()
        if row is None:
            raise PrincipalNotFoundError(f"principal {principal_id} does not exist")
        return StoredPrincipal(id=str(row[0]), type=row[1], email=row[2], status=row[3])


class TenantRepository:
    """Global tenant registry. The tenant row defines a boundary; it is not inside one."""

    def create(self, name: str, status: str = "active") -> StoredTenant:
        tenant_id = str(uuid.uuid4())
        with db.system_session() as cur:
            cur.execute(
                "INSERT INTO tenants (id, name, status) VALUES (%s, %s, %s) "
                "RETURNING id, name, status",
                (tenant_id, name, status),
            )
            row = cur.fetchone()
        return StoredTenant(id=str(row[0]), name=row[1], status=row[2])

    def get(self, tenant_id: str) -> Optional[StoredTenant]:
        with db.system_session() as cur:
            cur.execute(
                "SELECT id, name, status FROM tenants WHERE id = %s", (tenant_id,)
            )
            row = cur.fetchone()
        return (
            StoredTenant(id=str(row[0]), name=row[1], status=row[2]) if row else None
        )


class MembershipRepository:
    """Tenant-scoped. Every method here runs under the tenant's own isolation policy."""

    def create(
        self, tenant_id: str, principal_id: str, role: str, state: str = "active"
    ) -> StoredMembership:
        membership_id = str(uuid.uuid4())
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "INSERT INTO memberships (id, tenant_id, principal_id, state, role) "
                "VALUES (%s, %s, %s, %s, %s) "
                "RETURNING id, tenant_id, principal_id, state, role",
                (membership_id, tenant_id, principal_id, state, role),
            )
            row = cur.fetchone()
        return StoredMembership(
            id=str(row[0]),
            tenant_id=str(row[1]),
            principal_id=str(row[2]),
            state=row[3],
            role=row[4],
        )

    def get(self, tenant_id: str, membership_id: str) -> StoredMembership:
        """Read one membership.

        There is no `get(membership_id)` without a tenant, deliberately. A lookup by
        identifier alone would have to run unscoped, and an unscoped read of a tenant-owned
        table is the shape of a cross-tenant disclosure even when the caller means well.
        """
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT id, tenant_id, principal_id, state, role FROM memberships "
                "WHERE id = %s",
                (membership_id,),
            )
            row = cur.fetchone()
        if row is None:
            # Indistinguishable from "exists but belongs to another tenant", which is the
            # correct externally observable behaviour: confirming existence would leak that
            # another tenant holds this identifier.
            raise MembershipNotFoundError(
                f"membership {membership_id} not found in this tenant"
            )
        return StoredMembership(
            id=str(row[0]),
            tenant_id=str(row[1]),
            principal_id=str(row[2]),
            state=row[3],
            role=row[4],
        )

    def list_for_principal(
        self, tenant_id: str, principal_id: str
    ) -> Sequence[StoredMembership]:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT id, tenant_id, principal_id, state, role FROM memberships "
                "WHERE principal_id = %s ORDER BY created_at",
                (principal_id,),
            )
            rows = cur.fetchall()
        return [
            StoredMembership(
                id=str(r[0]),
                tenant_id=str(r[1]),
                principal_id=str(r[2]),
                state=r[3],
                role=r[4],
            )
            for r in rows
        ]


class ContextRepository:
    """Tenant-scoped active context storage."""

    def establish(
        self,
        tenant_id: str,
        principal_id: str,
        membership_id: str,
        correlation_id: str,
        ttl: timedelta = DEFAULT_CONTEXT_TTL,
    ) -> StoredContext:
        with db.tenant_session(tenant_id) as cur:
            # A principal may hold one live context per tenant. Revoking the previous one
            # rather than failing keeps re-authentication idempotent, and the partial unique
            # index in migration 003 enforces the invariant regardless of what this method
            # does.
            cur.execute(
                "UPDATE active_contexts SET revoked_at = now() "
                "WHERE principal_id = %s AND revoked_at IS NULL",
                (principal_id,),
            )
            cur.execute(
                "INSERT INTO active_contexts "
                "(tenant_id, principal_id, membership_id, correlation_id, expires_at) "
                "VALUES (%s, %s, %s, %s, now() + %s) "
                "RETURNING id, tenant_id, principal_id, membership_id, correlation_id, "
                "          established_at, expires_at, revoked_at",
                (tenant_id, principal_id, membership_id, correlation_id, ttl),
            )
            row = cur.fetchone()
        return self._row_to_context(row)

    def get(self, tenant_id: str, context_id: str) -> StoredContext:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT id, tenant_id, principal_id, membership_id, correlation_id, "
                "       established_at, expires_at, revoked_at "
                "FROM active_contexts WHERE id = %s",
                (context_id,),
            )
            row = cur.fetchone()
        if row is None:
            raise ContextNotFoundError(f"context {context_id} not found in this tenant")
        return self._row_to_context(row)

    def revoke(self, tenant_id: str, context_id: str) -> None:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "UPDATE active_contexts SET revoked_at = now() "
                "WHERE id = %s AND revoked_at IS NULL",
                (context_id,),
            )

    @staticmethod
    def _row_to_context(row) -> StoredContext:
        return StoredContext(
            id=str(row[0]),
            tenant_id=str(row[1]),
            principal_id=str(row[2]),
            membership_id=str(row[3]),
            correlation_id=row[4],
            established_at=row[5],
            expires_at=row[6],
            revoked_at=row[7],
        )


class AuditRepository:
    """Append-only audit writes.

    There is no `update` and no `delete` method, and adding one would not work: migration 003
    grants `audit_events` a SELECT policy and an INSERT policy and no others, so UPDATE and
    DELETE reach zero rows regardless of the SQL issued. The absence here mirrors an absence
    the database enforces, rather than relying on this class to be the only writer.
    """

    def record(
        self,
        tenant_id: str,
        principal_id: Optional[str],
        context_id: Optional[str],
        correlation_id: str,
        event_type: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        decision: Optional[str] = None,
        reason_code: Optional[str] = None,
    ) -> str:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "INSERT INTO audit_events "
                "(tenant_id, principal_id, context_id, correlation_id, event_type, action, "
                " resource_type, resource_id, decision, reason_code) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (
                    tenant_id,
                    principal_id,
                    context_id,
                    correlation_id,
                    event_type,
                    action,
                    resource_type,
                    resource_id,
                    decision,
                    reason_code,
                ),
            )
            return str(cur.fetchone()[0])

    def list_for_tenant(self, tenant_id: str, limit: int = 100) -> Sequence[dict]:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT id, correlation_id, event_type, action, resource_type, "
                "       resource_id, decision, reason_code, occurred_at "
                "FROM audit_events ORDER BY occurred_at DESC LIMIT %s",
                (limit,),
            )
            rows = cur.fetchall()
        return [
            {
                "id": str(r[0]),
                "correlation_id": r[1],
                "event_type": r[2],
                "action": r[3],
                "resource_type": r[4],
                "resource_id": r[5],
                "decision": r[6],
                "reason_code": r[7],
                "occurred_at": r[8].isoformat(),
            }
            for r in rows
        ]


class TenantResourceRepository:
    """A minimal tenant-owned resource, used by the Phase 1 slice as the authorization target."""

    def create(self, tenant_id: str, resource_name: str) -> str:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "INSERT INTO tenant_resources (tenant_id, resource_name) "
                "VALUES (%s, %s) RETURNING id",
                (tenant_id, resource_name),
            )
            return str(cur.fetchone()[0])

    def read(self, tenant_id: str, resource_id: str) -> Optional[dict]:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT id, resource_name, payload FROM tenant_resources WHERE id = %s",
                (resource_id,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return {"id": str(row[0]), "resource_name": row[1], "payload": row[2]}
