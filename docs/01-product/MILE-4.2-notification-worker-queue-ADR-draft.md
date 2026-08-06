# ADR — Notification worker/queue operational model

**STATUS: DRAFT / PROPOSED — NOT AUTHORIZED, NOT IN FORCE. Notification remains gated by DEC-P4-ENTRY §9. This ADR authorizes nothing and builds nothing; a build needs a separate operator authorization recorded first.**

---

## Context

The platform kernel today is entirely request-driven and synchronous: FastAPI + PostgreSQL 17 forced-RLS + psycopg3, with every write scoped by `tenant_session(tenant_id)` and placement resolved per request (`_connect_for_tenant`). There is **no worker, no lease, no queue, no async dispatch, and no background actor identity anywhere in the kernel.** The existing outbox (`002_*` `usage_outbox`) is metering-shaped (`capability_id`/`quantity`/`unit`) with no lease and no attempt history; the audit/lifecycle trail is append-only history, not a claimable work queue.

Per REVIEW-MILE-4.2-NOTIFICATION, the Notification worker/queue is therefore the kernel's **single biggest new operational surface** — greenfield, introducing for the first time (a) a long-lived process that holds no request context, (b) a leased hand-off to an external provider across a network boundary, and (c) an inbound callback endpoint with no session. Because the kernel forbids holding a tenant DB transaction open across the provider call (RESEARCH §9.1), correctness cannot come from row locks alone; it must come from durable, fenced, tenant-scoped state.

This ADR reconciles five design dimensions — worker execution & lease/fencing, retry/dead-letter/outcome-truth, tenant fairness & backpressure, dispatch tables & transactional outbox, and inbound callbacks/idempotency/egress — into one coherent operational model. It remains **advisory**: Notification is gated, and nothing here is authorized to run.

---

## Decision

Adopt a **Postgres-only transactional-outbox worker** — no Redis, broker, or external scheduler — built on a purpose-built `notification_*` table set, with a durable fenced lease, an append-only attempt/receipt evidence trail, and in-database fairness and backpressure. Five decisions form one model:

### 1. Tables (the substrate)

A purpose-built `notification_*` set, each tenant-scoped with **forced RLS, tenant-inclusive composite FKs, and `ON DELETE RESTRICT` on the append-only tables**. Four core tables plus two control-plane health tables:

