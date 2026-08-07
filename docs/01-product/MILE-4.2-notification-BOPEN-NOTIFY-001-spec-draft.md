# BOPEN-NOTIFY-001 — Notification foundation contract (DRAFT)

**STATUS: DRAFT / PROPOSED — NOT AUTHORIZED, NOT IN FORCE. Notification remains gated by DEC-P4-ENTRY §9. This spec authorizes nothing and builds nothing; it selects no provider and declares no completion. A build needs a separate operator authorization recorded first.**

---

## Controlled-document metadata

| Field | Value |
|---|---|
| **Document ID** | `BOPEN-NOTIFY-001` (proposed; pending governance ID-registry ratification) |
| **Version** | `1.0.0-draft` |
| **Owner** | bOPEN Agentic SE — Notification (Motor authoring; Codex independent reviewer) |
| **Issued** | 2026-08-06 |
| **Status** | DRAFT / PROPOSED — gated by DEC-P4-ENTRY §9 |
| **Governing artifacts** | DEC-P4-ENTRY §9; `RESEARCH-MILE-4.2-NOTIFICATION`; `REVIEW-MILE-4.2-NOTIFICATION`; AGENTS.md §6 (clean-room) |
| **Dependent / paired artifacts** | `ADR-NOTIFY-WQ` (worker/queue — tables, dispatch state machine, lease/fence, evidence split — **referenced, not re-decided**); `ADR-NOTIFY-PROVIDER` (adapter facade, channel→capability, callback obligations — **referenced, not re-decided**); Notification privacy & threat model; API/error/event/template schemas; retention rules; migration/rollback plan; ops runbooks; test matrix; EBIV evidence |
| **Evidence refs** | the four artifacts above; kernel files named in the Clean-room note |

This spec fixes the **foundation contract** — domain entities, the tenant-facing lifecycle projection, capabilities, the contract-level API surface, the stable error and event catalogues, and the template model. Mechanism (outbox, fenced lease, dispatch state machine, evidence-table split, adapter internals, callback verification order) is **owned by the paired ADRs and only referenced here**.

---

## 1. Domain entities and relationships

Six contract entities. Each tenant-owned table carries immutable `tenant_id`, tenant-inclusive composite FKs, forced RLS, and default-deny; append-only tables carry `ON DELETE RESTRICT` (the migration-014 lesson). Physical shapes are owned by `ADR-NOTIFY-WQ` §1; this section fixes their **contract identity and relationships**, not their columns.

- **`Notification`** — the durable tenant-owned orchestration record and the unit of logical identity: `{notification_id, tenant_id, purpose_code, channel, template_version_ref, recipient_snapshot_ref, lifecycle_state, revision, correlation_id, idempotency_key, timestamps}` with `UNIQUE(tenant_id, idempotency_key)`. One notification = **one recipient, one channel** (first slice). It is *not* the source event, the message body, or proof of anything downstream.
- **`Dispatch`** — the claimable send-window record (one-to-one with `Notification` in the first slice). Its `status` machine (`pending/leased/sending/reconciling/done/dead`), lease/fence columns, `send_key`, and `provider_id`/`provider_profile_version` binding are **owned by `ADR-NOTIFY-WQ`** and referenced here as the mechanism that projects the logical lifecycle (§2). Content-free by construction.
- **`Attempt`** — append-only, once-written-at-finalization per-attempt evidence (`attempt_no`, `provider_profile`, `provider_idempotency_ref`, `classified_outcome ∈ {provider_accepted, retryable_failed, terminal_failed, unknown}`, `safe_code`, `provider_message_id`, timing). Corrections append; they never overwrite.
- **`Receipt`** — append-only provider-observed transport truth (provider event id, provider-observed time, normalized transport status, raw-payload integrity ref, `applied|superseded|conflicting` projection marker). A receipt is a **candidate**, never self-promoting.
- **`TemplateVersion`** — the immutable published rendering contract (§3). `Notification.template_version_ref` binds the exact version rendered.
- **`RecipientSnapshotRef`** — a reference to the minimal, immutable resolved endpoint (`{endpoint_type, endpoint_value, purpose, party_id, resolved_at}`) produced by the Party ContactPoint resolver (`ContactPointRepository.resolve()`, migration 019). It is **evidence, not a contact master**. Per `ADR-NOTIFY-WQ` §10 the snapshot is **re-resolved at the start of each attempt** under `tenant_session`, bounded by a resolve→handoff freshness ceiling, and never carried across a retry. Notification stores the *reference*; the endpoint value is minimized/redacted everywhere else.

