# DEC-P2-DOCKET — Phase 2 pre-coding decision resolution docket

**Document ID:** `DEC-P2-DOCKET-001`
**Version:** `1.0`
**Status:** Proposed — awaiting Engineering Authority ratification
**Date:** 2026-07-29
**Owner:** Engineering Authority
**Governing artifacts:** [`BOPEN-P2-001`](../work-packages/BOPEN-P2-001-EXECUTION-PLAN.md) §21, §23 · [`BOPEN-IDP-001`](../04-platform/BOPEN-IDP-001.md) §20, §21
**Closes:** `DEC-0009` on ratification

---

## 1. Purpose

`BOPEN-P2-001` §21 lists fifteen decisions as `OPEN` and states: *"All OPEN decisions are
blocking unless the Engineering Authority explicitly classifies one as non-blocking with
rationale."* This docket proposes a resolution for each, binds it to the ADR that carries the
reasoning and to the code that implements it, and marks whether ratifying it costs a code
change.

**Nothing here is approved.** Each row is a recommendation. Ratification is a single act by
the Engineering Authority; see §5.

---

## 2. ADR identifier mapping

`docs/00-governance/artifact-numbering.md` fixes the ADR format as `ADR-<NNNN>`, and the
existing sequence runs `ADR-0001`..`ADR-0009`. The plan's `ADR-P2-00X` labels are therefore
recorded as aliases rather than filenames.

| Plan alias | Repository ADR | Subject | Status |
|---|---|---|---|
| `ADR-P2-001` | [`ADR-0010`](../adr/ADR-0010.md) | Broker deployment and adapter boundary | Proposed |
| `ADR-P2-002` | [`ADR-0011`](../adr/ADR-0011.md) | External identity uniqueness and linking | Proposed |
| `ADR-P2-003` | [`ADR-0012`](../adr/ADR-0012.md) | Invitation token generation, hashing, consumption | Proposed |
| `ADR-P2-004` | [`ADR-0013`](../adr/ADR-0013.md) | Membership transition atomicity and concurrency | Proposed |
| `ADR-P2-005` | [`ADR-0014`](../adr/ADR-0014.md) | Session store, context rotation, revocation | Proposed |
| `ADR-P2-006` | [`ADR-0015`](../adr/ADR-0015.md) | JWT algorithm, key custody, rotation, JWKS | Proposed |
| `ADR-P2-007` | [`ADR-0016`](../adr/ADR-0016.md) | SCIM ordering, idempotency, deprovision mapping | Proposed |
| `ADR-P2-008` | [`ADR-0017`](../adr/ADR-0017.md) | Group-to-role mapping governance | Proposed |
| `ADR-P2-009` | [`ADR-0018`](../adr/ADR-0018.md) | Delegated-grant approval and maximum duration | Proposed |
| `ADR-P2-010` | [`ADR-0019`](../adr/ADR-0019.md) | Identity audit classification and retention | Proposed |

---

## 3. Decision resolutions

`Delta` = does ratifying this cost a code change?

