# ADR — Notification worker/queue operational model

**STATUS: DRAFT / PROPOSED — NOT AUTHORIZED, NOT IN FORCE. Notification remains gated by DEC-P4-ENTRY §9. This ADR authorizes nothing and builds nothing; a build needs a separate operator authorization recorded first.**

---

## Controlled-document metadata

| Field | Value |
|---|---|
| **Document ID** | `ADR-NOTIFY-WQ` (proposed; pending governance ID-registry ratification) |
| **Version** | 2.1.0-draft |
| **Owner** | Architecture & Engineering Authority — Notification (Motor authoring; Codex independent reviewer) |
| **Issued** | 2026-08-06 |
| **Updated** | 2026-08-06 |
| **Status** | DRAFT / PROPOSED — gated by DEC-P4-ENTRY §9 |
| **Governing artifacts** | DEC-P4-ENTRY §9; MILE-4.2 notification foundation research + review; AGENTS.md §6 (clean-room) |
| **Dependent artifacts** | ADR-NOTIFY-PROVIDER (provider/channel); BOPEN-NOTIFY-001; API/error/event/template schemas; privacy & threat model; retention rules; migration/rollback/compensation plan; operations runbooks; test matrix; EBIV evidence |
| **Evidence refs** | `docs/01-product/MILE-4.2-notification-ADR-codex-review.md`; `docs/01-product/MILE-4.2-notification-foundation-research.md`; `docs/01-product/MILE-4.2-notification-foundation-review.md`; kernel files listed in the clean-room note |

This is version 2.1.0-draft: a revision of the prior draft that closes the independent reviewer's NEEDS-REVISION findings (INV-07, INV-09, INV-12, INV-14, INV-01/04, INV-10, adapter facade, PA-07/PA-08). It is DRAFT/advisory; it authorizes and builds nothing.

> **Changelog — 2.1.0-draft:** applied re-review corrections 1–9; concurrency proofs deferred to the build-time test matrix.

---

## Context

The platform kernel today is entirely request-driven and synchronous: FastAPI + PostgreSQL 17 forced-RLS + psycopg3, with every write scoped by `tenant_session(tenant_id)` and placement resolved per request (`_connect_for_tenant`). There is **no worker, no lease, no queue, no async dispatch, and no background actor identity anywhere in the kernel.** The existing outbox (`002_*` `usage_outbox`) is metering-shaped (`capability_id`/`quantity`/`unit`) with no lease and no attempt history; the audit/lifecycle trail is append-only history, not a claimable work queue.

Per REVIEW-MILE-4.2-NOTIFICATION, the Notification worker/queue is therefore the kernel's **single biggest new operational surface** — greenfield, introducing for the first time (a) a long-lived process that holds no request context, (b) a leased hand-off to an external provider across a network boundary, and (c) an inbound callback endpoint with no session. Because the kernel forbids holding a tenant DB transaction open across the provider call (RESEARCH §9.1), correctness cannot come from row locks alone; it must come from durable, fenced, tenant-scoped state — and, for the external send itself, from a deterministic provider idempotency key recorded before any byte leaves the process.

This ADR reconciles five design dimensions — worker execution & lease/fencing, retry/dead-letter/outcome-truth, tenant fairness & backpressure, dispatch tables & transactional outbox, and inbound callbacks/idempotency/egress — into one coherent operational model. It remains **advisory**: Notification is gated, and nothing here is authorized to run.

### The keystone that does not move: the provider-distrust truth-ladder

The design's foundation is the research ladder, unchanged and unweakened:

> **bOPEN accepted ≠ provider accepted ≠ transport delivered ≠ shown ≠ read ≠ acted upon.**

Every mechanism below serves this ladder. A 2xx from a provider is a **handoff**, never human delivery; `accepted → delivered` is advanced only by an authenticated receipt; an ambiguous send is `unknown`, never optimistically resolved. This is the keystone and it is the reference point for every revision in this version.

### What this revision corrects (reviewer verdict → this document)

The independent review returned **NEEDS REVISION** with seven specific defects. This version closes each at its root:

1. **INV-07 not defended** (fencing a DB row cannot prevent a duplicate external *send*) → Decision 3 splits INV-07 into two disjoint mechanisms: fencing governs concurrent *claims*; a deterministic pre-recorded idempotency key governs duplicate *sends*.
2. **INV-12 internally inconsistent** (one append-only row cannot be both pre-send marker and finalized record) → Decision 4 adopts the kernel's mutable-current-state-row + separate-append-only-history pattern: the marker lives on the mutable `notification_dispatch`; the finalized record is a once-written `notification_attempt`.
3. **INV-09 violated** (expired-lease resend; ambiguous generic 503) → Decision 5's classifier fails closed to `unknown` (generic 503 defaults to `unknown`), and Decision 6 forbids any blind resend of a `send_started` reclaim.
4. **INV-14 only aspirational** → Decision 7 gives concrete fairness SQL, a provider-binding column, a transactionally-reserved quota bucket, and a fenced one-probe breaker.
5. **INV-01/04 not yet defended by the elevated actor** → Decision 8 splits the one elevated role into two least-privilege principals with narrow RLS + column grants and body-independent audit routing.
6. **INV-10 only partially defended** → Decision 9 fixes the raw-byte verification order, early-callback quarantine, replay uniqueness, per-provider rate limiting, and secret rotation.
7. **Adapter facade incomplete / seams open** → Decision 10 freezes the cross-ADR seams (classifier ownership, callback handoff, provider binding) so worker and adapter cannot diverge.

---

## Decision

Adopt a **Postgres-only transactional-outbox worker** — no Redis, broker, or external scheduler — built on a purpose-built `notification_*` table set, with a durable fenced lease for **claim concurrency**, a deterministic provider idempotency key for **duplicate-send safety**, a mutable-current-state row plus separate append-only evidence trail, in-database fairness and backpressure, and two least-privilege service principals for the background and callback planes. Ten decisions form one model.

---

### 1. Tables (the substrate)

A purpose-built `notification_*` set, each tenant-scoped with **forced RLS, tenant-inclusive composite FKs, and `ON DELETE RESTRICT` on the append-only tables**. Mutable current-state rows and separate append-only history tables are kept strictly distinct (Decision 4).

