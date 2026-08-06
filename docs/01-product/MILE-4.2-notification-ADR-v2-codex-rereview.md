# MILE-4.2 — Notification ADRs v2, independent Codex re-review

**Reviewer:** Codex (independent, read-only sandbox) — advisory only; approves/authorizes/disposes nothing; does not alter the `DEC-P4-ENTRY §9` gate.
**Subject:** the revised DRAFT ADRs v2 — [worker/queue](MILE-4.2-notification-worker-queue-ADR-draft-v2.md) and [provider/channel](MILE-4.2-notification-provider-channel-ADR-draft-v2.md).
**Workspace anchor:** `HEAD 3559cb1` (the v2 commit).
**Issued/captured:** 2026-08-06 (full output captured — the prior review's `tail -80` truncation is corrected).
**Recorded by:** Claude (Motor) — transcribing the reviewer's captured verdict.

> Read-only: Codex wrote no files and ran no validation. This is the reviewer's advisory finding.

## Verdict: **STILL NEEDS REVISION** — but the v1 root causes are closed

Every v1 failing invariant moved to **PARTIALLY-CLOSED** (the design *decisions* are now sound), and `PA-07` is **CLOSED**. The residual issues are concrete algorithm/completeness defects where the illustrative SQL or text contradicts the (now-correct) stated decision — not fundamental redesigns.

| Finding | Status | Residual defect |
| :--- | :--- | :--- |
| `NOTIFY-INV-07` | PARTIALLY-CLOSED | Idempotency-key-before-send is correctly primary, but the expired-`sending` claim SQL resets the row to `leased` and send-start increments `attempt_no`, enabling a **new** key instead of guaranteed same-attempt reuse. |
| `NOTIFY-INV-12` | PARTIALLY-CLOSED | Mutable-current + once-written history is the stated model, but an `unknown` invocation isn't appended when observed, and later text inserts out-of-vocabulary `terminal_unknown`. |
| `NOTIFY-INV-09` | PARTIALLY-CLOSED | Before/after-effect boundary + generic-503→`unknown` are sound, but expired-send reclaim remains unsafe in the concrete claim/send-start sequence. |
| `NOTIFY-INV-14` | PARTIALLY-CLOSED | Binding/quota/breaker/fairness are concrete, but concurrent claimers can independently compute the same free slots and exceed the per-tenant inflight cap (a claim-race). |
| `NOTIFY-INV-01/04` | PARTIALLY-CLOSED | The worker claimer plane is specified, but the callback-role RLS/column/function confinement, audit, and callback-specific revocation are not comparably complete. |
| `NOTIFY-INV-10` | PARTIALLY-CLOSED | Signature/timestamp/order/quarantine/rate/rotation present, but the `raw_bytes` facade can't enforce the pre-allocation size limit and the composite replay key doesn't reliably dedupe a repeated event with a changed/null replay ID. |
| Cross-ADR seams | PARTIALLY-CLOSED | Classifier ownership, routing binding, callback handoff align; lifecycle vocabulary, reclaim execution, rendered-content dereferencing, and recipient-snapshot lifetime remain unresolved. |
| `PA-07` | **CLOSED** | "Candidate" = automatic deterministic validation/classification of transport evidence, not provider/human authority, not a business transition. |
| `PA-08` | PARTIALLY-CLOSED | Disclaimers, metadata, corrected `§6` reference present; but ADR-ID inconsistency and both drafts pre-recorded `ready_for_operator_review: true` despite the open review. |

## The 9 specific corrections before another operator-readiness review

1. Replace the claim SQL with **distinct** expired-`leased` and expired-`sending` transitions.
2. Prove same-attempt reclaim preserves `attempt_no` and reuses the **exact stored** idempotency key.
3. Append the original `unknown` attempt at observation time; keep `terminal_unknown` **solely as a lifecycle state** (not an attempt outcome).
4. **Serialize** tenant slot consumption so concurrent workers cannot exceed the inflight cap.
5. Freeze callback-role RLS/function/column grants, tenantless quarantine ownership, audit identity, and callback-specific revocation.
6. Move streaming size enforcement to the public endpoint **before** `raw_bytes` construction.
7. Strengthen replay uniqueness independently of a mutable/nullable replay ID.
8. Define rendered-content transfer/dereference and recipient-snapshot lifetime.
9. Reconcile the ADR IDs and **remove the pre-recorded `ready_for_operator_review: true`** assertions. *(Done 2026-08-06: both flags set to `false`.)*

> Advisory only. It approves nothing, authorizes nothing, builds nothing, disposes nothing; Notification remains gated by `DEC-P4-ENTRY §9`.