```
DomainEvent / authorized command
  → Notification (idempotency + purpose/preference/suppression + quota gates)
      ├─ RecipientSnapshotRef      (ContactPoint resolver, per-attempt)
      ├─ TemplateVersion           (immutable, pre-resolved locale)
      └─ Dispatch                  (ADR-NOTIFY-WQ)
             ├─ Attempt[]          (append-only)
             └─ Receipt[]          (append-only, receipt-driven ladder)
```

---

## 2. Notification lifecycle state machine (the tenant-facing projection)

The **dispatch** state machine is owned by `ADR-NOTIFY-WQ` §4 (D-EV-2). This section fixes the **logical `Notification.lifecycle_state`** that a caller sees — a *monotonic projection* computed from dispatch/attempt/receipt evidence. It **never regresses**, and once terminal it does not move (INV-11).

| State | Entered when | Terminal? | Projection source |
|---|---|---|---|
| `accepted` | request admitted: idempotency checked, purpose/preference/suppression passed, quota token reserved, dispatch enqueued | no | enqueue txn |
| `dispatching` | dispatch `leased`/`sending` | no | dispatch status |
| `suppressed` | admission-time policy prohibition (suppression/preference/prohibited purpose) | **yes** | policy gate |
| `cancelled` | pre-handoff cancellation accepted | **yes** | cancel op |
| `provider_accepted` | attempt `provider_accepted` (2xx + message id) — **a handoff, never delivery** | no | attempt |
| `delivered` | authenticated **receipt** advances the ladder | **yes** | receipt only |
| `delayed` | transient receipt (`delayed`); does not terminate | no | receipt |
| `failed` | attempt `terminal_failed`, or dead-letter after ceilings | **yes** | attempt / dead-letter |
| `unknown` | attempt `unknown`; awaiting reconciliation | no | attempt |
| `terminal_unknown` | reconciliation evidence exhausted (no idempotency-key/reconciliation-query capability) — the honest floor | **yes** | reconciliation floor |

Rules that hold the truth ladder (`accepted ≠ provider_accepted ≠ delivered ≠ read ≠ acted upon`):

- `provider_accepted → delivered` is **receipt-driven only**; a 2xx never auto-promotes.
- A **timeout after send is `unknown`, never `failed`** (INV-08); `unknown` is reconciled or floored at `terminal_unknown`, never blind-retried (INV-09).
- **Cancellation is best-effort and pre-handoff only** (INV-11); a provider-accepted send can never be rewritten as unsent.
- A late/conflicting receipt appends evidence but does not regress the projection.
- No lifecycle state authorizes or advances a business workflow (INV-15).

---

## 3. Template model

- **Tenant-owned template identity** (`template_code`, purpose, channel, locale set, lifecycle, revision) with **immutable published `TemplateVersion`s**: subject/body form, declared-variable **JSON schema**, content classification, allowed link/attachment behavior, renderer version, change reason.
- Lifecycle **`draft → published → retired`**; **published versions are immutable** — a change is a new version, never an edit.
- **A template cannot declare itself mandatory.** Mandatory-vs-preference is a *policy* decision by the governing product/platform, auditable and reviewable — never a template attribute (D-05).
- **Callers select a published template + schema-validated variables**; arbitrary caller-supplied bodies are not the default contract. Raw destinations/bodies are accepted **only** by a specifically authorized flow that owns its own validation (e.g. invitation), never the generic send.
- **Deterministic locale fallback is resolved before request acceptance** (D-08), not silently by a provider. bOPEN's published version is authoritative; a provider-side template is an adapter optimization only if conformance proves identical meaning.
- Channel-aware validation (headers, addresses, URLs, HTML/text, encodings) refuses header injection, unsafe schemes, template injection (INV-05). Render snapshot/hash is retained per privacy policy so an attempt is explainable without over-retaining content.

---

## 4. Capability set

| Capability | Scope | Notes |
|---|---|---|
| `notification.request` | tenant service/principal | create + enqueue one notification (send path) |
| `notification.read`, `notification.list` | tenant | redacted status; **no search-by-raw-destination** |
| `notification.cancel` | tenant | best-effort pre-handoff |
| `notification.retry`, `notification.reconcile` | **operator/admin only** | human-initiated, audited; never automatic |
| `notification.template.create` / `.publish` / `.retire` | tenant admin | immutable-version discipline |
| `notification.preference.manage`, `notification.suppression.manage` | tenant admin | suppression removal is a separate audited act |
| `notification.export` | tenant admin | distinct, audited; redacted evidence only |
| `notification.callback` | **public, unauthenticated-but-verified**, per provider | authority from stored binding only (AUTH-D1) |
| `notification.provider.manage` | **platform/operator only** | provider selection deferred (D-04/D-07) |