| Table | Shape | Role |
|---|---|---|
| `notifications` | mutable state row | Orchestration record: `id`, `tenant_id`, `purpose`, `channel`, template-version ref, recipient-snapshot ref, `lifecycle_state`, `revision`, `correlation_id`, `idempotency_key` with **`UNIQUE (tenant_id, idempotency_key)`**. |
| `notification_dispatch` | mutable / claimable **current-state row** | The outbox work-queue row and the whole send-window state machine: `dispatch_id`, `tenant_id`, composite FK `(tenant_id, notification_id)`, `status` (pending/leased/sending/reconciling/done/dead), `attempt_no`, `send_key`, `send_started_at`, `available_at` (backoff gate), **`lease_owner`, `lease_expires_at`, `lease_fence BIGINT`**, `next_visible_at`, `dead_lettered_at`, and the enqueue-time binding **`provider_id`, `provider_profile_version`**. **Content-free** — ids, scheduling, and lease/send control columns only. |
| `notification_attempt` | append-only (SELECT+INSERT only) **immutable history** | Per-attempt evidence, INSERTed **exactly once at finalization**: `attempt_id`, `tenant_id`, composite FK `… ON DELETE RESTRICT`, `attempt_no`, `provider_profile`, request fingerprint, **`provider_idempotency_ref`** (sourced from the mutable `send_key`), `started_at`/`ended_at`, **`classified_outcome`** (`provider_accepted`/`retryable_failed`/`terminal_failed`/`unknown`), `safe_code`, `provider_message_id`, `next_retry_at`. |
| `notification_receipt` | append-only, same policy | Provider-observed truth: provider event id, provider-observed time, normalized transport status, raw-payload integrity ref, `applied|superseded|conflicting` projection marker. |
| `notification_callback_event` | append-only, same policy | Accepted-callback dedup ledger keyed on a **deterministic `dedup_key`** — `dedup_key = digest(provider_id ‖ provider_message_id ‖ provider_event_id ‖ payload_signature_digest)` computed from stable, signature-covered fields — with `UNIQUE (provider_id, provider_message_id, dedup_key)`. The dedup key does **not** depend on a mutable/nullable provider `replay_id`; `replay_id` (when present) is stored as evidence only, so a redelivered event with a changed or null `replay_id` still collides. |
| `notification_callback_quarantine` | append-only, same policy | Verified-but-unbound early callbacks (content-free), re-resolved on a bounded pass. |
| `notification_quota` | control-plane current-state row | Token-bucket admission: `(tenant_id, purpose, window_start)` → `tokens_used`, `tokens_limit`. |
| `notification_quota_suspend` | control-plane flag | Emergency per-tenant suspension, **never** conflated with ordinary quota. |
| `notification_fairness` | control-plane current-state row | Interleave cursor: `(tenant_id PK, last_served_at)`. |
| `notification_provider_health` | control-plane current-state row | Circuit breaker + probe fence: `(provider_id, state, failure_count, opened_at, half_open_at, probe_fence BIGINT, probe_owner, probe_lease_expires_at)`, plus per-provider callback-rate counter. |

All tenant-owned tables register in **both** `TENANT_SCOPED_TABLES` (RLS classification) and the trial→paid `COPY_ORDER`, parents before children (`notifications` before `notification_dispatch`/`_attempt`/`_receipt`/`_callback_event`/`_callback_quarantine`) — the cross-inventory coverage test fails loud on any unmapped tenant-scoped table.

**Reconciliation note (lease location).** The lease lives as **columns on `notification_dispatch`**, not as a separate `notification_dispatch_lease` table, keeping the claim, the fence, the `send_key`, the `send_started_at` marker, and the visibility gate in one atomically-updated row. The separate-lease-table variant is recorded as a rejected alternative. The dispatch row is tenant-scoped **and** carries an additional worker-role RLS policy (Decision 8); it is a tenant-scoped table whose content-free columns are additionally visible to one elevated, column-restricted role.

---

### 2. Enqueue (transactional outbox) with provider binding and quota reservation

Inside a single `tenant_session` transaction the caller inserts the `notifications` row **plus** a `notification_dispatch` row (`status='pending'`), **reserves one quota token** (Decision 7-D3), and **resolves the provider binding** — all atomic with any business write sharing that transaction — then commits. An enqueue can never be lost or leaked relative to its cause, can never exist without a token, and is never claimable without a bound provider.

- **Provider/profile binding is a column, resolved at enqueue** (`provider_id`, `provider_profile_version`), by the channel→adapter selection of the provider ADR (first proposed slice: the single `email` adapter; multi-adapter selection *policy* stays deferred — NOTIFY-D-07 — but the *column is always populated*). This is the reviewer's seam-3 fix: the scheduler cannot "skip open-provider work" if the work carries no provider identity.
- A retried `notification.request` collides on `UNIQUE(tenant_id, idempotency_key)` and returns the existing notification/dispatch instead of enqueuing a second one (**NOTIFY-INV-06**). Send idempotency is caller/event-scoped, **not** content-hashed (which wrongly collapses two legitimately-distinct sends and fails to fence a pre-render retry).

---

### 3. Split INV-07 into two mechanisms with disjoint scopes

The reviewer is right that fencing a DB row cannot prevent a duplicate *external* send: a worker that sent, then lost its lease, has *already sent*. So the lease/fence is demoted from "the INV-07 mechanism" to what it actually is — a **claim-concurrency** control inside the database. The at-most-once-effective guarantee moves to a **deterministic provider idempotency key recorded before the send** and to a **send-start protocol** that never blind-resends an ambiguous attempt.

- **Lease + monotonic `lease_fence` (DB clock) governs concurrent CLAIMS only.** It guarantees at most one worker *acts on* a dispatch row at a time and that a resumed stale worker's DB writes match nothing (fenced CAS). It makes **no** claim about network sends — the row lock and the lease both live entirely inside Postgres. This is the worker analogue of the optimistic `revision` CAS already used on mutable state rows.
- **A deterministic per-attempt provider idempotency key governs duplicate EXTERNAL SENDS** and is the **primary at-most-once-effective mechanism.** Where the provider honors it, two physical sends carrying the same key collapse to one provider-side effect.

`provider_idempotency_key = deterministic_key(dispatch_id, attempt_no)` — a pure function of the **attempt** identity (not the notification, not content). Recomputable by any worker from durable columns; never random, never stored-only. Granularity is **per-attempt**, and that is load-bearing:

- A **reclaim of the same attempt** (crash mid-send) recomputes the **same** key → a safe re-send collapses at the provider.
- A **fresh retry** of a `retryable_failed` attempt increments `attempt_no` → a **new** key → it genuinely re-sends, correct precisely because a provably-before-effect failure created no provider-side message.

Determinism-from-stored-identity echoes how placement/`resolve_context` derive authority from stored facts, never from a caller-supplied or randomly-minted token ("a header cannot create authority").

*Invariants:* INV-07 (now split: fencing = concurrent claims; key = duplicate sends), INV-06, INV-09.

---

### 4. Evidence model split — mutable current-state row + separate append-only history (closes INV-12)

The prior draft made `notification_attempt` simultaneously (a) append-only "SELECT+INSERT only" evidence and (b) a row *stamped `sending` before the provider call* and carrying a *provider idempotency ref recorded before send*. Those cannot both be true. The kernel already solved this shape and never conflates the two: `workflow_instances` is the mutable current-state row, `workflow_history` is the separate append-only record, and `apply_transition` (workflow_repositories.py) writes both in one transaction; migration 014 protects the history with `ON DELETE RESTRICT` and 013 makes it SELECT+INSERT-only. Notification adopts that split verbatim, with the one adaptation the workflow engine never needs — the advance is split around a network send the kernel forbids holding a transaction across (RESEARCH §9.1).

**D-EV-1 — Two artifacts, never one.** The mutable current-state row is `notification_dispatch` (analogue of `workflow_instances`); the immutable records are `notification_attempt` + `notification_receipt` (analogue of `workflow_history`): **SELECT+INSERT-only RLS policies, no UPDATE/DELETE policy, tenant-inclusive composite FK `ON DELETE RESTRICT`**. No pre-send column, no `started`-marker, and no reconciliation state ever lives on the immutable tables — they are written exactly once, at finalization.

**D-EV-2 — The state machine lives entirely on the mutable `notification_dispatch` row.** States and the only legal transitions (`now()` is the DB clock throughout):

