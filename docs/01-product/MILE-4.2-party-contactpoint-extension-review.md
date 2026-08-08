# MILE-4.2 — Party ContactPoint extension, independent advisory review

**Document ID:** `REVIEW-MILE-4.2-PARTY-CONTACTPOINT`  
**Version:** `1.0.0`  
**Status:** **Independent advisory review — RETURN FOR REVISION.** During this review, the operator's separate implementation authorization was recorded at [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §10 (commit `59145875037e21cf3a1b9c9ae1488e9696477a36`). That authority does not convert this review to approval or close its findings.  
**Issued:** 2026-08-05  
**Reviewer:** Codex (agent, verifier role for this design review) — advisory only; no approval or disposition authority  
**Subject:** [`RESEARCH-MILE-4.2-PARTY-CONTACTPOINT`](MILE-4.2-party-contactpoint-extension-research.md), raised by Claude (agent, Cortex role)  
**Governing:** `AGENTS.md` §§2, 4–16, 20.3; [`BOPEN-GOV-EBIV-001`](../00-governance/BOPEN-GOV-EBIV-001.md); [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §10; `BOPEN-PARTY-001`  
**Authority boundary:** This is an independent architecture review of an unimplemented design. It is not an EBIV ballot on code, operator disposition, implementation authorization, release, deployment, or production evidence.

---

## 1. Reviewed artifact and revision

| Field | Value |
| :--- | :--- |
| Reviewed artifact | `docs/01-product/MILE-4.2-party-contactpoint-extension-research.md` |
| Document ID/version | `RESEARCH-MILE-4.2-PARTY-CONTACTPOINT` version `1.0.0` |
| Maker/raiser recorded in subject | Claude (agent, Cortex role) |
| Reviewer | Codex (agent) |
| Independence conclusion | Codex is not recorded as author or editor of the subject; this review does not modify the subject |
| Subject SHA-256 | `a900b1e33268afe07c04e9235dc79f2f44c7014b8e2e8f3eb53f33b708b1ad79` |
| Subject Git blob | `0aac8185964dce213681a54e3f1c74c138044f5b` (computed; subject is uncommitted) |
| Subject size | `38,618` bytes |
| Surrounding repository baseline | commit `08a48795d7a1037051ed21e27f9ff3099da16943`; tree `4bd9f189066874efc0015d505e6d720c3c54df9c` |
| Anchor limitation | The subject is an untracked working-tree file. Its SHA-256 and computed Git blob bind the bytes reviewed, but no commit currently contains it or this review. |
| Concurrent state change | HEAD advanced during review to authorization commit `59145875037e21cf3a1b9c9ae1488e9696477a36` (tree `2af212cc1fd9a6a3bf387b9ad1c77a02dc1b2932`), and uncommitted implementation files appeared. They were not part of the design subject or this verdict. |

The review therefore establishes byte-level traceability to the local subject, not a claim that the
subject belongs to the baseline commit.

## 2. Scope and control baseline

The review asks whether the proposed ContactPoint extension preserves the Party/Principal/Notification
boundaries and is sufficiently specified to become an authorization candidate. The baseline requires:

- Party-owned contact data must remain distinct from authentication identity and Notification state;
- the bOPEN platform owns the shared Party package and exposes ContactPoint only through versioned
  module capability contracts; Notification remains a separate consumer;
- an authenticated Principal, active Membership, server-validated tenant context, authorization,
  entitlement, and module/capability state must be separate gates;
- tenant data must use forced RLS, default deny, same-tenant database integrity, and zero cross-tenant
  disclosure;
- verification evidence must bind to the exact endpoint value it proves and survive mutation or
  deletion attempts;
- consent, purpose, verification, preference, suppression, and delivery outcome must not be conflated;
- sensitive endpoints must not leak through lookup, logs, events, exports, hashes, or error behavior;
- durable domain events must use a transactional outbox and remain correlated with append-only audit
  evidence without carrying a raw endpoint;
- implementation remains closed until contracts, decisions, named tests, exact candidate evidence,
  independent ballot, and operator disposition exist.

External standards named by the subject were treated as informative vocabulary/syntax inputs. They do
not replace an owned bOPEN trust, consent, normalization, or verification contract.

## 3. Overall assessment

The proposed ownership boundary is correct: **ContactPoint belongs to Party, Notification consumes a
one-send snapshot, and `principals.email` is never an implicit business destination.** Composite
tenant foreign keys, forced RLS, uniform refusal, append-only evidence, migration inventory coverage,
and the explicit closed verification seam are all strong choices.

The design is not yet safe to advance as an authorization candidate. Its update capability permits
the endpoint value to change on the existing record, while no invariant requires that such a change
invalidate the old verification. This creates a direct destination-integrity gap: a newly written
address or phone could retain `verified` evidence earned by the old value. The design also uses
"authorized" and "consented" purpose language where the model stores only a purpose classification,
and its verification state currently absorbs bounce/complaint signals that belong to delivery,
suppression, or endpoint lifecycle.

These are contract-level gaps, not implementation details. They must be resolved in the research and
future `BOPEN-PARTY-002` before authorization.

## 4. Findings

| ID | Severity | Control | Observation | Required action | Owner | Due | Evidence needed | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `CP-REV-F01` | **high** | Verification binding / destination integrity | `party.contact_point.update` may change `endpoint_value`, but no invariant forces the prior verification to become unusable. The row can therefore represent a new destination with old verification evidence. | Make endpoint value immutable by version, or atomically reset the contact point to `unverified`, clear current verification evidence, append an invalidation event, and require fresh verification whenever the normalized destination changes. A stale snapshot must remain historical evidence only and must never authorize a later send. | ContactPoint design owner | Before authorization candidate | Contract state machine plus tests proving verified→value-change cannot resolve until the new value is verified | **Open — blocking revision** |
| `CP-REV-F02` | **high** | Consent/purpose/authorization separation | The executive summary and keystone call a purpose field "consented" or "authorized", but §10.4 says consent, suppression, and verification are separate. A stored purpose code is not evidence that contacting the Party is currently lawful or permitted. | Rename the field semantics to purpose classification/eligibility. Define the resolver as technical endpoint resolution only, or require an explicit policy decision/grant input. Notification must independently evaluate consent, preference, suppression, authorization, and mandatory-message policy before dispatch. `RecipientSnapshot` must not assert consent. | Architecture Authority + Notification design owner | Before contract freeze | Owned purpose/consent contract and refusal tests for withdrawn consent, suppression, and wrong purpose | **Open — blocking revision** |
| `CP-REV-F03` | medium | Principal/membership/context chain | Static architecture validation found the `principal-membership-context` control group incomplete. The resolver request names tenant/context but does not explicitly bind authenticated principal, active membership or delegated service grant, authorization, entitlement, and module state. | Add the full server-validated execution chain and fail-closed rules for human/service callers. Client-supplied tenant or Party identifiers remain input, never authority. | ContactPoint design owner | Before authorization candidate | Updated contract and named missing/inactive/wrong-tenant/unauthorized/missing-entitlement tests | **Open** |
| `CP-REV-F04` | medium | State-machine integrity | `failed` mixes verification failure with hard bounce, complaint, and re-check failure; `retire` exists as a capability without a separate endpoint lifecycle state. These facts have different owners and recovery rules. | Separate endpoint lifecycle (`active`, `suspended`, `retired`, as decided) from ownership/control verification. Treat bounce/complaint as delivery/suppression inputs unless a governed rule explicitly invalidates verification. Define every allowed and refused transition. | ContactPoint + Notification design owners | Before contract freeze | Two-axis state model and invalid-transition matrix | **Open** |
| `CP-REV-F05` | medium | Evidence integrity | Verification history is described conditionally ("If verification carries history" and "if versioned") although `CP-INV-07` depends on append-only evidence. | Make verification/lifecycle evidence mandatory whenever verification state exists; bind each event to the exact endpoint-value version or keyed digest, method, actor/service, correlation, and transition. Preserve it with `ON DELETE RESTRICT` or a governed tombstone. | ContactPoint design owner | Before authorization candidate | Schema contract plus direct-update, direct-delete, and parent-cascade refusal tests | **Open** |
| `CP-REV-F06` | medium | Endpoint confidentiality | "Safe hashes" and encryption/tokenization "where practical" are not a defined privacy boundary. A stable unkeyed email/phone hash is enumerable and can become a cross-tenant correlation key. | Select the protection contract before build: ciphertext/token plus tenant-scoped keyed lookup material where lookup is required; prohibit global deterministic hashes, cross-tenant uniqueness, raw values in telemetry, and unrestricted exports. Define key rotation and recovery. | Security + Architecture Authorities | Before contract freeze | Threat model, crypto/key ADR, redaction tests, key-rotation and backup/restore evidence plan | **Open** |
| `CP-REV-F07` | low | Value normalization | RFC 5322 syntax and E.164 numbering form do not by themselves establish deliverability, ownership, or a universal safe canonicalization rule. | Preserve entered/display form separately from normalized routing value; define conservative, versioned per-type normalization and refuse unsupported ambiguity. Do not infer verification from syntax. | ContactPoint design owner | Contract freeze | Normalization fixtures including international, case, Unicode, malformed, and ambiguous inputs | **Open** |

## 5. Tenant-isolation verdict

**Design direction passes; evidence does not yet exist.** Tenant ownership, composite
`(tenant_id, party_id)` integrity, forced RLS, default deny, `db.tenant_session`, opaque refusal, and
trial-to-paid registration are correctly required. The future package must also test indirect leakage
through search, export, cache, background jobs, events, logs, keyed lookup material, and dedicated
placement. Unknown cross-tenant behavior remains a closed exit gate.

## 6. Authorization and entitlement verdict

**Incomplete.** The capability list is useful, but the design must explicitly bind authenticated
Principal/service identity, active Membership or delegated grant, validated context, entitlement,
module enablement, and per-action authorization. `resolve` being service-scoped does not itself grant
permission to send, and verification/purpose do not establish consent or policy authorization.

## 7. Data, event, audit, and recovery verdict

The append-only/cascade lesson and `TENANT_SCOPED_TABLES`/`COPY_ORDER` obligations are well carried
forward. Before authorization, the model must bind verification to an immutable value version,
separate lifecycle from verification and delivery feedback, make history mandatory, select protected
lookup material, and define key rotation, backup/restore, retention, deletion, idempotency, and
concurrent primary selection. Events must omit raw endpoints and any globally correlatable digest.

## 8. Evidence examined

| Evidence ID | Procedure | Result | Scope/limit |
| :--- | :--- | :--- | :--- |
| `CP-REV-E01` | SHA-256 and `git hash-object` over the subject | **PASS** — hashes recorded in §1 | Byte identity only; subject remains uncommitted |
| `CP-REV-E02` | Repository inspection of migration 010 | **PASS** — `parties(tenant_id,id)` uniqueness, composite Party-relationship FKs, forced RLS observed | Existing Party behavior, not ContactPoint evidence |
| `CP-REV-E03` | Repository inspection of migration 014 | **PASS** — append-only parent FK uses `ON DELETE RESTRICT` | Existing Workflow precedent only |
| `CP-REV-E04` | Inspection of `TENANT_SCOPED_TABLES`, `COPY_ORDER`, and migration coverage test | **PASS** — cross-inventory fail-loud control exists | Future ContactPoint tables do not exist |
| `CP-REV-E05` | `check_architecture.py <subject> --strict` | **FAIL — 83%**; `principal-membership-context` control group incomplete | Static design completeness, not runtime conformance |

No ContactPoint implementation artifact is included in this design verdict. Uncommitted migration,
repository, API, and test files appeared concurrently after the subject was bound; they require a
separate exact-candidate review and EBIV ballot. The live authority-bootstrap run consequently found
the working-tree `COPY_ORDER` names while the configured verification database lacked migration 019,
and failed two trial-to-paid tests with `UndefinedTable: party_contact_points`. That is disclosed as
concurrent environment/candidate drift, not treated as evidence for or against this design verdict.

## 9. Conditions and final disposition

**`RETURN FOR REVISION`.** `CP-REV-F01` and `CP-REV-F02` are load-bearing boundary defects in the
current proposal; the remaining findings must be resolved or explicitly governed before contract
freeze. A revised subject should:

1. bind verification to an immutable endpoint value/version and invalidate it on every value change;
2. separate purpose classification from consent, suppression, authorization, and dispatch policy;
3. add the full Principal → Membership/grant → active context → authorization → entitlement/module
   execution chain;
4. separate endpoint lifecycle, verification state, and delivery/suppression facts;
5. make append-only evidence and the endpoint confidentiality/key contract non-optional; and
6. rerun strict architecture validation and bind the revised bytes to a commit before any authorization
   decision.

This closes the **independent review action** by recording a falsifiable disposition and revision
conditions. It does not close the ContactPoint design as accepted, does not add to or retract the
operator's separately recorded implementation authority, and does not dispose an EBIV verdict.
Operator and Architecture Authority decisions remain separate.

```text
execution_authority: false
approval_authority: false
ebiv_ballot: false
operator_disposition: false
production_activation_authority: false
completion_claimed: false
```
