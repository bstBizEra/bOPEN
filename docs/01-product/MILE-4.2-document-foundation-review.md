# MILE-4.2 — Document foundation, advisory review

**Document ID:** `REVIEW-MILE-4.2-DOCUMENT`
**Version:** `1.0.0`
**Status:** **Advisory review — no authorization, no build.** Document remains gated ([`DEC-P4-ENTRY`](../decisions/DEC-P4-ENTRY.md) §9). This closes the review step of the operator's sequential foundation study (Document → Location → Notification → Calendar); Location's research enters next.
**Issued:** 2026-08-05
**Reviewer:** Claude (agent, Motor role) — advisory only, no approval authority
**Subject:** [`RESEARCH-MILE-4.2-DOCUMENT`](MILE-4.2-document-foundation-research.md) (authored by Codex) and [the Document foundation page](../05-foundation/document/README.md)
**Reviewer standpoint:** built and disposed the Party/Money/Workflow/UOM foundations and the hybrid-tenancy machinery (placement, dedicated-DB provisioning, trial→paid migration), so this review focuses on alignment with those verified patterns and on the cross-slice interactions a document store has with them.

---

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

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
