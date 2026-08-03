# BOPEN-BERP-PLAN-001 — Post-production ERP Solution Plan

**Version:** 0.2.0
**Status:** Planned Direction — deferred; no implementation authority
**Owner:** Product Authority
**Issued:** 2026-08-03
**Updated:** 2026-08-03
**Governing artifacts:** `BOPEN-ARCH-001`, `BOPEN-TENANT-001`, `BOPEN-AUTHZ-001`,
`BOPEN-MOD-001`, `BOPEN-ENT-001`, `docs/01-product/product-boundary.md`
**Dependent future artifact:** `BOPEN-BERP-001` work package — not yet raised or accepted

---

## 1. Announcement

bOPEN will complete its governed platform-kernel path first. The ERP solution program begins
**only after both** of these conditions are recorded:

1. the applicable bOPEN Alpha scope has completed its accepted test and independent-verification
   gates; and
2. a production-version baseline has been versioned, operationally qualified, and accepted by the
   appropriate authority.

Passing Alpha tests alone does not open ERP implementation. A production deployment is also not
implied by this plan. Entry requires a separately accepted `BOPEN-BERP-001` work package after the
two conditions above are met.

This announcement does not change, reopen, delay, or add acceptance criteria to any current bOPEN
phase, milestone, decision, or work package.

## 2. Product boundary

bOPEN remains the platform governance kernel and owns shared platform concerns:

- principal, identity, tenant, membership, and active context;
- authorization, entitlement, capability registration, and module availability;
- cross-product audit correlation, integration contracts, and tenant placement metadata.

The ERP solution owns ERP business execution. ERPNext is the intended initial ERP engine, without
becoming part of the bOPEN kernel. It may own:

- accounting and the general ledger;
- accounts receivable, accounts payable, invoicing, payment, and tax processing;
- procurement, inventory, assets, and other selected ERP capabilities;
- ERP operational workflows and financial statements.

Other industry systems remain separate products. They integrate later through versioned APIs and
domain events rather than sharing ERPNext or bOPEN database tables.

## 3. System-of-record rules

1. ERPNext is the sole posting authority for the ERP general ledger unless a later approved
   decision replaces it.
2. Industry products emit business outcomes or accounting requests; they do not maintain a second
   competing ledger.
3. Customer, supplier, item, and party ownership must be decided contract-first before
   bidirectional synchronization is authorized.
4. A bOPEN `Tenant` is not an ERPNext `Company`. The planned default mapping is a bOPEN tenant to a
   Frappe Site, with one or more ERPNext Companies inside that site; the final cardinality requires
   a future approved decision.
5. Cross-system database access and cross-database foreign keys are prohibited. Integration uses
   versioned contracts, idempotency keys, correlation IDs, outbox/inbox delivery, and
   reconciliation evidence.

## 4. Deferred execution sequence

| Stage | Outcome | Entry condition |
|---|---|---|
| ERP-0 | Accept `BOPEN-BERP-001`, source-of-truth matrix, tenancy mapping, security review, and rollback plan | Alpha and production baseline conditions both met |
| ERP-1 | Establish ERPNext operational baseline and Accounting/General Ledger | ERP-0 accepted |
| ERP-2 | Add Finance, procurement, inventory, assets, and other selected ERP modules | Each module has an accepted contract and owner |
| ERP-3 | Connect independent industry products through APIs and domain events | Idempotency, reconciliation, failure handling, and audit evidence pass |
| ERP-4 | Enable commercial module composition through bOPEN capabilities and entitlements | Cross-system authorization and tenant-isolation evidence pass |

No stage is authorized by this document.

## 5. Production-baseline entry evidence

The future ERP work package shall not be accepted until the production-version baseline identifies:

- the exact bOPEN release commit, tree, version, and supported contract versions;
- admissible security, tenant-isolation, authorization, and end-to-end evidence for its declared
  production scope;
- deployment, upgrade, rollback, backup/restore, disaster-recovery, observability, and incident
  procedures;
- unresolved defects and explicit operational limitations;
- the authority responsible for release acceptance and production activation.

This is a planning boundary, not a claim that the current bOPEN tree is production-ready.

## 6. Traceability and non-effects

- Product boundary: `docs/01-product/product-boundary.md`.
- Existing bERP profile: this document supersedes the former two-line conceptual note at this
  path while preserving its rule that ERPNext is not the bOPEN kernel.
- Research basis: Frappe Site is the operational isolation unit; ERPNext Company is an internal
  business structure, not the bOPEN tenant-security boundary.
- Current implementation: unchanged.
- Current contracts: unchanged.
- Current phase and milestone gates: unchanged.
- Merge, deployment, release, and production activation authority: not granted.

## 7. Approval

The operator directed this plan to be recorded on 2026-08-03 as work that follows bOPEN Alpha and
the production-version baseline. Architecture, contract, security, implementation, deployment,
and activation decisions remain subject to their own future governed artifacts.
