# EVD-OPTION-A-DEDICATED-AUTH-CHAIN-MAKER — a usable dedicated tenant

**Document ID:** `EVD-OPTION-A-DEDICATED-AUTH-CHAIN-MAKER`
**Version:** `1.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision
**Issued:** 2026-08-04
**Implements:** [`DEC-P35-TENANCY-MODEL`](../../decisions/DEC-P35-TENANCY-MODEL.md) §11 (Option A, authorized)
**Candidate:** the commit carrying this submission (filled on commit)
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifier:** Codex
**Suites:** canonical **551/551** against PostgreSQL, with a second real database provisioned

---

## 1. What this is — and the one property it defends

The fix that makes a dedicated tenant **usable**. The §10 provisioning slice proved a dedicated
tenant's domain data routes to its own database, but the tenant could not be *onboarded*:
`memberships`, `active_contexts` and `audit_events` foreign-key `principal_id` to the global
`principals`, and a foreign key cannot hold across the control/dedicated database split — so creating
a membership for a dedicated tenant raised `ForeignKeyViolation`.

The defended property: **a dedicated tenant can be given a membership and a context — the auth chain
completes — while its principal stays global in the control database, not copied.** Migration 016
drops the three cross-database `principal_id` foreign keys (columns kept as soft references), the same
reasoning migration 009 applied to `audit_events.context_id`.

**Clean-room (`AGENTS.md` §6):** the decision (drop the FK vs replicate vs route) was reasoned from
this schema and the 009 precedent, not adapted from any external framework.

## 2. Defensive verification

The propositions assert the chain that was **refused** now **completes**, and that the principal is
**not** replicated into the dedicated database (which would silently adopt Option B). No offensive
objective; two local verification databases.

## 3. Propositions (traced in `invariant-traceability.csv`)

`tests/isolation/test_dedicated_auth_chain.py`, executed SQL across two databases:

| ID | The kernel must… | Test |
| :--- | :--- | :--- |
| `P4-AUTHCHAIN-01` | let a dedicated tenant be given a membership, landing in its own database | `test_a_dedicated_tenants_membership_lands_in_its_database` |
| `P4-AUTHCHAIN-02` | keep the principal global in control — not copied into the dedicated database | `test_the_principal_stays_global_in_control_and_is_not_copied` |
| `P4-AUTHCHAIN-03` | let a dedicated tenant establish a context in its own database | `test_a_dedicated_tenant_can_establish_a_context` |

**Attack angle for the verifier:** roll migration 016 back and the membership creation in
`setUpClass` fails with `ForeignKeyViolation` — the whole class goes red, which is the point.
Confirm the principal exists in the control database and is **absent** from the dedicated database
(a copy would mean Option B was taken by accident). Confirm the membership and context are found by
querying the dedicated database directly.

## 4. Execution

```text
python tools/run_tests.py     551/551 OK   (live PostgreSQL, a second DB provisioned)
```

Migration 016 drops `memberships_principal_id_fkey`, `active_contexts_principal_id_fkey` and
`audit_events_principal_id_fkey`, keeping the columns and documenting each as a soft reference. The
relationship the database can no longer enforce across databases is still checked in the application:
`principals.get` reads the principal from the control registry, and `POST /v1/contexts` checks the
membership names the caller's principal. Nothing routes or replicates principals — they stay a single
global registry, which is what lets a principal belong to several tenants at once.

## 5. What this does NOT establish (disclosed)

1. **No orphan handling on principal deletion.** The application role has no DELETE policy on
   `principals` (migration 007) and no code path deletes one, so a dangling `principal_id` is not
   reachable today. If principal deletion is ever built, cleanup for these three columns is its
   concern — recorded, not built.
2. **New dedicated tenants.** The trial→paid migration of an *existing* shared-pool tenant to a
   dedicated database (moving its rows across databases atomically) remains a separate deferred slice.
3. **The FK drop weakens a same-database guarantee, and closes a covert channel.** On the shared
   pool, a membership's `principal_id` is no longer FK-guaranteed (it was `ON DELETE CASCADE`/`SET
   NULL` before); the application validation above is now the guarantee everywhere — the deliberate
   trade for a uniform schema across shared and dedicated databases. As a **side effect it closes a
   covert channel**: the FK check bypassed row security, so before 016 a membership for a
   hidden-but-real principal succeeded while one for a non-existent principal raised a violation —
   an observable difference that let principal existence be probed. After 016 both are admitted
   identically. `test_dropping_the_cross_database_principal_fk_moves_integrity_to_the_application`
   (updated from the prior FK test) records both consequences.
4. **One verifier, not two** (two-agent profile).

## 6. Authority

A maker's submission. `EBIV` §8: a passing suite carries no verdict weight.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
