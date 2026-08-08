# MILE-4.2 — Notification foundation, research & design

**Document ID:** `RESEARCH-MILE-4.2-NOTIFICATION`  
**Version:** `1.0.0`  
**Status:** **Research — advisory. Current sequential research slice; buildable only on separate operator authorization.** Notification remains gated by [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §9.  
**Issued:** 2026-08-05  
**Owner:** Architecture & Engineering Authority  
**Raised by:** Codex (agent, advisory role) — research and planning only; no approval authority  
**Entry evidence:** The operator explicitly entered Notification research on 2026-08-05 after the Location research slice.  
**Governing:** `AGENTS.md` §§2, 7–15; [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md); [`CAPABILITY-MATRIX`](CAPABILITY-MATRIX.md)  
**Dependent artifacts:** Future `BOPEN-NOTIFY-001`, recipient/contact contract, accepted work package, provider/channel ADR, privacy and threat model, API/event contracts, operations runbooks, test matrix, and EBIV evidence  
**Clean-room:** Standards and provider behavior are requirements sources only. No provider SDK, schema, template, migration, or test is copied into bOPEN.

---

## 1. Executive summary

The recommended foundation is a **provider-neutral Transactional Notification Orchestrator**. It
accepts an authorized and idempotent request or eligible domain event, resolves a recipient through a
governed contract, applies purpose/channel/preference/suppression policy, renders a published template
version, queues delivery durably, invokes a replaceable provider adapter, records attempts and
receipts, reconciles ambiguous outcomes, and exposes tenant-safe status and operational evidence.

It is not marketing automation, campaign management, chat, a contact master, an authentication
system, a workflow approval mechanism, or proof that a human read or acted on a message. The first
slice should support **one recipient and transactional email** through one contract-tested provider
adapter plus a deterministic fake. SMS, push, outbound webhooks, bulk campaigns, and in-app inboxes
remain independently governed later slices.

A material dependency is unresolved: the repository does not yet expose a shared Party contact-point
contract suitable for recipient resolution. Notification MUST NOT silently use `principals.email` as
a delivery destination merely because it is an authentication identifier. A future
`NotificationRecipientResolver` contract must bind the source, verification, purpose, tenant,
effective interval, and authority for each resolved endpoint before implementation.

This document ends at research. The operator will review it under the established pattern. Calendar
research does not begin until that review step is closed or the operator explicitly directs it.

## 2. Research question and method

### 2.1 Research question

What is the smallest reliable, secure, multi-tenant notification foundation that lets all bOPEN
products send transactional notices without duplicating provider integrations, secrets, retry logic,
templates, preferences, delivery evidence, or privacy controls—and without turning bOPEN into a
marketing or communications product?

### 2.2 Method and source hierarchy

The research used, in order:

1. approved bOPEN platform/foundation boundaries and current repository behavior;
2. CloudEvents 1.0.2 for interoperable event metadata concepts;
3. SMTP (RFC 5321) for the distinction between accepting transport responsibility and final outcome;
4. RFC 3464 for delayed, failed, delivered, relayed, and expanded delivery-status semantics;
5. RFC 5322 for Internet email message-format requirements;
6. RFC 9110 for HTTP retry signaling used by provider APIs;
7. architecture inference and recommendations, clearly separated from those facts.

CloudEvents informs the trigger/envelope boundary; it does not define Notification delivery state or
guarantee exactly-once processing. External sources remain informative until adopted by an approved
bOPEN contract.

## 3. Scope

### 3.1 In scope

- authorized notification requests and governed subscriptions to eligible domain events;
- purpose, urgency, channel, locale, correlation, idempotency, and requested-delivery constraints;
- versioned templates with declared variables and publication lifecycle;
- governed recipient resolution and immutable per-notification destination snapshots;
- preference, suppression, mandatory-notice, tenant policy, and quota decision seams;
- durable queue, delivery-attempt state, bounded retry, dead-letter, reconciliation, and receipts;
- provider-neutral email adapter and deterministic fake adapter;
- tenant-safe status, cancellation before dispatch, operator retry/reconciliation, and audit;
- RLS, authorization, entitlement/module separation, privacy, retention, events, metrics, migration,
  backup/restore, and evidence controls;
- future channel adapter seams without enabling the channels themselves.

### 3.2 Out of scope

- marketing campaigns, journeys, segmentation, promotions, experiments, lead scoring, and analytics;
- bulk unsolicited messages, purchased lists, and cross-tenant audiences;
- owning Party/contact master data or treating Principal authentication fields as contact consent;
- chat, inbox collaboration, comments, support tickets, and social messaging;
- business/workflow decisions, approvals, state transitions, timers, and escalation policy;
- SMS, mobile/web push, WhatsApp/social, voice, and outbound webhook delivery in the first slice;
- mailing-list expansion, multi-recipient batches, CC/BCC, and provider-side mutable templates;
- promising exactly-once external delivery, final inbox placement, human receipt, reading, or action;
- using notification success/failure as authorization or completion evidence for a business action;
- provider selection, credentials, billing, sender-domain production readiness, and DNS configuration.

### 3.3 Assumptions

- Tenant is the data, policy, quota, and isolation boundary.
- Party is the intended source of business-recipient identity/contact relationships, but the exact
  contact-point contract is a pre-build decision.
- The existing bOPEN event envelope/outbox patterns are requirements inputs; Notification needs its
  own approved dispatch/outbox/inbox contract rather than silently reusing a usage-specific table.
- P0 remains a modular monolith with durable PostgreSQL state and provider adapters.
- The first slice delivers one logical notification to one resolved recipient on one channel.
- A platform invitation flow may be used as a reference fixture only if it passes its own
  authorization and anti-enumeration controls; it does not make authentication email a universal
  notification endpoint.

## 4. Current facts and interpretations

| Class | Statement |
| :--- | :--- |
| Repository fact | `CAPABILITY-MATRIX` defines Notification Engine as transactional Email/SMS/Push/Webhook alerts, depending on Events and Party, for all satellite products. |
| Repository fact | Notification remains gated by `DEC-P4-ENTRY` §9. Research does not authorize implementation or a channel/provider. |
| Repository fact | The current repository has usage-specific outbox behavior, but no approved general Notification dispatch contract or shared Party contact-point contract was found. |
| Repository fact | `principals.email` exists for account/identity behavior; context code explicitly prohibits trusting an email claim for subject binding. |
| External fact | CloudEvents standardizes common event metadata for interoperability; it does not define notification delivery truth. |
| External fact | SMTP acceptance transfers responsibility to deliver or report failure, but failure can still occur after acceptance. |
| External fact | RFC 3464 distinguishes delivery-status actions including delayed, failed, delivered, relayed, and expanded. |
| Interpretation | `provider_accepted` must be distinct from `transport_delivered`, and neither proves human read/action. |
| Recommendation | Build a transactional orchestrator with explicit recipient resolution, immutable template/render provenance, durable attempts, and replaceable adapters. |

The approved matrix names future channels. It does not require all four channels in the first slice or
permit channel-specific security concerns to be hidden behind one undifferentiated “send” function.

## 5. Domain distinctions

| Concept | Normative proposal | Must not be confused with |
| :--- | :--- | :--- |
| `NotificationRequest` | Authorized intent to notify one recipient for one governed purpose | Proof of provider acceptance or delivery |
| `Notification` | Durable tenant-owned orchestration record | Source domain event, workflow state, or message body alone |
| `TemplateVersion` | Immutable published rendering contract for channel/locale/variables | Provider-side mutable template or authorization policy |
| `RecipientRef` | Reference passed to a governed resolver | Raw unverified destination or Principal identity |
| `RecipientSnapshot` | Minimal resolved channel endpoint and provenance frozen for this send | Party/contact master or continuing consent |
| `DeliveryAttempt` | One bounded provider invocation and observed outcome | One notification or proof of human receipt |
| `DeliveryReceipt` | Authenticated provider status observation | Independently verified human behavior |
| Preference | Recipient/tenant choice for eligible purpose/channel | Authorization, entitlement, or mandatory-notice rule |
| Suppression | Explicit prohibition or safety block on an endpoint/purpose/channel | Ordinary retryable provider failure |
| Domain event | Business fact that may trigger a request | Instruction that inherently grants permission to notify |

The engine MUST preserve these truth levels:

```text
accepted by bOPEN
  != accepted by provider/SMTP receiver
  != transport delivered
  != placed in inbox/displayed by device
  != read by a human
  != acted upon
```

## 6. Options and recommendation

| Option | Boundary integrity | Reliability | Portability | Privacy/control | P0 complexity | Disposition |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| Full omnichannel marketing platform | 1 | 4 | 2 | 2 | 1 | Reject — wrong product boundary |
| Each product invokes providers directly | 1 | 2 | 1 | 1 | 4 | Reject — duplicate secrets, retry, policy, audit, and status semantics |
| Provider-specific notification service | 3 | 4 | 1 | 3 | 4 | Reject — contracts inherit vendor semantics and lock-in |
| Transactional orchestrator + recipient/provider adapters | 5 | 5 | 5 | 5 | 4 | **Recommend** |

The recommendation accepts at-least-once internal processing with idempotency and explicit ambiguous
outcomes. Claiming exactly-once external delivery would be stronger than the mechanisms can prove.

## 7. Proposed model

```text
DomainEvent / authorized command
  -> NotificationRequest
  -> policy + idempotency + quota
  -> RecipientResolver -> RecipientSnapshot
  -> TemplateVersion -> RenderSnapshot
  -> Notification
      ├─ DeliveryAttempt[] -> ProviderAdapter
      ├─ DeliveryReceipt[]
      └─ NotificationHistory[]
```

### 7.1 `NotificationRequest` and `Notification`

Proposed fields include immutable IDs, `tenant_id`, source/correlation/context references, purpose,
channel, recipient reference, template/version request, locale, priority, idempotency key, schedule
constraint, lifecycle, revision, and timestamps. Arbitrary caller-supplied message bodies are not the
default contract; callers select a published template and schema-validated variables.

One notification has one recipient/channel in the first slice. A product that needs multiple
recipients creates separately authorized/idempotent requests. Provider batching MAY optimize dispatch
later without changing logical identity, isolation, status, or per-recipient evidence.

### 7.2 `Template` and `TemplateVersion`

Proposed fields:

- tenant-owned template identity, governed code, purpose, channel, locale, lifecycle, revision;
- immutable published versions containing subject/body form, declared variable JSON schema, content
  classification, allowed link/attachment behavior, renderer version, and change reason;
- draft → published → retired lifecycle; published versions are immutable;
- deterministic locale fallback decided before request acceptance, not silently by provider;
- render snapshot/hash retained according to privacy policy so an attempt can be explained without
  retaining sensitive full content longer than necessary.

Header values, addresses, URLs, HTML/text, encodings, and line breaks require channel-aware validation
to prevent header injection, unsafe schemes, template injection, and content confusion. Provider-side
templates may be an adapter optimization only if the bOPEN version remains the source of truth and
conformance proves identical meaning.

### 7.3 Recipient resolution

```text
RecipientRef + purpose + channel + tenant/context
  -> NotificationRecipientResolver
  -> verified RecipientSnapshot or explicit refusal
```

The resolver response SHOULD include endpoint type/value, Party/contact reference or explicit
invitation destination provenance, verification/effective state, locale, preference/suppression
inputs, and a resolver version. It MUST bind to the same tenant and authorized purpose.

Rules:

- `principals.email` MUST NOT become a universal destination by implicit lookup;
- a Party relationship does not itself authorize contact for every purpose;
- raw destination input is accepted only by a specifically authorized flow whose contract owns its
  validation and purpose (for example, an invitation), never by the generic send endpoint;
- the snapshot is immutable evidence for one notification but is not a new contact master;
- destination values are encrypted or tokenized where practical and redacted in logs/status/events;
- contact verification, consent, preference, suppression, and mandatory-notice policy remain
  distinct decisions.

### 7.4 Notification lifecycle

```text
accepted -> queued -> dispatching
   |           |          |
   |           |          +-> provider_accepted -> delivered | delayed | failed
   |           +------------> suppressed | cancelled | failed
   +-------------------------> suppressed | cancelled

ambiguous provider outcome -> unknown -> reconciled_to_known | terminal_unknown
```

Cancellation is best-effort and only accepted before an irreversible provider handoff. A completed
or provider-accepted attempt cannot be represented as unsent merely because cancellation was later
requested.

### 7.5 `DeliveryAttempt` and `DeliveryReceipt`

Attempt fields include attempt number, adapter/provider profile, request fingerprint, provider
idempotency reference where supported, start/end, classified outcome, safe response code, next retry,
and correlation. Receipts include authenticated provider message binding, provider event ID,
provider-observed time, normalized status, raw-payload integrity reference/retention policy, and
processing result.

Attempt/receipt/history rows are append-only. Corrections append a new observation; they do not erase
prior claims.

## 8. Policy, preferences, and suppression

Notification purposes SHOULD be governed, versioned codes, for example:

- mandatory security/operational notice;
- transactional action/result notice;
- optional transactional update.

Marketing purpose is excluded. A template cannot declare itself mandatory. The governing product or
platform policy decides whether a notice may bypass an ordinary preference, and that decision remains
auditable and reviewable.

The policy decision includes principal/service actor, membership and active tenant context,
authorization, entitlement/module state, purpose, recipient relationship, channel, preference,
suppression, lifecycle, time, quota, content classification, and approval state where required.

Suppression sources may include invalid/unverified endpoint, hard bounce, complaint, provider block,
tenant emergency suspension, recipient preference, or security policy. Retry must not bypass a
suppression. Removing a suppression is a separate authorized/audited action, not a side effect of a
new request.

## 9. Reliability and provider boundary

### 9.1 Durable flow

```text
source transaction/outbox or authenticated API
  -> inbox/dedup
  -> notification transaction
  -> pending dispatch claim
  -> provider call outside DB transaction
  -> attempt result transaction
  -> receipt/reconciliation
  -> status events + audit + metrics
```

- Where source and Notification share a transaction, an outbox records intent atomically. Across
  services/databases, an inbox/dedup contract prevents duplicate request creation.
- Provider network calls never hold a tenant database transaction open.
- Workers use leases/claims with expiry and fencing so crashes do not create concurrent unbounded
  attempts.
- Retry policy classifies retryable, terminal, throttled, and unknown outcomes; uses bounded
  exponential backoff/jitter, provider `Retry-After` where valid, attempt/age ceilings, and dead-letter
  visibility.
- A timeout after sending may be `unknown`, not `failed`. Blind retry is forbidden unless provider
  idempotency or reconciliation makes duplication safe enough under the approved policy.
- Provider acceptance means responsibility/handoff, not final delivery. DSN/provider receipts may
  later update delayed, failed, relayed, or delivered transport state.
- Exactly-once external delivery is not claimed. Idempotency, provider keys, reconciliation, and
  duplicate-tolerant message design reduce but cannot erase all uncertainty.

### 9.2 Provider adapter

The adapter contract includes:

- canonical rendered message and sender profile reference;
- one recipient snapshot and request/idempotency/fingerprint references;
- classified synchronous response, provider message ID, retry hint, and safe diagnostic;
- receipt/callback verification and normalization;
- timeout, connection failure, rate limit, authentication/configuration failure, malformed response,
  partial/ambiguous response, and provider outage semantics;
- secrets, network egress, TLS, residency, data retention, quotas, cost, metrics, and revocation seams.

Provider selection requires an ADR. Credentials are runtime secrets, never template/tenant rows or
events. Platform-selected sender/provider is the recommended first profile; tenant bring-your-own
provider is a later control-plane slice.

### 9.3 Callback security

- callbacks use a provider-specific authenticated adapter with signature/key validation, timestamp
  window, replay ID, payload limits, content type/schema, and raw-byte verification order;
- the server resolves provider message ID to stored tenant/attempt context; callback tenant fields do
  not establish context;
- unknown, duplicate, stale, wrong-provider, wrong-message, invalid-transition, or bad-signature
  callbacks are refused and tenant-safe;
- secret rotation accepts only an explicit bounded overlap and is auditable;
- public callback endpoints are rate-limited and must not disclose whether a provider message or
  recipient exists.

Outbound webhook notifications are deferred because they add SSRF, DNS rebinding, redirect, egress,
signature, response-limit, and tenant-controlled destination risks beyond transactional email.

## 10. Security, tenancy, privacy, and operations

### 10.1 Execution chain and tenant isolation

An authenticated **Principal** or governed service principal with active **Membership** operates
through server-validated **active tenant context**. **Authorization**, **entitlement**, module
availability, purpose policy, recipient relationship, preference, suppression, quota, and lifecycle
are separate gates. Commercial access and action permission remain distinct.

Every tenant-owned table carries immutable `tenant_id`, tenant-inclusive foreign keys/uniqueness,
forced RLS, default-deny policies, and fail-closed missing/ambiguous/inactive context. All tables must
remain aligned between the repository's tenant-scoped inventory and trial→paid `COPY_ORDER`, with
parent-before-child copy and live migration evidence.

Cross-tenant disclosure through direct IDs, status, templates, recipient lookup, preferences,
suppression, worker claims, callbacks, provider IDs, retries, exports, analytics, events, logs,
metrics, traces, caches, timing, and error differences is zero.

### 10.2 Content and destination privacy

- Destination, template variables, rendered content, provider raw response, links, and attachments
  are classified and minimized independently.
- Generic status returns redacted destination and no body/variables. Search by raw destination is not
  a general capability.
- Logs/events/metrics contain identifiers, safe hashes, normalized outcome, latency, adapter profile,
  and reason code—not credentials, tokens, full destination, subject/body, or provider raw payload.
- Retention may differ for notification metadata, render evidence, destination snapshot, attempts,
  receipts, audit, and provider data. Purge preserves the required tombstone/correlation evidence.
- Attachments reference authorized Document versions. A Document link or prior access does not grant
  dispatch-time permission; the service principal must obtain a purpose-bound, expiring authorized
  content grant.
- Links use allowlisted schemes and purpose-bound tokens; secrets and bearer credentials are never
  rendered into ordinary message content.

### 10.3 Abuse and fairness

- Per-tenant, purpose, recipient, channel, template, actor, and provider quotas protect shared
  capacity; platform emergency suspension remains separate from ordinary entitlement.
- Idempotency and anti-enumeration prevent retry/response differences from revealing account or
  endpoint existence.
- High-volume operations, template publication, preference override, suppression removal, retry, and
  export require separate capabilities and audit.
- Notification status MUST NOT expose whether a named email belongs to an existing Principal/Party.
- Workers schedule fairly so one tenant/provider outage cannot starve others.

### 10.4 Recovery and observability

- Backup/restore includes notification, template version, snapshot, attempt, receipt, suppression,
  history, and dedup/lease state with integrity/reconciliation evidence.
- Trial→paid migration freezes tenant writes at the existing data chokepoint; copy coverage and
  ordering must include every Notification table.
- Metrics cover accepted, suppressed, queued age, dispatch latency, provider acceptance, delayed,
  delivery/failure, unknown, retry, dead-letter, callback rejection, quota, and per-tenant fairness
  without sensitive labels.
- Runbooks cover provider outage/auth failure, key rotation, sender suspension, callback attack,
  backlog drain, duplicate/unknown outcome, hard-bounce suppression, restore, and emergency stop.

## 11. Proposed capabilities, APIs, and events

### 11.1 Capabilities

- `notification.request`;
- `notification.read`, `notification.list`;
- `notification.cancel`;
- `notification.retry`, `notification.reconcile`;
- `notification.template.create`, `notification.template.publish`,
  `notification.template.retire`;
- `notification.preference.manage`, `notification.suppression.manage`;
- `notification.export`;
- `notification.provider.manage` — platform/operator scope only in the first profile.

Stable errors must distinguish invalid input/context, unauthenticated, unauthorized, missing
entitlement/module, recipient unresolved/unverified, suppressed, template unpublished/invalid,
idempotency conflict, quota, invalid lifecycle, stale revision, cancellation too late, provider
retryable/terminal/unknown, and callback invalid—without revealing recipient/account existence.

### 11.2 Events

- `notification.accepted.v1`;
- `notification.suppressed.v1`;
- `notification.dispatched.v1`;
- `notification.provider_accepted.v1`;
- `notification.delivery_delayed.v1`;
- `notification.transport_delivered.v1`;
- `notification.failed.v1`;
- `notification.terminal_unknown.v1`;
- `notification.cancelled.v1`.

Events use the bOPEN envelope and transactional outbox. They exclude raw destination, full rendered
content, provider secrets, and unaudited provider payload. Subscription rules prevent Notification
status events from recursively generating themselves. Consumers deduplicate and tolerate replay and
out-of-order receipts within the contract's stated ordering boundary.

## 12. Proposed first implementation slice — not authorized

1. Resolve the recipient/contact dependency and freeze `NotificationRecipientResolver` without
   making `principals.email` the default destination.
2. Freeze `BOPEN-NOTIFY-001`, purpose/channel vocabulary, request/status/error schemas, template and
   recipient contracts, idempotency/retry/unknown rules, privacy/retention, capabilities, events, and
   provider adapter.
3. Add tenant-scoped notification, template/version, recipient snapshot, attempt, receipt,
   suppression/preference, history, inbox/dedup, lease, and outbox state with forced RLS,
   append-only controls, migration/rollback/compensation, and copy ordering.
4. Implement one-recipient transactional email requests, policy evaluation, deterministic rendering,
   queue/worker, provider invocation, status, cancellation-before-handoff, retry/dead-letter,
   reconciliation, callback ingestion, audit, and events.
5. Provide a deterministic fake adapter and one selected email provider adapter behind identical
   contract tests. Provider ADR and secrets/operations evidence are required before production use.
6. Implement template draft/publish/retire, locale fallback, variable schema validation, content
   safety, and immutable render provenance.
7. Add tenant isolation, independent authorization gates, anti-enumeration, idempotency, concurrency,
   worker crash/lease, provider ambiguity, callback forgery/replay, quotas/fairness, privacy,
   migration, backup/restore, audit, outbox replay, and dead-letter tests.
8. Validate two bounded flows: an authorized platform invitation using an explicit destination, and
   one Party-resolved transactional product notice after the contact contract exists.
9. Submit maker evidence against an exact candidate for independent EBIV ballot and separate operator
   disposition.

Deferred: SMS, push, webhooks, in-app inbox, bulk/multi-recipient, provider failover, tenant BYO
provider, marketing/consent management, attachment delivery, and delivery/read analytics.

## 13. Required invariants and defensive verification

| ID | Invariant | Required refusal/acceptance evidence |
| :--- | :--- | :--- |
| `NOTIFY-INV-01` | Tenant isolation | Wrong/missing/inactive context cannot read, infer, request, retry, cancel, template, resolve, callback, export, cache, or observe foreign notifications |
| `NOTIFY-INV-02` | Independent gates | Unauthenticated, unauthorized, missing-entitlement, disabled-module, expired-grant, prohibited-purpose, preference, suppression, and quota cases fail independently |
| `NOTIFY-INV-03` | Recipient integrity | Cross-tenant, unresolved, unverified, expired, malformed, wrong-purpose/channel endpoint and implicit Principal-email lookup are refused |
| `NOTIFY-INV-04` | Anti-enumeration | Response body/status/timing/log/audit differences do not reveal whether a Principal, Party, destination, template, or provider message exists |
| `NOTIFY-INV-05` | Template integrity | Cross-tenant, draft/retired, stale, schema-mismatched, header-injecting, unsafe-link, and unsupported-locale render is refused |
| `NOTIFY-INV-06` | Idempotency | Duplicate API/event/inbox/callback creates no unintended duplicate notification, attempt, receipt, history, or status event |
| `NOTIFY-INV-07` | Attempt fencing | Concurrent/expired worker lease and stale revision cannot dispatch or overwrite a newer attempt |
| `NOTIFY-INV-08` | Outcome truth | Provider acceptance is never reported as human delivery/read/action; delayed/failed/unknown states remain distinct |
| `NOTIFY-INV-09` | Retry safety | Terminal/suppressed/cancelled outcome is not retried; ambiguous outcome is reconciled or safely idempotent before retry |
| `NOTIFY-INV-10` | Callback trust | Bad signature, replay, stale timestamp, oversized/malformed body, wrong provider/message binding, unknown ID, and invalid transition are refused |
| `NOTIFY-INV-11` | Cancellation truth | Cancellation after provider handoff cannot rewrite the message as unsent; pre-handoff cancellation prevents dispatch |
| `NOTIFY-INV-12` | Append-only evidence | Direct update/delete and parent cascade cannot erase attempts, receipts, render provenance, or history |
| `NOTIFY-INV-13` | Privacy/secrets | Logs, errors, events, metrics, status, caches, and exports omit credentials, tokens, full endpoints, bodies, variables, and raw provider payload beyond authorized scope |
| `NOTIFY-INV-14` | Fairness/abuse | Tenant/purpose/recipient/provider quota refuses excess loudly without starving other tenants or bypassing emergency suspension |
| `NOTIFY-INV-15` | Workflow boundary | Notification request/result cannot grant authorization or advance/complete a business workflow by itself |
| `NOTIFY-INV-16` | Failure/recovery | Provider outage, partial response, worker crash, DB failure, outbox replay, dead-letter, backup/restore, and trial→paid migration preserve status/evidence and cross-tenant denial |

Each proposition must trace to a named executed test at an exact commit/tree. Live PostgreSQL is
required for RLS, lease/concurrency, append-only/cascade, outbox/inbox, migration, and recovery claims.
Real provider and callback evidence is required before production adapter qualification. A fake
adapter proves only owned orchestration/contract behavior. Unknown cross-tenant or ambiguous-delivery
behavior keeps the exit gate closed.

## 14. Risks and unresolved decisions

| ID | Decision/risk | Recommendation before authorization |
| :--- | :--- | :--- |
| `NOTIFY-D-01` | Recipient/contact source | Freeze Party ContactPoint or another owned resolver contract; never default to `principals.email` |
| `NOTIFY-D-02` | Reference flows | Use authorized invitation + one Party-resolved product notice; preserve anti-enumeration |
| `NOTIFY-D-03` | First channel | Transactional email only; defer SMS/push/webhook/in-app |
| `NOTIFY-D-04` | Provider | Select through ADR covering residency, retention, cost, quotas, secrets, sender/domain setup, callback security, SLA, revocation, and replacement |
| `NOTIFY-D-05` | Purpose/preference model | Define mandatory vs transactional vs optional; template cannot self-override preference |
| `NOTIFY-D-06` | Delivery truth | Adopt explicit bOPEN normalized states; provider accepted/delivered never implies human read/action |
| `NOTIFY-D-07` | Idempotency and unknown outcome | Define key scope, dedup window, provider key support, reconciliation, retry/age ceilings, and terminal-unknown operations |
| `NOTIFY-D-08` | Template/render ownership | bOPEN published version is authoritative; define locale fallback, renderer, safe HTML/text, and provider-template conformance |
| `NOTIFY-D-09` | Retention/privacy | Set separate periods for metadata, endpoint snapshot, render evidence, attempts, receipts, audit, and provider raw data |
| `NOTIFY-D-10` | Outbox/inbox topology | Define a general auditable event/dispatch contract; do not overload the usage-specific outbox silently |
| `NOTIFY-D-11` | Quotas and emergency stop | Define tenant/provider/purpose fairness, backpressure, operational suspension, and recovery |
| `NOTIFY-D-12` | Attachments and links | Defer or require purpose-bound Document access and token rules; never inherit permission from a link |
| `NOTIFY-D-13` | Provider callback public boundary | Define verification, replay, rotation, rate limits, privacy, raw-body retention, and incident response |
| `NOTIFY-D-14` | Status/search/export | Define redaction and capabilities so endpoints/account existence cannot be enumerated |

`NOTIFY-D-01` is a pre-build dependency. The other decisions must be resolved or explicitly deferred
without silent implementation defaults.

## 15. Required successor artifacts and exit gates

Before implementation:

1. operator review of this research closes the sequential research step without a blocking boundary
   defect;
2. a recipient/contact-point or `NotificationRecipientResolver` contract is accepted;
3. operator records a bounded Notification authorization in `DEC-P4-ENTRY` or its governed successor;
4. `NOTIFY-D-01` through `NOTIFY-D-14` are resolved or explicitly deferred;
5. `BOPEN-NOTIFY-001`, provider/channel ADR, API/error/event/template schemas, privacy/threat model,
   migration/rollback/compensation, operations runbooks, test matrix, and work package are frozen;
6. any material provider, egress, public callback, data-placement, or trust-boundary change receives
   the required ADR and architecture baseline first;
7. maker, eligible independent verifier, candidate anchors, evidence paths, and stop conditions are
   named.

Implementation exit requires executed acceptance/refusal tests, live RLS/concurrency/migration and
backup/restore evidence, real provider/callback conformance, repository/clean-room checks,
traceability, independent EBIV ballot, and operator disposition. Release, provider production
configuration, sender activation, deployment, and production activation remain separate.

## 16. Source register

Retrieved 2026-08-05. External standards are informative requirements sources unless a future
approved bOPEN artifact explicitly adopts a requirement.

| Source | Evidence class | Use in this research |
| :--- | :--- | :--- |
| [`CAPABILITY-MATRIX`](CAPABILITY-MATRIX.md) | Approved repository specification | Foundation purpose, dependencies, future channels, and consumers |
| [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §9 | Repository authority record | Current Notification gate status |
| [CloudEvents specification 1.0.2](https://github.com/cloudevents/spec/tree/v1.0.2) | CNCF specification | Common event metadata and trigger-envelope comparison |
| [RFC 5321 — SMTP](https://datatracker.ietf.org/doc/html/rfc5321) | IETF standard | Provider/receiver acceptance responsibility and post-acceptance failure distinction |
| [RFC 3464 — Delivery Status Notifications](https://datatracker.ietf.org/doc/html/rfc3464) | IETF standard | Delayed/failed/delivered/relayed status vocabulary and receipt security considerations |
| [RFC 5322 — Internet Message Format](https://datatracker.ietf.org/doc/html/rfc5322) | IETF standard | Email message-format and header requirements source |
| [RFC 9110 — HTTP Semantics](https://datatracker.ietf.org/doc/html/rfc9110) | IETF standard | Provider HTTP retry signaling, including `Retry-After` |

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
