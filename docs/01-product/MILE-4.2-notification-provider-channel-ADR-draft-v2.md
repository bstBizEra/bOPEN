# ADR — Notification provider/channel adapter contract

**STATUS: DRAFT / PROPOSED — NOT AUTHORIZED, NOT IN FORCE. Notification remains gated by DEC-P4-ENTRY §9. This ADR authorizes nothing and builds nothing; a build needs a separate operator authorization recorded first, and no production provider is selected here.**

---

## Controlled-document metadata

| Field | Value |
|---|---|
| **Document ID** | `ADR-NOTIFY-PROVIDER` (proposed; pending governance ID-registry ratification) |
| **Version** | `2.0.0-draft` |
| **Owner** | bOPEN Agentic SE — Notification (Motor authoring; Codex independent reviewer) |
| **Issued** | 2026-08-06 |
| **Updated** | 2026-08-06 |
| **Status** | DRAFT / PROPOSED — gated by DEC-P4-ENTRY §9 |
| **Governing artifacts** | DEC-P4-ENTRY §9; MILE-4.2 foundation research + review (NOTIFY-INV-*); AGENTS.md §6 (clean-room independence); the paired worker/queue ADR (`ADR-NOTIFY-WQ`, lease/fence/evidence internals — referenced, not re-decided) |
| **Dependent artifacts** | `BOPEN-NOTIFY-001`; API/error/event/template schemas; privacy & threat model; retention rules; migration/rollback/compensation plan; operations runbooks; provider-qualification test matrix; EBIV evidence package |
| **Evidence refs** | `docs/01-product/MILE-4.2-notification-ADR-codex-review.md`; kernel files named in the Clean-room note below |

*Proposing a Document ID and version is traceability metadata for governance to register; it is not self-authorization.*

---

## Context

The Notification worker/queue ADR fixes the kernel's operational substrate — the transactional outbox, the fenced lease, the mutable `notification_dispatch` current-state row plus the separate append-only `notification_attempt` / `notification_receipt` evidence tables, the crash-safe send-start protocol, and in-database fairness. It stops at the process boundary where a leased dispatch leaves the kernel and crosses a network to a provider. It deliberately does **not** define the shape of that crossing. This ADR does, and only that: the **provider-neutral adapter contract and channel model**, independent of the worker loop.

This concern is separable because the worker's correctness (lease/fence, send-start protocol, retry loop, dead-letter, reconciliation) is provider-agnostic by construction — it manipulates a `notification_dispatch` row and classified `notification_attempt` outcomes, never a vendor SDK. The adapter is the narrow, owned seam between that machinery and any concrete provider. Getting the seam right is what lets NOTIFY-D-07 (provider selection) stay deferred without blocking the design: a stable facade plus a deterministic test adapter fully specify and contract-test the orchestrator before any vendor exists.

Two established kernel disciplines govern the seam. First, the **fail-closed / distrust posture** already enforced by `resolve_context` (a missing or ambiguous context reads zero, refuses identically) and by placement (`_verify_placement` / `tenant_session` fails closed on an unresolved or mis-routed tenant). Second, the Location foundation's **candidate-is-never-self-promoting** pattern: `location_repositories.observe()` records a provider/sensor point as a *candidate* — never truth on creation. A notification provider's response is exactly this kind of candidate: recorded, classified, but never self-promoting to truth. The ContactPoint extension already built (migration 019, `contact_point_repositories.py`) supplies the recipient side — endpoint types `email` and `phone`, a channel→endpoint_type map (`email→email`, `sms→phone`), and the rule that a channel with no matching **verified** endpoint is a refusal (CP-D-06). This ADR's channel model aligns to those endpoint types rather than inventing its own, and — following the reviewer's recipient-boundary finding — assigns recipient validation to the orchestrator that holds the tenant session, not to the adapter that holds only a disposed snapshot.

Notification remains gated. Nothing here is authorized to run.

---

## Decision

Adopt a single **owned adapter facade** (a `bst_*`-style boundary decoupling the kernel from every vendor) plus a **channel → provider-capability model**, under one keystone rule: **a provider response is a handoff candidate, never delivery and never authority.** No production provider is selected (NOTIFY-D-07 deferred); a deterministic **fake adapter** is the **specified test adapter** — the only adapter this design specifies — and it exists to serve contract tests.

