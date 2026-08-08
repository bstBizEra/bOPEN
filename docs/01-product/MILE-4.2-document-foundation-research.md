# MILE-4.2 — Document foundation, research & design

**Document ID:** `RESEARCH-MILE-4.2-DOCUMENT`  
**Version:** `1.0.0`  
**Status:** **Research — advisory. A future slice; buildable only on operator authorization.** Document remains gated by [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §9.  
**Issued:** 2026-08-05  
**Owner:** Architecture & Engineering Authority  
**Raised by:** Codex (agent, advisory role) — no approval authority  
**Governing:** `AGENTS.md` §§2, 7–15; [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md); [`CAPABILITY-MATRIX`](CAPABILITY-MATRIX.md)  
**Dependent artifacts:** Future `BOPEN-DOC-001`, accepted work package, object-storage ADR, contracts, threat model, test matrix, and EBIV evidence  
**Clean-room:** Standards and products are requirements sources only; no upstream implementation is copied.

---

## 1. Executive summary

The recommended foundation is a **tenant-scoped Document Registry with immutable versions and a
provider-neutral content-storage adapter**. bOPEN owns document identity, metadata, version lineage,
links to governed resources, retention/hold state, access decisions, content integrity, and audit.
An object-storage provider owns durable binary storage behind a replaceable adapter.

The foundation is not a full document-management suite. Editing, collaboration, OCR, e-signature,
records classification, rich search, and product-specific document workflows remain separate slices.
The first slice should support secure upload, quarantine/validation, immutable versions, authorized
download, resource linking, archive/retention, and provider replacement without exposing storage
credentials or bucket keys.

### 1.1 Remaining-foundation research sequence

The operator directed that the remaining foundations be researched **sequentially**, not treated as
one simultaneous design package:

| Order | Foundation | Research boundary | Entry to research |
| :---: | :--- | :--- | :--- |
| **1 — current** | Document | Registry/version/retention + storage adapter; not full DMS/OCR/e-signature | This document |
| 2 | Location | Address/place/point/provenance; not GIS/routing/telemetry | Document research reviewed |
| 3 | Notification | Reliable transactional delivery; not marketing automation/chat | Location research reviewed |
| 4 | Calendar | Business calendar/working-time rules; not booking/shift/general recurrence | Notification research reviewed |

Research completion does not authorize implementation. Each foundation remains independently gated,
and any later build proceeds one foundation at a time under its own authorization and evidence cycle.

## 2. Boundary

### In scope

- document identity and tenant-owned metadata;
- immutable content versions with byte length, media type, and cryptographic digest;
- logical links from a document to one or more authorized bOPEN resources;
- provider-neutral blob storage and short-lived authorized transfer grants;
- upload processing state, malware/format validation seam, quarantine, and rejection;
- retention policy, legal/administrative hold seam, archive, and deletion eligibility;
- append-only version/history and correlated audit/domain events;
- idempotency, optimistic concurrency, RLS, backup/restore, and integrity verification.

### Out of scope

- collaborative editing, office rendering, comments, annotation, check-in/check-out, and folders as
  a universal business hierarchy;
- OCR, classification AI, semantic search, thumbnailing, and format conversion implementations;
- electronic-signature ceremonies and certificate validation;
- product-specific evidence admissibility or statutory records schedules;
- public file hosting, anonymous sharing, permanent pre-signed URLs, and direct client-chosen keys;
- storing binary content in the transactional PostgreSQL database by default.

## 3. Domain distinctions

| Concept | Meaning | Must not be confused with |
| :--- | :--- | :--- |
| `Document` | Stable tenant-owned logical document identity | One binary file or one version |
| `DocumentVersion` | Immutable metadata and content reference for one submitted version | Mutable current document metadata |
| `ContentObject` | Provider-neutral reference to encrypted binary bytes | Client-visible bucket/key or database row containing the bytes |
| `DocumentLink` | Authorized relation to a business/platform resource | Ownership of that resource or permission to access it |
| `RetentionPolicy` | Rule controlling deletion eligibility | Backup retention or product-specific legal advice |
| `Hold` | Explicit suspension of eligible deletion | Ordinary archive state |
| Evidence record | A product/governance claim about evidentiary meaning | Any uploaded document automatically becoming evidence |

OASIS CMIS separates a document object from its content stream and uses stable object identity; that
pattern supports the bOPEN separation without requiring CMIS compatibility in the first slice.

## 4. Options

| Option | Boundary | Operability | Portability | P0 fit | Disposition |
| :--- | :---: | :---: | :---: | :---: | :--- |
| Full ECM/DMS in bOPEN | 1 | 2 | 2 | 1 | Reject — excessive scope and product overlap |
| Raw object-store URLs owned by each product | 1 | 2 | 1 | 4 | Reject — inconsistent authz, retention, lineage, and tenant isolation |
| Registry + immutable versions + storage adapter | 5 | 5 | 5 | 4 | **Recommend** |

## 5. Proposed model and lifecycle

```text
Document
  ├─ DocumentVersion[] ──> ContentObject (provider adapter)
  ├─ DocumentLink[] ──> governed resource
  ├─ RetentionAssignment[]
  └─ DocumentHistory[]
```

Proposed entities: `Document`, `DocumentVersion`, `DocumentLink`, `RetentionAssignment`, `Hold`, and
`DocumentHistory`. The storage adapter returns an opaque content reference; the tenant, bucket, key,
credentials, and encryption context are never accepted from an untrusted client.

Two independent state axes prevent conflation:

```text
content_processing: pending_upload -> quarantined -> available | rejected
document_lifecycle: active <-> archived -> deletion_pending -> deleted_tombstone
```

Only validated `available` content may be downloaded. A hold refuses transition to
`deletion_pending`. `deleted_tombstone` preserves identity, digest, lineage, deletion authority, and
audit metadata without retaining the content when policy permits deletion.

## 6. Security and data controls

- The execution chain is explicit: an authenticated **Principal** must hold an active
  **Membership**, operate through server-validated **active tenant context**, pass current
  **authorization**, and—where the commercial/module contract requires it—pass **entitlement** and
  module availability independently. Commercial access and action permission remain separate gates.
- Every row is tenant-owned with forced RLS; storage keys are additionally namespaced and bound to
  trusted tenant context by the server.
- RLS is default-deny defense in depth, not a replacement for service authorization. Missing,
  ambiguous, expired, inactive, or inconsistent context must fail closed. Cross-tenant disclosure
  through IDs, links, storage URLs, search, cache, events, logs, exports, support access, and provider
  callbacks is prohibited.
- Upload and download grants are short-lived, single-purpose, size/type constrained, and issued only
  after current authorization. Possessing an old URL is not continuing authority.
- Completion verifies expected length and a strong digest before a version becomes available.
- Deduplication, if later introduced, is tenant-local and must not create a cross-tenant existence
  oracle.
- Content remains quarantined until the configured validation/scanning policy succeeds. Scanner
  outage fails closed for availability, not open.
- Filenames are display metadata, never filesystem paths. Media type is verified rather than trusted
  solely from the client.
- Encryption, provider credentials, key rotation, backup, restore, regional placement, and deletion
  evidence are adapter-operational responsibilities governed by bOPEN contracts.
- Support access requires a time-bounded audited grant; content must not appear in logs, event bodies,
  or error messages.

## 7. Proposed capabilities and events

Capabilities: `document.create`, `document.read`, `document.version.add`, `document.download`,
`document.link.manage`, `document.archive`, `document.retention.manage`, `document.hold.manage`, and
`document.delete.request`.

Events: `document.created.v1`, `document.version_available.v1`, `document.version_rejected.v1`,
`document.link_changed.v1`, `document.archived.v1`, `document.hold_changed.v1`, and
`document.content_deleted.v1`.

Event payloads contain identifiers and safe metadata, not document bytes, pre-signed URLs, secrets,
or unrestricted filenames. Delivery uses the transactional outbox and consumer deduplication.

## 8. Proposed first slice

1. Freeze `BOPEN-DOC-001`, storage adapter, schemas, processing/lifecycle states, errors, and
   retention semantics.
2. Implement document registration, upload initiation/finalization, authorized download, version
   addition, resource linking, archive, and deletion eligibility.
3. Provide one development adapter and one explicitly selected production-candidate adapter behind
   identical contract tests; provider selection requires its own ADR.
4. Require content length/digest verification and a replaceable validation/scanning interface before
   making bytes available.
5. Add RLS, tenant-safe object naming, idempotency, concurrency, outbox, audit, backup/restore, and
   compensating cleanup for abandoned/failed uploads.
6. Validate first through a real consumer contract, recommended PropTech or bPro, without building
   that product inside this work package.

Deferred: OCR, previews, e-signature, public sharing, full-text search, collaboration, folder trees,
and product-owned records schedules.

## 9. Required refusal tests

| Invariant | Refusal/acceptance evidence |
| :--- | :--- |
| Tenant isolation | Wrong/missing context cannot list, link, download, search, infer, or delete foreign content |
| Transfer authority | Expired, reused, wrong-purpose, wrong-size, and wrong-tenant upload/download grants are refused |
| Integrity | Length/digest mismatch and incomplete upload remain unavailable |
| Quarantine | Unvalidated or rejected content cannot be downloaded, previewed, or linked as available |
| Immutability | Version content/digest cannot be replaced after availability; a new version is required |
| Link authorization | Linking does not grant document or target-resource access; unauthorized targets are refused without existence disclosure |
| Retention/hold | Premature deletion and deletion under active hold are refused |
| Idempotency | Retry creates no duplicate document, version, content object, or event |
| Concurrency | Stale metadata revision is refused |
| Cleanup | Failed finalization cannot orphan available DB metadata or silently retain untracked content |
| Audit | Accepted and refused sensitive operations are correlated without logging content/secrets |

### 9.1 Verification evidence and exit gate

Each invariant must be traced to a named executed test at an exact commit/tree, with environment,
procedure, result, verifier, timestamp, and failure-loud evidence. Acceptance criteria include live
PostgreSQL RLS behavior, real storage-adapter contract tests, failed-upload compensation, content
integrity, provider outage, backup/restore, and cross-tenant negative probes. The exit gate remains
closed when any non-waivable control is untested, evidence is missing, or cross-tenant behavior is
unknown. Maker evidence, an independent EBIV verifier ballot, operator disposition, release, and
production activation remain separate acts.

## 10. Decisions before authorization

1. Reference consumer: PropTech or bPro.
2. Production object-storage profile and data residency requirements.
3. Required validation/scanning policy and outage behavior.
4. Initial retention/hold semantics and who may administer them.
5. Whether multiple resource links are first-slice scope.
6. Whether download is proxied or short-lived direct transfer per deployment profile.
7. Data classification, maximum size, allowed types, encryption-key ownership, and deletion SLA.

Successor artifacts: operator gate amendment, `BOPEN-DOC-001`, storage ADR, provider contract,
migration/rollback plan, threat model, test matrix, work package, maker evidence, verifier ballot, and
operator disposition.

## 11. Source register

Retrieved 2026-08-05.

| Source | Use |
| :--- | :--- |
| [`CAPABILITY-MATRIX`](CAPABILITY-MATRIX.md) | Approved bOPEN purpose, dependencies, and consumers |
| [`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §9 | Current gate state |
| [OASIS CMIS 1.1](https://docs.oasis-open.org/cmis/CMIS/v1.1/CMIS-v1.1.html) | Stable document identity, content-stream separation, version/retention concepts |
| [IANA Media Types](https://www.iana.org/assignments/media-types/media-types.xhtml) | Governed media-type vocabulary |

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
