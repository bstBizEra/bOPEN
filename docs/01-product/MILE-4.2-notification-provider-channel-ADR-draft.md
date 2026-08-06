# ADR — Notification provider/channel adapter contract

**STATUS: DRAFT / PROPOSED — NOT AUTHORIZED, NOT IN FORCE. Notification remains gated by DEC-P4-ENTRY §9. This ADR authorizes nothing and builds nothing; a build needs a separate operator authorization recorded first, and no production provider is selected here.**

---

## Context

The Notification worker/queue ADR fixes the kernel's operational substrate — the transactional outbox, the fenced lease, the append-only attempt/receipt evidence, in-database fairness — and stops at the process boundary where a leased dispatch leaves the kernel and crosses a network to a provider. It deliberately does **not** define the shape of that crossing. This ADR does, and only that: the **provider-neutral adapter contract and channel model**, independent of the worker loop.

This concern is separable because the worker's correctness (lease/fence, retry loop, dead-letter, reconciliation) is provider-agnostic by construction — it manipulates a `notification_dispatch` row and classified `notification_attempt` outcomes, never a vendor SDK. The adapter is the narrow, owned seam between that machinery and any concrete provider. Getting the seam right is what lets NOTIFY-D-07 (provider selection) stay deferred without blocking the design: a stable facade plus a deterministic fake adapter fully specify and contract-test the orchestrator before any vendor exists.

Two established kernel disciplines govern the seam. First, the **fail-closed / distrust posture** already enforced by `resolve_context` (a missing or ambiguous context reads zero, refuses identically) and by placement (`_connect_for_tenant` fails closed on an unresolved or mis-routed tenant). Second, the Location foundation's **candidate-requiring-acceptance** pattern: `location_repositories.observe()` records a provider/sensor point as a *candidate* — never accepted on creation — and `accept_observation()` is a distinct, authorized act carrying its own provenance (LOC-INV-06). A notification provider's response is exactly this kind of candidate: recorded, classified, but never self-promoting to truth. The ContactPoint extension already built (migration 019, `contact_point_repositories.py`) supplies the recipient side — endpoint types `email` and `phone`, a channel→endpoint_type map (`email→email`, `sms→phone`), and the rule that a channel with no matching **verified** endpoint is a refusal (CP-D-06). This ADR's channel model aligns to those endpoint types rather than inventing its own.

Notification remains gated. Nothing here is authorized to run.

---

## Decision

Adopt a single **owned adapter facade** (a `bst_*`-style boundary decoupling the kernel from every vendor) plus a **channel → provider-capability model**, under one keystone rule: **a provider response is a handoff candidate, never delivery and never authority.** No production provider is selected (NOTIFY-D-07 deferred); a deterministic **fake adapter** is the only adapter this design admits, and it exists to serve contract tests.

### 1. Channel → provider capability model

A **channel** is a transport family aligned to a ContactPoint endpoint type: `email` (endpoint `email`) and `sms` (endpoint `phone`) form the first slice; only `email` is authorized for a first build, `sms` is modeled but deferred. A channel maps to **one-or-more provider adapters**; a provider adapter **declares** — as static capability metadata, not runtime negotiation — which channels it serves and which of four capabilities it supports:

- **send** (mandatory) — synchronous handoff of one rendered message.
- **delivery-receipt / callback** — the provider will asynchronously report transport outcome to a verified endpoint.
- **idempotency-key** — the provider accepts and de-dupes on a caller-supplied key.
- **reconciliation-query** — the provider answers "what became of message X?" for an `unknown` outcome.

Capability is **declared and honored, never assumed**: absent `idempotency-key` and `reconciliation-query`, the worker ADR's `terminal_unknown` floor is the correct honest dead-end (at-least-once with honest ambiguity; exactly-once is not claimed). A channel with no capable, verified-endpoint-matched adapter is a **refusal**, mirroring CP-D-06 — never a silent drop. The only adapter this ADR authorizes is the **fake**: it declares all four capabilities deterministically so contract tests exercise the full matrix without a vendor.

### 2. The owned adapter interface (facade)

