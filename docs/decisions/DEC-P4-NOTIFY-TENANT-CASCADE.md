# DEC-P4-NOTIFY-TENANT-CASCADE — deleting a tenant erases its notification evidence

**Decision ID:** `DEC-P4-NOTIFY-TENANT-CASCADE`
**Version:** `1.0.0`
**Status:** **Proposed — decision request raised under `AGENTS.md` §16 (a destructive path lacks a recovery strategy)**
**Issued:** 2026-08-08
**Owner:** Engineering / Security Authorities
**Raised by:** Claude (agent, Motor role) — maker of the artifact the defect is in
**Governing:** `AGENTS.md` §8, §14; `BOPEN-GOV-EBIV-001`; `RESEARCH-MILE-4.2-NOTIFICATION` `NOTIFY-INV-12`

---

## 1. The finding, reproduced rather than reasoned

Independent verification of Notification Stage 1 (Codex, ballot commit `bd42b2e`) probed tenant
deletion on a disposable tenant holding notification evidence:

```text
POST_DELETE_TENANTS=0
POST_DELETE_NOTIFICATIONS=0
POST_DELETE_NOTIFICATION_DISPATCH=0
POST_DELETE_NOTIFICATION_ATTEMPT=0
POST_DELETE_NOTIFICATION_RECEIPT=0
```

**The deletion succeeded and erased the attempt and receipt rows.** PostgreSQL followed the parallel
`tenant_id ON DELETE CASCADE` paths; the `ON DELETE RESTRICT` foreign keys on
`fk_attempt_dispatch` and `fk_receipt_dispatch` preserved nothing.

The maker had disclosed this as a gap but predicted the opposite behaviour — that the deletion would
*raise* and be blocked. The maker was wrong in the safer direction's favour, which is why the probe
mattered.

## 2. What it contradicts

`021_notification_foundation.sql` states in its header that a recorded attempt or receipt survives
deletion "through the tenant cascade above it, a whole tenant". **It does not.** The cascade limb of
`NOTIFY-INV-12` — *"Direct update/delete and parent cascade cannot erase attempts, receipts, render
provenance"* — is not defended.

Two `ON DELETE RESTRICT` foreign keys were placed to enforce append-only evidence, and they do
enforce it against a *direct* dispatch delete (three propositions confirm that). They are simply not
on the path a tenant delete takes: `notification_attempt.tenant_id` and
`notification_dispatch.tenant_id` each reference `tenants(id) ON DELETE CASCADE` independently, so
the rows are removed by the tenant edge before the dispatch edge is ever consulted.

## 3. Severity

**Latent, not active.** No tenant-deletion path exists in `tools/` or `platform_kernel/` today, so
nothing in the running system can trigger it. That is the only reason this is a decision request
rather than an incident.

It is nonetheless the kind of defect that becomes severe silently: the first tenant-offboarding
feature written against this schema would destroy delivery evidence as a side effect, and the append-
only design would have given every reader the opposite expectation. The same shape almost certainly
applies to other foundations carrying `tenant_id ON DELETE CASCADE` alongside append-only history —
that is worth checking before it is decided here.

## 4. Options

| # | Option | Assessment |
| :--- | :--- | :--- |
| 1 | **Correct the migration header only** and record that tenant deletion destroys evidence by design | Cheapest and honest, but concedes that `NOTIFY-INV-12`'s cascade limb is undefended — a research invariant would be silently narrowed by an implementation choice |
| 2 | **Make the tenant edge `RESTRICT` on the evidence tables**, so a tenant holding evidence cannot be deleted until it is archived | Defends the invariant as written. Turns tenant deletion into an operation with a prerequisite, which is a product decision, not only a schema one |
| 3 | **Separate evidence retention from tenant lifetime** — archive or tombstone evidence before the cascade | Defends the invariant and keeps deletion possible; the largest change, and it reaches data-retention policy |
| 4 | **Accept and defer to the worker/callback stage**, with a disclosed `UNVERIFIED` row standing | Acceptable only while no tenant-deletion path exists; needs a named condition that revisits it before one is built |

No option is recommended here. The maker of the defective artifact is the wrong party to choose
between narrowing an invariant and changing a retention model, and §14 makes a destructive path
without a recovery strategy an Engineering/Security decision.

## 5. What this decision request does not do

It does not change the migration, alter any ballot, or dispose the Notification package. Stage 1
remains **not confirmed**: 19 propositions carry admissible `CONFIRMED` ballots, one is
`INADMISSIBLE` on a mechanism attribution, and an operator disposition under EBIV §6.5 has not been
recorded.

Raised advisory-only. Confers no implementation, approval, merge, release or production authority.

---

## 6. Amendment 2026-08-08 — the defect is systemic, and the correct pattern is already in this repository

§3 said the same shape "may apply to other foundations" and that this was worth checking before
deciding. It was checked. **It applies to 11 tables across 4 foundations, three of which are already
operator-disposed.**

Scan basis: every table protected by an `ON DELETE RESTRICT` foreign key — whether declared at
`CREATE TABLE` or added by a later `ALTER` — paired against the action on its own
`tenant_id REFERENCES tenants(id)` edge.

