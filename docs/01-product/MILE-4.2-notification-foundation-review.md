# MILE-4.2 — Notification foundation, advisory review

**Document ID:** `REVIEW-MILE-4.2-NOTIFICATION`
**Version:** `1.0.0`
**Status:** **Advisory review — no authorization, no build.** Notification remains gated ([`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §9). This closes the review step for Notification in the operator's sequence (Document → Location → **Notification** → Calendar); Calendar's research enters next.
**Issued:** 2026-08-05
**Reviewer:** Claude (agent, Motor role) — advisory only, no approval authority
**Subject:** [`RESEARCH-MILE-4.2-NOTIFICATION`](MILE-4.2-notification-foundation-research.md) (authored by Codex) and [the Notification foundation page](../05-foundation/notification/README.md)
**Reviewer standpoint:** built and disposed Party/Money/Workflow/UOM and the hybrid-tenancy machinery (placement, dedicated-DB provisioning, trial→paid migration, the `tenant_session` freeze), so this review focuses on the dependency on the Party foundation, on new operational surface the kernel does not yet have, and on alignment with the verified patterns.

---

## 1. Overall assessment

**The strongest of the three research slices so far, and correctly the most cautious — recommend
proceeding to authorization once `NOTIFY-D-01` (the recipient/contact dependency) is resolved and the
`NOTIFY-D` decisions are made.** The recommended shape — a provider-neutral *transactional*
orchestrator (not marketing/chat), one recipient + email in the first slice, versioned immutable
templates, durable attempts with retry/dead-letter/reconciliation, authenticated receipts, and the
explicit truth-level ladder — is right, and the boundary discipline is excellent.

**The sequential process is compounding:** this research pre-addressed every prior cross-slice
finding — §10.1 requires table/`COPY_ORDER` alignment, `NOTIFY-INV-12` refuses **cascade** deletion of
append-only evidence (the migration-014 lesson), and §10.4 explicitly says trial→paid "freezes tenant
writes **at the existing data chokepoint**" — a direct reference to the `tenant_session` freeze built
and disposed on 2026-08-05. It even names the outbox trap the Document review raised (`NOTIFY-D-10`:
"do not overload the usage-specific outbox silently"). Those arrive already handled.

## 2. The keystone is the truth-level ladder — affirm it

Notification's equivalent of Money's currency-mismatch and Location's coordinate-validity is §5's
ladder:

```text
accepted by bOPEN ≠ accepted by provider ≠ transport delivered ≠ shown by device ≠ read ≠ acted upon
```

This is the one property whose collapse makes the foundation dangerous — a system that reports
`provider_accepted` as "delivered" (or worse, as authorization/completion of a business action,
`NOTIFY-INV-15`) is actively misleading. The research holds it firmly, including the genuinely hard and
correct distributed-systems stances: **a timeout after send is `unknown`, not `failed`**, and **blind
retry is forbidden** unless provider idempotency or reconciliation makes duplication safe
(`NOTIFY-INV-08/09`). This is the right hill to defend, and it is the hardest part to test — the refusal
matrix should keep a live "ambiguous outcome → unknown → reconciled | terminal_unknown" probe, not
only the happy path.

## 3. Cross-foundation and platform interactions (this review's main value)

1. **The Party ContactPoint dependency (`NOTIFY-D-01`) is real and is the critical path — confirmed
   from having built Party.** The Party foundation as disposed has `parties` and `party_relationships`
   and **no contact-point entity** (no email/phone/address-of-contact). So there is genuinely nothing
   to resolve a business recipient against today, and the research is right to make this a pre-build
   blocker and to forbid `principals.email` as a default destination (a principal is an *auth
   identity*, not a consented contact — the same reason the kernel already refuses to trust an email
   claim for subject binding). Two clean paths, both already in the plan (step 8):
   - **(a) A Party ContactPoint extension slice first** — a tenant-scoped `party_contact_points`
     table (endpoint type/value, verification state, purpose, effective interval) owned by *Party*,
     not Notification. Notification must not become a contact master (§3.2 correctly excludes this).
     This is the cleaner long-term path and lets `NotificationRecipientResolver` resolve against Party.
   - **(b) Explicit-destination flow only in the first slice** — the authorized invitation path, which
     owns its own destination validation and anti-enumeration, with no Party resolution. This unblocks
     a first slice without waiting on Party, and defers Party-resolved notices.
   Recommend naming which of (a)/(b) the first slice targets *before* authorization, since it changes
   the dependency graph and the migration surface.

2. **Notification introduces the kernel's first background worker/queue — the biggest new operational
   surface, and it is greenfield.** Everything in the kernel today is request-driven and synchronous;
   there is no worker, lease, dead-letter, or async dispatch machinery. `NOTIFY-INV-07` (worker
   lease/fencing so a crash cannot create concurrent unbounded attempts) and §9.1's "provider call
   outside the DB transaction" are correct and necessary, but they are **new infrastructure**, not a
   variation on an existing pattern. This deserves its own operational ADR (worker model, lease/fence
   store, backpressure, fairness across tenants so one provider outage cannot starve others,
   `NOTIFY-INV-14`). Flagging it so the first-slice estimate reflects that it builds a new runtime
   surface, not just tables and endpoints.

3. **Outbox: a dedicated notification dispatch table, not `usage_outbox`.** The codebase has two
   patterns: `usage_outbox` (migration 002, entitlement metering) and the `lifecycle_events`/audit
   envelope. Neither fits message dispatch — `usage_outbox` is metering-shaped, and audit is
   append-only history, not a work queue. `NOTIFY-D-10` is right to require a *general auditable
   dispatch contract*; recommend a purpose-built `notification_*` outbox/inbox/lease set rather than
   reusing either. (This also keeps `INV-MIGRATE-COVERAGE-01` honest — the new tables must join
   `TENANT_SCOPED_TABLES` and `COPY_ORDER`, which §10.1 already requires.)

4. **"Callback tenant fields do not establish context" is AUTH-D1 applied to provider callbacks —
   good precedent alignment.** §9.3 resolves a provider message ID to stored tenant/attempt context
   and refuses to let a callback's own tenant field grant authority. That is exactly the AUTH-D1
   principle the kernel already enforces ("a header cannot create authority"), now extended to an
   inbound webhook. Worth citing that precedent in `BOPEN-NOTIFY-001` so the callback path reuses the
   established discipline rather than inventing a parallel one. The decision to **defer outbound
   webhooks** (SSRF/DNS-rebinding/egress risk) is also correct.

5. **Anti-enumeration (`NOTIFY-INV-04`) matches the kernel's existing opaque-refusal posture.**
   Notification status must not reveal whether an email belongs to a Principal/Party — the same
   uniform-refusal discipline as `resolve_context`'s identical-403 and the placement seam's uniform
   mis-route refusal. Consistent; keep timing/response/log differences out of the enumeration surface.

## 4. Minor notes

- **Attachments reference Document versions (§10.2)** — good that a Document link does not grant
  dispatch-time content access; this correctly anticipates the Document foundation's authorized-grant
  model, and is a clean example of foundations composing without inheriting each other's permissions.
- **Purpose model (`NOTIFY-D-05`)**: "a template cannot declare itself mandatory" is the right control
  — mandatory-vs-preference is a policy decision, not a template attribute.
- **Reference flows (step 8)** — the platform invitation as an explicit-destination fixture, plus one
  Party-resolved notice once (1a) exists, is the right pair; it exercises the hard path (resolution +
  policy) without building a product.

## 5. Recommendation and what remains before any build

Ready to move toward a first slice **after**: (1) `NOTIFY-D-01` is resolved — choose path (a) Party
ContactPoint extension or (b) explicit-destination-only first slice — without defaulting to
`principals.email`; (2) `NOTIFY-D-02`–`NOTIFY-D-14` are resolved or explicitly deferred; (3) the new
operational surface (workers/leases/dead-letter) gets its ADR; (4) the successor artifacts
(`DEC-P4-ENTRY` gate amendment, `BOPEN-NOTIFY-001`, provider/channel ADR, privacy/threat model,
migration/rollback plan, operations runbooks, test matrix) are frozen with authorization recorded
**before** any build.

This review authorizes nothing and builds nothing. Notification remains gated; Calendar's research is
the next step in the operator's sequence.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
