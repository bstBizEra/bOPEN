"""Tenant-scoped workflow state engine — MILE-4.2 (authorized DEC-P4-ENTRY §8).

A generic state machine for business processes. A *definition* names the states and the transitions
allowed between them; an *instance* carries a current state for one subject; a *transition* moves an
instance along one edge the definition allows and appends to an immutable history.

Every method runs through `db.tenant_session`, so isolation is the row-level-security policy's
property and this module's, and nothing else — the same contract as `repositories.py`. There is no
unscoped read of a workflow table, deliberately: an unscoped read of a tenant-owned table is the
shape of a cross-tenant disclosure even when the caller means well.

The one invariant that makes this a state *machine* rather than a mutable field is enforced in
`apply_transition`: a move the definition does not list is refused, and the refusal, the state
change and the history row are one transaction — either all happen or none do.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Sequence

import psycopg

from . import db


class WorkflowRepositoryError(RuntimeError):
    """Base for workflow repository failures."""


class WorkflowDefinitionError(WorkflowRepositoryError):
    """A definition is malformed — the initial state or a transition endpoint is not a declared
    state. Rejected before it can produce instances that can never move."""


class WorkflowDefinitionNotFoundError(WorkflowRepositoryError):
    """A definition does not exist in this tenant (indistinguishable from another tenant's)."""


class WorkflowInstanceNotFoundError(WorkflowRepositoryError):
    """An instance does not exist in this tenant (indistinguishable from another tenant's)."""


class WorkflowTransitionError(WorkflowRepositoryError):
    """The requested move is not an edge the definition allows from the current state. This is the
    state-machine invariant: an instance cannot jump to an arbitrary state."""


@dataclass(frozen=True)
class StoredWorkflowDefinition:
    id: str
    tenant_id: str
    name: str
    initial_state: str
    states: tuple[str, ...]
    transitions: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class StoredWorkflowInstance:
    id: str
    tenant_id: str
    definition_id: str
    current_state: str
    subject_ref: str


@dataclass(frozen=True)
class StoredWorkflowTransition:
    id: str
    tenant_id: str
    instance_id: str
    from_state: str
    to_state: str
    actor_principal_id: str | None


def _definition(row) -> StoredWorkflowDefinition:
    return StoredWorkflowDefinition(
        id=str(row[0]),
        tenant_id=str(row[1]),
        name=row[2],
        initial_state=row[3],
        states=tuple(row[4]),
        transitions=tuple(tuple(pair) for pair in row[5]),
    )


def _instance(row) -> StoredWorkflowInstance:
    return StoredWorkflowInstance(
        id=str(row[0]),
        tenant_id=str(row[1]),
        definition_id=str(row[2]),
        current_state=row[3],
        subject_ref=row[4],
    )


class WorkflowRepository:
    """Tenant-scoped. Every method runs under the tenant's own isolation policy."""

    _DEF_COLUMNS = "id, tenant_id, name, initial_state, states, transitions"
    _INST_COLUMNS = "id, tenant_id, definition_id, current_state, subject_ref"

    def create_definition(
        self,
        tenant_id: str,
        name: str,
        initial_state: str,
        states: Sequence[str],
        transitions: Sequence[Sequence[str]],
    ) -> StoredWorkflowDefinition:
        # Validate the shape here rather than trusting the caller: a definition whose initial state
        # or a transition endpoint is not a declared state would mint instances that start outside
        # their own state set or can never move. That is a definition defect, so it is a 422 at the
        # edge, not a runtime surprise on the first transition.
        state_set = set(states)
        if not states:
            raise WorkflowDefinitionError("a definition must declare at least one state")
        if initial_state not in state_set:
            raise WorkflowDefinitionError("initial_state must be one of the declared states")
        normalised: list[tuple[str, str]] = []
        for pair in transitions:
            if len(pair) != 2:
                raise WorkflowDefinitionError("each transition must be a [from, to] pair")
            src, dst = pair[0], pair[1]
            if src not in state_set or dst not in state_set:
                raise WorkflowDefinitionError(
                    "every transition endpoint must be a declared state"
                )
            normalised.append((src, dst))

        definition_id = str(uuid.uuid4())
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                f"INSERT INTO workflow_definitions "
                f"(id, tenant_id, name, initial_state, states, transitions) "
                f"VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb) RETURNING {self._DEF_COLUMNS}",
                (
                    definition_id,
                    tenant_id,
                    name,
                    initial_state,
                    json.dumps(list(states)),
                    json.dumps([list(p) for p in normalised]),
                ),
            )
            row = cur.fetchone()
        return _definition(row)

    def get_definition(self, tenant_id: str, definition_id: str) -> StoredWorkflowDefinition:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                f"SELECT {self._DEF_COLUMNS} FROM workflow_definitions WHERE id = %s",
                (definition_id,),
            )
            row = cur.fetchone()
        if row is None:
            raise WorkflowDefinitionNotFoundError(
                f"definition {definition_id} not found in this tenant"
            )
        return _definition(row)

    def start_instance(
        self, tenant_id: str, definition_id: str, subject_ref: str
    ) -> StoredWorkflowInstance:
        """Create an instance sitting at its definition's initial state.

        The initial state is read from the definition rather than accepted from the caller, so an
        instance can never begin in a state the definition does not know. Reading the definition
        under the tenant session means a definition from another tenant is simply not found — the
        composite foreign key would refuse the insert too, but failing at the read gives the caller
        a clean 404 rather than a constraint error.
        """
        instance_id = str(uuid.uuid4())
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT initial_state FROM workflow_definitions WHERE id = %s",
                (definition_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise WorkflowDefinitionNotFoundError(
                    f"definition {definition_id} not found in this tenant"
                )
            initial_state = row[0]
            cur.execute(
                f"INSERT INTO workflow_instances "
                f"(id, tenant_id, definition_id, current_state, subject_ref) "
                f"VALUES (%s, %s, %s, %s, %s) RETURNING {self._INST_COLUMNS}",
                (instance_id, tenant_id, definition_id, initial_state, subject_ref),
            )
            created = cur.fetchone()
        return _instance(created)

    def get_instance(self, tenant_id: str, instance_id: str) -> StoredWorkflowInstance:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                f"SELECT {self._INST_COLUMNS} FROM workflow_instances WHERE id = %s",
                (instance_id,),
            )
            row = cur.fetchone()
        if row is None:
            raise WorkflowInstanceNotFoundError(
                f"instance {instance_id} not found in this tenant"
            )
        return _instance(row)

    def apply_transition(
        self,
        tenant_id: str,
        instance_id: str,
        to_state: str,
        actor_principal_id: str | None = None,
    ) -> StoredWorkflowInstance:
        """Move an instance to `to_state`, but only along an edge its definition allows.

        The whole operation is one transaction. The read of the current state, the check against the
        definition's transitions, the update, and the append to history either all commit or all roll
        back. A concurrent transition is serialised by the row lock taken with FOR UPDATE, so two
        callers cannot both read `draft` and both move it.
        """
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT current_state, definition_id FROM workflow_instances "
                "WHERE id = %s FOR UPDATE",
                (instance_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise WorkflowInstanceNotFoundError(
                    f"instance {instance_id} not found in this tenant"
                )
            current_state, definition_id = row[0], str(row[1])

            cur.execute(
                "SELECT transitions FROM workflow_definitions WHERE id = %s",
                (definition_id,),
            )
            def_row = cur.fetchone()
            if def_row is None:
                # The composite FK makes this unreachable in practice; kept explicit so a future
                # schema change cannot turn it into a confusing NoneType error.
                raise WorkflowDefinitionNotFoundError(
                    f"definition {definition_id} not found in this tenant"
                )
            allowed = {(pair[0], pair[1]) for pair in def_row[0]}

            if (current_state, to_state) not in allowed:
                raise WorkflowTransitionError(
                    f"transition {current_state!r} -> {to_state!r} is not allowed by the definition"
                )

            cur.execute(
                f"UPDATE workflow_instances "
                f"SET current_state = %s, updated_at = CURRENT_TIMESTAMP "
                f"WHERE id = %s RETURNING {self._INST_COLUMNS}",
                (to_state, instance_id),
            )
            updated = cur.fetchone()

            cur.execute(
                "INSERT INTO workflow_history "
                "(id, tenant_id, instance_id, from_state, to_state, actor_principal_id) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    str(uuid.uuid4()),
                    tenant_id,
                    instance_id,
                    current_state,
                    to_state,
                    actor_principal_id,
                ),
            )
        return _instance(updated)

    def list_history(
        self, tenant_id: str, instance_id: str, limit: int = 100
    ) -> Sequence[StoredWorkflowTransition]:
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "SELECT id, tenant_id, instance_id, from_state, to_state, actor_principal_id "
                "FROM workflow_history WHERE instance_id = %s ORDER BY at LIMIT %s",
                (instance_id, limit),
            )
            rows = cur.fetchall()
        return [
            StoredWorkflowTransition(
                id=str(r[0]),
                tenant_id=str(r[1]),
                instance_id=str(r[2]),
                from_state=r[3],
                to_state=r[4],
                actor_principal_id=r[5],
            )
            for r in rows
        ]