| From | To | Trigger | Guarded by (fenced CAS) | Immutable write |
|---|---|---|---|---|
| `pending` | `leased` | first claim (never sent) | `status='pending'`; sets `lease_fence=lease_fence+1` | none |
| expired `leased` | `leased` | **re-claim of a never-sent row** — safe to issue a fresh attempt | `status='leased' AND lease_expires_at<now()`; sets `lease_fence=lease_fence+1` | none |
| expired `sending` | `reconciling` | **re-claim of a row where a send may have gone out** — MUST NOT blind-resend; routes to reconciliation | `status='sending' AND lease_expires_at<now()`; sets `lease_fence=lease_fence+1`; **preserves `attempt_no` and the stored `send_key`/`provider_idempotency_ref` (no new key minted)** | none yet |
| `leased` | `sending` | record send-intent (D-EV-3) — genuinely new attempt | `WHERE dispatch_id=:id AND lease_fence=:fence AND status='leased'` | none |
| `sending` | `done` | finalize `provider_accepted`/`terminal_failed` | same fenced guard on `status='sending'` | **INSERT 1 attempt** |
| `sending` | `pending` | finalize `retryable_failed` (backoff) | same guard; sets `available_at`, clears `send_key`/`send_started_at` | **INSERT 1 attempt** |
| `sending` | `reconciling` | finalize **observed** `unknown` | same guard | **INSERT 1 attempt (`unknown`)** — appended at observation |
| `reconciling` | `done`/`dead` | reconciliation resolves (D-EV-5) | fenced; **reuses the same `attempt_no`/`send_key`** for the resolve/query path (never mints a new key) | **INSERT 1 attempt** with the resolved outcome (`provider_accepted`/`terminal_failed`/`unknown`); dispatch is floored at the `terminal_unknown` **lifecycle** state when evidence is exhausted — `terminal_unknown` is never an attempt outcome |

**D-EV-3 — The pre-send intent is a marker on the MUTABLE row, committed before bytes leave — never on the immutable attempt.** The `leased→sending` transition is its own short transaction that commits *before* the provider call:

```
UPDATE notification_dispatch
   SET status='sending', attempt_no = attempt_no + 1,
       send_key = deterministic_key(dispatch_id, attempt_no + 1),
       send_started_at = now()
 WHERE dispatch_id=:id AND lease_fence=:fence AND status='leased'
RETURNING attempt_no, send_key;      -- zero rows ⇒ fenced out ⇒ abandon, do not send
```

`send_key` is the deterministic provider idempotency key (Decision 3), stamped here so it is durable and crash-visible *before* the send, and forwarded to the provider where `idempotency-key` is declared. `workflow_instances` never needs a `sending` state because its whole advance is one in-process transaction; `notification_dispatch` does, because the advance is split around a call the kernel cannot hold a transaction across.

**D-EV-4 — The immutable attempt is INSERTed exactly once, at completion, in the SAME transaction as the mutable state advance — fenced.** After the send returns (fresh short txn, provider call already outside any transaction), the fenced UPDATE runs first; only if it returns a row does the INSERT run, so the two are atomic and a fenced-out worker writes nothing:

```
UPDATE notification_dispatch SET status = :next, ...      -- next per D-EV-2
 WHERE dispatch_id=:id AND lease_fence=:fence AND status='sending'
RETURNING attempt_no;                                     -- zero rows ⇒ discard send result entirely
-- only on a returned row, same txn:
INSERT INTO notification_attempt
  (attempt_id, tenant_id, dispatch_id, attempt_no, provider_profile, provider_idempotency_ref,
   started_at, ended_at, classified_outcome, safe_code, provider_message_id)
VALUES (…, :attempt_no, …, :send_key, :send_started_at, now(), :classified_outcome, …);
```

`started_at` is copied from the mutable `send_started_at` and `ended_at` is `now()` — both known at the single INSERT, so no row is ever pre-stamped and later updated. A resumed stale worker whose fence was superseded matches zero rows and its late send cannot insert a competing attempt or overwrite the newer one (**INV-07**). Every content-bearing write (render, recipient snapshot, this attempt INSERT) runs under `tenant_session(tenant_id)` as `bopen_app` on its own connection, resolving placement exactly like a request — the cross-tenant worker role never touches the append-only tables.

**D-EV-5 — Crash recovery reads the MUTABLE state to detect an in-flight send; it never infers from absence and never blind-resends.** A worker that dies between D-EV-3's commit and D-EV-4 leaves the durable signature `status='sending'` with a populated `send_key`/`send_started_at` and **no finalized attempt for that `attempt_no`**. On lease expiry a new claimant (new fence) reads this and transitions `sending→reconciling` rather than resending — the pre-send marker is precisely what distinguishes "send was in flight" from "send never started." The reclaim **preserves the row's `attempt_no` and its stored `send_key`/`provider_idempotency_ref`** (it does not re-enter `leased→sending`, so no new key is minted); the reconcile/resolve path in Decision 6 works from that same stored key. This is distinct from the expired-`leased` reclaim of a **never-sent** row, which is safe to issue as a genuinely fresh attempt (new `attempt_no`, new key). Resolution is evidence-driven (Decision 6).

**D-EV-6 — LATE and CONFLICTING evidence appends; it never mutates history and never regresses the projection.** A provider callback arriving after a terminal state is still verified and the receipt is still INSERTed append-only — evidence is never dropped as a *write*. What is gated is the *projection* onto mutable state:

- `notification_receipt` carries the provider-observed timestamp and an `applied|superseded|conflicting` marker computed at insert against the current projection. A receipt older than the applied one, or one contradicting an already-terminal attempt (e.g. `delivered` after a recorded hard-bounce), is inserted `superseded`/`conflicting` and does **not** advance `notifications.lifecycle_state`.
- The mutable lifecycle projection is **monotonic along the receipt-driven ladder** (`accepted → delivered → …`) and, once terminal, does not move. A late/conflicting receipt adds a history row for operator triage; it rewrites no prior row and regresses no state — a handoff already recorded can never be rewritten as unsent (**INV-11**).
- Replay is idempotent via `notification_callback_event`'s deterministic `dedup_key` (`digest(provider_id ‖ provider_message_id ‖ provider_event_id ‖ payload_signature_digest)`, over stable signature-covered fields — **not** a mutable/nullable `replay_id`), so a redelivered callback — even one whose `replay_id` changed or is null — maps to the same attempt and produces no second receipt or status event (**INV-06**).

*Kernel consistency:* the dispatch↔attempt/receipt split *is* the `workflow_instances`↔`workflow_history` pattern (013/014), the same discipline ContactPoint (019) and Location (020) use; Location's `observe()`→`accept_observation()` candidate rule is mirrored — a provider result is a candidate receipt, appended and classified, never self-promoting the mutable projection.

---

### 5. Refined classifier — the line is *provably-before-effect* vs *not-provably-before-effect*, failing closed to `unknown`

Replace the loose "before bytes / after bytes" wording with a **point-of-no-return** test: was there provable absence of any provider-side effect?

| Provider return | Class | Rationale |
|---|---|---|
| DNS failure, connection refused, TLS/connect timeout — request never written | `retryable_failed` | Provably before-effect; safe to re-send on a **new** attempt. |
| Complete `429`/`503` that provably rejected at admission (validated `Retry-After`, or provider-profile-declared "503 = pre-admission rejection") | `retryable_failed` | Clean "come back later"; no message created. Honor validated `Retry-After` (RFC 9110). |
| Write/read timeout or connection reset **after** request bytes were flushed, before a complete response | `unknown` | Cannot distinguish "never arrived" from "processed, response lost." |
| `500`/`502`/`504` received after the full request was sent | `unknown` | A gateway 502/504 can mean the origin processed and the response was lost. |
| **Generic `503` with no proof of pre-admission rejection**, received after bytes were sent | `unknown` (default) | A 503 from an intermediary *after* the origin accepted cannot be assumed before-effect; only a provider-profile declaration downgrades it. |
| `400`/hard bounce/suppressed | `terminal_failed` | Deterministic non-retryable. |
| Malformed / ambiguous / no-result | `unknown` | Fail closed; refuse to guess a favorable state. |
| `2xx` + provider message id | `provider_accepted` | A **handoff**, never delivery; promoted to `delivered` only by an authenticated receipt. |

**The classifier fails closed toward `unknown`, never toward `retryable`.** `retryable` authorizes an automatic re-send, so it is granted only on *proven* before-effect; every genuine ambiguity is `unknown` and routes to reconciliation, not a resend. This is the single most important change for INV-09: the generic-503 ambiguity the reviewer flagged now resolves to `unknown` by default.

