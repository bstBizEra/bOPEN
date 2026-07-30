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

# Scopes a producer can declare when no tenant applies. These reach the `tenant_scope` column;
# the identifier column is NULL, which `chk_lifecycle_tenant_agreement` in migration 005
# requires. They are no longer looked for in the tenant position — see `record`.
UNSCOPED_TENANT_SENTINELS = {"unknown", "scoped"}

# The full vocabulary, matching `chk_lifecycle_scope` in migration 005 and `TENANT_SCOPES` in
# `kernel_core.audit`. Kept as a literal rather than imported from the check constraint for the
# usual reason a copy is acceptable here: this one is asserted equal to the producer's list by
# the contract suite, so drift fails a test rather than widening a control.
ALLOWED_TENANT_SCOPES = {"tenant"} | UNSCOPED_TENANT_SENTINELS


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
        """Route the event by the scope its producer declared.

        This used to decide by matching `tenant_id` against `UNSCOPED_TENANT_SENTINELS`. On the
        context-switch denial path that identifier is the request body's tenant field, so the
        caller chose the route: naming your tenant `unknown` filed your own denial under a NULL
        tenant, where no SELECT policy reaches it. Reproduced end to end on 2026-07-30 — of two
        identical denials, the one whose requested tenant was the literal string `unknown`
        vanished from the tenant's audit trail.

        The scope is now the producer's word, and the producer reaches it by parsing rather than
        by recognising a magic value, so `unknown` is one unresolvable string among infinitely
        many and carries no special power.
        """
        tenant_scope = str(event.get("tenant_scope") or "").strip()

        if tenant_scope not in ALLOWED_TENANT_SCOPES:
            raise LifecycleEventPersistenceError(
                f"lifecycle event declares an unusable tenant scope: {tenant_scope!r}. "
                f"Expected one of {sorted(ALLOWED_TENANT_SCOPES)}. The producer sets this; an "
                f"event arriving without it was built by something that bypassed "
                f"AuditDispatcher.emit_lifecycle_event."
            )

        if tenant_scope in UNSCOPED_TENANT_SENTINELS:
            # A pre-resolution event: the tenant is genuinely not known yet. It is written with a
            # null identifier and the scope preserved, under the policy migration 006 adds.
            # Migration 005 alone refused these rows outright, which lost exactly the audit
            # records describing failures that occur before a tenant is established.
            self._insert(event, tenant_id=None, tenant_scope=tenant_scope, scoped_write=False)
            return

        tenant_value = str(event.get("tenant_id") or "").strip()
        try:
            tenant_id = str(uuid.UUID(tenant_value))
        except ValueError:
            raise LifecycleEventPersistenceError(
                f"lifecycle event declares tenant scope but carries {tenant_value!r} in the "
                f"tenant position, which is not a tenant identifier. This is a producer defect "
                f"and is deliberately loud: silently rerouting it to the unscoped bucket is the "
                f"behaviour that made caller-supplied values a routing decision."
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