Two reviewer-driven corrections shape this revision. (1) **The recipient/render seam moves out of the adapter:** the orchestrator resolves and validates the recipient under `tenant_session` and hands the adapter an already-validated snapshot plus a rendered-content reference; the adapter performs no recipient validation, because it structurally cannot. (2) **The classifier has a single owner:** the worker/queue ADR owns the closed four-class vocabulary; this ADR's adapter only *maps* a vendor return onto it and cannot mint a fifth class.

### 1. Channel → provider capability model

A **channel** is a transport family aligned to a ContactPoint endpoint type: `email` (endpoint `email`) and `sms` (endpoint `phone`) form the first slice; **`email` is the proposed first implementation scope**, `sms` is modeled but deferred. A channel maps to **one-or-more provider adapters**; a provider adapter **declares** — as static capability metadata, not runtime negotiation — which channels it serves and which of four capabilities it supports:

- **send** (mandatory) — synchronous handoff of one rendered message.
- **delivery-receipt / callback** — the provider will asynchronously report transport outcome to a verified endpoint.
- **idempotency-key** — the provider accepts and de-dupes on a caller-supplied key.
- **reconciliation-query** — the provider answers "what became of message X?" for an `unknown` outcome.

Capability is **declared and honored, never assumed**: absent `idempotency-key` and `reconciliation-query`, the worker ADR's `terminal_unknown` floor is the correct honest dead-end (at-least-once *effort* with honest ambiguity; exactly-once is not claimed). A channel with no capable, verified-endpoint-matched adapter is a **refusal**, mirroring CP-D-06 — never a silent drop. The **specified test adapter (a deterministic fake)** declares all four capabilities deterministically so contract tests exercise the full matrix without a vendor.

*Provider/profile binding itself is a control column on the dispatch row (`provider_id`, `provider_profile_version`), resolved at enqueue by this channel→adapter selection so a bound provider exists before the row is claimable — owned by the worker/queue ADR's schema and referenced here, not re-decided.*

### 2. The owned adapter interface (facade — four members, complete)

A stable `bst_notification_adapter` facade — one owned interface, vendor SDKs hidden entirely behind concrete implementations — decouples the kernel from vendor updates. It is the kernel's own owned-boundary / `bst_*`-wrapper discipline (the same pattern that keeps `tenant_session` the sole tenant-scope authority) applied to the vendor seam, and it is developed clean-room under AGENTS.md §6. The facade is **exactly four members**, and nothing outside them touches domain state:

1. **`capabilities() -> {channels_served, {send, delivery-receipt, idempotency-key, reconciliation-query}}`** — **static declared metadata**, never runtime negotiation or provider probing.
2. **`send(canonical_send_request) -> canonical_bounded_response`** — the only content-touching call; a **pure translation boundary**: no DB access, no `tenant_session`, no recipient re-resolution, no state transition, no internal retry. One send maps to one classified response and returns.
3. **`verify_callback(raw_bytes, headers) -> verified_provider_observation | Refusal`** — cryptographic verification and vendor→canonical normalization on **raw bytes before parse** (§4). It does **not** open `tenant_session` and does **not** look up the stored binding — those are worker-owned, authority-bearing acts.
4. **`reconcile(provider_ref) -> canonical_bounded_response`** — present **only** where `reconciliation-query` is declared; resolves an `unknown` by evidence (query the provider), never by resending.

**Canonical send request** (worker → adapter, assembled under `tenant_session` before the send; the adapter receives the *result* of resolution/rendering, never the authority to perform them):

| Field | Meaning / adapter obligation |
|---|---|
| `channel` | transport family (`email`; `sms` modeled, deferred). |
| `recipient_snapshot` | frozen `{endpoint_type, endpoint_value, purpose, party_id, resolved_at}` — **already validated by the orchestrator; the adapter MUST NOT re-resolve, re-validate, or cross-check tenancy** (it holds no tenant and no session). |
| `rendered_content_ref` | opaque, integrity-bound handle to the rendered template-version output; dereferenced to bytes for transport only. Raw body, template variables, and recipient value never flow through adapter logs or domain fields. |
| `idempotency_key` | the deterministic, attempt-derived value the worker ADR computes and records *before* send; forwarded to the provider **only** where the profile declares `idempotency-key`. |
| `provider_profile` / version | selects the concrete implementation and its vendor→canonical mapping rules. |
| `correlation_id` | opaque trace tag. |
| `tenant_id` (optional) | **opaque routing/correlation tag only** — never a validation or trust input; the adapter performs no tenant check with it, because RLS + orchestrator `resolve()` already did. |