**Design boundary — tzdb-free.** The foundation carries **no timezone-database dependency**. All internal timestamps, lease/backoff gates, quota windows, and callback timestamp windows use the **UTC DB clock (`now()`)** per `ADR-NOTIFY-WQ`. Any `schedule_constraint` is an **absolute UTC instant**, never a wall-clock-plus-zone that would require tzdb resolution; templates render **language locale only**, not local civil time. This keeps the send/claim path deterministic and free of tzdb drift, and is an explicit test-matrix line.

---

## 5. API surface (contract level — operations, inputs/outputs by name; not implementations)

| Operation | Inputs (by name) | Outputs (by name) |
|---|---|---|
| **CreateNotificationRequest** | `idempotency_key`, `purpose_code`, `channel`, `recipient_ref` **or** authorized `explicit_destination`, `template_code`, `template_version_selector`, `variables`, `locale`, `priority`, `correlation_id`, `schedule_constraint?` (UTC), `context_ref` | `notification_id`, `lifecycle_state`, `revision` (idempotent replay returns the **existing** record) |
| **ReadNotification** | `notification_id` | redacted view: `{notification_id, purpose_code, channel, lifecycle_state, redacted_destination, last_classified_outcome, revision, timestamps}` — **no body/variables/raw destination** |
| **ListNotifications** | filter `{purpose_code?, lifecycle_state?, time_window?, correlation_id?}`, `page_cursor` | page of redacted views; no raw-destination filter |
| **CancelNotification** | `notification_id`, `revision` | `cancel_result ∈ {cancelled, too_late}` |
| **RetryDispatch** *(operator)* | `notification_id`, `reason`, `accept_duplicate_risk` | audited `retry_receipt` |
| **ReconcileDispatch** *(operator)* | `notification_id` | `reconcile_result ∈ {resolved_outcome, still_unknown}` |
| **IngestProviderCallback** *(public)* | `raw_bytes`, `headers` | uniform `ingest_result ∈ {accepted, refused}` (non-oracle) |
| **CreateTemplate / PublishTemplateVersion / RetireTemplateVersion** | `template_code`, version body/schema, `change_reason` (+ `template_version_id` for publish/retire) | `template_version_id`, `lifecycle` |
| **ManagePreference / ManageSuppression** | `subject_ref`, `purpose_code`, `channel`, `action` | `state`, audit ref |
| **ExportNotificationEvidence** | `scope`, `time_window` | redacted evidence bundle ref + audit ref |

Every write is optimistic-concurrency guarded (`revision`); every operation is subject to the independent gates of §6 in order.

---

## 6. Stable error-code catalogue (uniform, tenant-safe, anti-enumeration)

Codes are **stable machine identifiers**. The load-bearing rule (INV-04): **no response body, status, timing, log, or audit routing may reveal whether a Principal, Party, destination, template, or provider message exists.** Existence-sensitive failures therefore **collapse to one code with identical shape and constant work**; the true internal reason is recorded in audit **under the resolved tenant only**, never returned to the caller.

| Code | Triggers | Anti-enumeration behavior | Retryable |
|---|---|---|---|
| `NOTIFY-E-INPUT-INVALID` | schema/malformed request, bad locale/purpose shape | distinct — reveals no existence | no |
| `NOTIFY-E-UNAUTHENTICATED` | no valid principal/session | distinct | no |
| `NOTIFY-E-UNAUTHORIZED` | capability/authorization denied | distinct | no |
| `NOTIFY-E-ENTITLEMENT-MISSING` | missing entitlement / disabled module | distinct (commercial, not existence) | no |
| `NOTIFY-E-RECIPIENT-UNAVAILABLE` | recipient unresolved, unverified, expired, cross-tenant, wrong purpose/channel, **suppressed**, or implicit `principals.email` lookup | **collapsed** — single code, identical shape, constant work; reason audited internally only | no |
| `NOTIFY-E-TEMPLATE-INVALID` | caller's own template unpublished/retired/schema-mismatch/unsafe-render | distinct **within tenant** (caller's own template; RLS makes cross-tenant refs impossible) | no |
| `NOTIFY-E-IDEMPOTENCY-CONFLICT` | same `idempotency_key`, different payload | distinct; exact replay is a **non-error** returning the existing record | no |
| `NOTIFY-E-QUOTA-EXCEEDED` | token bucket exhausted / backpressure threshold | **distinct and loud by design** (INV-14) | **yes** |
| `NOTIFY-E-LIFECYCLE-INVALID` | illegal transition (e.g. cancel a terminal) | distinct | no |
| `NOTIFY-E-REVISION-STALE` | optimistic-concurrency mismatch | distinct | yes (re-read) |
| `NOTIFY-E-CANCEL-TOO-LATE` | cancellation after provider handoff | distinct (no existence leak) | no |
| `NOTIFY-E-CALLBACK-REFUSED` | any callback failure: size/type/timestamp/signature/binding/replay/rate/invalid-transition | **collapsed** — one uniform non-oracle response, constant-work past size/type gate (CB-6) | no |