**Ownership (frozen, closes seam 2).** The **worker/queue ADR OWNS the classifier** — it *defines* the closed four-class enum and the dividing line, and is the sole consumer that drives retry/dead-letter/reconciliation. The enum lives in worker-owned domain code and the `notification_attempt.classified_outcome` column constraint. The **provider/channel adapter MAPS ONLY** `vendor_return → exactly one canonical class`; it cannot mint a fifth class and does not re-define the enum. **`terminal_unknown` is NOT a fifth class** — it is a **reconciliation-lifecycle floor state** on the dispatch/reconciliation track, reached only after an `unknown` attempt exhausts idempotency/reconciliation evidence. Both ADRs state this explicitly.

*Invariants:* INV-08 (four distinct closed classes; `provider_accepted` ≠ delivered), INV-09 (only `retryable_failed` auto-requeues).

---

### 6. Retry, reconciliation & dead-letter — no blind resend of `unknown` or expired `send_started`

**Bounded retry (INV-09):** only `retryable_failed` re-queues automatically — exponential backoff with jitter, honoring a *validated* `Retry-After`, capped by both a max-attempts count and a wall-clock message-age ceiling (whichever binds first). Retry is refused if a suppression, cancellation, or terminal outcome exists, checked at claim time under the lease. Exhausting either ceiling routes to dead-letter. A fresh retry increments `attempt_no` → a new `send_key` (Decision 3).

