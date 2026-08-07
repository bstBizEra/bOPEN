# Notification test & refusal matrix (DRAFT)

**STATUS: DRAFT / PROPOSED — NOT AUTHORIZED, NOT IN FORCE. Notification remains gated by DEC-P4-ENTRY §9. This document plans tests; it authorizes nothing, builds nothing, selects no provider, and runs no test. A governed tests-first build needs a separate operator authorization recorded first.**

---

## Controlled-document metadata

| Field | Value |
|---|---|
| **Document ID** | `TESTMATRIX-NOTIFY` (proposed; pending governance ID-registry ratification) |
| **Version** | `1.0.0-draft` |
| **Owner** | bOPEN Agentic SE — Notification (Motor authoring; Codex independent reviewer) |
| **Issued** | 2026-08-06 |
| **Updated** | 2026-08-06 |
| **Status** | DRAFT / PROPOSED — gated by DEC-P4-ENTRY §9 |
| **Governing artifacts** | DEC-P4-ENTRY §9; `ADR-NOTIFY-WQ` v2.1.0-draft (tables/state/security plane — table & state source of truth); `ADR-NOTIFY-PROVIDER` v2.1.0-draft (adapter facade/classifier mapping); notification privacy & threat model; MILE-4.2 notification foundation research + review (NOTIFY-INV-01…16, NOTIFY-D-01…14); AGENTS.md §6 (clean-room); BOPEN-GOV-EBIV-001 (R2 executed-evidence, R3 anchors, R5 loud) |
| **Dependent artifacts** | `BOPEN-NOTIFY-001`; migration/rollback/compensation plan; operations runbooks; the EBIV evidence package (`invariant-traceability.csv`) a build would produce |
| **Evidence refs** | `tests/isolation/test_rls_database_behavior.py`; `tools/migrate_tenant_to_dedicated.py` (COPY_ORDER); `docs/evidence/phase-3.5/invariant-traceability.csv` (CSV shape); kernel migrations 013/014/019/020 |

*Proposing a Document ID/version is traceability metadata for governance to register; it is not self-authorization.*

`ready_for_operator_review: false`

> This is a **plan** for the test suite a governed build would implement: the *structure and coverage*, not exhaustive test code. It is CONSISTENT with the v2.1 ADRs and re-decides nothing in them; where a ceiling/constant is deferred there, it stays deferred here and the test asserts the *mechanism*, not a number.

---

## 1. Test taxonomy and the EBIV evidence contract

Every row below becomes a named test producing **executed evidence** at a **candidate commit** — the EBIV R2 discipline the kernel already follows (`invariant-traceability.csv`: `invariant_id, invariant_source, invariant_statement, test_id, test_file, evidence_kind, mechanism_whose_removal_breaks_it, status`). A row is only `verified_by_execution` when its named test ran green against the stated substrate; anything unrun is recorded `UNVERIFIED` and **loudly**, never silently green (EBIV R5, mirroring `INV-EVIDENCE-LOUD-01`). Evidence kinds mirror the kernel's: `executed_sql`, `executed_python`, `executed_http`, `executed_tool`. Concurrency obligations (§4) are `executed_sql` against **live PostgreSQL 17 forced-RLS**, never a mock — a mock cannot exhibit `FOR UPDATE SKIP LOCKED`, transaction isolation, or fenced-CAS zero-row semantics.

Suites, mirroring the kernel's layout (`tests/isolation/`, `tests/integration/`, `tests/unit/`):

- **A. Refusal suite** (§3) — every input/boundary/transition the system MUST reject loudly, `executed_http`/`executed_sql`.
- **B. Positive-path suite** (§5) — the admitted ladders, `executed_http`.
- **C. Concurrency & durability suite** (§4) — the ADR's build-time verification obligations, `executed_sql`/`executed_python` on live PostgreSQL with real crash injection.
- **D. Coverage suite** — cross-inventory `TENANT_SCOPED_TABLES` ∩ `COPY_ORDER` (INV-MIGRATE-COVERAGE-01), `executed_python`.
- **E. Contract suite** — the deterministic fake adapter exercising every classified outcome and the CB-1 order (`ADR-NOTIFY-PROVIDER` §Consequences), `executed_python`.

The **uniform tenant-safe refusal** referenced throughout is the kernel's established non-oracle posture (`INV-HTTP-REFUSAL-OPAQUE-01`, `resolve_context` identical-403): same status, same body shape, no timing/log/audit tell that discloses whether a Principal, Party, destination, template, or provider message exists. The refusal *reason code* is distinct and safe; the *disclosure surface* is identical.