**Canonical bounded response** (adapter → worker — bounded, safe, domain-shaped; exactly four fields):
- `provider_message_id` (opaque);
- `classified_outcome` — exactly one of the worker-owned closed set `provider_accepted` / `retryable_failed` / `terminal_failed` / `unknown` (§5). The adapter **maps** a vendor return onto that set and **cannot invent a fifth class**;
- `provider_profile` / version that produced the result;
- `safe_diagnostic` — a normalized reason code, never a raw payload.

**No provider secret, no raw provider payload, and no vendor-shaped object crosses into domain state.** Secrets live as runtime configuration behind the facade; raw payloads are retained (if at all) only as an integrity-referenced blob under the append-only receipt policy, never as domain fields. The adapter is a *pure translation boundary*: canonical in, canonical out.

### 3. Provider distrust (the keystone — unchanged, wording clarified per PA-07)

**An HTTP 200 from a provider is a HANDOFF, not delivery — and not authorization of any business action.** This is the adapter surface's equivalent of the worker ADR's outcome-truth ladder and Location's candidate discipline. The full research ladder is preserved verbatim and remains the keystone:

> `bOPEN accepted ≠ provider accepted ≠ transport delivered ≠ shown ≠ read ≠ acted upon`

- A provider result is recorded as a **candidate and then deterministically classified and verified by the system** into append-only provider-observed transport evidence (attempt outcome + authenticated receipt). **This "acceptance" is the automatic classifier + receipt verification — it is not a provider-authorized or human-authorized business transition, and it advances no business workflow.** The parallel to Location's `observe()` is the **candidate-is-never-self-promoting** discipline, **not** a per-message human sign-off: Notification does not require a human to accept every provider response. `provider_accepted` (2xx + message id) is the handoff class; it is **never** promoted to `delivered` without an **authenticated receipt** (§4). The `provider_accepted → delivered` ladder is receipt-driven only.
- The adapter **fails closed**, like `resolve_context` and placement: a malformed, ambiguous, low-confidence, or unmappable provider response resolves to `unknown`, never to a favorable state. Silence and garbage both resolve to distrust, not to success.
- A provider result **never advances or completes a business workflow** by itself (NOTIFY-INV-15). "Provider said OK" authorizes nothing downstream.
- The adapter treats the provider as an **untrusted external party across a trust boundary**, symmetric to how the callback path treats the inbound webhook — both directions distrust the vendor.

### 4. Callback verification contract (adapter side — completed hardening)

Delivery receipts arrive at the worker ADR's per-provider verified public endpoint. `verify_callback` owns **cryptographic verification + vendor→canonical normalization on raw bytes**; it owns nothing authority-bearing. This states the adapter's complete obligations at that surface, consistent with — not re-deciding — the worker ADR's binding lookup and tenant-scoped receipt append.

**CB-1 — Total raw-byte verification order; nothing parsed first.** Each step runs on raw bytes before the next; JSON parse is strictly last, so an unauthenticated caller cannot make the endpoint do meaningful work with garbage:
1. **size** — reject over a fixed byte cap **before** reading/allocating the full body (defends the unauthenticated endpoint against a parse-bomb / memory DoS);
2. **content-type** — reject a mistyped body;
3. **timestamp window** — from a signed header field, range-checked against the DB clock;
4. **HMAC / signature** — over the exact raw bytes, against the provider's active-or-overlap secret (CB-4);
5. **only now parse** and normalize to `{provider_message_id, provider_event_id, normalized_transport_status}`.

No allocation-heavy or schema step precedes signature verification.

**CB-2 — Authority derives ONLY from the stored provider-message binding (AUTH-D1), and the WORKER performs it.** `verify_callback` returns a verified observation; it does **not** resolve a tenant. The **worker** looks the `provider_message_id` up against the stored `notification_attempt` (the sole source of `tenant_id` and context) under the elevated callback role, then opens `tenant_session(stored_tenant_id)` as `bopen_app` to append the receipt. Any tenant/account/recipient field in the callback body is **inert** — "a header cannot create authority," applied to a webhook body. The adapter never sees or selects a tenant.

