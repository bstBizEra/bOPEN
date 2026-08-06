# Notification privacy & threat model

**STATUS: DRAFT / PROPOSED — NOT AUTHORIZED, NOT IN FORCE. Notification remains gated by DEC-P4-ENTRY §9. This document authorizes nothing, builds nothing, decides no provider, and records no completion; a build needs a separate operator authorization recorded first.**

---

## Context

This is the privacy and threat model named as a required successor artifact by REVIEW-MILE-4.2-NOTIFICATION §5 and RESEARCH-MILE-4.2-NOTIFICATION §15(5). It sits beside — and is consistent with, without re-deciding — the two Notification ADR drafts: the worker/queue operational model (transactional outbox, fenced lease, append-only attempt/receipt evidence, in-database fairness) and the provider/channel adapter contract (owned facade, channel→capability model, the provider-distrust keystone). Those ADRs fix *mechanism*. This document fixes *what an adversary would try, what is at stake, and which existing kernel control or NOTIFY-INV invariant refuses them* — a security and privacy lens over the same surfaces.

Notification is the first foundation to add three surfaces the kernel has never had: a long-lived background worker holding an elevated cross-tenant role; egress to a provider across a network; and an unauthenticated-but-verified public inbound callback endpoint. Every kernel surface until now has been request-driven, synchronous, and scoped by `tenant_session(tenant_id)` under forced RLS, with `resolve_context` failing closed on a missing or ambiguous context (identical-403, no enumeration oracle), placement (`_connect_for_tenant`) failing closed on an unresolved or mis-routed tenant, and the AUTH-D1 rule that *a header cannot create authority*. Notification must extend those disciplines onto genuinely new ground rather than inventing parallel ones. This model treats each new surface as hostile by default.

---

## Assets

What an attacker (external, cross-tenant, malicious provider, or curious insider) wants, ranked by sensitivity:

1. **Message content** — the rendered subject/body and the template variables that fill it. Frequently PII (names, account facts, security codes, transaction details). The rendered output and the variable set are classified and minimized independently (RESEARCH §10.2).
2. **The resolved recipient endpoint** — the email/phone value produced by the ContactPoint resolver and frozen into the `RecipientSnapshot`. Discloses both an identity and a fact of contact.
3. **The tenant→notification linkage itself** — that *this tenant* is sending *this purpose* to *this party* is sensitive even with content stripped. Existence is an asset; anti-enumeration (NOTIFY-INV-04) protects it.
4. **Delivery metadata / status** — lifecycle state, classified outcomes, timing, provider message ids. Leaks existence, behavior, and volume if exposed with tenant-identifying labels.
5. **Provider secrets** — signing/HMAC keys and API credentials. Compromise enables callback forgery and egress abuse. They are runtime configuration behind the adapter facade, never template rows, tenant rows, events, or logs (provider/channel ADR §2, §5).
6. **Template content** — subject/body forms and declared variable schemas; tenant-owned, cross-tenant readable would leak business structure.
7. **Provider raw payloads** — retained only as an integrity-referenced blob under the append-only receipt policy, never as domain fields (provider/channel ADR §2).

---

## Trust boundaries & new surfaces

Each crossing below is a *first-of-its-kind* surface for this kernel; that novelty is itself a risk multiplier — there is no prior hardening to inherit, only patterns to extend.

- **Caller → kernel (existing, hardened).** The authenticated request path: Principal + active Membership + server-validated tenant context + independent authorization/entitlement/purpose/quota gates. This is the one boundary the kernel already understands; Notification adds only new capabilities behind it.
- **Kernel → provider (NEW: egress).** A leased dispatch leaves the process and crosses a network to an external, untrusted party. The kernel has never before made an outbound call carrying tenant PII off-box. The provider is distrusted symmetrically to the inbound webhook (provider/channel ADR §3).
- **Provider → inbound callback → kernel (NEW: unauthenticated public endpoint).** A per-provider public endpoint with no session and no caller identity. Its authority derives *only* from a stored provider-message binding, never from the callback body — AUTH-D1 applied to a webhook. This is the kernel's first public unauthenticated surface.
- **Background worker actor (NEW: elevated cross-tenant role).** A long-lived process holding no request context, running the claim/lease under a narrow worker/system RLS role (`USING(true)`, SELECT/UPDATE on the content-free `notification_dispatch` columns and the provider-id lookup path). It is the kernel's first standing cross-tenant identity and its single largest new attack surface.

