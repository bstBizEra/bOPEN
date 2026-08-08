# MILE-4.2 — Document foundation, advisory review

**Document ID:** `REVIEW-MILE-4.2-DOCUMENT`
**Version:** `1.0.0`
**Status:** **Advisory review — no authorization, no build.** Document remains gated ([`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §9). This closes the review step of the operator's sequential foundation study (Document → Location → Notification → Calendar); Location's research enters next.
**Issued:** 2026-08-05
**Reviewer:** Claude (agent, Motor role) — advisory only, no approval authority
**Recorded by:** Codex (agent) — document control and traceability only; not the reviewer
**Subject:** [`RESEARCH-MILE-4.2-DOCUMENT`](MILE-4.2-document-foundation-research.md) (authored by Codex) and [the Document foundation page](../05-foundation/document/README.md)
**Reviewer standpoint:** built and disposed the Party/Money/Workflow/UOM foundations and the hybrid-tenancy machinery (placement, dedicated-DB provisioning, trial→paid migration), so this review focuses on alignment with those verified patterns and on the cross-slice interactions a document store has with them.

---

## 0. Scope and control baseline

This advisory review evaluates a research/design artifact, not implementation. Its control baseline
requires an authenticated **Principal** with active **Membership** and server-validated **active
tenant context**; **authorization** and **entitlement** are evaluated as separate gates. Tenant-owned
data requires forced **RLS**, default-deny behavior, fail closed handling, and zero **cross-tenant**
disclosure. The **platform** foundation exposes versioned **module/package capability** contracts;
durable changes use a transactional **outbox**, domain **events**, and correlated **audit** evidence.
Verification requires named executed **tests**, traceable **evidence**, explicit acceptance criteria,
and an exit gate that remains closed when a non-waivable control is unknown.

## 1. Overall assessment

**Sound and well-bounded; recommend proceeding to authorization once the §10 decisions are made and
the cross-slice items in §4 below are folded into the build plan.** The recommended shape — a
tenant-scoped Document Registry with immutable versions and a provider-neutral content-storage adapter
— is the right foundation: it owns identity, metadata, lineage, retention/hold and audit while
delegating durable bytes to a replaceable adapter, and it deliberately excludes full DMS, OCR and
e-signature. That boundary discipline matches how Money and UOM were scoped (one property defended,
the rest deferred), and the research's refusal-test matrix (§9) maps cleanly onto the EBIV model.

## 2. Where it aligns with the verified bOPEN patterns (strengths)

- **Identity separated from content**, using OASIS CMIS as a *requirements source only* (clean-room,
  `AGENTS.md` §6) — the same posture Money/UOM took toward ISO-4217 and SI/UCUM.
- **`ContentObject` is opaque**; tenant, bucket, key, credentials and encryption context are never
  accepted from an untrusted client. Short-lived, single-purpose, size/type-constrained transfer
  grants; an old URL is not continuing authority. This is the right shape for object storage.
- **Fail-closed throughout** — missing/expired/ambiguous context refuses; a scanner outage refuses
  *availability* rather than opening it; length+digest verified before a version becomes `available`.
  This is the EBIV/`AGENTS.md` §8 discipline the kernel already enforces elsewhere.
- **Two independent state axes** (`content_processing` vs `document_lifecycle`) prevent the classic
  conflation of "uploaded" with "usable", and the `deleted_tombstone` preserves identity/lineage/audit
  without content — good for retention and for not breaking references.
- **Forced RLS per row** as defense in depth, explicitly *not* a substitute for service authorization.

## 3. The refusal-test matrix (§9) is strong

The eleven invariants (tenant isolation, transfer authority, integrity, quarantine, immutability, link
authorization, retention/hold, idempotency, concurrency, cleanup, audit) are the right negatives, and
requiring each to trace to a named executed test at an exact commit/tree is exactly the EBIV R2/R4/R5
bar the disposed foundations met. No change needed here beyond executing it.

## 4. Cross-slice interactions to fold into the build plan (the review's main value)

These are the couplings a document store has with the tenancy/migration machinery already built and
disposed. None is a flaw in the research; each is a build-time obligation worth naming now.

1. **Every tenant-scoped table must be registered in TWO places, and a control enforces it.** The
   proposed `documents`, `document_versions`, `document_links`, `retention_assignments`, `holds` and
   `document_history` are all tenant-scoped. Each must be added to **`TENANT_SCOPED_TABLES`**
   (`tests/isolation/test_rls_database_behavior.py`) **and** to the trial→paid migrate tool's
   **`COPY_ORDER`** (`tools/migrate_tenant_to_dedicated.py`). The coverage test
   `INV-MIGRATE-COVERAGE-01` fails the suite if the two disagree — it caught exactly this for UOM's
   `uom_custom_units` on 2026-08-05. Design the migration order (parents before children:
   `documents` → `document_versions`/`document_links`/`retention_assignments`/`holds` →
   `document_history`) up front.

2. **Content placement vs the trial→paid migration — the one to decide before building.** When a
   tenant migrates shared→dedicated, the migrate tool copies its *metadata rows* into the dedicated
   database, but the **content lives in object storage and does not move**. So the `ContentObject`
   reference must be **placement-portable** — still resolvable to the same bytes after the control
   registry flips the tenant to `dedicated`. Two questions the research leaves open (§6 mentions
   "regional placement" but not this): (a) does a paying/dedicated tenant get a **dedicated bucket or
   prefix**, or does content stay in the shared object store keyed by tenant? and (b) if content is
   ever to follow the tenant, that is a *second* cross-database/store move on top of the metadata
   migration and should be an explicit, separately-gated slice. Recommend: first slice keeps content
   in a tenant-namespaced shared store and makes the reference portable; dedicated content storage is
   a later decision.

3. **Append-only must survive cascade deletion, not only direct writes.** `document_history` and
   immutable `document_version` content are append-only. The immutability invariant (§9) names
   content-replacement, but should also name **cascade deletion**: deleting a `Document` must not
   silently `ON DELETE CASCADE` away its history/versions. This is the exact failure migration 014
   fixed for `workflow_history` (a verifier reproduced a cascade that erased an append-only trail).
   Use `ON DELETE RESTRICT` (or the tombstone path) so a document with history cannot be hard-deleted
   out from under it; a policy-permitted content deletion is the `deleted_tombstone`, which the design
   already has.

4. **The migration freeze already covers document writes (no action, worth knowing).** Because every
   tenant-scoped write goes through `db.tenant_session`, a document create/version/link during a
   trial→paid migration is refused by the `TenantMigratingError` freeze automatically. The foundation
   inherits that safety for free.

## 5. Minor notes

- **Outbox (§7):** a transactional outbox already exists (`usage_outbox`, migration 002). State
  whether Document reuses that pattern/table or adds its own, so the event-delivery mechanism is one
  auditable thing rather than two.
- **Reference consumer (§10.1):** **PropTech** is the strongest first consumer — title deeds and land
  documents pair naturally with the UOM area units (`rai`/`ngan`) just disposed, giving a real
  end-to-end slice without building the product.
- **Media-type verification (§6):** verifying rather than trusting the client's declared type is
  correct; name the verification library/approach in `BOPEN-DOC-001` so it is testable, not assumed.

## 6. Recommendation and what remains before any build

The design is ready to move toward a first slice **after**:

1. the operator resolves the §10 decisions (reference consumer, storage profile/residency, scanning
   policy + outage behavior, retention/hold administration, link cardinality, proxied vs direct
   transfer, classification/size/type/key-ownership/deletion SLA);
2. the build plan adopts the §4 cross-slice obligations (classification + `COPY_ORDER`, content
   placement portability, append-only cascade protection);
3. the successor artifacts named in the research (§10) are produced — a `DEC-P4-ENTRY` gate amendment,
   `BOPEN-DOC-001`, the storage ADR, the migration/rollback plan, threat model and test matrix — and
   authorization is recorded **before** any build, as it was for Money/Workflow/UOM.

This review authorizes nothing and builds nothing. Document remains gated; Location's research is the
next step in the operator's sequence.

## 7. Traceability and review disposition

### 7.1 Reviewed artifact and registration baseline

| Field | Value |
| :--- | :--- |
| Reviewed artifact | `docs/01-product/MILE-4.2-document-foundation-research.md` |
| Document ID | `RESEARCH-MILE-4.2-DOCUMENT` version `1.0.0` |
| Subject SHA-256 | `48ab486dcb8c68c7537e7b9f184d48ca4c470a1635b8907636e5c58c1425415d` |
| Subject Git blob (computed, not yet committed) | `fdf80ea5acd1e4337a5d3f707687a6a6d560176a` |
| Subject size | `13,239` bytes |
| Original review commit | `6aa2d0be5cf339ebec54ff55369e147904aee214` |
| Original review tree/blob | tree `812ebeb6d91ca77ec2ccee69b1f09b32100d541f`; review blob `6f54840e98f035b60da99728b1af14feed8b4b2e` |
| Revision caveat | The original advisory review is committed, but its research subject was uncommitted. The subject SHA-256/computed blob bind the reviewed bytes; this traceability addendum is also a working-tree change until a later controlled commit anchors it. |

The original review commit identifies the surrounding governed state and the pre-addendum review. It
is **not** represented as a candidate containing the uncommitted research subject or this addendum.

### 7.2 Evidence examined

| Evidence ID | Procedure | Result | Scope/limit |
| :--- | :--- | :--- | :--- |
| `DOC-REV-E01` | `check_architecture.py ... --strict` against the subject | **PASS — 100%**, all six control groups | Static architecture completeness, not implementation evidence |
| `DOC-REV-E02` | `tools/validate_repository.py` | **PASS** | Repository/governance structure only |
| `DOC-REV-E03` | `tools/check_clean_room.py` | **PASS** | Clean-room repository check only |
| `DOC-REV-E04` | bopen-architecture package validation | **PASS — 36 checks** | Validates the review skill/package, not Document implementation |
| `DOC-REV-E05` | bopen-architecture static evaluations | **PASS — 8/8** | Deterministic skill evaluations, not runtime conformance |
| `DOC-REV-E06` | `git diff --check` | **PASS** | Text/whitespace check only |

The evidence was executed by Codex on 2026-08-05 in the local bOPEN workspace. No Document source,
migration, runtime, PostgreSQL behavior, storage adapter, backup/restore, security scan, or EBIV ballot
exists; none is claimed by this advisory review.

### 7.3 Findings register

| Finding ID | Severity | Control | Observation | Required action | Owner | Due | Evidence needed | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `DOC-REV-F01` | medium | Tenant migration coverage | Every new tenant table must stay aligned between `TENANT_SCOPED_TABLES` and `COPY_ORDER` | Freeze table list and parent-before-child copy order in the work package | Future Document maker | Before build authorization | Coverage and live trial-to-paid migration tests | **Open** |
| `DOC-REV-F02` | high | Content placement portability | Metadata may migrate shared→dedicated while binary content remains external | Decide the first-slice storage placement and prove opaque references survive placement change | Architecture Authority | Before build authorization | Storage ADR plus migration/recovery probe | **Open** |
| `DOC-REV-F03` | high | Append-only integrity | Direct-write protection alone does not prevent cascade deletion of versions/history | Use tombstone/restrict semantics and test parent-delete refusal | Future Document maker | Before candidate ballot | Live PostgreSQL direct and cascade refusal tests | **Open** |
| `DOC-REV-F04` | medium | Event delivery | The research does not yet select reuse/extension of the existing outbox mechanism | Bind one auditable outbox contract and recovery behavior | Architecture Authority | Contract freeze | Event contract and replay/dead-letter evidence | **Open** |
| `DOC-REV-F05` | low | Content validation | Media-type verification is required but the mechanism is not yet selected | Name the replaceable validation interface and acceptance/refusal rules | Security reviewer | Contract freeze | Contract tests with mismatched and malformed content | **Open** |

### 7.4 Advisory disposition

**`APPROVE WITH CONDITIONS` — advisory research review only.** The proposed boundary is suitable to
serve as the basis for the next controlled decision package, subject to `DOC-REV-F01` through
`DOC-REV-F05` and the operator decisions listed in the research §10. This disposition:

- closes the Document **research review step** in the sequential study;
- permits Location research to be prepared next under the recorded sequence;
- does not accept `BOPEN-DOC-001`, because it does not yet exist;
- does not authorize Document implementation, source mutation, migration, provider selection,
  release, deployment, production activation, or an EBIV verdict;
- does not convert the surrounding repository baseline into a reviewed implementation candidate.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