| Table | `tenant_id` edge | Introduced by | |
| :--- | :--- | :--- | :--- |
| `audit_events` | **RESTRICT** | `003_phase1_context_audit.sql` | safe |
| `lifecycle_events` | **RESTRICT** | `005_lifecycle_audit_and_rollout.sql` | safe |
| `workflow_history` | CASCADE | `014_workflow_history_survives_its_instance.sql` | **at risk** |
| `party_contact_points` | CASCADE | `019_party_contact_points.sql` | **at risk** |
| `party_contact_point_verification_events` | CASCADE | `019` | **at risk** |
| `location_address_versions` | CASCADE | `020_location_foundation.sql` | **at risk** |
| `location_geometry_observations` | CASCADE | `020` | **at risk** |
| `location_external_identifiers` | CASCADE | `020` | **at risk** |
| `location_relationships` | CASCADE | `020` | **at risk** |
| `location_history` | CASCADE | `020` | **at risk** |
| `notification_dispatch` | CASCADE | `021_notification_foundation.sql` | **at risk** |
| `notification_attempt` | CASCADE | `021` | **at risk** |
| `notification_receipt` | CASCADE | `021` | **at risk** |

### 6.1 Epistemic status — what is reproduced and what is inferred

**Reproduced live:** the notification tables only, by Codex on a disposable tenant (§1).

**Inferred for the other eight:** the declared constraint semantics are identical, and the migration
set contains **no trigger, no rule and no `DEFERRABLE` constraint** anywhere, so nothing can
intervene between the declaration and the behaviour. The inference is strong but it is an inference;
a verifier should reproduce it per foundation before any fix is accepted.

### 6.2 The repository already knows the answer

`audit_events` and `lifecycle_events` carry `tenant_id ... ON DELETE RESTRICT` and are not exposed.
This is not an unsolved design question — it is a pattern that was solved for the Phase 1 and Phase 3
audit tables and **not carried forward into the Phase 4 foundations**.

`migration 009` states the underlying rule plainly: *"PostgreSQL performs foreign-key actions with
row security bypassed"*. An append-only guarantee built from policies is therefore only as strong as
every `ON DELETE` action that can reach the row.

### 6.3 The sharpest illustration is `workflow_history`

Migration `014` exists **for this exact class of defect**. Its header records a live reproduction:

> transition recorded → 1 row; direct DELETE on history → 0 rows; DELETE the parent instance →
> history cascades 1 → 0
>
> *"A recorded transition erased, every direct-DELETE test still green while it happened."*

It closed the hole on the **instance** edge and left the **tenant** edge `CASCADE`. The same
migration that teaches this lesson is on the at-risk list. Notification's header cites "the
migration-014 lesson applied in advance" — it inherited both the fix and the gap.

### 6.4 What changes for this decision

The options in §4 were framed for one foundation. They now read differently: option 1 (correct the
header only) would concede the cascade limb of an append-only guarantee across four foundations, and
option 2 (`RESTRICT` the tenant edge) would simply apply the pattern `003` and `005` already use.

Three affected foundations — Workflow, ContactPoint, Location — have recorded operator dispositions.
Whether a disposed artifact carrying a latent defect of this shape needs re-disposition is a question
this request does not answer and should not.

Still latent: no tenant-deletion path exists in `tools/` or `platform_kernel/`. Nothing here is an
active data-loss path today.

## 7. Decision 2026-08-08 — Option 2, and the existing dispositions stand

| Field | Value |
| :--- | :--- |
| **Decision** | **Option 2 — make the `tenant_id` edge `ON DELETE RESTRICT`** on the 11 at-risk evidence tables, applying the pattern `audit_events` (003) and `lifecycle_events` (005) already use |
| **Rejected** | Option 1 (header-only) — it would narrow a research invariant by implementation default across four foundations, which §16 exists to prevent |
| **Scope** | One migration covering all 11 tables, not four per-foundation migrations. The defect is one shape with one fix; splitting it would multiply the verification cost without changing the change |
| **Work package** | `WP-P35-08` (drafted; **not yet accepted** — entry gate still required) |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — Engineering & Security Authorities |
| **Decision timestamp** | 2026-08-08 |
| **Recorded by** | Claude (agent, Motor role), transcribing an operator decision. `execution_authority: false`, `approval_authority: false` |

The recommendation for Option 2 came from the maker of one of the defective artifacts. §4 said that
party should not choose between narrowing an invariant and changing a retention model, and that
still holds — what makes this admissible is that the operator, not the maker, made the choice.

### 7.1 Turning tenant deletion into a conditional operation is the accepted cost

Under `RESTRICT`, a tenant holding evidence cannot be deleted until that evidence is archived or
released. That is a product consequence, not only a schema one, and it is accepted deliberately: a
tenant-offboarding feature must now be written to confront evidence retention rather than to
silently destroy it. Option 3 (separate retention from tenant lifetime) remains the fuller answer
and is **not foreclosed** — `RESTRICT` is the floor that makes its absence loud instead of silent.

### 7.2 The three existing dispositions are not reopened

Workflow, ContactPoint and Location carry recorded operator dispositions made on the evidence
available at the time. Those dispositions remain accurate statements about what was verified then,
and the defect is now annotated in each foundation's README.

Reopening them is unnecessary because **the fix supplies its own cycle**: migration `022` changes
those tables, which produces a new candidate requiring its own verification and its own disposition.
The corrected state will be disposed on its own evidence rather than by amending a past record.

### 7.3 Verifier eligibility, checked before roles were assigned

`git blame` across all five migrations, `test_rls_database_behavior.py` and
`migrate_tenant_to_dedicated.py` shows **Claude only** — the `BizEra` lines are the disclosed
attribution gap of §21.4 and are Claude-authored. **Codex authored nothing on this surface and is
eligible under both readings of EBIV §3.** Checked first this time, after `WP-P35-07` assigned a
verifier who turned out to be disqualified.
