# EVD-MILE-4.2-WORKFLOW-MAKER — Workflow State Engine foundation

**Document ID:** `EVD-MILE-4.2-WORKFLOW-MAKER`
**Version:** `1.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision
**Issued:** 2026-08-03
**Implements:** [`DEC-P4-ENTRY`](../../decisions/DEC-P4-ENTRY.md) §8 (Workflow State Engine, MILE-4.2)
**Candidate:** `a09022d`
**Blob — `013_workflow_state_engine.sql`:** `f5e58332918dafde84e1cba592d7440301e257b4`
**Blob — `workflow_repositories.py`:** `d9fff1b0b93e77dbd8c901368d9a39c2e758aa94`
**Blob — `api.py`:** `e50569363ccfc64947d414f36a15190f59f196ec`
**Blob — `invariant-traceability.csv`:** `82aa16c1045623dd42f2478c95d19774fb9d1001`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifier:** Codex
**Suites:** canonical **539/539** against PostgreSQL (18 workflow tests added; 0 skips with the admin URL set)

---

## 1. What this is — and the one property it defends

A generic, tenant-scoped **state machine** for business processes. A **definition** names the states
and the transitions allowed between them; an **instance** carries a current state for one subject; a
**transition** moves an instance from one state to another — but **only along an edge the definition
allows**. That refusal is the whole point: without it a "workflow" is just a mutable string field.

The defended property: **a transition the definition does not list is refused, and the instance does
not move.** The check of the current state, the validation against the definition, the state update
and the append to history are **one transaction** — either all happen or none do.

**Clean-room (`AGENTS.md` §6):** independently designed. This is the ordinary finite-state-machine
pattern (states, allowed transitions, an instance's current state, an immutable transition log),
implemented from first principles — not adapted from any upstream workflow engine's source.

## 2. Defensive verification

Every proposition asserts the platform **refuses** an illegal move or a cross-tenant access, and
**admits** a legal one. No offensive objective.

## 3. Propositions (traced in `invariant-traceability.csv`)

**Group A — engine at the database and repository** (`tests/isolation/test_workflow_isolation.py`):

| ID | The engine must… | Test |
| :--- | :--- | :--- |
| `P4-WF-01` | keep one tenant's definition invisible to another | `test_a_definition_created_in_one_tenant_is_invisible_to_another` |
| `P4-WF-02` | keep one tenant's instance invisible to another | `test_an_instance_created_in_one_tenant_is_invisible_to_another` |
| `P4-WF-03` | refuse a cross-tenant definition write (WITH CHECK) | `test_a_cross_tenant_definition_insert_is_refused` |
| `P4-WF-04` | refuse an instance of another tenant's definition (composite FK) | `test_an_instance_of_another_tenants_definition_is_refused` |
| `P4-WF-05` | keep recorded history immutable to a direct UPDATE/DELETE | `test_recorded_history_cannot_be_updated_or_deleted` |
| `P4-WF-06` | refuse a transition the definition does not allow, leaving state unchanged | `test_the_repository_refuses_a_disallowed_transition` |
| `P4-WF-07` | keep recorded history from being erased by deleting its instance (cascade) | `test_recorded_history_survives_an_attempt_to_delete_its_instance` |

**Group B — HTTP layer** (`tests/integration/test_workflow_http.py`, executed HTTP, bearer-gated):

| ID | The kernel must… | Test |
| :--- | :--- | :--- |
| `P4-WF-HTTP-01` | begin an instance at its definition's initial state | `test_define_start_and_read_begins_at_initial_state` |
| `P4-WF-HTTP-02` | move on an allowed edge and record history | `test_an_allowed_transition_moves_the_instance_and_records_history` |
| `P4-WF-HTTP-03` | accumulate history in order across transitions | `test_history_accumulates_in_order_across_transitions` |
| `P4-WF-HTTP-04` | refuse a disallowed edge (422) and leave the state unchanged | `test_a_disallowed_transition_is_refused_and_leaves_the_state_unchanged` |
| `P4-WF-HTTP-05` | refuse a malformed definition (422) | `test_a_malformed_definition_is_refused` |
| `P4-WF-HTTP-06` | keep an instance private to its tenant (404) | `test_an_instance_is_invisible_to_another_tenant_over_http` |
| `P4-WF-HTTP-07` | keep a definition private to its tenant (404) | `test_a_definition_is_invisible_to_another_tenant_over_http` |
| `P4-WF-HTTP-08` | refuse transitioning another tenant's instance (404) | `test_another_tenant_cannot_transition_your_instance` |
| `P4-WF-HTTP-09` | require a bearer to start an instance (401 without) | `test_starting_an_instance_requires_a_bearer` |

**Attack angle for the verifier:** with a valid bearer, drive an instance `draft → approved` directly
(skipping `submitted`) — it must be 422 and the instance must still read `draft`, with **no** history
row for the refused move; hold tenant B's bearer and try to read or transition tenant A's instance
(must be 404); attempt `UPDATE workflow_history SET to_state=...` inside a tenant session (must affect
0 rows — append-only). The transition is atomic: a refused move writes nothing.

## 4. Execution

```text
python tools/run_tests.py     539/539 OK   (live PostgreSQL, BOPEN_ADMIN_DATABASE_URL set)
```

Migration 013 adds `workflow_definitions`, `workflow_instances` and `workflow_history`, all
tenant-scoped by RLS. The composite FK `(tenant_id, definition_id) → workflow_definitions(tenant_id,
id)` makes an instance of another tenant's definition impossible at the database. `workflow_history`
grants SELECT and INSERT only, so a recorded transition cannot be altered — the same append-only
discipline as the audit trail. Mutation intuition: drop the transition check in `apply_transition`
and `P4-WF-06`/`P4-WF-HTTP-04` break; add an UPDATE policy to `workflow_history` and `P4-WF-05`
breaks.

## 5. What this does NOT establish (disclosed)

1. **No per-transition role authorization yet.** A transition is gated by a valid bearer
   (`resolve_context`) and by the definition's allowed edges. Restricting *which role* may take a
   given edge (e.g. only a `manager` may `approve`) is a later slice; the definition schema leaves
   room for it. Recorded so the verifier does not read the bearer gate as role-level authz.
2. **No timers, no parallel/branching states, no sub-workflows.** This is a single linear/branching
   state machine per instance, not BPMN.
3. **The lifecycle event on each transition is the audit record** (`workflow_instance:transition`),
   consistent with the rest of the kernel's domain endpoints — not a separate event bus.
4. **No definition versioning or migration of running instances** across a definition change.

## 6. Verification history — one refutation, closed

The first candidate `a09022d` was verified by Codex, which **CONFIRMED 14 of 15** propositions and
**REFUTED `P4-WF-05`** under an independent lens the maker's tests had not covered
(`workflow_history_append_only_cascade_bypass`, ballot `blt_879fef0cfc4a`):

> A direct `DELETE` on `workflow_history` reaches zero rows, but the instance foreign key was
> `ON DELETE CASCADE`, so deleting the parent `workflow_instances` row erased the history through
> the referential path — which PostgreSQL performs with row security bypassed. Recorded history was
> therefore deletable. Reproduced live.

This is the same carve-out migration 009 closed for the audit trail, which the maker did not carry to
the new table. Fixed at root cause by **migration 014**: `workflow_history.fk_wf_instance` changed
from `ON DELETE CASCADE` to `ON DELETE RESTRICT`. An instance that has recorded a transition can no
longer be deleted out from under its history, and the two longer cascade paths (definition- and
tenant-deletion) now fail on the same RESTRICT. `RESTRICT` rather than dropping the key because a
workflow instance is durable business state, not an ephemeral referent like a context — the
distinction migration 009 itself draws between `context_id` (drop FK) and `tenant_id` (RESTRICT). The
reproduction is now proposition `P4-WF-07`, verified by execution.

This candidate re-submits with that fix for re-ballot.

## 7. Authority

A maker's submission. `EBIV` §8: a passing suite carries no verdict weight.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
