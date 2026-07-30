"""
PostgreSQL sink for the Phase 2 lifecycle audit envelope.

Work package: BOPEN-P35-001
Governing artifacts: BOPEN-P1-001-EXECUTION-PLAN §10.2; AGENTS.md §8, §13
Table: migration 005 `lifecycle_events`, INSERT policies from 005 and 006

Implements `kernel_core.audit.LifecycleEventSink`. The Protocol is declared there and the
implementation lives here because `packages/kernel-core` imports `platform_kernel` zero times.

Before this existed, `AuditDispatcher` appended to a Python list, so every Phase 2 audit record —
invitation, membership transition, SCIM provisioning, context switch, delegation — was lost on
restart and differed per worker.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Sequence

from platform_kernel import db

# The producer emits these in the tenant position on paths that run before a tenant is resolved.
# They are not identifiers and must not reach a UUID column — the same class of error as
# `mem_<uuid>` in a uuid column, which is an open finding elsewhere in this repository.
UNSCOPED_TENANT_SENTINELS = {"unknown", "scoped"}


class LifecycleEventPersistenceError(RuntimeError):
    """Raised when an audit event could not be made durable.

    This is deliberately not swallowed. An audit sink that silently drops what it cannot write
    produces a trail that is worse than no trail: it looks complete. `AGENTS.md` §11 requires
    security-sensitive work to carry negative tests, and the negative case here is a write that
    fails — the caller must be able to see it.
    """


class PostgresLifecycleEventSink:
    """Writes lifecycle events to `lifecycle_events`.

    The table is append-only by policy: migration 005 grants SELECT and INSERT and nothing else,
    so UPDATE and DELETE reach zero rows whatever SQL is issued. This class has no update or
    delete method, and adding one would not work.
    """

    def record(self, event: Dict[str, Any]) -> None:
        tenant_value = str(event.get("tenant_id") or "").strip()

        if tenant_value in UNSCOPED_TENANT_SENTINELS:
            # A pre-resolution event: the tenant is genuinely not known yet. It is written with a
            # null identifier and the sentinel preserved as scope, under the policy migration 006
            # adds. Migration 005 alone refused these rows outright, which lost exactly the audit
            # records describing failures that occur before a tenant is established.
            self._insert(event, tenant_id=None, tenant_scope=tenant_value, scoped_write=False)
            return

        try:
            tenant_id = str(uuid.UUID(tenant_value))
        except ValueError:
            raise LifecycleEventPersistenceError(
                f"lifecycle event carries a tenant value that is neither a UUID nor a known "
                f"scope sentinel: {tenant_value!r}. Recognised sentinels are "
                f"{sorted(UNSCOPED_TENANT_SENTINELS)}."
            )

        self._insert(event, tenant_id=tenant_id, tenant_scope="tenant", scoped_write=True)

    def _insert(
        self,
        event: Dict[str, Any],
        tenant_id: Optional[str],
        tenant_scope: str,
        scoped_write: bool,
    ) -> None:
        import json

        params = (
            event["event_id"],
            event["event_type"],
            int(event.get("event_version", 1)),
            event["occurred_at"],
            event["correlation_id"],
            event.get("causation_id"),
            event["actor_principal_id"],
            tenant_id,
            tenant_scope,
            event["subject_type"],
            event["subject_id"],
            event["outcome"],
            event["reason_code"],
            json.dumps(event.get("metadata") or {}),
        )

        statement = (
            "INSERT INTO lifecycle_events "
            "(event_id, event_type, event_version, occurred_at, correlation_id, causation_id, "
            " actor_principal_id, tenant_id, tenant_scope, subject_type, subject_id, outcome, "
            " reason_code, metadata) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)"
        )

        # A scoped write opens the tenant's own session so the row-level policy authorises it.
        # An unscoped write cannot: there is no tenant to open a session for, and the policy that
        # admits it (migration 006) matches on `tenant_id IS NULL` instead.
        session = db.tenant_session(tenant_id) if scoped_write else db.system_session()
        with session as cur:
            cur.execute(statement, params)

    def list_for_tenant(self, tenant_id: str, limit: int = 100) -> Sequence[Dict[str, Any]]:
        """Read a tenant's lifecycle events.

        No tenant predicate appears in the query. The row-level security policy scopes it, which
        is the same arrangement `repositories.py` uses and for the same reason: a hand-written
        filter would mean the caller believed isolation was its responsibility.

        Unscoped events are invisible here, and that is not an oversight. They belong to no
        tenant, so returning them to whichever tenant asked would be inventing an owner. Reading
        them needs an administrative path that does not exist yet.
        """
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT event_id, event_type, event_version, occurred_at, correlation_id, "
                "       causation_id, actor_principal_id, subject_type, subject_id, outcome, "
                "       reason_code, metadata "
                "FROM lifecycle_events ORDER BY occurred_at DESC LIMIT %s",
                (limit,),
            )
            rows = cur.fetchall()

        return [
            {
                "event_id": str(row[0]),
                "event_type": row[1],
                "event_version": row[2],
                "occurred_at": row[3].isoformat() if isinstance(row[3], datetime) else row[3],
                "correlation_id": row[4],
                "causation_id": row[5],
                "actor_principal_id": row[6],
                "subject_type": row[7],
                "subject_id": row[8],
                "outcome": row[9],
                "reason_code": row[10],
                "metadata": row[11],
            }
            for row in rows
        ]