**CB-3 — Early-callback quarantine (verified-early ≠ forged).** A callback that passes CB-1 verification but whose `provider_message_id` matches no stored binding — because the send-start row is not yet committed/visible — must **not** be dropped as "unknown," which would lose a legitimately early receipt. **Signature is verified before quarantine**, so forged bytes never enter it; the verified-but-unbound observation is handed to the worker for append-only quarantine and bounded re-resolution once the attempt commits. Because the idempotency key / binding is derived and recorded *before* send, the quarantine window is only the commit-visibility race; after a bounded quarantine-age ceiling with no match, the entry becomes an operator-visible dead record — never a receipt, never a state change.

**CB-4 — Secret rotation with bounded, auditable overlap.** Each provider holds at most two active signing secrets (`current` + `previous`), the `previous` carrying an explicit `not_after`. Verification (CB-1 step 4) tries `current` then `previous`; a body verifying only under an expired `previous` is refused. Rotation promotes new→`current`, demotes old→`previous` with a bounded window, drops old at `not_after` — overlap bounded and recorded, never unbounded acceptance. Secrets are runtime config behind the facade — never a tenant row, never an event field (NOTIFY-INV-13). Per-provider revocation is dropping that provider's secrets, halting its callbacks alone.

**CB-5 — Replay maps to the same attempt.** A redelivered callback keyed on `(provider, provider_message_id, provider_event_id[, replay_id])` collides on the append-only uniqueness key and is a no-op: no second receipt, no second status event (NOTIFY-INV-06). Ordering is a lattice, not a stream — the worker's receipt projection advances only monotonically; a stale or already-superseded observation is still stored append-only but does not rewrite state. Convergence is independent of callback arrival order.

**CB-6 — Uniform, tenant-safe refusal (the non-oracle).** Unknown id, wrong-provider/wrong-message binding, bad signature, stale timestamp, oversized/mistyped body, over-rate, invalid transition — all refused **identically**, constant-work past the size/type gate, disclosing nothing about whether a message or recipient exists (NOTIFY-INV-04, -10). *Per-provider callback rate limiting, keyed only on `provider_id` (never resolving a tenant or message to decide throttling), and the tenant-safe audit routing of these refusals are the worker/callback security plane's concern (owned there); the adapter surfaces the verification verdict, the worker enforces the plane.*

### 5. Single classifier — adapter maps, worker owns (closes cross-ADR finding #2)

There is **one** classifier, **one** closed vocabulary, used verbatim in both ADRs. The short-form aliases (`accepted` / `retryable` / `terminal`) that made the drafts appear to disagree are killed.

| Class | Meaning (dividing line: *provably-before-effect* vs *not-provably-before-effect*) |
|---|---|
| `provider_accepted` | 2xx + provider message id — a **handoff**, never human delivery; promoted to `delivered` only by an authenticated receipt (§3, §4). |
| `retryable_failed` | DNS/connect-refused/TLS-connect-timeout, or a `429`/`503` that provably rejected the request **at admission** (validated `Retry-After`, or a profile-declared "503 = pre-admission rejection") — **provably before any provider-side effect**; safe to re-send on a **new** attempt. |
| `terminal_failed` | `400` / hard bounce / suppressed — deterministic non-retryable. |
| `unknown` | write/read timeout or reset **after** request bytes flushed; `500`/`502`/`504` after the full request was sent; **generic `503` with no proof of pre-admission rejection**; malformed / no-result — cannot distinguish "never arrived" from "processed, response lost." |

**Ownership model (frozen):**
- The **worker/queue ADR OWNS the classifier** — it *defines* the closed enum, the *provably-before-effect* dividing line, and it is the sole consumer that drives retry / dead-letter / reconciliation from the class. The enum lives in worker-owned domain code and the `notification_attempt.classified_outcome` column constraint. This ADR **references** it; it does not restate or re-decide it.
- The **provider/channel adapter MAPS ONLY** — its single job is `vendor_return → exactly one canonical class`. It **cannot mint a fifth class**. A vendor return it cannot confidently map resolves to `unknown` (fail-closed), never to a favorable class.
- **The classifier fails closed toward `unknown`, never toward `retryable_failed`.** `retryable_failed` authorizes an automatic re-send, so it is granted only on *proven* before-effect; every genuine ambiguity (the generic-503 case the reviewer flagged) is `unknown` and routes to the worker's reconciliation ladder, not to a resend.
- **`terminal_unknown` is NOT a fifth class.** It is a **reconciliation-lifecycle floor state** on the worker's dispatch/reconciliation track, reached only after an `unknown` attempt exhausts idempotency/reconciliation evidence. Both ADRs state this explicitly so the four-class classifier stays closed.