---

## 2. What is deliberately NOT tested here

Provider selection and production credentials (NOTIFY-D-04/-07) — the suite runs the **deterministic fake adapter only**; exactly-once is never asserted (`terminal_unknown` is the honest floor). Outbound webhook/egress (T7 in the threat model) — deferred, no SSRF suite. Timing-uniformity *measurement under load* (T2/T3/T4) — flagged as a residual to measure, not a pass/fail unit assertion. Retention constants (NOTIFY-D-09) — the test asserts tombstone/correlation survives purge, not a period. Dedicated-DB queue topology — the coverage test runs per-placement once topology is decided.

---

## 3. Refusal matrix — every rejection the system MUST make loudly

Each row: the rejected input/boundary/transition → the NOTIFY-INV it defends → the expected uniform tenant-safe refusal. All are Suite A unless noted. Every row needs an executed test at a candidate commit (EBIV R2).

| # | Rejected input / boundary / transition | Defends | Expected refusal (uniform, tenant-safe) |
|---|---|---|---|
| R1 | Cross-tenant read/list/cancel/retry/export of a foreign notification, attempt, or receipt | INV-01 | RLS yields zero rows; identical-404/403, no existence tell |
| R2 | Request with unset / unknown / inactive tenant context | INV-01, -02 | Zero-row deny-default; uniform 403 (mirrors `INV-TENANT-DENY-DEFAULT-01/02`) |
| R3 | Unauthenticated `notification.request` (context id alone, no bearer) | INV-02 | Bearer-only refusal (mirrors `INV-BEARER-WRITE-01`); no fallback to header identity |
| R4 | Authorized principal but **missing entitlement / disabled module / prohibited purpose** | INV-02 | Independent gate fails on its own; distinct safe code; fails separately from auth/quota/suppression |
| R5 | Suppressed / cancelled / preference-opted-out recipient at request or claim | INV-02, -09 | Refused independently; a terminal/suppressed outcome is never retried |
| R6 | Recipient: cross-tenant, unresolved, unverified, expired, malformed, wrong-purpose/channel endpoint | INV-03 | Orchestrator `resolve()` under `tenant_session` refuses; no partial send |
| R7 | Implicit `principals.email` used as a destination | INV-03 | Refused — a principal is an auth identity, not a consented contact (NOTIFY-D-01) |
| R8 | Unknown / unsupported **channel** (no capable, verified-endpoint-matched adapter) | INV-03, -05 | Refuse before send (CP-D-06 mirror); never a silent drop |
| R9 | Unknown / unbound **provider** (dispatch with no `provider_id` binding) | INV-14 (D1) | Not claimable — scheduler cannot claim work carrying no provider identity |
| R10 | Template: cross-tenant, draft/retired, stale, schema-mismatched, unsupported-locale | INV-05 | Render refused; immutable published version only |
| R11 | Template render: header injection, unsafe link scheme, HTML/text confusion, bad encoding | INV-05 | Channel-aware validation refuses; allowlisted schemes + purpose-bound tokens only |
| R12 | Template attempting to declare itself mandatory | INV-05 | Refused — mandatory-vs-preference is policy, not a template attribute (NOTIFY-D-05) |
| R13 | Duplicate `notification.request` on `(tenant_id, idempotency_key)` | INV-06 | No second notification/dispatch; returns the existing one (UNIQUE collision) |
| R14 | Callback: **oversized body** (streaming read limit at the public endpoint, pre-buffer) | INV-10 | Aborted before the `raw_bytes` buffer is allocated; uniform refusal (parse-bomb defense) |
| R15 | Callback: wrong **content-type** | INV-10 | Refused on raw bytes before parse (CB-1 step 1) |
| R16 | Callback: **stale / future timestamp** outside the signed window | INV-10 | Refused after content-type, before HMAC (CB-1 step 2), against DB clock |
| R17 | Callback: **bad signature / HMAC** over exact raw bytes | INV-10, -05 | Refused before parse (CB-1 step 3); only verified bytes proceed |
| R18 | Callback: **replay** of a valid event (same/changed/null `replay_id`) | INV-06, -12 | Deterministic `dedup_key` collides; no second receipt/status event |
| R19 | Callback: **wrong-provider / wrong-message binding**, unknown id | INV-01, -04, -10 | Uniform refusal; body tenant/account field inert (AUTH-D1) |
| R20 | Callback **body asserting tenant authority** to route/scope | INV-01; AUTH-D1 | Body field inert; authority only from stored `provider_message_id` binding |
| R21 | Callback: invalid / regressive transition (e.g. `delivered` after hard-bounce) | INV-08, -11 | Stored append-only as `superseded`/`conflicting`; projection does not regress |
| R22 | **Quota exceeded** at admission (token bucket empty) | INV-14, -02 | Zero-row `RETURNING`; distinct **retryable** quota code, refused loudly, independent gate |
| R23 | **Backpressure**: per-tenant queue depth / oldest-age over soft threshold | INV-14 | Same loud retryable refusal; never silently dropped or unbounded-queued |
| R24 | Emergency **suspension** active for tenant | INV-14 | Claim excluded via `notification_quota_suspend`; never conflated with ordinary quota |
| R25 | Unsupported / undeclared **capability** requested (e.g. idempotency-key on a provider without it) | INV-09 | Refuse the capability request; degrade to honest `terminal_unknown` floor, never fake it |
| R26 | Ambiguous / malformed / no-result provider response | INV-08 | Classified `unknown`, fail closed; never a favorable state |
| R27 | Callback over **per-provider rate limit** (keyed only on `provider_id`) | INV-04, -14 | Throttled before binding lookup; flood at provider A cannot starve provider B |
| R28 | Body verifying only under an **expired `previous`** signing secret | INV-10 | Refused; overlap is bounded and `not_after`-gated (CB-6/CB-4) |
| R29 | Existence probe via status/list "search by raw destination" | INV-04 | No such capability exists; status returns redacted destination only |
| R30 | Secret / raw payload / full endpoint / body / variable requested in event, metric, log, export | INV-13 | Absent by construction; only ids, safe hashes, normalized codes surface |