Provider outcome classes (`provider_accepted` / `retryable_failed` / `terminal_failed` / `unknown`) are **not synchronous request errors** — they surface as attempt outcomes / lifecycle states / events, driven by the worker-owned classifier (`ADR-NOTIFY-WQ` §5).

---

## 7. Event catalogue (lifecycle/audit envelope — safe metadata only)

Events ride the **bOPEN envelope + transactional outbox**. Payload carries **only** safe metadata: `notification_id`, tenant scope, `purpose_code`, `channel`, `lifecycle_state`, `classified_outcome`, opaque `provider_message_id`, `correlation_id`, timestamps, safe reason code. They **exclude** raw destination, rendered content, variables, provider secrets, and raw provider payload (INV-13). Subscription rules prevent status events from recursively re-triggering; consumers deduplicate and tolerate replay/out-of-order within the stated ordering boundary.

`notification.accepted.v1` · `notification.suppressed.v1` · `notification.dispatched.v1` · `notification.provider_accepted.v1` · `notification.delivery_delayed.v1` · `notification.transport_delivered.v1` · `notification.failed.v1` · `notification.terminal_unknown.v1` · `notification.cancelled.v1` · `notification.dead_letter.v1` *(operational; supports the audited operator retry/reconcile flows)*.

---

## 8. Disposition of NOTIFY-D-01 … NOTIFY-D-14 (no silent defaults)

| ID | Disposition |
|---|---|
| **D-01** recipient/contact source | **RESOLVED — path (a).** Resolve against **Party ContactPoint** (`contact_point_repositories.resolve()`, migration 019); `RecipientSnapshotRef` binds source/verification/purpose/tenant/effective-window. `principals.email` is **never** a default destination. |
| **D-02** reference flows | **RESOLVED.** Authorized **invitation** (explicit destination, owns its own validation) **plus** one **Party-resolved** transactional notice; anti-enumeration preserved on both. |
| **D-03** first channel | **RESOLVED.** Transactional **email only**; `sms` (endpoint `phone`) modeled but deferred; push/webhook/in-app out. |
| **D-04** provider | **DEFERRED** to `ADR-NOTIFY-PROVIDER` / D-07 — deterministic fake adapter only; no production provider selected. |
| **D-05** purpose/preference model | **RESOLVED.** Three governed purpose tiers (mandatory security/operational · transactional · optional transactional); marketing excluded; **a template cannot self-declare mandatory**; bypass is an audited policy decision. |
| **D-06** delivery truth | **RESOLVED.** Normalized bOPEN states + the truth ladder (§2); `provider_accepted`/`delivered` never imply human read/action. |
| **D-07** idempotency & unknown | **RESOLVED at contract level:** caller/event-scoped `UNIQUE(tenant_id, idempotency_key)`; per-attempt deterministic `send_key`; `unknown`→reconcile-or-`terminal_unknown`. **Provider-specific** capability/reconciliation tables **deferred** with D-04. |
| **D-08** template/render ownership | **RESOLVED.** bOPEN published version authoritative; deterministic pre-accept locale fallback; recorded renderer version; safe HTML/text; provider-template use requires proven conformance. |
| **D-09** retention/privacy | **PARTIAL.** Contract fixes independent classes/retention *shape* and tombstone-on-purge; **concrete periods deferred** to the runbook ADR — explicitly, not silently. |
| **D-10** outbox/inbox topology | **FLAGGED — under-resolved.** The *"purpose-built `notification_*` dispatch, never overload `usage_outbox`"* part is **resolved** (owned by `ADR-NOTIFY-WQ` §1). The **dedicated-DB queue topology** (shared control plane vs. per-placement worker/roles/health) remains **OPEN** and must be decided before any build. |
| **D-11** quotas & emergency stop | **FLAGGED — under-resolved.** Contract fixes the *shape*: token-bucket quota as an **independent loud-refusing gate** (INV-14), emergency suspension **separate** from quota, fairness-shaped claim. **Concrete quota windows/limits, backpressure thresholds, and cross-provider fairness constants are OPEN** — deferred to runbook/scheduling ADRs, not defaulted here. |
| **D-12** attachments & links | **DEFERRED.** No attachments in the first slice; links use allowlisted schemes + purpose-bound tokens; Document-version grants are purpose-bound/expiring, never inherited. |
| **D-13** provider callback public boundary | **FLAGGED — under-resolved.** Verification order, replay, rotation, and per-provider rate limiting are **specified** in the ADRs. **OPEN and deferred:** raw-body **retention period**, **incident-response** procedure, and **cross-provider DDoS posture beyond per-provider rate limiting** — must carry their own runbook/security decision before build. |
| **D-14** status/search/export | **RESOLVED.** Redacted status; **no search-by-raw-destination**; export is a distinct **audited** capability returning redacted evidence only. |