### 6. Adapter-side idempotency-key contribution to duplicate safety

The at-most-once-effective guarantee is not the adapter's to make, but the adapter is the mechanism through which it holds at the provider boundary. The worker computes a **deterministic, attempt-derived** `idempotency_key` and records it *before* any byte leaves the process; the adapter **forwards that exact key to the provider where `idempotency-key` is declared**, and forwards the **same** key unchanged on a worker-directed reclaim re-send of the same attempt — so two physical sends carrying one key collapse to a single provider-side effect. The adapter **never mints, randomizes, or caches its own key**, and **never resends on its own initiative**: a reclaim re-send is authorized only by the worker's capability-gated reclaim rule; `reconcile()` (where declared) resolves an `unknown` by *query*, not by resend. This is the adapter's half of the split INV-07 defense — the fence bounds concurrent claims inside the DB; the pre-recorded key, forwarded here, bounds duplicate external sends.

### 7. Provider profile & governance

Each concrete adapter (when one is later selected) carries a governed **provider profile**: terms/version reference; **the vendor→canonical mapping table** feeding the worker's classifier and breaker (including any profile-declared "503 = pre-admission rejection" downgrade, with `Retry-After`); **residency** constraints; **redaction / tenant-safe logging** rules (identifiers and safe hashes only — never full endpoint, body, variables, or raw payload, NOTIFY-INV-13); and **secret rotation with a bounded overlap window** (CB-4). The profile is metadata *about* the adapter, not a tenant-writable row and not an event field. **Provider selection, credentials, billing, sender-domain readiness, and failover are a SEPARATE later decision** — named and deferred here (NOTIFY-D-04, NOTIFY-D-07), not resolved.

### 8. Refusal matrix (adapter surface — transport refusals only)

Every failure the adapter can itself observe is refused **loudly and tenant-safely** — a distinct, safe reason code, no silent success, no enumeration oracle. **The recipient-snapshot validation row of the prior draft is removed** (superseded by the orchestrator-owned recipient boundary; the adapter holds no tenant and no session and structurally cannot validate a disposed snapshot):

