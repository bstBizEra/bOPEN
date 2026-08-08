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