---

## Threat enumeration

A STRIDE/LINDDUN-style sweep kept concrete to bOPEN. Each row: threat → surface → the NOTIFY-INV invariant or existing kernel control that governs → mitigation → residual.

| # | Threat | Surface | Governing invariant / control | Mitigation | Residual |
|---|---|---|---|---|---|
| T1 | **Cross-tenant disclosure via the worker's elevated role** — the standing cross-tenant identity reads or writes another tenant's content | Worker actor | NOTIFY-INV-01; forced RLS; worker-role policy scope | Worker role is confined to content-free `notification_dispatch` columns + provider-id lookup; every **content touch** (render, snapshot, attempt-result) opens a *separate* connection under `tenant_session(tenant_id)`, resolving placement like a request; contexts never share a connection | A coding error touching content under the worker role instead of `tenant_session` bypasses RLS — must be a named test (forced-RLS on every background content touch) |
| T2 | **Existence oracle via status** — probing `notification.read`/`list` to learn whether an email/party exists | Caller → kernel | NOTIFY-INV-04; `resolve_context` identical-403 posture | Uniform tenant-safe refusals; status returns redacted destination, no body/variables; no "search by raw destination" capability; unresolved-recipient and unauthorized fail identically | Timing side-channels in resolution require constant-time-shaped refusal; residual until measured |
| T3 | **Existence oracle via callback responses** — forging callbacks to distinguish "known message" from "unknown" by reply differences | Inbound callback | NOTIFY-INV-04, -10 | Unknown id, wrong-provider/wrong-message binding, bad signature, stale timestamp, oversized body all refused **identically** — no body/status/timing difference discloses existence | Timing uniformity across the verify path must be tested, not assumed |
| T4 | **Enumeration via timing** — same as T2/T3 but through latency rather than response body | Caller & callback | NOTIFY-INV-04 | Fail-closed paths shaped to avoid early-exit timing tells; DB-clock, not content-dependent branching, on the refusal path | Micro-timing leakage is hard to fully erase; flagged as a residual to measure under load |
| T5 | **Callback forgery** — attacker posts a fabricated "delivered" to promote a message or fabricate truth | Inbound callback | NOTIFY-INV-10; AUTH-D1 | HMAC/signature + timestamp window + size/content-type limits verified on **raw bytes before parse**; authority from stored binding only | Provider-secret compromise defeats signature check — see T9; forgery resistance is only as strong as secret custody |
| T6 | **Callback replay** — re-sending a captured valid callback to double-process | Inbound callback | NOTIFY-INV-06, -12 | `(provider, provider_message_id, provider_event_id)` + replay id recorded append-only; redelivery maps to the same attempt, emits no second receipt/event; stale-timestamp and already-terminal transitions dropped | Replay within the timestamp window before first processing is bounded by window width — a tuning residual |
| T7 | **SSRF via callback URL / egress destination** — coercing the kernel into calling an attacker-chosen address | Kernel → provider / callback | Deferred-scope control (RESEARCH §9.3; both ADRs) | Outbound webhook delivery (tenant-controlled destinations) is **explicitly deferred** — the SSRF/DNS-rebinding/redirect vector is out of the first slice; provider egress targets are fixed adapter configuration, not tenant-supplied | Present only if egress is later enabled — must carry its own ADR with allow-listing before it exists |
| T8 | **Callback body claims tenant authority** — a `tenant_id`/account field in the callback body attempts to select the isolation context | Inbound callback | AUTH-D1; NOTIFY-INV-01 | The body tenant field is **inert**; `provider_message_id` → stored attempt is the sole source of `tenant_id`; receipt write opens `tenant_session(stored_tenant_id)` only after binding | None beyond an implementation regression; covered by a named refusal test |
| T9 | **Provider-secret leakage** — signing keys or API credentials surface in logs, events, domain state, or exports | All | NOTIFY-INV-13 | Secrets are runtime config behind the facade; never template/tenant rows or event fields; logs carry identifiers + safe hashes only; secret rotation uses a bounded auditable overlap window | Runtime secret store compromise is out of this model's scope (infra/ops); rotation limits blast radius |
| T10 | **Template / content injection** — header injection, unsafe link schemes, template-language injection, content confusion | Caller (template author) → render | NOTIFY-INV-05 | Channel-aware validation of headers/addresses/URLs/HTML/text/encodings; allowlisted link schemes + purpose-bound tokens; immutable published template versions; schema-validated variables; a template cannot declare itself mandatory | Renderer bugs remain possible — the render/validation path needs its own injection test suite |
| T11 | **PII over-retention or over-broadcast** — content or precise recipient appears in events, metrics, logs, or lives longer than needed | Events / metrics / logs / retention | NOTIFY-INV-13; RESEARCH §10.2, §11.2 | Events exclude raw destination, full content, secrets, raw payload; metrics carry no sensitive labels; per-class retention with tombstone/correlation preserved on purge; render snapshot/hash retained only as long as privacy policy allows | Retention constants are deferred to runbook ADRs — over-retention is a real risk until they are set and enforced |
| T12 | **Egress abuse** — using the send path as a spam cannon or to exfiltrate via crafted recipients | Kernel → provider | NOTIFY-INV-14, -02 | Per-tenant/purpose/recipient/provider quotas as independent loud-refusing gates; fairness-shaped claim; emergency suspension separate from quota; recipient must match a **verified** endpoint (CP-D-06) — raw destinations only via a specifically authorized flow | Outbound webhooks deferred (T7); abuse via legitimate providers bounded by quota tuning |
| T13 | **Compromised / rogue provider** — the provider returns malicious, oversized, or misleading responses | Kernel → provider | NOTIFY-INV-08; provider-distrust keystone; fail-closed posture | Adapter is a pure translation boundary: bounded canonical response, no vendor object into domain state; malformed/ambiguous → classified `unknown`, never a favorable state; a 200 is a handoff candidate, never `delivered` without an authenticated receipt | A provider that lies *plausibly* (fake `accepted`) is bounded to a handoff claim, not delivery truth; deeper provider trust is deferred to the provider ADR |
| T14 | **Log / metric label leakage** — otherwise-safe telemetry carries a tenant-identifying or recipient-identifying label | Logs / metrics / traces | NOTIFY-INV-13 | Metrics cover queued age, dispatch latency, outcome class, breaker/quota state **without** sensitive labels; logs carry ids, safe hashes, normalized reason codes only | Label hygiene is easy to regress; needs a lint/test guard on metric cardinality and label sets |
| T15 | **Append-only evidence erasure** — a cascade delete or direct update destroys attempt/receipt/render provenance | Storage | NOTIFY-INV-12 | `notification_attempt`/`_receipt` are INSERT+SELECT only with `ON DELETE RESTRICT`; corrections append a new observation, never overwrite (the migration-014 cascade lesson) | Superuser/DBA action outside the app is out of scope; app-path erasure is closed |
| T16 | **False "delivered" claim** — reporting provider acceptance (or a timeout) as human delivery/read/action | Worker / status / events | NOTIFY-INV-08, -15; the truth ladder | `accepted ≠ delivered ≠ read ≠ acted upon`; `accepted→delivered` is receipt-driven only; timeout is `unknown`, never `failed`/`delivered`; a notification result authorizes/advances no business workflow | `terminal_unknown` is an honest permanent ambiguity, not a bug — accepted as residual (exactly-once impossible) |