| Condition | Adapter behavior |
|---|---|
| Unknown / unsupported channel | Refuse before send — no adapter for channel. |
| Capability not declared (e.g. idempotency-key requested, unsupported) | Refuse the *request for that capability*; degrade to the honest floor (no key/reconciliation → worker's `terminal_unknown` on ambiguity), never fake the capability. |
| Provider timeout / connection failure **provably before** bytes sent | Classify `retryable_failed`. |
| Provider write/read timeout / reset / 5xx **after** bytes sent, or generic `503` without proof of pre-admission rejection | Classify `unknown` — never `terminal_failed`, never `delivered`; hand to the worker's reconciliation. |
| Ambiguous / no-result / malformed provider response | Classify `unknown`, fail closed — refuse to guess a favorable state. |
| Callback size / content-type / timestamp / signature failure | Refuse on raw bytes before parse (§4, CB-1). |
| Callback with unresolvable / wrong-message binding | Return the verified observation for worker-side quarantine (CB-3) or uniform refusal (CB-6); the adapter never resolves a tenant. Authority is the stored binding only (AUTH-D1); body tenant field is inert. |

---

## Invariants defended

- **NOTIFY-INV-08 (outcome truth) + the provider-distrust keystone:** a 200 is a handoff candidate; `provider_accepted` never auto-promotes to `delivered` without an authenticated receipt; the adapter maps onto the closed worker-owned classifier and cannot mint a fifth outcome; the four classes stay distinct with a *provably-before-effect* dividing line.
- **NOTIFY-INV-15 (workflow boundary):** a provider result authorizes and completes nothing downstream; "acceptance" is deterministic classification/verification, not a business transition (PA-07).
- **NOTIFY-INV-10 (callback trust — now fully defended):** total raw-byte order size→type→timestamp→HMAC→parse (CB-1); authority from the stored binding, worker-performed (CB-2); verified-early quarantine separates early from forged (CB-3); bounded-overlap rotation (CB-4); replay maps to the same attempt (CB-5).
- **NOTIFY-INV-01 / -04 (isolation / anti-enumeration):** the adapter is removed from the tenant-isolation-critical path — it holds no tenant, resolves none, and validates no snapshot; every callback refusal is a single non-oracle response (CB-6).
- **NOTIFY-INV-03 (recipient integrity):** enforcement **relocated** to the orchestrator's `tenant_session` `resolve()` (verified/effective-window/purpose/channel/tenant, forced RLS), which the adapter consumes as a validated-by-construction snapshot — *strengthened* by moving it to the only layer that can enforce it.
- **NOTIFY-INV-06 (idempotency):** deterministic attempt-derived key forwarded where declared, same key on a worker-directed reclaim; callback replay maps to the same attempt.
- **NOTIFY-INV-09 (retry safety):** `unknown` is reconciled via declared idempotency-key/reconciliation-query or floored at `terminal_unknown`; the adapter never blind-re-sends and never retries internally; generic 503 defaults to `unknown`.
- **NOTIFY-INV-13 (privacy/secrets):** no secret or raw payload crosses into domain state; rendered content passes as an opaque ref; profile logging is redacted.

---

## Alternatives considered and rejected

- **Call a provider SDK directly from the kernel (no facade).** Rejected: couples domain state to vendor semantics and update cadence, and makes the deterministic fake — the only thing that lets NOTIFY-D-07 stay deferred — impossible. The owned `bst_notification_adapter` boundary (the kernel's own owned-boundary discipline, developed clean-room under AGENTS.md §6) is mandatory.
- **Let the adapter validate the recipient snapshot (staleness / cross-tenant).** Rejected: the frozen `RecipientSnapshot` carries no `tenant_id`, no `revision`, no `effective_to`, and no DB handle — the adapter is *structurally incapable* of the check. Validation belongs to the orchestrator's `tenant_session` `resolve()`, whose SQL *is* the validation.
- **Treat the provider message id (or provider "place"/entity) as domain identity.** Rejected: an opaque, vendor-scoped, non-tenant-bound token cannot be a domain key; it is stored *on* the attempt as a lookup handle, never *as* the notification's identity.
- **Trust the callback's tenant/account field to route or scope.** Rejected — the AUTH-D1 violation; the body field is inert, authority is the stored binding only.
- **Runtime capability negotiation / probing the provider.** Rejected: capability is declared static metadata; probing invites a lying or degraded provider to claim more than it honors. Declared-and-honored fails closed; assumed-and-negotiated fails open.
- **Adapter mints or caches its own idempotency key, or resends on its own initiative.** Rejected: duplicate safety depends on the *worker's* pre-recorded, attempt-derived key; an adapter-minted or content-hash key collapses legitimately distinct sends and cannot fence a pre-render retry. The adapter forwards; it never invents and never self-resends.
- **A single shared authenticated callback endpoint across providers.** Rejected: verification is provider-specific (per-provider secret/signature scheme); one endpoint cannot verify raw bytes for many schemes.
- **Let the adapter promote `provider_accepted` to `delivered` on a 2xx.** Rejected — the exact truth-ladder collapse the keystone forbids; only an authenticated receipt promotes.
- **Blind-resend an `unknown` to force at-least-once on a no-key provider.** Rejected — the INV-09 violation; `unknown` is reconciled or floored at `terminal_unknown`, never gambled.

---

## Consequences

- **A stable owned seam exists** between the worker loop and any future vendor. Adding a provider later is implementing one four-member facade against a fixed contract and a passing contract-test suite — not touching the orchestrator, the tables, or domain state.
- **The fake (specified test) adapter is load-bearing.** It must deterministically produce every classified outcome (`provider_accepted` / `retryable_failed` / `terminal_failed` / `unknown`), simulate callbacks with valid and invalid signatures across the CB-1 order, honor/deny each declared capability, and echo a forwarded idempotency key — because it is the *only* thing that proves owned orchestration behavior before a real provider is qualified. A fake proves contract conformance, never production readiness.
- **Contract-test matrix implications:** every refusal-matrix row; the vendor→canonical mapping per capability profile; `provider_accepted`-without-receipt never showing `delivered`; the full CB-1 raw-byte order enforced before parse; verified-early quarantine vs forged; callback replay/wrong-binding uniform refusal (no oracle); idempotency-key forwarded-and-reused on reclaim; capability-absent → honest-floor behavior. **Recipient-validation belongs to the orchestrator's test surface, not the adapter's.**
- **Governance surface:** each future concrete adapter needs its provider profile reviewed (residency, redaction, rotation, vendor→canonical mapping) as part of its own authorization — this ADR fixes the *shape* of that review, not any provider's answer.
- **No new runtime actor is introduced here** — the worker, roles, and endpoint are the worker ADR's. This ADR is a contract over the crossing that ADR already owns.

---

## Explicitly deferred

- **Production provider selection, credentials, billing, sender-domain / DNS readiness** (NOTIFY-D-04, NOTIFY-D-07) — a separate ADR with residency, retention, cost, quotas, secrets, SLA, and revocation.
- **Outbound webhook / egress delivery** — a distinct, larger trust boundary (SSRF, DNS-rebinding, redirect, response-limit, tenant-controlled destination); its own ADR.
- **Tenant bring-your-own provider + provider failover** — multiplies profile and breaker cardinality; must revisit fairness and secret custody.
- **Multi-provider routing / least-cost / weighted selection** across adapters for one channel — modeled as one-or-more here, but the *selection policy* among them is deferred (NOTIFY-D-07); the `provider_id` binding column is always populated at enqueue regardless.
- **SMS and later channels' production enablement** — `sms` (endpoint `phone`) is modeled; push/voice/webhook/in-app are out.
- **Concrete constants** — timeout budgets, signature schemes, size cap bytes, timestamp window, rate-bucket rates, rotation-overlap duration, quarantine-age ceiling — deferred to the concrete-adapter/runbook ADR.

Each deferred item requires its **own** decision record; none is authorized here.

---

## Clean-room note

Designed independently under **AGENTS.md §6** (clean-room independence): standards and provider behavior are requirements sources only. **No vendor SDK, schema, template, callback format, or test was copied.** The facade shape, channel→capability model, four-member interface, canonical request/response, distrust keystone, single-classifier mapping, and callback obligations were derived from the kernel's own patterns — `resolve_context`/placement fail-closed, `location_repositories.observe()` candidate-is-never-self-promoting discipline, `contact_point_repositories.resolve()` returning a disposed frozen `RecipientSnapshot` (no `tenant_id`, no session) with CP-D-06 channel mapping, the AUTH-D1 header-cannot-create-authority rule, and the kernel's owned-boundary / `bst_*`-wrapper facade discipline — plus the RESEARCH invariants (§9.1 no-txn-across-network, §9.2 adapter contract, §9.3 callback security, NOTIFY-INV-*), the REVIEW findings (recipient boundary belongs before the adapter; single classifier owner + vocabulary; callback ownership handoff; PA-07/PA-08), and the paired worker/queue ADR (classifier, lease/fence, send-start protocol, evidence tables, `provider_id` binding — referenced, not re-decided). The earlier draft's `(AGENTS.md §11 facade pattern)` citation is **dropped** — in this repository AGENTS.md §11 concerns testing, not facades (reviewer-confirmed); the facade discipline is grounded in the kernel's own `bst_*` boundary pattern and §6 clean-room independence instead. Files consulted for grounding: `docs/01-product/MILE-4.2-notification-foundation-research.md`, `docs/01-product/MILE-4.2-notification-foundation-review.md`, `docs/01-product/MILE-4.2-notification-ADR-codex-review.md`, `docs/01-product/MILE-4.2-notification-worker-queue-ADR-draft.md`, `services/platform-kernel/python/platform_kernel/location_repositories.py`, `services/platform-kernel/python/platform_kernel/contact_point_repositories.py`, `services/platform-kernel/python/platform_kernel/db.py`, `infrastructure/database/014_workflow_history_survives_its_instance.sql`.

---

## Authority block

```yaml
adr: notification-provider-channel-adapter-contract
document_id: ADR-NOTIFY-PROVIDER            # proposed; pending governance registration
version: 2.0.0-draft
status: DRAFT / PROPOSED
gated_by: DEC-P4-ENTRY §9
truth_status: partially_supported
authority_status: advisory_only
implementation_status: candidate
risk_class: high
execution_authority: false
approval_authority: false
production_activation_authority: false
provider_selection_authority: false
completion_claimed: false
self_certification:
  agent_id: claude-motor
  peer_agent_id: codex-reviewer
  certification_scope: advisory_only
  execution_authority: false
  approval_authority: false
  ready_for_operator_review: true
```

> This ADR recommends an adapter/provider contract only. It authorizes nothing, builds nothing, and selects no provider. A build — and any concrete provider — requires a separate operator authorization recorded first; Notification remains gated by DEC-P4-ENTRY §9.
