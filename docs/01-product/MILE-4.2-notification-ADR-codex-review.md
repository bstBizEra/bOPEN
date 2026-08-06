# MILE-4.2 — Notification ADRs, independent Codex review (captured excerpt)

**Reviewer:** Codex (independent, read-only sandbox) — advisory only, approves/authorizes/disposes nothing.
**Subject:** the two DRAFT ADRs — [worker/queue](MILE-4.2-notification-worker-queue-ADR-draft.md) (`2842b4b`) and [provider/channel](MILE-4.2-notification-provider-channel-ADR-draft.md) (`0230c22`), both Claude-team-authored (Codex is the reviewer-not-author).
**Issued/captured:** 2026-08-06
**Recorded by:** Claude (Motor) — transcribing the reviewer's captured output.

> **Capture note (honest scope).** The dispatch command piped Codex's output through `tail -80`, so
> this file preserves only the **final portion** of the review: the cross-ADR/kernel consistency
> findings (§4), what-remains (§5), the readiness verdict (§6), and findings `PA-07`/`PA-08`. The
> earlier per-ADR assessment, confirmed strengths, and findings `PA-01`–`PA-06` were **not captured**
> and can be re-run. The captured portion below carries the actionable core — the verdict and the
> specific invariant failures.

---

### PA-07 — Medium: provider distrust wording needs one clarification

The Location analogy uses a separate authorized `accept_observation` action. Notification does not appear to require a human acceptance of every provider response. State explicitly that "candidate requiring acceptance" means deterministic validation/classification into provider-observed transport evidence — not a provider-authorized or human-authorized business transition.

### PA-08 — Medium: draft authority and traceability metadata need correction

Phrases such as "only email is authorized for a first build" and "the only adapter this ADR authorizes" conflict with the ADR's own no-authority status. Replace them with "proposed first implementation scope" and "specified test adapter."

The ADRs also lack the controlled-document metadata required by repository rules: document ID, version, owner, issue/update date, governing/dependent artifacts, and evidence references. The references to "AGENTS.md §11 facade pattern" are inaccurate; root §11 concerns testing.

---

## 4. Cross-ADR and kernel consistency

The two ADRs agree on the major trust boundary but disagree or leave gaps at the operational seam:

1. **Expired lease handling:** the worker treats an expired lease as reclaimable work, while the adapter admits that duplicate safety depends on provider idempotency/reconciliation. These cannot remain separate decisions.
2. **Classifier ownership:** the worker "owns" the classifier; the adapter maps vendor responses; the provider profile supplies classification. Freeze a single ownership model and one vocabulary: `provider_accepted`, `retryable_failed`, `terminal_failed`, `unknown`.
3. **Provider routing:** the scheduler must skip open-provider work, but the dispatch row has no provider/profile binding. The adapter allows one-or-more providers while routing policy is deferred.
4. **Callback ownership:** the worker owns the endpoint and database transition; the adapter owns verification and normalization. Define the exact handoff between raw edge input, verified provider observation, stored binding lookup, tenant-scoped receipt append, and lifecycle projection.
5. **Recipient boundary:** the provider ADR assigns staleness/cross-tenant validation to the adapter, but the disposed ContactPoint snapshot cannot support it. Validation belongs before the adapter unless the ContactPoint contract is deliberately extended.
6. **Placement:** all disposed repositories perform tenant content operations through `tenant_session`; the worker's cross-tenant claim is a new privileged plane. It cannot inherit tenant placement/freeze correctness merely by opening a later tenant session.
7. **Append-only pattern:** Workflow, ContactPoint, and Location demonstrate mutable current state plus separate immutable history in the same transaction. Notification must follow that pattern explicitly; a single attempt row cannot serve as both pre-send marker and finalized immutable evidence.
8. **Provider-distrust consistency:** both ADRs correctly preserve the research ladder (`bOPEN accepted ≠ provider accepted ≠ transport delivered ≠ shown ≠ read ≠ acted upon`). That part is internally consistent and should remain the keystone.

## 5. What remains before build-authorization-readiness (reviewer list)

1. Replace the current lease sequence with a crash-safe send-start protocol that does not resend expired `send-started` work without proven provider idempotency.
2. Freeze the immutable attempt/observation/receipt schema and all allowed state transitions, including late and conflicting evidence.
3. Define the complete adapter facade, classifier ownership, response constraints, reconciliation semantics, and provider qualification requirements.
4. Resolve dedicated-DB queue topology, placement enumeration, migration freeze, callbacks during cutover, and global versus per-placement health state.
5. Specify worker and callback service principals, database roles, column grants/functions, authorization checks, audit identity, and revocation.
6. Provide implementable SQL/state machines for fair claim, per-tenant inflight limits, quota reservation, backpressure, and one-probe circuit breaking.
7. Resolve provider-profile binding and callback identity, early-callback quarantine, replay uniqueness, ordering, rate limiting, raw-byte size enforcement, and secret rotation.
8. Freeze the recipient/render contracts at the orchestrator-to-adapter seam.
9. Resolve or explicitly defer all `NOTIFY-D-01` through `NOTIFY-D-14` without leaving implementation defaults. `NOTIFY-D-10`, `D-11`, and `D-13` are not yet adequately resolved by these drafts.
10. Produce `BOPEN-NOTIFY-001`, API/error/event/template schemas, privacy and threat model, retention rules, migration/rollback/compensation plan, operations runbooks, test matrix, and accepted work package.
11. Require live PostgreSQL concurrency/RLS/migration/restore evidence and real-provider callback/idempotency evidence before provider qualification. A fake adapter proves only the owned contract.
12. Only after those revisions may the operator separately consider bounded build authorization. Verification, disposition, deployment, provider activation, and production activation remain distinct later acts.

## 6. Readiness verdict

**NEEDS REVISION.** Specific reasons:

- `NOTIFY-INV-07` is **not defended**: fencing a database update does not prevent concurrent or duplicate external **sends**.
- `NOTIFY-INV-12` is **internally inconsistent**: an append-only attempt cannot be both stamped before send and finalized after send in one row.
- `NOTIFY-INV-09` is **violated** by expired-lease resend and ambiguous generic 503 classification.
- `NOTIFY-INV-14` is **only aspirational** until placement, provider binding, scheduler state, quota transactions, and breaker fencing are specified.
- The elevated worker/callback authorization and RLS design does **not yet defend** `NOTIFY-INV-01/04`.
- The callback contract **only partially defends** `NOTIFY-INV-10`.
- The adapter facade is **incomplete** and does not match the current ContactPoint or rendered-content boundaries.

> This is an advisory reviewer finding only. It approves nothing, authorizes nothing, builds nothing, and disposes nothing.