---

## Privacy & data minimization

- **Classification.** Message content (subject/body), template variables, and the resolved recipient endpoint are the high-sensitivity classes; delivery metadata (state, timing, outcome class, provider message id) is medium; safe hashes and reason codes are low. Each is minimized independently — the presence of a low-sensitivity metric never justifies carrying a high-sensitivity field alongside it.
- **What may appear where.** Events (`notification.*.v1`), metrics, logs, traces, and caches carry **only** safe metadata: identifiers, safe hashes, normalized outcome, latency, adapter profile, reason code. **Never** raw destination, subject/body, template variables, provider secrets, or raw provider payload. This is the same redaction posture the disposed Location and ContactPoint foundations apply to coordinates and endpoint values.
- **Status responses** return a redacted destination and no body/variables; there is no general "search by raw destination" capability, because that would itself be an enumeration oracle (T2).
- **Retention & deletion.** Notification metadata, render evidence, destination snapshot, attempts, receipts, audit, and provider raw data may each carry a *different* retention period. Purge preserves the required **tombstone/correlation** evidence so history is not silently rewritten (append-only, NOTIFY-INV-12). Concrete periods are deferred to the runbook ADR — their absence is a tracked residual, not a silent default.
- **Attachments/links** reference authorized Document versions; a prior link or access does **not** grant dispatch-time content permission — the service principal must obtain a purpose-bound, expiring authorized grant. Links use allowlisted schemes and purpose-bound tokens; bearer credentials are never rendered into content.
- **Support access** to content or recipient values is not ambient. It should be a **time-bounded, audited grant** — a distinct authorized act that appears in the audit trail, never a standing read for operators.