| Table | Shape | Role |
|---|---|---|
| `notifications` | mutable state row | Orchestration record: `id`, `tenant_id`, `purpose`, `channel`, template-version ref, recipient-snapshot ref, `lifecycle_state`, `revision`, `correlation_id`, `idempotency_key` with **`UNIQUE (tenant_id, idempotency_key)`**. |
| `notification_dispatch` | mutable / claimable | The outbox work-queue row: `dispatch_id`, `tenant_id`, composite FK `(tenant_id, notification_id)`, `status` (pending/leased/done/dead), `available_at` (backoff gate), `attempt_count`, **`lease_owner`, `lease_expires_at`, `lease_fence BIGINT`**, `next_visible_at`, `dead_lettered_at`. **Content-free** — ids and control columns only. |
| `notification_attempt` | append-only (SELECT+INSERT only) | Evidence: `attempt_id`, `tenant_id`, composite FK `… ON DELETE RESTRICT`, `attempt_no`, provider profile, request fingerprint, **provider idempotency ref**, `started_at`/`ended_at`, **classified outcome** (accepted/retryable/terminal/**unknown**), safe code, `next_retry_at`. |
| `notification_receipt` | append-only, same policy | Provider-observed truth: provider event id, provider-observed time, normalized transport status, raw-payload integrity ref. |
| `notification_quota` | control-plane | Token-bucket admission: `(tenant_id, purpose, window_start, count)`. |
| `notification_provider_health` | control-plane | Circuit breaker: `(provider_id, state, failure_count, opened_at, half_open_at)`. |

All tenant-owned tables register in **both** `TENANT_SCOPED_TABLES` (RLS classification) and the trial→paid `COPY_ORDER`, parents before children (`notifications` before `notification_dispatch`/`_attempt`/`_receipt`) — the cross-inventory coverage test fails loud on any unmapped tenant-scoped table.

**Reconciliation note (lease location).** The lease lives as **columns on `notification_dispatch`**, not as a separate `notification_dispatch_lease` table. This keeps the claim, the fence, and the visibility gate in one atomically-updated row (the majority design across the worker-execution and outbox dimensions); the separate-lease-table variant is recorded as a rejected alternative. The dispatch row is tenant-scoped **and** carries an additional worker-role RLS policy (below); it is not a content-free control-plane table divorced from RLS — it is a tenant-scoped table whose content-free columns are additionally visible to one elevated role.

### 2. Enqueue (transactional outbox)

Inside a single `tenant_session` transaction the caller inserts the `notifications` row **plus** a `notification_dispatch` row (`status='pending'`) and commits — **atomic with any business write sharing that transaction**, so an enqueue can never be lost or leaked relative to its cause. A retried `notification.request` collides on `UNIQUE(tenant_id, idempotency_key)` and returns the existing notification/dispatch instead of enqueuing a second one (**NOTIFY-INV-06**).

### 3. Claim / lease / fence (worker execution)

A dedicated **worker/system role** — not `tenant_session` (whose empty tenant reads zero rows under the standard policy), and not session-scoped advisory locks (invisible to RLS, lost on disconnect, unauditable) — runs the claim under an explicit, narrow worker RLS policy (`USING(true)`, SELECT/UPDATE only) confined to the content-free columns of `notification_dispatch` and the provider-id lookup path. This is the only cross-tenant surface, and it discloses no message content (RESEARCH §10.1 "worker claims" zero-disclosure surface).

- **Claim (short txn):** `SELECT … WHERE status='pending' OR (status='leased' AND lease_expires_at < now()) … FOR UPDATE SKIP LOCKED LIMIT n`, then `UPDATE … SET status='leased', lease_owner=:worker, lease_expires_at = now() + :ttl, lease_fence = lease_fence + 1`. `now()` is the **DB clock** (no worker-clock skew); `ttl` must exceed provider-call timeout + margin. `SKIP LOCKED` gives contention-free claiming (no thundering herd); the lease gives correctness across the open send window that the row lock — released at commit, *before* the send — cannot.
- **Commit the claim, close the transaction, then call the provider outside any DB transaction** (RESEARCH §9.1). No tenant transaction is ever held open across the network call.
- **Renew (heartbeat)** for long sends: `UPDATE … SET lease_expires_at = now()+:ttl WHERE dispatch_id=:id AND lease_fence=:fence`. Zero rows ⇒ lease stolen ⇒ abandon.
- **Release / result (fenced CAS, fresh short txn after the send):** append a `notification_attempt` row and advance state guarded by `… WHERE dispatch_id=:id AND lease_fence=:fence AND status='leased'`. **Zero rows = fenced out: discard the send result, do not retry.** A crashed/paused worker that resumes past expiry finds a newer claim has incremented `lease_fence`; its stale CAS matches nothing and its late send cannot overwrite the newer attempt.

Every **content touch** — render, recipient snapshot, attempt-result write — runs in a separate connection under `tenant_session(tenant_id)`, resolving placement exactly like a request. Nesting stays forbidden; the two contexts never share a connection.

### 4. Outcome truth, retry & dead-letter

The **classified outcome of an attempt — not the notification row — is the source of truth.** `sending` is stamped *before* the provider call leaves the process, so a crash mid-call is recoverable as `unknown`, never silently retried.

A response classifier (**NOTIFY-INV-08**) maps each provider return into exactly one class, on the dividing line of *send-attempted vs. send-not-attempted*:

- `provider_accepted` — 2xx with provider message id: a **handoff, not human delivery**. Never promoted to `delivered` without an authenticated receipt (RESEARCH §7.5); the `accepted→delivered` ladder is receipt-driven only.
- `retryable_failed` — 429/503/connection-refused/DNS, *before* bytes plausibly sent.
- `terminal_failed` — 400/hard-bounce/suppressed.
- `unknown` — timeout/reset/5xx *after* request bytes were written.

**Bounded retry (NOTIFY-INV-09):** only `retryable_failed` re-queues automatically — exponential backoff with jitter, honoring a *validated* `Retry-After` (RFC 9110), capped by both a max-attempts count and a wall-clock message-age ceiling (whichever binds first). Retry is refused if a suppression, cancellation, or terminal outcome exists, checked at claim time under the lease. Exhausting either ceiling routes to `dead_letter`.

**Blind retry is forbidden for `unknown`.** An `unknown` attempt is never auto-re-sent. It enters a reconciliation loop resolved by *evidence, not assumption*: (a) a provider idempotency key — recorded on the attempt **before** send, derived deterministically from the attempt id — lets a safe re-send collapse to the same provider message; or (b) a receipt/query lookup resolves the real outcome. Absent both, after a reconciliation-age ceiling it becomes `terminal_unknown` — an honest, operator-visible dead-end, never rewritten to `delivered` or `failed`.

**Dead-letter** is a durable, tenant-scoped flag (a state on the dispatch/attempt, not a separate mutable queue) carrying last classified outcome, attempt count, and safe diagnostic. It surfaces via `notification.dead_letter.v1` and supports an **authorized, audited** operator `notification.retry` / `notification.reconcile` — human-initiated, never automatic.

### 5. Fairness & backpressure (in Postgres)

Three cooperating mechanisms over the same tables defend **NOTIFY-INV-14** against a heavy tenant or a sick provider starving everyone:

- **Fair claim** — the claim `SELECT … FOR UPDATE SKIP LOCKED` is *fairness-shaped*, not global-FIFO: a `LATERAL` per candidate tenant caps claimable rows at `max_inflight_per_tenant`, ordered `available_at` within tenant and interleaved across tenants least-recently-served-first. A heavy tenant's backlog can never exceed its slot share.
- **Per-tenant quota (NOTIFY-INV-02, -14)** — `notification_quota` token bucket, evaluated at admission (`notification.request`) and re-checked at claim, as an **independent gate** failing separately from auth/entitlement/suppression. Excess is refused *loudly* with a distinct retryable quota error — never silently dropped, never queued unbounded. Emergency suspension is a separate flag, never conflated with ordinary quota.
- **Per-provider circuit breaker (NOTIFY-INV-14, -16)** — `notification_provider_health` closed/open/half-open. On trip, the fair-claim query **skips** messages bound to the open provider, so an outage on provider A cannot consume worker slots destined for healthy provider B; those messages simply age (age is metered). After cooldown, exactly one half-open probe lease issues; success closes, failure re-opens.

Backpressure: admission reads per-tenant queue depth and oldest-message age; crossing a soft threshold returns the same loud retryable refusal. Metrics (queued age, per-tenant fairness, breaker state, quota) surface saturation without sensitive labels (**NOTIFY-INV-13**).

### 6. Inbound callbacks & send idempotency

Provider status callbacks are accepted at a **single unauthenticated-but-verified public endpoint per provider adapter**. A callback's authority derives **only** from a stored provider-message binding — **never** from any tenant/account/recipient field in the callback body (**AUTH-D1 applied to webhooks**).

- Verification runs on **raw bytes, before parse**: HMAC/signature against the active (or bounded-overlap rotated) provider secret, timestamp window, and payload-size/content-type limits (**NOTIFY-INV-10**).
- Only then is `provider_message_id` extracted and looked up — under the **elevated worker/system role** (the same role that claims; not `tenant_session`, which forbids an empty tenant) — against the stored `notification_attempt` row, which is the **sole source of `tenant_id`** and attempt context.
- The normalized receipt write then opens `tenant_session(stored_tenant_id)` so forced RLS scopes it correctly. A `tenant_id` in the callback body is inert — it never selects the session variable isolation depends on ("a header cannot create authority").
- Unknown ids, wrong-provider/wrong-message binding, and invalid lifecycle transitions are refused **identically and tenant-safely**, with no body/status/timing difference disclosing whether a message or recipient exists (**NOTIFY-INV-04, -01**).
- **Dedup/replay:** `(provider, provider_message_id, provider_event_id)` plus replay id are recorded append-only, so a redelivered callback maps to the same attempt and produces no second status event or receipt (**NOTIFY-INV-06, -12**). Stale-timestamp and already-terminal transitions are dropped, not applied.

**Send idempotency** is caller/event-scoped via `UNIQUE(tenant_id, idempotency_key)` — **not** content-hashed (which wrongly collapses two legitimately-distinct sends and fails to fence a pre-render retry). Where the provider supports its own key, the adapter forwards the deterministic attempt-derived value so a provider-side retry across a post-send timeout also de-dupes.

---

## Invariants defended

- **NOTIFY-INV-06 (idempotency):** `UNIQUE(tenant_id, idempotency_key)` on enqueue; append-only callback replay keys on inbound.
- **NOTIFY-INV-07 (no concurrent/expired-lease or stale-revision dispatch):** durable lease + **monotonic `lease_fence`** on DB clock; fenced CAS on renew and result; a resumed stale worker's write matches nothing.
- **NOTIFY-INV-08 (outcome truth):** classifier separates accepted/retryable/terminal/**unknown** on send-attempted vs. not; `accepted` never auto-promoted to `delivered` without a receipt; dispatch status ≠ delivery truth.
- **NOTIFY-INV-09 (bounded retry, no blind retry):** only `retryable_failed` re-queues, double-ceiling capped; `unknown` never auto-re-sent, resolved by idempotency/reconciliation or floored at `terminal_unknown`.
- **NOTIFY-INV-14 (no starvation):** fairness-shaped claim + per-tenant quota + per-provider breaker.
- **NOTIFY-INV-01/-04 (isolation / non-disclosure):** forced RLS on all tenant-owned reads/writes including the background actor; uniform tenant-safe callback refusals.
- **NOTIFY-INV-10 (callback integrity):** signature + timestamp + size checks on raw bytes before parse.
- **NOTIFY-INV-12 (append-only evidence):** `notification_attempt`/`_receipt` are INSERT+SELECT only, `ON DELETE RESTRICT` — closing the migration-014 cascade-erasure trap.
- **NOTIFY-INV-02 (independent gates):** quota fails separately from auth/entitlement/suppression.
- **NOTIFY-INV-13/-16 (safe metrics / migration freeze + forced RLS):** unlabeled saturation metrics; design honors the migrating freeze and forced-RLS floor.

---

## Alternatives considered and rejected

- **`FOR UPDATE SKIP LOCKED` alone / advisory locks / pure lease-poll:** the row lock releases at commit *before* the send (protects the claim, not the in-flight attempt); advisory locks are RLS-invisible, connection-fragile, unauditable; pure poll thunders on hot rows. The **hybrid `SKIP LOCKED` claim + durable fenced lease** is the only option correct across the open send window.
- **Separate `notification_dispatch_lease` table:** rejected in favor of lease **columns on the dispatch row**, keeping claim/fence/visibility in one atomic update. (Recorded so the alternative is traceable.)
- **Treat timeout as `failed` and retry** — silently duplicates real sends. **Treat timeout as `delivered`** — fabricates human delivery, breaks INV-08. **Mutate one attempt row across retries** — destroys append-only evidence (INV-12).
- **Overloading `usage_outbox`** — metering-shaped, no lease, no attempt history; couples dispatch to metering (NOTIFY-D-10). **A single status-column table as both queue and evidence** — a row cannot be both mutable-claimable and append-only; hence the dispatch/attempt split.
- **External token bucket / broker (Redis, SQS):** breaks outbox atomicity, adds a store outside RLS/backup/migration coverage, contradicts the Postgres-only and greenfield-caution constraints.
- **Global FIFO claim / one worker per tenant / LISTEN-NOTIFY-only dispatch:** starvation; non-scaling; no durable lease, fairness, or backpressure surface, respectively.
- **Trusting a callback tenant field to route/scope** — the AUTH-D1 violation. **A shared authenticated callback endpoint across providers** — verification is provider-specific. **Content-hash idempotency** — collapses distinct sends, fails pre-render fencing.
- **Tenant-controlled outbound webhook destinations (egress):** an SSRF/DNS-rebinding/redirect vector — a separate, larger trust boundary; deferred.

---

## Consequences

- **A new operational actor exists.** The kernel gains its first long-lived background process, its first elevated worker/system role, and its first unauthenticated public endpoint. Each is a new attack/failure surface requiring its own monitoring.
- **Ops runbook needs:** worker liveness/heartbeat and lease-expiry reclaim; dead-letter drain and the audited operator `notification.retry`/`notification.reconcile` flows; circuit-breaker state inspection and manual open/close; quota/backpressure alerting on queued age and per-tenant fairness; provider-secret rotation with bounded overlap; `terminal_unknown` triage.
- **Placement fan-out.** For dedicated-DB tenants the dispatch tables live in each placement DB (control tables and worker fan out per placement); the shared-control-plane-only variant and per-database-queue variant are both recorded as deferred topology decisions to resolve before build.
- **Test-matrix implications:** lease steal/fence CAS rejection under concurrency; crash-mid-send → `unknown` recovery; no-blind-retry of `unknown`; classifier table per class; fairness under a heavy-tenant + open-provider load; quota loud-refusal path; callback signature/timestamp/replay/wrong-binding uniform refusal (no oracle); cross-inventory coverage (`TENANT_SCOPED_TABLES` ∩ `COPY_ORDER`) for all four core tables; forced-RLS on every background content touch.

---

## Explicitly deferred

- **Production provider selection** and per-provider classifier/idempotency/reconciliation capability tables (open decision **NOTIFY-D-07**); where a provider offers neither idempotency key nor reconciliation query, `terminal_unknown` is the correct floor — **exactly-once is not claimed** (at-least-once with honest ambiguity).
- **Outbound webhook / egress delivery** — separate trust boundary (SSRF/allow-listing/signing/response-limits), its own ADR.
- **Tenant BYO provider and provider failover** (RESEARCH §12) — multiplies breaker cardinality; must revisit fairness.
- **Scheduling refinements:** weighted WFQ / per-tenant priority, purpose-tier shedding, adaptive quota autotuning, global send ceilings, multi-worker breaker consensus.
- **Push wakeup (LISTEN/NOTIFY)** — polling accepted for now; latency deferred.
- **Concrete constants** — backoff, max-attempt/age ceilings, lease TTL, quota windows — deferred to adapter/runbook ADRs.
- **Dedicated-DB queue topology** (shared control plane vs. per-placement) — resolve before any build.

Each deferred item requires its **own** decision record; none is authorized here.

---

## Clean-room note

Designed independently from standards/patterns as requirements sources (AGENTS.md §6). No upstream or third-party queue/worker code was copied; table shapes, lease/fence semantics, classifier, and callback verification were derived from the kernel's own forced-RLS, composite-FK, append-only `ON DELETE RESTRICT`, and `tenant_session`/placement patterns, plus the RESEARCH invariants and the REVIEW findings. Files consulted for grounding: `docs/01-product/MILE-4.2-notification-foundation-research.md`, `docs/01-product/MILE-4.2-notification-foundation-review.md`, `infrastructure/database/002_phase3_entitlement_metering.sql`, `infrastructure/database/014_workflow_history_survives_its_instance.sql`, `services/platform-kernel/python/platform_kernel/db.py`, `tools/migrate_tenant_to_dedicated.py` (COPY_ORDER), `tests/isolation/test_rls_database_behavior.py` (TENANT_SCOPED_TABLES).

---

## Authority block

```yaml
adr: notification-worker-queue-operational-model
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
  certification_scope: advisory_only
  execution_authority: false
  approval_authority: false
  ready_for_operator_review: true
```

> This ADR recommends an architecture only. It authorizes nothing and builds nothing. A build requires a separate operator authorization recorded first; Notification remains gated.