**Refusal-suite property tests (cross-cutting).** (a) *Non-oracle*: for every refusal class on the callback surface, response status+body+shape are byte-identical and constant-work past the size/type gate (INV-04, -10). (b) *Independent gates*: each of auth, entitlement, purpose, preference, suppression, quota is shown to fail **alone** with the others passing (INV-02, mirroring the kernel's separate-gate discipline). (c) *Audit routing is body-independent*: a refusal that resolved no binding files to the tenant-null operational trail, chosen by whether a real binding existed — never by any body field (`context_service._deny` rule).

---

## 4. Build-time verification obligations — required live-PostgreSQL concurrency tests

`ADR-NOTIFY-WQ` §7 and §Consequences explicitly **defer concurrency proof to the tests-first build** ("This ADR fixes the mechanism; the build supplies the proof"). Those obligations are enumerated here as Suite C — each is `executed_sql`/`executed_python` against **live PostgreSQL 17 under real transaction isolation and forced RLS**, with genuine concurrent claimers and real crash injection (process kill / connection drop between commits), producing executed evidence at a candidate commit (EBIV R2). A mock substrate cannot discharge any of these; a row that cannot run reports failure loudly (R5).

| # | Concurrency / durability obligation | Mechanism whose removal breaks it | Defends |
|---|---|---|---|
| C1 | **Lease steal / fence CAS rejection.** Two workers claim the same dispatch; the loser's later fenced UPDATE (`WHERE lease_fence=:fence`) matches **zero rows** and writes nothing | monotonic `lease_fence` (DB clock) + fenced CAS on `notification_dispatch` | INV-07 (claim half) |
| C2 | **Crash mid-send → `unknown` recovery, same-attempt key reuse.** Kill a worker between the `leased→sending` commit and finalization; the reclaimer finds `status='sending'` + populated `send_key`, transitions `sending→reconciling`, **reuses the same `attempt_no`/`send_key`**, and issues **no duplicate send** | pre-send marker on the mutable row + preserve-key-on-reclaim rule (D-EV-3/D-EV-5) | INV-07, -09, -16 |
| C3 | **No blind-retry of expired `sending`.** An expired-lease reclaim of a `send_started` row **never** mints a new key for auto-retry; it reconciles or floors at `terminal_unknown` | classifier fail-closed + Decision 6 capability-gated reclaim | INV-09 |
| C4 | **Duplicate-send collapse.** Two physical sends carrying the identical deterministic `send_key` (crash-reclaim path) collapse to one provider-side effect at the fake adapter that honors idempotency-key | `deterministic_key(dispatch_id, attempt_no)` recorded before send | INV-06, -07 |
| C5 | **Fresh retry re-sends.** A `retryable_failed` attempt increments `attempt_no` → a **new** key → genuinely re-sends (proven before-effect) | per-attempt key granularity | INV-09 |
| C6 | **Per-tenant inflight slot cap not exceeded under concurrency.** N concurrent claimers against a tenant with 10,000 queued rows never collectively exceed `:max_inflight_per_tenant` | `FOR UPDATE` serialization on the `notification_fairness` row before `free_slots` compute (or atomic reserved-slot UPDATE) | INV-14 |
| C7 | **Least-recently-served interleave / no starvation.** A heavy tenant does not starve others; `ORDER BY last_served_at ASC` + `LATERAL … LIMIT LEAST(free_slots,…)` yields at most `free_slots` per pass | fairness cursor + LATERAL cap | INV-14 |
| C8 | **Breaker skip + single fenced probe.** Only one probe is ever in flight; a stalled probe worker that resumes finds a newer `probe_fence` and its CAS matches nothing | `probe_fence` fenced exactly like the lease | INV-14, -16 |
| C9 | **Quota reservation atomicity.** Concurrent admissions cannot over-spend the bucket; a rolled-back enqueue returns its token; claim **validates, never re-spends** | conditional `ON CONFLICT … WHERE tokens_used < tokens_limit RETURNING` | INV-14, -02, -06 |
| C10 | **Append-only attempt/receipt resist UPDATE/DELETE.** Direct UPDATE and DELETE on `notification_attempt`/`_receipt`/`_callback_event` are refused (no such policy exists) | SELECT+INSERT-only RLS (013 pattern) | INV-12 |
| C11 | **Parent-cascade erasure refused.** Deleting a parent `notifications`/dispatch row cannot cascade-erase evidence | `ON DELETE RESTRICT` on the composite FK (migration-014 lesson) | INV-12 |
| C12 | **Late/conflicting receipt appends without regressing projection.** A `delivered` arriving after a recorded terminal state inserts `superseded`/`conflicting` and moves no mutable lifecycle state | monotonic receipt-driven projection | INV-11, -08 |
| C13 | **Worker role cannot touch content.** A coding error writing content on the `bopen_notify_claimer` connection fails on **privilege**, not review; every content touch re-enters `tenant_session` as `bopen_app` | column-level GRANT confinement + separate connection | INV-01, -13 |
| C14 | **Callback role confinement.** `bopen_notify_callback` can read only the column-restricted binding tuple, INSERT only the append-only callback tables; holds no dispatch/content grant | forced-RLS + column GRANT (CB-SEC-01b) | INV-01, -04 |
| C15 | **Revocation fails closed.** `DROP POLICY … TO bopen_notify_claimer`/`bopen_notify_callback` degrades the plane to **zero-visibility**, never open-visibility | ordinary tenant policy remaining + empty claimer tenant context | INV-01 |
| C16 | **Migrating-freeze honored on background writes.** A content touch for a migrating tenant raises `TenantMigratingError` at `tenant_session` | placement freeze at the data chokepoint (mirrors `INV-MIGRATE-FREEZE-DATA-PATH-01`) | INV-16 |
| C17 | **INV-MIGRATE-COVERAGE for the new tables.** `COPY_ORDER` asserted equal to RLS-classified `TENANT_SCOPED_TABLES`, parents before children; any unmapped tenant-scoped `notification_*` table fails loud | cross-inventory coverage test (Suite D) | INV-12, -16; INV-MIGRATE-COVERAGE-01 |

**Substrate note.** C1–C9 and C12 require concurrent sessions against one live database; C2 requires real mid-transaction process death, not a simulated exception; C10–C11 require the actual RLS policies and FK actions (which act *past* RLS). None is discharged by unit-level mocking — this is the same `executed_sql` bar the isolation suite already meets.

---

## 5. Positive matrix — the admitted paths

Suite B (`executed_http`) plus Suite E contract paths. Each proves an admitted ladder end-to-end and needs executed evidence at a candidate commit.

| # | Admitted path | Proves | Anchors |
|---|---|---|---|
| P1 | **Enqueue is idempotent.** `notification.request` inserts `notifications` + `notification_dispatch(pending)` + reserves one quota token + binds `provider_id`, all in one `tenant_session` transaction; a replay returns the same pair | transactional outbox atomicity; INV-06 | — |
| P2 | **Verified send.** Claim → `leased→sending` (marker committed) → fake-adapter `send` → `provider_accepted` → one `notification_attempt` INSERTed once at finalization | send-start protocol; INV-08, -12 | attempt row |
| P3 | **`provider_accepted → receipt → delivered` ladder.** A signed callback passes CB-1, binds via stored `provider_message_id`, appends `notification_receipt`, advances the monotonic projection to `delivered` | receipt-driven promotion only; INV-08, -11 | receipt row |
| P4 | **Reconcile unknown → resolved.** An `unknown` attempt with `reconciliation-query` declared resolves by provider query (no resend) and writes the outcome row reusing the same `attempt_no`/`send_key` | reconciliation without blind resend; INV-09 | — |
| P5 | **Reconcile unknown → `terminal_unknown` floor.** With neither idempotency-key nor reconciliation-query declared, the dispatch floors at `terminal_unknown` (`status='dead'`), operator-visible, never rewritten | honest ambiguity floor; INV-08, -09 | — |
| P6 | **Retryable backoff cycle.** `retryable_failed` re-queues with backoff/jitter, honors a *validated* `Retry-After`, increments `attempt_no`, and stops at the max-attempt/age ceiling → dead-letter | bounded retry; INV-09 | attempt rows |
| P7 | **Early-callback quarantine → promote.** A verified callback whose binding is not yet visible is quarantined content-free, then promoted to a tenant-scoped receipt once the attempt commits | quarantine window = commit race; INV-10 | quarantine → receipt |
| P8 | **Dead-letter operator flow.** An authorized, audited operator `notification.retry`/`notification.reconcile` is admitted; an unauthorized one is refused (crosses to R4) | human-initiated only; INV-09, -15 | audit row |
| P9 | **Fake-adapter contract matrix.** The deterministic fake produces each of the four classified outcomes, simulates valid+invalid signatures across CB-1, honors/denies each capability, echoes the forwarded key | adapter maps only, mints no fifth class; INV-08 | Suite E |
| P10 | **Provider result advances no business workflow.** A `provider_accepted` (or a receipt) authorizes and completes nothing downstream | workflow boundary; INV-15 | — |

---

## 6. Traceability & completeness gate

Every §3/§4/§5 row maps to at least one NOTIFY-INV; conversely each NOTIFY-INV-01…16 must be covered by ≥1 row before the suite is `ready_for_operator_review`. Mapping check: INV-01 (R1,R2,R19,R20,C13–C15), INV-02 (R3,R4,R5,R22,C9), INV-03 (R6,R7,R8,R10), INV-04 (R19,R27,R29,C14), INV-05 (R10,R11,R12,R17), INV-06 (R13,R18,C4,C9,P1), INV-07 (C1,C2,C4), INV-08 (R21,R26,P2,P3,P9,C12), INV-09 (R5,R25,C2,C3,C5,P4,P5,P6), INV-10 (R14–R19,R27,R28,P7), INV-11 (R21,C12,P3), INV-12 (R18,C10,C11,C17), INV-13 (R30,C13), INV-14 (R9,R22,R23,R24,C6,C7,C8,C9), INV-15 (P8,P10), INV-16 (C2,C8,C16,C17). No invariant is unmapped. The suite emits a `notification` slice of `invariant-traceability.csv` in the kernel's exact 8-column shape; a build merges it into the EBIV package, and `check_evidence_anchors.py` (INV-EVIDENCE-ANCHOR-01) resolves each cited commit/object (R3).

---

## Clean-room note

Designed independently under AGENTS.md §6: standards are requirements sources only. No upstream test suite was copied. The taxonomy, refusal rows, concurrency obligations, and positive ladders were derived from the two v2.1 ADRs (tables, state machine, classifier, security plane — referenced, not re-decided), the privacy/threat model's STRIDE/LINDDUN sweep, the RESEARCH invariants (NOTIFY-INV-01…16) and decisions (NOTIFY-D-01…14), the REVIEW's "keep a live ambiguous-outcome probe" instruction, and the kernel's own executed-evidence patterns — `tests/isolation/test_rls_database_behavior.py`, `tools/migrate_tenant_to_dedicated.py` (COPY_ORDER / INV-MIGRATE-COVERAGE-01), migrations 013/014/019/020, and the EBIV `invariant-traceability.csv` shape. This document plans tests; it re-decides no ADR.

---

## Authority block

```yaml
document: notification-test-and-refusal-matrix
document_id: TESTMATRIX-NOTIFY          # proposed; pending governance registration
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

> This document plans a tests-first build's suite only. It authorizes nothing, builds nothing, runs no test, and selects no provider. A build requires a separate operator authorization recorded first; Notification remains gated by DEC-P4-ENTRY §9. Verification, disposition, deployment, provider activation, and production activation remain distinct later operator acts.