| ID | Question | Proposed resolution | ADR | Delta |
|---|---|---|---|:--:|
| D-P2-001 | Canonical broker name/version | Ory Polis (ex-BoxyHQ Jackson), self-hosted behind `BrokerPort`. **Exact release and image digest deferred to the environment contract**, which does not yet exist. Boundary decided; release not. | 0010 | none |
| D-P2-002 | Invitation token digest scheme | `hmac-sha256-v1` — HMAC-SHA256 under a server pepper held outside the database, over a 256-bit CSPRNG token, constant-time compare, scheme persisted per record | 0012 | **yes** |
| D-P2-003 | Invitation lifetime | 7 days, hard upper bound 30 days | 0012 | none |
| D-P2-004 | Duplicate invitation policy | One open invitation per `(tenant, normalized destination, purpose)` | 0012 | none |
| D-P2-005 | Membership terminal-state semantics | No implicit reactivation; terminal states carry no outbound transition, enforced by the contract loader | 0013 | none |
| D-P2-006 | Context token lifetime | 5 minutes; clock skew ≤ 60 seconds | 0014 | none |
| D-P2-007 | JWT algorithm and key custody | ES256; keys in external KMS/HSM; mandatory `kid`; versioned JWKS; 90-day signing key with 24-hour overlap; `alg=none` and algorithm negotiation rejected | 0015 | **yes** |
| D-P2-008 | Context supersession | One active context per session; latest wins; prior superseded on switch | 0014 | none |
| D-P2-009 | SCIM deprovision target state | Per-directory policy, default `suspended`, `revoked` available; hard delete prohibited with no override | 0016 | none |
| D-P2-010 | SCIM ordering strategy | Highest-observed provider sequence plus monotonic deprovision tombstone barrier | 0016 | none |
| D-P2-011 | Group-to-role mapping owner | Tenant authority proposes mappings; Security Authority owns the assignable-role allowlist; unmapped groups inert; no platform-wide role targets | 0017 | none |
| D-P2-012 | Support grant maximum | 8 hours, case reference mandatory | 0018 | none |
| D-P2-013 | Partner grant maximum | Contract-defined, hard ceiling 90 days, no auto-renew. **Ceiling is a placeholder pending Product Authority input.** | 0018 | none |
| D-P2-014 | Revocation propagation objective | New issuance denied immediately; active contexts invalidated within one token lifetime (≤ 5 min + skew) | 0014 | none |
| D-P2-015 | Audit/outbox failure semantics | Fail closed: an audit contract violation aborts the operation. **A durable outbox and reconciliation queue are NOT implemented** — the current sink is in-memory. | 0019 | **yes** |

**Thirteen of fifteen ratify at zero code cost**, because the implementation deliberately took
the plan's own §21 recommended defaults. Three carry a delta: D-P2-002, D-P2-007 and D-P2-015.

---

## 4. Implementation deltas if ratified as proposed

| # | Delta | Size | Blocking for |
|---|---|---|---|
| 1 | **D-P2-002** — replace `Sha256TokenHasher` with a peppered HMAC hasher and provision the pepper. Confined to the `TokenHasher` port and its wiring; engine, contracts and tests unaffected beyond the scheme identifier. | Small | Not blocking for test environments. Current unkeyed SHA-256 over a 256-bit token is not a vulnerability, only a weaker posture — if the Authority prefers to defer, record it as an accepted risk rather than leave it silent. |
| 2 | **D-P2-007** — implement an ES256 signer, KMS integration, JWKS endpoint and rotation runbook. `TokenSigner` already isolates the change; validator structural rules carry over. | Medium–large | **Blocking for any production activation.** The shipped `DeterministicTestSigner` is symmetric and non-production. |
| 3 | **D-P2-015** — durable append-only audit sink plus outbox/reconciliation for events that cannot join the same transaction. | Medium | Blocking for production; fail-closed behaviour is already correct. |

---

## 5. Ratification

To ratify: set **Status: Accepted** on each ADR in `docs/adr/ADR-0010.md`..`ADR-0019.md`,
complete the approval record block in each, and record the outcome against `DEC-0009` in
[`DECISION-REGISTER.md`](DECISION-REGISTER.md).

Per [`approval-policy.md`](../00-governance/approval-policy.md), security, tenant-isolation,
authorization and privacy decisions require **Security Authority concurrence**. That applies
to ADR-0011, ADR-0012, ADR-0015, ADR-0016, ADR-0017, ADR-0018 and ADR-0019.

Ratifying these ten ADRs and fifteen decisions satisfies two of the twelve
`BOPEN-P2-001` §23 entry-gate items. **It does not by itself open the entry gate**, which also
requires the baseline receipt, named maker/checker/security-reviewer/completion-authority, the
approved token and key-management contract, a frozen broker version and dependency lock, and a
recorded **GO**.

## 6. Authoring note

This docket and the ten ADRs were authored by the maker agent. They carry **no approval
authority**. Per `BOPEN-P2-001` §22 the Engineering Authority approves ADRs and the maker
implements only authorized paths; the maker has not signed any approval record and has not
recorded the entry-gate decision.