**Expired-lease reclaim of a `send_started` attempt MUST NOT blind-resend (closes cross-ADR finding #1).** A reclaimer that finds `phase='sending'` with an expired lease and an intent marker but no finalized attempt sees a genuinely **`unknown`** send. It follows exactly one proven path, chosen by declared provider capability:

- **`idempotency-key` declared →** a re-send is permitted *because* it reuses the identical stored `send_key`; the provider collapses it to at-most-one effect. This is the **only** path on which a reclaim re-issues bytes. Result written as the attempt's outcome row.
- **`reconciliation-query` declared (no key) →** query the provider by message id/`send_key` to resolve the true outcome and write the outcome row. **No resend.**
- **Neither declared →** after a reconciliation-age ceiling, INSERT one immutable attempt classified **`unknown`** (the honest observed outcome, if one was not already appended at observation) and floor the **dispatch** at the **`terminal_unknown` lifecycle state** (`status='dead'`) — operator-visible, never rewritten to `delivered`/`failed`, never resent by the worker. `terminal_unknown` is a dispatch/reconciliation lifecycle floor, **not** an attempt `classified_outcome`; the attempt row always carries one of the four canonical outcomes (`unknown` here).

An `unknown` attempt is **never** promoted to a fresh `attempt_no` for auto-retry (that is the blind resend INV-09 forbids), and a reconcile/resolve of it **reuses the same `attempt_no` and stored `send_key`** rather than minting a new key. Only `retryable_failed` increments the attempt.

**Dead-letter** is a durable, tenant-scoped state on the dispatch/attempt (not a separate mutable queue) carrying last classified outcome, attempt count, and safe diagnostic. It surfaces via `notification.dead_letter.v1` and supports an **authorized, audited** operator `notification.retry`/`notification.reconcile` — human-initiated, never automatic. Any manual resend that accepts duplicate risk is an authorized, audited operator act, never a worker decision.

*Kernel consistency:* fail-closed on ambiguity, identical to `resolve_context`/placement refusing to guess a favorable state; the candidate-requiring-acceptance discipline — a provider result is evidence, never self-promoting truth.

---

### 7. Fairness & backpressure (concrete SQL, closes INV-14)

All timestamps are the **DB clock** (`now()`), never a worker clock. All scheduler reads ride the content-free worker-role RLS surface (Decision 8): `provider_id`, health, quota counters, and fairness cursors are not message content, so cross-tenant scheduling discloses nothing (INV-01/-04/-13).

**D1 — Provider binding is a dispatch column (see Decision 2)** so the claim can join `notification_provider_health` on `dispatch.provider_id` and filter by breaker state **before** a slot is spent.

**D2 — The fair claim is one concrete LATERAL query: per-tenant inflight cap + least-recently-served interleave + breaker skip.** A control table `notification_fairness (tenant_id PK, last_served_at)` holds the interleave cursor; live inflight is *derived* (counting unexpired leases — single source of truth, no drift):

```sql
-- Short transaction, bopen_notify_claimer role. now() = DB clock.
WITH candidate_tenant AS (
    SELECT d.tenant_id,
           (SELECT count(*) FROM notification_dispatch x
             WHERE x.tenant_id = d.tenant_id
               AND x.status IN ('leased','sending')
               AND x.lease_expires_at >= now())               AS inflight,
           COALESCE(f.last_served_at, 'epoch'::timestamptz)    AS last_served_at
    FROM   notification_dispatch d
    JOIN   notification_provider_health h ON h.provider_id = d.provider_id
    LEFT   JOIN notification_fairness f   ON f.tenant_id   = d.tenant_id
    WHERE  (d.status = 'pending'
            OR (d.status IN ('leased','sending') AND d.lease_expires_at < now()))
      AND  d.available_at <= now()
      AND  h.state = 'closed'
      AND  NOT EXISTS (SELECT 1 FROM notification_quota_suspend s
                        WHERE s.tenant_id = d.tenant_id AND s.active)
    GROUP  BY d.tenant_id, f.last_served_at
),
eligible AS (
    SELECT tenant_id, (:max_inflight_per_tenant - inflight) AS free_slots
    FROM   candidate_tenant
    WHERE  inflight < :max_inflight_per_tenant       -- per-tenant inflight CAP (INV-14)
    ORDER  BY last_served_at ASC                     -- LEAST-RECENTLY-SERVED interleave
    LIMIT  :tenant_fanout
),
claimed AS (
    SELECT c.dispatch_id, c.tenant_id
    FROM   eligible e
    CROSS  JOIN LATERAL (
        SELECT d.dispatch_id, d.tenant_id
        FROM   notification_dispatch d
        JOIN   notification_provider_health h
               ON h.provider_id = d.provider_id AND h.state = 'closed'
        WHERE  d.tenant_id = e.tenant_id
          AND  (d.status = 'pending'
                OR (d.status IN ('leased','sending') AND d.lease_expires_at < now()))
          AND  d.available_at <= now()
        ORDER  BY d.available_at                      -- oldest-due first WITHIN tenant
        FOR UPDATE OF d SKIP LOCKED
        LIMIT  LEAST(e.free_slots, :batch_per_tenant)
    ) c
)
UPDATE notification_dispatch d
SET    status = CASE
                  WHEN d.status = 'sending'                      -- expired-`sending`: a send MAY have gone out
                  THEN 'reconciling'                             --   → route to reconciliation, never blind-resend
                  ELSE 'leased'                                  -- `pending` / expired-`leased`: never sent → fresh attempt
                END,
       lease_owner=:worker,
       lease_expires_at = now() + :ttl,               -- ttl > provider-call timeout + margin
       lease_fence = d.lease_fence + 1
       -- attempt_no and send_key are DELIBERATELY left untouched: an expired-`sending` reclaim
       -- reuses the SAME attempt_no and stored send_key/provider_idempotency_ref (Decisions 3 & 6);
       -- a NEW key is minted only by the leased→sending send-intent of a genuinely new attempt (D-EV-3).
FROM   claimed
WHERE  d.dispatch_id = claimed.dispatch_id
RETURNING d.dispatch_id, d.tenant_id, d.lease_fence, d.status, d.provider_id;
```

Then, in the **same transaction**, sink the just-served tenant to the back of the interleave order:

```sql
INSERT INTO notification_fairness (tenant_id, last_served_at)
SELECT DISTINCT tenant_id, now() FROM claimed
ON CONFLICT (tenant_id) DO UPDATE SET last_served_at = now();
```

The `LATERAL … LIMIT LEAST(free_slots, …)` makes "no tenant exceeds its slot share" a **query-enforced guarantee** — a tenant with 10,000 queued rows still yields at most `free_slots` this pass. `ORDER BY last_served_at ASC` interleaves; `SKIP LOCKED` keeps concurrent workers contention-free; `h.state='closed'` filters open/half-open providers *before* a slot is consumed.

**Slot consumption is serialized per tenant (closes INV-14 claim-race).** The `SELECT count(*) … free_slots` computation is not by itself race-safe: two concurrent claimers can each read the same `inflight`, each derive the same `free_slots`, and each claim up to that many rows — together exceeding `:max_inflight_per_tenant`. So the claim transaction **serializes per-tenant slot consumption**: before computing `free_slots` it takes a `SELECT … FOR UPDATE` row lock on that tenant's `notification_fairness` row (the same row the pass sinks to the back of the interleave), so a second concurrent claimer for the same tenant blocks until the first commits and then re-reads the now-current `inflight`. (An equivalent formulation reserves slots with an atomic `UPDATE notification_fairness SET inflight_reserved = inflight_reserved + :n … WHERE inflight_reserved + :n <= :cap RETURNING` in the same transaction.) Either way, two claimers cannot both spend the same free slots; the per-tenant cap holds under concurrency, not just in the single-claimer read.

> **Build-time verification obligation.** The concurrency correctness of this claim/slot/quota SQL — the per-tenant cap under concurrent claimers, fenced-lease CAS rejection, one-probe breaker fencing, and quota reservation atomicity — is **proven in the tests-first build on live PostgreSQL** (concurrent-claimer / race tests against real transaction isolation), not asserted at the ADR level. This ADR fixes the mechanism; the build supplies the proof.

**D3 — Per-tenant quota is a token bucket RESERVED transactionally at admission, VALIDATED (not re-spent) at claim.** At `notification.request`, reserve one token in the *same transaction* as the outbox insert:

```sql
INSERT INTO notification_quota AS q
       (tenant_id, purpose, window_start, tokens_used, tokens_limit)
VALUES (:tenant, :purpose, date_trunc('minute', now()), 1, :limit)
ON CONFLICT (tenant_id, purpose, window_start) DO UPDATE
   SET tokens_used = q.tokens_used + 1
   WHERE q.tokens_used < q.tokens_limit
RETURNING tokens_used;   -- zero rows ⇒ bucket exhausted ⇒ refuse loudly (distinct retryable quota error)
```

A rolled-back enqueue returns the token — atomic by construction. **At claim, the token is VALIDATED, not spent again** (a message admitted in window *W* may be claimed later; charging twice would double-bill): the claim-time check is the `notification_quota_suspend` emergency-suspension filter already in D2. Admission is the single point of spend; claim re-validates live standing. Quota is an **independent gate** (INV-02) failing on its own `WHERE`, separately from auth/entitlement/suppression.

**D4 — One-probe circuit breaker, fenced exactly like the lease.** Ordinary claims require `state='closed'`. The single probe is a separate, fenced, one-row claim:

```sql
UPDATE notification_provider_health
SET    state='half_open', probe_fence = probe_fence + 1,
       probe_owner = :worker, probe_lease_expires_at = now() + :probe_ttl
WHERE  provider_id = :p AND state='open' AND now() >= half_open_at
RETURNING probe_fence;                              -- zero rows ⇒ someone else probes; stand down
```

The winner leases **exactly one** dispatch for that provider (gated on holding `probe_fence`) and sends it. A fenced CAS closes on success (`state='closed', failure_count=0`) or re-opens on failure (`state='open', half_open_at = now() + :cooldown`), guarded by `probe_fence=:fence`; **zero rows ⇒ a newer probe superseded this one; discard the result, do not mutate.** A stalled probe worker that resumes finds a newer `probe_fence`; its CAS matches nothing and its late result cannot flip the breaker — the same fencing invariant as the send lease, applied to the breaker. At most one probe is ever in flight.

**Backpressure:** admission reads per-tenant queue depth and oldest-message age; crossing a soft threshold returns the same loud retryable refusal. Metrics (queued age, per-tenant fairness, breaker state, quota) surface saturation without sensitive labels (**INV-13**).

*No new external store, no broker, no Redis* — all fairness/quota/breaker state is Postgres control-plane rows under the same backup/migration/RLS coverage.

---

### 8. Worker/callback security plane — principals, roles, narrow RLS, audit identity, revocation (closes INV-01/04)

**The keystone correction: one role was two planes.** The prior draft granted the same elevated role both the cross-tenant *claim/lease* and the public *callback binding-lookup* — two attack surfaces with opposite exposure (a private background loop vs. an unauthenticated internet endpoint). This revision **splits them into two least-privilege principals**, neither of which is `bopen_app`, a superuser, or a table owner.

**Worker claim plane**

- **WQ-SEC-01 — Dedicated claimer DB role `bopen_notify_claimer`,** distinct from `bopen_app`; the *only* role that may run the fair-claim/lease/renew/fence loop. It has **no grant of any kind** on the content tables — structurally incapable of touching a message, recipient, subject, body, or variable.
- **WQ-SEC-02 — Narrow content-free RLS policy, role-scoped, column-restricted.** Under `FORCE ROW LEVEL SECURITY`, `notification_dispatch` carries **two** policies: the ordinary tenant policy `TO bopen_app` (`USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true),'')::uuid)`), and a second `TO bopen_notify_claimer` for `SELECT, UPDATE` with `USING (true)` — cross-tenant *by design*, confined by **column-level GRANTs**: `SELECT (dispatch_id, tenant_id, notification_id, status, available_at, attempt_no, lease_owner, lease_expires_at, lease_fence, next_visible_at, provider_id, provider_profile_version, send_key, send_started_at)` and `UPDATE (status, lease_owner, lease_expires_at, lease_fence, next_visible_at, attempt_no, send_key, send_started_at)`. Every granted column is an id or a scheduling/lease scalar. A fully-compromised claimer sees a work list of opaque `(dispatch_id, tenant_id, notification_id, provider_id)` tuples — never what any of them says or to whom. The claimer additionally gets `SELECT` on `notification_provider_health`/`notification_fairness` and `SELECT, UPDATE` on the content-free quota/suspension control rows.
- **WQ-SEC-03 — Content touches re-enter through `tenant_session` as `bopen_app`; the privileged plane never inherits placement/freeze (closes finding #6).** Claiming resolves a `tenant_id`; it does not confer the right to *act* on that tenant. Every content touch — render, recipient-snapshot resolve, attempt/receipt append — runs on a **separate connection authenticated as `bopen_app`**, entered through `tenant_session(stored_tenant_id)`, where the migrating-freeze (`TenantMigratingError`), placement resolution/verification (`_verify_placement`), and forced RLS live. Because `bopen_notify_claimer` holds zero grants on content tables, a coding error that tried to write content on the claim connection fails on privilege, not on reviewer vigilance. The two connections never share a transaction (nesting refused by `_reject_conflicting_scope`).
- **WQ-SEC-04 — Audit identity for the background actor.** Provision two governed **service principals** (`principals.type='service'`) — `notify-worker` and `notify-callback` — and stamp every attempt/receipt/history/audit row with the service `principal_id` plus the `correlation_id` carried from enqueue. Audit *scope* is decided by the **stored** `tenant_id`, never by any provider/callback body value — the `context_service._deny` fix: scope chosen by whether the value is a real tenant identifier; the raw attempted value stays in metadata as evidence, not routing input.
- **WQ-SEC-05 — Revocation is concrete and fails closed.** (a) `ALTER ROLE bopen_notify_claimer NOLOGIN` halts the claim plane without touching tenant data; (b) suspending the `notify-worker` service principal trips the independent auth gate (INV-02); (c) `DROP POLICY … TO bopen_notify_claimer` removes cross-tenant reach — and because the ordinary tenant policy remains and the claimer's tenant context is empty, the plane degrades to **zero-visibility**, never open-visibility, mirroring `system_session` reading zero rows.

**Inbound callback plane**

- **CB-SEC-01 — Callback ingest is a third, weaker principal `bopen_notify_callback`,** granted only: `SELECT` on the content-free binding-lookup path (`provider_message_id`/`send_key` → `tenant_id` + `attempt_id`), `INSERT` into the append-only callback tables, and `SELECT, UPDATE` on the per-provider callback-rate counter. **No lease/dispatch grant, no content grant** — the internet-facing surface cannot claim work, send, or read a message. The receipt *write* re-enters `tenant_session(stored_tenant_id)` as `bopen_app` after binding.
- **CB-SEC-01b — Forced-RLS, column-confined binding lookup (parity with WQ-SEC-02).** Like the claimer, `bopen_notify_callback` runs under `FORCE ROW LEVEL SECURITY`. Its only read is a narrow, **column-restricted** binding lookup on `notification_attempt` — `SELECT (attempt_id, tenant_id, dispatch_id, provider_profile, provider_idempotency_ref, provider_message_id)` — the id/lookup scalars a binding needs and nothing more (structurally no request fingerprint beyond the lookup handle, and no body/recipient/subject/variable, which live on no table it can touch). A policy `TO bopen_notify_callback FOR SELECT USING (true)` is **cross-provider by necessity** (the unauthenticated endpoint holds no tenant context yet) but confined by column grants to opaque binding tuples: a fully-compromised callback principal learns only that some `(provider_message_id → tenant_id, attempt_id)` binding exists — never what the message says or to whom. `INSERT` is limited to the append-only callback tables (`notification_callback_event`, `notification_callback_quarantine`); `SELECT, UPDATE` is limited to the content-free per-provider callback-rate counter on `notification_provider_health`. It holds **no** grant on `notification_dispatch`, `notifications`, render/recipient tables, or the fairness/quota control rows.
- **CB-SEC-01c — Tenantless-quarantine ownership.** A verified-but-unbound early callback (its send-start row not yet visible — CB-SEC-03) is **owned by the callback principal**: it `INSERT`s the content-free quarantine row under **no** tenant context (the tenant is not yet known), and a bounded re-resolution pass — running as `bopen_notify_callback` for the lookup, then re-entering `tenant_session(stored_tenant_id)` as `bopen_app` once the binding appears — promotes it to a tenant-scoped receipt append or, past the quarantine-age ceiling, to an operator-visible dead record. The quarantine table is content-free precisely so this pre-binding, tenantless custody discloses nothing.
- **CB-SEC-01d — Audit identity for the callback actor (parity with WQ-SEC-04).** Every callback ingest, quarantine, refusal, and resulting receipt is stamped with the governed `notify-callback` service principal (`principals.type='service'`, provisioned alongside `notify-worker` in WQ-SEC-04) plus the `correlation_id` recovered from the bound attempt. Audit *scope* is the **stored** `tenant_id` from the resolved binding — **never** any tenant/account/recipient field in the callback body (the `context_service._deny` rule applied to webhooks); a refusal that resolved no binding files to the tenant-null operational trail (CB-SEC-07), chosen by whether a real binding existed, not by any body value.
- **CB-SEC-01e — Callback-specific revocation, fails closed (parity with WQ-SEC-05).** (a) `ALTER ROLE bopen_notify_callback NOLOGIN` halts inbound ingest alone, without touching the worker plane or tenant data; (b) suspending the `notify-callback` service principal trips the independent auth gate (INV-02); (c) `DROP POLICY … TO bopen_notify_callback` removes the cross-provider binding-lookup reach — and because the callback principal carries no tenant context, the surface degrades to **zero-visibility**, never open-visibility (mirroring `system_session` reading zero rows); (d) per-provider callback revocation is dropping that provider's signing secrets (CB-SEC-06), halting that provider's callbacks alone.

---

### 9. Inbound callbacks — total raw-byte verification, quarantine, replay, rate limit, rotation (closes INV-10)

Provider status callbacks are accepted at a **single unauthenticated-but-verified public endpoint per provider adapter**. A callback's authority derives **only** from a stored provider-message binding — **never** from any tenant/account/recipient field in the body (**AUTH-D1 applied to webhooks**).

- **CB-SEC-02 — Total raw-byte verification order, nothing parsed first,** as a hard gate, each step on raw bytes before the next, JSON parse strictly last:
  0. **size — enforced at the public endpoint by a streaming read limit, BEFORE the `raw_bytes` buffer is constructed.** The endpoint caps the request body as it streams and aborts an oversized body *without allocating the full buffer* (parse-bomb / memory-DoS defense on the unauthenticated endpoint). This gate lives at the endpoint, **not** in the adapter's `verify_callback(raw_bytes, …)`: by the time the adapter holds `raw_bytes` the body is already buffered, so a size check there would be too late to prevent the allocation. `verify_callback` is therefore only ever handed an already-size-bounded buffer.
  1. **content-type** — reject a mistyped body;
  2. **timestamp window** — from a signed header field, range-checked against the DB clock;
  3. **HMAC/signature** — over the exact raw bytes, against the provider's active-or-overlap secret;
  4. **only now parse.**
- **CB-SEC-03 — Early-callback quarantine distinguishes verified-but-early from forged.** A callback that passes verification but whose `provider_message_id` matches no stored binding (send-start row not yet visible) is written append-only to `notification_callback_quarantine` (content-free) and re-resolved by a bounded pass once the attempt commits. **Signature is verified before quarantine** — forged bytes never enter it. Because `send_key` is derived before send, the binding key exists pre-send, so the quarantine window is only the commit-visibility race. After a bounded quarantine-age ceiling with no match, the entry becomes an operator-visible dead record — never a receipt, never a state change. This names the reviewer's finding-#4 seam: raw edge input → verified observation → *quarantine if unbound* → stored-binding lookup → tenant-scoped receipt append → lifecycle projection.
- **CB-SEC-04 — Replay uniqueness (independent of a nullable replay ID) and order-insensitive convergence.** Every accepted callback is recorded append-only under `notification_callback_event`'s **deterministic `dedup_key`** — `digest(provider_id ‖ provider_message_id ‖ provider_event_id ‖ payload_signature_digest)`, derived from stable, signature-covered fields — with `UNIQUE (provider_id, provider_message_id, dedup_key)`. The key **does not depend on a mutable/nullable provider `replay_id`**: a redelivered event whose `replay_id` is changed or null still yields the same `dedup_key`, so it collides and is a no-op (INV-06/-12). `replay_id`, when present, is stored as evidence only. Transport status is a lattice, not a stream — the receipt *projection* advances only monotonically along the ladder using the provider-observed timestamp; a stale or already-terminal transition is still stored append-only but does not rewrite projected state (a late `delayed` cannot un-do a `delivered`). Convergence is independent of arrival order and needs no trust in provider sequencing.
- **CB-SEC-05 — Per-provider rate limit, keyed only on provider.** A per-provider token bucket is evaluated **before** binding lookup, keyed **only** on `provider_id` — the endpoint must never resolve a tenant or message to decide whether to throttle. A flood at provider A's endpoint cannot starve provider B's ingest.
- **CB-SEC-06 — Secret rotation with bounded, auditable overlap.** Each provider holds at most two active signing secrets (`current` + `previous`, the `previous` carrying an explicit `not_after`). Verification tries `current` then `previous`; a body verifying only under an expired `previous` is refused. Overlap is bounded and recorded append-only. Secrets are runtime config behind the adapter facade — never a tenant row, never an event field (INV-13). Per-provider revocation is dropping that provider's secrets.
- **CB-SEC-07 — One uniform, tenant-safe refusal across the entire surface (the non-oracle).** Every rejection — oversize, mistyped, stale, bad signature, unknown/early/wrong-provider/wrong-message binding, replay, over-rate, invalid transition — returns **one identical response** (same status, body, shape, and constant-work past the size/type gate so timing does not separate "message exists" from "does not"). The rejection is filed to audit under the **stored** `tenant_id` only when a binding actually resolved; otherwise to a tenant-null operational trail chosen by whether a real binding existed — **never by any body field** (the `context_service._deny` scope rule applied to webhooks). No response, timing, or audit-routing difference discloses whether a message, recipient, Principal, or Party exists (**INV-04/-01**).

**Callback ownership handoff (closes finding #4):** the **callback plane (`bopen_notify_callback`)** owns verify → quarantine-if-unbound → binding lookup; the **content plane (`bopen_app` via `tenant_session`)** owns the tenant-scoped receipt append and lifecycle projection. The provider ADR's adapter `verify_callback` is the *verification contract* (crypto + vendor→canonical normalization on raw bytes); this ADR fixes *which principal executes it and against which grants*. Neither ADR re-decides the other.

---

### 10. Freeze the cross-ADR seams so worker and adapter cannot diverge

- **Seam 1 (expired-lease resend):** made one decision, not two — the worker owns the send-start protocol, fence, `phase` machine, and reclaim rule (Decisions 3, 4, 6); a reclaim resend is permitted **only** by Decision 6's capability-gated path. The adapter never retries internally — it maps one send to one classified response and returns.
- **Seam 2 (classifier):** one owner (worker), one closed four-class vocabulary, adapter maps only, `terminal_unknown` demoted to a lifecycle floor state (Decision 5).
- **Seam 3 (provider routing):** the dispatch row carries `provider_id`/`provider_profile_version`, resolved at enqueue (Decision 2), so "skip open-provider work" is expressible (Decision 7-D1).
- **Seam 4 (callback ownership):** verify/normalize = adapter; binding lookup + tenant-scoped append + projection = worker (Decision 9).
- **Recipient/render seam (finding #5 + finding #8 — frozen):** recipient resolution and all staleness/cross-tenant/verification/purpose/channel validation are performed by the **worker orchestrator** via `ContactPointRepository.resolve()` inside `tenant_session(tenant_id)` — *not* the adapter, which holds no `tenant_id` and no connection and performs **no recipient validation**. Two lifetimes are frozen here so worker and adapter cannot diverge on them:
  - **Rendered-content transfer/dereference.** The orchestrator renders the template-version output under `tenant_session` and hands the adapter an **integrity-bound `rendered_content_ref`** (an opaque handle) — **not** inline bytes carried through domain state. The reference is **dereferenced to transport bytes at send time, within the same attempt's handoff**, for transport only; raw body and template variables never flow through adapter logs or domain fields. The reference is valid only for that attempt's handoff window; a reference that cannot be dereferenced within the attempt is a fail-closed refusal, never a stale or partial send.
  - **`RecipientSnapshot` lifetime/validity.** The snapshot is **resolved at the start of each attempt** under `tenant_session`, is valid **only within a bounded resolve→handoff freshness ceiling**, and is **never carried across a retry**. Every genuinely new attempt (including a reclaim that issues a fresh attempt) **re-resolves** it; a snapshot older than the ceiling at handoff is **re-resolved before send, never trusted indefinitely**. A stale, superseded, or unresolvable snapshot fails closed at the orchestrator *before any byte leaves* — the adapter is never handed an expired snapshot to reason about, because it structurally cannot.

*Kernel consistency:* single-owner-per-concern, the same discipline that keeps `tenant_session` the sole authority for tenant scope and forbids a second, divergent path.

---

## Invariants defended

- **NOTIFY-INV-06 (idempotency):** `UNIQUE(tenant_id, idempotency_key)` on enqueue; deterministic per-attempt `send_key`; append-only callback replay key.
- **NOTIFY-INV-07 (split, now defended):** fencing bounds concurrent *claims* (monotonic `lease_fence`, DB clock, fenced CAS); the deterministic pre-recorded `send_key` bounds duplicate *external sends*. A resumed stale worker's write matches nothing and its late send collapses at the provider.
- **NOTIFY-INV-08 (outcome truth):** closed four-class classifier on provably-before-effect vs not; `provider_accepted` ≠ delivered; dispatch status ≠ delivery truth.
- **NOTIFY-INV-09 (bounded, no blind retry):** only `retryable_failed` re-queues; generic 503 defaults to `unknown`; expired-lease `send_started` reclaim never blind-resends; `unknown` reconciled or floored at `terminal_unknown`.
- **NOTIFY-INV-11 (late-evidence truth):** late/conflicting receipts append without rewriting history or regressing the monotonic projection.
- **NOTIFY-INV-12 (append-only evidence):** mutable `notification_dispatch` current-state row + separate once-written `notification_attempt`/`_receipt` history (013/014 pattern), SELECT+INSERT-only, `ON DELETE RESTRICT` — no dual-purpose row; the migration-014 cascade-erasure trap closed.
- **NOTIFY-INV-14 (no starvation):** query-enforced per-tenant inflight cap + least-recently-served interleave (D2); transactionally-reserved quota with loud refusal + independent gate (D3); provider-binding breaker skip (D1) + single fenced probe (D4).
- **NOTIFY-INV-01/-04 (isolation / non-disclosure):** the only cross-tenant surface (`bopen_notify_claimer`, `USING(true)`) is confined by column grants to content-free ids/control scalars; all content re-scopes through `tenant_session` + forced RLS as `bopen_app`; the callback principal reads no content; every callback refusal is a single non-oracle response with body-independent audit routing.
- **NOTIFY-INV-10 (callback integrity):** total raw-byte order size→type→timestamp→HMAC→parse; early-callback quarantine; replay uniqueness + order-insensitive projection; per-provider rate limit; bounded-overlap rotation.
- **NOTIFY-INV-02 (independent gates):** quota INSERT fails on its own `WHERE`; service-principal suspension fails auth independently of role/policy/rate.
- **NOTIFY-INV-13/-16 (safe metrics / migration freeze + forced RLS):** unlabeled saturation metrics; every background content touch honors the migrating freeze and forced-RLS floor via `tenant_session`.

---

## Alternatives considered and rejected

- **`FOR UPDATE SKIP LOCKED` alone / advisory locks / pure lease-poll:** the row lock releases at commit *before* the send; advisory locks are RLS-invisible, connection-fragile, unauditable; pure poll thunders. The **hybrid `SKIP LOCKED` claim + durable fenced lease + deterministic send-key** is the only option correct across the open send window *and* the external duplicate-send boundary.
- **Fencing a DB row as the INV-07 mechanism for sends** — rejected: it cannot prevent a duplicate external send (the reviewer's finding). Fencing governs claims; the key governs sends.
- **One `notification_attempt` row serving as both pre-send marker and finalized evidence** — rejected: destroys the append-only guarantee (INV-12). The marker lives on the mutable dispatch row; the attempt is written once at finalization.
- **Blind-resending `unknown` to force at-least-once on a no-key provider** — rejected as the exact INV-09 violation the reviewer identified; `terminal_unknown` is the honest floor.
- **Treat timeout as `failed` and retry** (silently duplicates) / **as `delivered`** (fabricates delivery, breaks INV-08) — both rejected.
- **One elevated role for both claim and callback binding-lookup** — rejected: collapses two opposite exposure surfaces; split into `bopen_notify_claimer` and `bopen_notify_callback`.
- **Trusting a callback tenant field to route/scope** — the AUTH-D1 violation. **Shared authenticated callback endpoint across providers** — verification is provider-specific. **Content-hash idempotency** — collapses distinct sends, fails pre-render fencing.
- **Separate `notification_dispatch_lease` table:** rejected in favor of lease columns on the dispatch row, keeping claim/fence/`send_key`/visibility in one atomic update.
- **Overloading `usage_outbox`** — metering-shaped, no lease, no attempt history; couples dispatch to metering (NOTIFY-D-10).
- **External token bucket / broker (Redis, SQS):** breaks outbox atomicity, adds a store outside RLS/backup/migration coverage, contradicts the Postgres-only and greenfield-caution constraints.
- **Global FIFO claim / one worker per tenant / LISTEN-NOTIFY-only dispatch:** starvation; non-scaling; no durable lease/fairness/backpressure surface.
- **Tenant-controlled outbound webhook destinations (egress):** an SSRF/DNS-rebinding/redirect vector — a separate, larger trust boundary; deferred.

---

## Consequences

- **New operational actors exist.** The kernel gains its first long-lived background process, its first elevated (and now *split*) worker/system roles, its first governed service principals, and its first unauthenticated public endpoint. Each is a new attack/failure surface requiring its own monitoring.
- **Two least-privilege DB roles + two service principals** must be provisioned and governed; revocation levers (NOLOGIN, principal suspend, policy drop) are runbook items.
- **Ops runbook needs:** worker liveness/heartbeat and lease-expiry reclaim; crash-in-flight `sending→reconciling` recovery; dead-letter drain and the audited operator `notification.retry`/`notification.reconcile` flows; circuit-breaker/probe inspection and manual open/close; quota/backpressure alerting on queued age and per-tenant fairness; per-provider callback-rate and quarantine-age monitoring; provider-secret rotation with bounded overlap; `terminal_unknown` triage.
- **Placement fan-out.** For dedicated-DB tenants the dispatch tables live in each placement DB; control tables and the worker fan out per placement, and both the claimer and callback roles must be provisioned in each placement DB. The privileged claim plane re-enters `tenant_session` for every content touch, so placement/freeze correctness is re-derived per write, never inherited. Whether the claimer/callback roles are per-placement in the dedicated-DB topology ties to the unresolved queue-topology decision.
- **Test-matrix implications:** lease steal/fence CAS rejection under concurrency; crash-mid-send → `sending`-marker recovery and no blind resend; deterministic-key reuse collapses duplicate sends; generic-503 → `unknown`; classifier table per class; append-only INSERT-once + `ON DELETE RESTRICT` cascade-erasure resistance; fairness under a heavy-tenant + open-provider load with query-enforced cap; quota loud-refusal + rollback-returns-token; one-probe breaker fencing; callback size→type→timestamp→HMAC→parse order, quarantine, replay uniqueness, per-provider rate limit, uniform non-oracle refusal + body-independent audit routing; column-grant confinement of `bopen_notify_claimer`; forced-RLS on every background content touch; cross-inventory coverage (`TENANT_SCOPED_TABLES` ∩ `COPY_ORDER`) for all tenant-owned tables.

---

## Explicitly deferred

- **Production provider selection** and per-provider classifier/idempotency/reconciliation capability tables (NOTIFY-D-07); where a provider offers neither idempotency key nor reconciliation query, `terminal_unknown` is the correct floor — **exactly-once is not claimed** (at-least-once effort with honest ambiguity).
- **Outbound webhook / egress delivery** — separate trust boundary (SSRF/allow-listing/signing/response-limits), its own ADR.
- **Tenant BYO provider and provider failover** (RESEARCH §12) — multiplies breaker cardinality; must revisit fairness.
- **Scheduling refinements:** weighted WFQ / per-tenant priority, purpose-tier shedding, adaptive quota autotuning, global send ceilings, multi-worker breaker consensus.
- **Push wakeup (LISTEN/NOTIFY)** — polling accepted for now; latency deferred.
- **Concrete constants** — backoff, max-attempt/age ceilings, lease TTL, probe TTL, quota windows, callback size cap, timestamp window, rate-bucket rates, rotation-overlap duration, quarantine-age ceiling — deferred to adapter/runbook ADRs.
- **Dedicated-DB queue topology** (shared control plane vs. per-placement), placement enumeration, callbacks during cutover, and global-vs-per-placement health state — resolve before any build.
- **Cross-provider callback-endpoint DDoS posture** beyond per-provider rate limiting.

Each deferred item requires its **own** decision record; none is authorized here.

---

## Clean-room note

Designed independently from standards/patterns as requirements sources (AGENTS.md §6). No upstream or third-party queue/worker code was copied; table shapes, the claim/fence semantics, the mutable-current-state + separate-append-only-history split, the deterministic send-key, the classifier, the role/principal split, and callback verification were derived from the kernel's own forced-RLS, role-scoped-policy, composite-FK `ON DELETE RESTRICT`, append-only, and `tenant_session`/placement patterns, plus the RESEARCH invariants and the REVIEW findings. Files consulted for grounding: `docs/01-product/MILE-4.2-notification-foundation-research.md`, `docs/01-product/MILE-4.2-notification-foundation-review.md`, `docs/01-product/MILE-4.2-notification-ADR-codex-review.md`, `infrastructure/database/002_phase3_entitlement_metering.sql`, `infrastructure/database/013_*` + `014_workflow_history_survives_its_instance.sql` (mutable current-state + append-only history, `ON DELETE RESTRICT`), `infrastructure/database/019_*`/`020_*` (ContactPoint/Location), `services/platform-kernel/python/platform_kernel/db.py` (`tenant_session`, `_verify_placement`, migrating freeze, `_reject_conflicting_scope`), `services/platform-kernel/python/platform_kernel/workflow_repositories.py` (`apply_transition`), `services/platform-kernel/python/platform_kernel/contact_point_repositories.py` (`RecipientSnapshot`, `resolve()`), `tools/migrate_tenant_to_dedicated.py` (COPY_ORDER), `tests/isolation/test_rls_database_behavior.py` (TENANT_SCOPED_TABLES). (This ADR does not cite an "AGENTS.md §11 facade pattern"; the facade discipline derives from the kernel's own owned-boundary/`bst_*` wrapper pattern and the clean-room independence rule, AGENTS.md §6.)

---

## Authority block

```yaml
adr: notification-worker-queue-operational-model
document_id: ADR-NOTIFY-WQ
version: 2.1.0-draft
status: DRAFT / PROPOSED
gated_by: DEC-P4-ENTRY §9
truth_status: partially_supported
authority_status: advisory_only
implementation_status: candidate
risk_class: high
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
self_certification:
  agent_id: claude-motor
  peer_agent_id: codex-reviewer
  certification_scope: advisory_only
  execution_authority: false
  approval_authority: false
  ready_for_operator_review: false   # independent re-review 2026-08-06: STILL NEEDS REVISION
```

> This ADR recommends an architecture only. It authorizes nothing and builds nothing. Email is the **proposed first implementation scope**; the specified test adapter is a deterministic fake — no ADR here authorizes a channel, an adapter, a build, a provider activation, or a production activation. A build requires a separate operator authorization recorded first; Notification remains gated by DEC-P4-ENTRY §9. Verification, disposition, deployment, provider activation, and production activation remain distinct later operator acts.