A stable `bst_notification_adapter` facade — one owned interface, vendor SDKs hidden entirely behind concrete implementations — decouples the kernel from vendor updates (AGENTS.md §11 facade pattern). It exposes a **canonical send request → canonical bounded response** contract, and nothing else touches domain state.

**Canonical send request** (what the worker hands the adapter, assembled under `tenant_session` before the send):
- `tenant_id` and `channel`;
- the **resolved recipient snapshot** from the ContactPoint resolver (a frozen, minimal endpoint value + provenance — not a live contact lookup);
- a **content reference** to the rendered template-version output (a ref/handle, not raw body sprayed through logs);
- a **correlation / idempotency key** — the deterministic attempt-derived value the worker ADR already defines, forwarded to the provider only where `idempotency-key` is declared.

**Canonical bounded response** (what the adapter returns — bounded, safe, domain-shaped):
- `provider_message_id` (opaque);
- a **classified outcome** — exactly one of `accepted` / `retryable` / `terminal` / `unknown`, using the **same classifier the worker ADR owns** (this ADR does not re-define it; the adapter's job is to *map* a vendor return onto that closed set and refuse to invent a fifth class);
- the **provider profile / version** that produced the result;
- a **safe diagnostic** — a normalized reason code, never a raw payload.

**No provider secret, no raw provider payload, and no vendor-shaped object crosses into domain state.** Secrets live as runtime configuration behind the facade; raw payloads are retained (if at all) only as an integrity-referenced blob under the append-only receipt policy, never as domain fields. The adapter is a *pure translation boundary*: canonical in, canonical out.

### 3. Provider distrust (the keystone)

**An HTTP 200 from a provider is a HANDOFF, not delivery — and not authorization of any business action.** This is the adapter surface's equivalent of the worker ADR's outcome-truth ladder and Location's candidate discipline:

- A provider result is a **candidate requiring acceptance** into transport truth, exactly as `observe()` records a point that only `accept_observation()` promotes. `accepted` (2xx + message id) is the handoff class; it is **never** promoted to `delivered` without an **authenticated receipt** (§4). The `accepted → delivered` ladder is receipt-driven only.
- The adapter **fails closed**, like `resolve_context` and placement: a malformed, ambiguous, low-confidence, or cross-tenant provider response is **refused / classified `unknown`**, never trusted into a favorable state. Silence and garbage both resolve to distrust, not to success.
- A provider result **never advances or completes a business workflow** by itself (NOTIFY-INV-15). "Provider said OK" authorizes nothing downstream.
- The adapter treats the provider as an **untrusted external party across a trust boundary**, symmetric to how the callback path treats the inbound webhook — both directions distrust the vendor.

### 4. Callback verification contract (adapter side)

Delivery receipts arrive at the worker ADR's per-provider verified public endpoint; this ADR states the **adapter's obligations** at that surface (consistent with, not re-deciding, the worker ADR):

- **Verify on raw bytes, before parse:** HMAC/signature against the active (or bounded-overlap rotated) provider secret; a **timestamp window**; **size and content-type limits**. Parsing precedes nothing.
- **Authority derives ONLY from the stored provider-message binding (AUTH-D1).** The adapter extracts `provider_message_id`, looks it up against the stored attempt (the sole source of `tenant_id` and context), and **ignores any tenant/account/recipient field in the callback body** — "a header cannot create authority," now applied to a webhook body. Only after binding does the receipt write open `tenant_session(stored_tenant_id)`.
- **Refuse uniformly and tenant-safely.** Unknown id, wrong-provider/wrong-message binding, bad signature, stale timestamp, oversized/mistyped body, invalid transition — all refused identically, disclosing nothing about whether a message or recipient exists (NOTIFY-INV-04, -10). Replay maps to the same attempt and produces no second receipt (NOTIFY-INV-06).

### 5. Provider profile & governance

Each concrete adapter (when one is later selected) carries a governed **provider profile**: terms/version reference; **rate-limit and retry classification** feeding the worker's classifier and breaker; **residency** constraints; **redaction / tenant-safe logging** rules (identifiers and safe hashes only — never full endpoint, body, variables, or raw payload, NOTIFY-INV-13); and **secret rotation with a bounded overlap window** (two valid secrets during rotation, auditable, no unbounded acceptance). The profile is metadata *about* the adapter, not a tenant-writable row and not an event field. **Provider selection, credentials, billing, sender-domain readiness, and failover are a SEPARATE later decision** — named and deferred here (NOTIFY-D-04, NOTIFY-D-07), not resolved.

### 6. Refusal matrix (adapter surface)

Every failure is refused **loudly and tenant-safely** — a distinct, safe reason code, no silent success, no enumeration oracle:

| Condition | Adapter behavior |
|---|---|
| Unknown / unsupported channel | Refuse before send — no adapter for channel. |
| Capability not declared (e.g. idempotency-key requested, unsupported) | Refuse the *request for that capability*; degrade to the honest floor (no key → `terminal_unknown` on ambiguity), never fake the capability. |
| Invalid / stale / cross-tenant recipient snapshot | Refuse — the snapshot must match the send's tenant and a verified endpoint (CP-D-06); no live re-resolution to "fix" it. |
| Provider timeout / connection failure *before* bytes sent | Classify `retryable`. |
| Provider timeout / reset / 5xx *after* bytes sent | Classify `unknown` — never `failed`, never `delivered`; hand to reconciliation. |
| Ambiguous / no-result / malformed provider response | Classify `unknown`, fail closed — refuse to guess a favorable state. |
| Callback signature / timestamp / size / content-type failure | Refuse on raw bytes before parse. |
| Cross-tenant / wrong-message callback binding | Refuse — authority is the stored binding only (AUTH-D1); body tenant field is inert. |

---

## Invariants defended

- **NOTIFY-INV-08 (outcome truth) + the provider-distrust keystone:** a 200 is a handoff candidate; `accepted` never auto-promotes to `delivered` without an authenticated receipt; the adapter maps onto the closed classifier and cannot mint a fifth outcome.
- **NOTIFY-INV-15 (workflow boundary):** a provider result authorizes and completes nothing downstream.
- **NOTIFY-INV-10 (callback trust):** signature/timestamp/size on raw bytes before parse; authority from the stored provider-message binding (AUTH-D1), never the body.
- **NOTIFY-INV-01 / -04 (isolation / anti-enumeration):** cross-tenant provider or callback binding refused; uniform tenant-safe refusals across the matrix; no timing/response oracle.
- **NOTIFY-INV-03 (recipient integrity):** the adapter consumes a frozen verified recipient snapshot; a mismatched, stale, or cross-tenant snapshot is refused, aligning to CP-D-06.
- **NOTIFY-INV-06 (idempotency):** deterministic attempt-derived key forwarded where declared; callback replay maps to the same attempt.
- **NOTIFY-INV-09 (retry safety):** `unknown` is reconciled via declared idempotency-key/reconciliation-query or floored at `terminal_unknown`; the adapter never blind-re-sends.
- **NOTIFY-INV-13 (privacy/secrets):** no secret or raw payload crosses into domain state; profile logging is redacted.

---

## Alternatives considered and rejected

- **Call a provider SDK directly from the kernel (no facade).** Rejected: couples domain state to vendor semantics and update cadence, defeats AGENTS.md §11's facade rule, and makes the deterministic fake — the only thing that lets NOTIFY-D-07 stay deferred — impossible. The owned `bst_notification_adapter` boundary is mandatory.
- **Treat the provider message id (or provider "place"/entity) as domain identity.** Rejected: an opaque, vendor-scoped, non-tenant-bound token cannot be a domain key; it is stored *on* the attempt as a lookup handle, never *as* the notification's identity. (Mirrors Location refusing a provider place id as canonical.)
- **Trust the callback's tenant/account field to route or scope.** Rejected — the AUTH-D1 violation; the body field is inert, authority is the stored binding only.
- **Runtime capability negotiation / probing the provider for what it supports.** Rejected: capability is declared static metadata; probing invites a lying or degraded provider to claim more than it honors. Declared-and-honored fails closed; assumed-and-negotiated fails open.
- **A single shared authenticated callback endpoint across providers.** Rejected: verification is provider-specific (per-provider secret/signature scheme); one endpoint cannot verify raw bytes for many schemes. (Consistent with the worker ADR.)
- **Content-hash idempotency at the adapter.** Rejected: collapses two legitimately distinct sends and fails to fence a pre-render retry; the key is caller/event-scoped and attempt-derived (worker ADR).
- **Let the adapter promote `accepted` to `delivered` on a 2xx.** Rejected — the exact truth-ladder collapse the keystone forbids; only an authenticated receipt promotes.

---

## Consequences

- **A stable owned seam exists** between the worker loop and any future vendor. Adding a provider later is implementing one facade against a fixed contract and a passing contract-test suite — not touching the orchestrator, the tables, or domain state.
- **The fake adapter is load-bearing.** It must deterministically produce every classified outcome (accepted/retryable/terminal/unknown), simulate callbacks with valid and invalid signatures, and honor/deny each declared capability — because it is the *only* thing that proves owned orchestration behavior before a real provider is qualified. A fake proves contract conformance, never production readiness.
- **Contract-test matrix implications:** every refusal-matrix row; the classifier mapping per capability profile; `accepted`-without-receipt never showing `delivered`; callback signature/timestamp/size/replay/wrong-binding uniform refusal (no oracle); cross-tenant snapshot and cross-tenant callback binding refused; capability-absent → honest-floor behavior.
- **Governance surface:** each future concrete adapter needs its provider profile reviewed (residency, redaction, rotation) as part of its own authorization — this ADR fixes the *shape* of that review, not any provider's answer.
- **No new runtime actor is introduced here** — the worker, role, and endpoint are the worker ADR's. This ADR is a contract over the crossing that ADR already owns.

---

## Explicitly deferred

- **Production provider selection, credentials, billing, sender-domain / DNS readiness** (NOTIFY-D-04, NOTIFY-D-07) — a separate ADR with residency, retention, cost, quotas, secrets, SLA, and revocation.
- **Outbound webhook / egress delivery** — a distinct, larger trust boundary (SSRF, DNS-rebinding, redirect, response-limit, tenant-controlled destination); its own ADR.
- **Tenant bring-your-own provider + provider failover** — multiplies profile and breaker cardinality; must revisit fairness and secret custody.
- **Multi-provider routing / least-cost / weighted selection** across adapters for one channel — modeled as one-or-more here, but the *selection policy* among them is deferred.
- **SMS and later channels' production enablement** — `sms` (endpoint `phone`) is modeled; push/voice/webhook/in-app are out.
- **Concrete constants** — timeout budgets, signature schemes, rotation-overlap duration, rate-limit numbers — deferred to the concrete-adapter/runbook ADR.

Each deferred item requires its **own** decision record; none is authorized here.

---

## Clean-room note

Designed independently under AGENTS.md §6/§11: standards and provider behavior are requirements sources only. **No vendor SDK, schema, template, callback format, or test was copied.** The facade shape, channel→capability model, canonical request/response, distrust keystone, and callback obligations were derived from the kernel's own patterns — `resolve_context`/placement fail-closed, `location_repositories.observe()/accept_observation()` candidate discipline, `contact_point_repositories` endpoint types and CP-D-06 channel mapping, and the AUTH-D1 header-cannot-create-authority rule — plus the RESEARCH invariants (§9.2 adapter contract, §9.3 callback security, NOTIFY-INV-*), the REVIEW findings (provider ADR as a named successor artifact; AUTH-D1 applied to callbacks; outbound webhooks deferred), and the just-drafted worker/queue ADR (classifier, lease/fence, outbox — referenced, not re-decided). Files consulted for grounding: `docs/01-product/MILE-4.2-notification-foundation-research.md`, `docs/01-product/MILE-4.2-notification-foundation-review.md`, `docs/01-product/MILE-4.2-notification-worker-queue-ADR-draft.md`, `services/platform-kernel/python/platform_kernel/location_repositories.py`, `services/platform-kernel/python/platform_kernel/contact_point_repositories.py`.

---

## Authority block

```yaml
adr: notification-provider-channel-adapter-contract
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

> This ADR recommends an adapter/provider contract only. It authorizes nothing, builds nothing, and selects no provider. A build — and any concrete provider — requires a separate operator authorization recorded first; Notification remains gated by DEC-P4-ENTRY §9.