---

## Residual risks & explicitly deferred

- **Outbound webhook egress** — the SSRF / DNS-rebinding / redirect / tenant-controlled-destination boundary is deferred to its own ADR (T7). Not present in the first slice.
- **Production provider trust** — provider selection, credentials, residency, and the real-world trust of a concrete vendor are deferred (NOTIFY-D-04, NOTIFY-D-07); this model assumes the deterministic fake adapter only.
- **Exactly-once impossibility** — the design is at-least-once with honest ambiguity; `terminal_unknown` is the correct floor where a provider offers neither idempotency key nor reconciliation query. This is an accepted residual, not a defect (T16).
- **Timing side-channels** (T2/T3/T4) — uniform-response is specified; uniform-*timing* must be measured under load, not assumed.
- **Retention constants** (T11) — periods and purge cadence are deferred to the runbook ADR; over-retention is a live risk until they are set.
- **Metric label hygiene** (T14) — needs an enforced guard so a future label addition cannot leak tenancy/recipient identity.
- **Secret-store and DBA/superuser compromise** (T9/T15) — outside this model's application-layer scope; noted so the operational review owns them.
- **Dedicated-DB placement fan-out** — how the worker, callback endpoint, and evidence tables distribute across per-placement databases is an open topology decision (worker ADR) with its own isolation implications; must resolve before build.

Each deferred item requires its **own** decision record; none is resolved here.

---

## Refusal-posture summary

Everything below is refused **uniformly and tenant-safely** — a distinct safe reason code, no silent success, no enumeration oracle, no timing/response tell that discloses whether a Principal, Party, destination, template, or provider message exists:

- unauthenticated, unauthorized, missing-entitlement, disabled-module, prohibited-purpose, preference, suppression, and quota cases — each failing **independently** (NOTIFY-INV-02);
- cross-tenant, unresolved, unverified, expired, malformed, or wrong-purpose/channel recipient, and any implicit `principals.email` lookup (NOTIFY-INV-03);
- cross-tenant, draft/retired, stale, schema-mismatched, header-injecting, unsafe-link, or unsupported-locale template render (NOTIFY-INV-05);
- callback with bad signature, replay, stale timestamp, oversized/malformed body, wrong provider/message binding, unknown id, or invalid transition (NOTIFY-INV-10, -04);
- callback body attempting to assert tenant authority — inert; authority is the stored binding only (AUTH-D1);
- ambiguous/malformed provider response — classified `unknown`, fail closed, never a favorable state (NOTIFY-INV-08);
- quota/backpressure excess — refused **loudly** with a distinct retryable code, never silently dropped or queued unbounded (NOTIFY-INV-14).

---

## Clean-room note

Designed independently under AGENTS.md §6: standards and provider behavior are requirements sources only. No provider SDK, schema, template, callback format, or test was copied. The asset list, trust-boundary map, threat sweep, and mitigations were derived from the kernel's own patterns — forced RLS + `tenant_session`, `resolve_context` fail-closed identical-403, placement (`_connect_for_tenant`) mis-route uniform refusal, the AUTH-D1 header-cannot-create-authority rule, the append-only `ON DELETE RESTRICT` evidence discipline (migration-014 lesson), and the disposed Location/ContactPoint redaction of sensitive values — plus the RESEARCH invariants (NOTIFY-INV-01…16, §10 privacy), the REVIEW findings (privacy/threat model as a named successor artifact; AUTH-D1 applied to callbacks; the worker as new operational surface; anti-enumeration), and the two ADR drafts (worker/queue and provider/channel) — referenced for the surfaces they introduce, **not re-decided** here. Files consulted for grounding: `docs/01-product/MILE-4.2-notification-foundation-research.md`, `docs/01-product/MILE-4.2-notification-foundation-review.md`, `docs/01-product/MILE-4.2-notification-worker-queue-ADR-draft.md`, `docs/01-product/MILE-4.2-notification-provider-channel-ADR-draft.md`.

---

## Authority block

```yaml
document: notification-privacy-threat-model
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

> This document models privacy and threats only. It authorizes nothing, builds nothing, and selects no provider. A build — and any concrete provider — requires a separate operator authorization recorded first; Notification remains gated by DEC-P4-ENTRY §9.