**D-01 remains the pre-build dependency.** The three flagged items (**D-10, D-11, D-13**) are **not resolved by this spec** and are named as build-blocking open decisions, each requiring its own decision record.

---

## 9. Invariants traceability (summary)

INV-01/-04 — tenant isolation + anti-enumeration: collapsed `RECIPIENT-UNAVAILABLE`/`CALLBACK-REFUSED` codes, redacted status, no raw-destination search, body-independent audit. INV-02 — independent ordered gates (auth/entitlement/purpose/preference/suppression/quota) each failing separately. INV-03/-05 — recipient/template integrity via resolver + immutable versions. INV-06/-07/-09 — idempotency key, split fencing/send-key, no blind retry (owned by `ADR-NOTIFY-WQ`, referenced). INV-08/-11 — truth-ladder projection, receipt-driven, monotonic, non-regressing. INV-12 — append-only attempt/receipt, `ON DELETE RESTRICT`. INV-13 — safe-metadata-only events/logs. INV-14 — loud quota + fairness. INV-15 — no workflow authorization. INV-16 — migration-freeze + forced-RLS on every background content touch. Each proposition traces to a **named executed test at an exact tree** in the future test matrix; live PostgreSQL required for RLS/lease/append-only/migration claims.

---

## 10. Clean-room note

Designed independently under **AGENTS.md §6**: standards are requirements sources only; no provider SDK, schema, template, or test was copied. Entities, the logical lifecycle projection, capability set, API/error/event catalogues, and template model were derived from the kernel's own patterns — forced RLS + `tenant_session`, `resolve_context` fail-closed identical-403, placement mis-route uniform refusal, AUTH-D1 (a header cannot create authority), the `workflow_instances`↔`workflow_history` mutable+append-only split with `ON DELETE RESTRICT` (013/014), `contact_point_repositories.resolve()` returning a disposed `RecipientSnapshot` (019), and `TENANT_SCOPED_TABLES`∩`COPY_ORDER` coverage — plus the RESEARCH invariants (NOTIFY-INV-01…16), the REVIEW findings, and the two paired v2.1 ADRs (worker/queue and provider/channel) and the privacy & threat model, **referenced and kept consistent with, never re-decided**. Files consulted: `docs/01-product/MILE-4.2-notification-{foundation-research,foundation-review,worker-queue-ADR-draft-v2,provider-channel-ADR-draft-v2,privacy-threat-model-draft}.md`; `services/platform-kernel/python/platform_kernel/{db.py,workflow_repositories.py,contact_point_repositories.py}`; `infrastructure/database/{013,014,019,020}_*`; `tests/isolation/test_rls_database_behavior.py`; `tools/migrate_tenant_to_dedicated.py`.

---

## 11. Authority block

```yaml
document: bopen-notify-001-foundation-contract
document_id: BOPEN-NOTIFY-001            # proposed; pending governance registration
version: 1.0.0-draft
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
  ready_for_operator_review: false
```

> This spec fixes a foundation contract only. It authorizes nothing, builds nothing, and selects no provider. Three decisions (**D-10 queue topology, D-11 quota/emergency-stop constants, D-13 callback public-boundary retention/incident/DDoS**) remain open and build-blocking. A build requires a separate operator authorization recorded first; Notification remains gated by DEC-P4-ENTRY §9.
