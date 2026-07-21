# QUAL-P0-02 — Synthetic Identity Qualification Subject

**Version:** 0.1
**Status:** Drafting authorized; not accepted
**Owner:** Security/Architecture Authorities
**Issue date:** 2026-07-22
**Dependencies:** Independently accepted QUAL-P0-00 commit `a2fc4b1f907b17911ffbd3cb8e0992b806c90bb6`; Program Goal v0.2
**Governing artifacts:** BOPEN-GOV-001 Draft; BOPEN-GOAL-001 Draft; BOPEN-ARCH-001 Draft; BOPEN-SEC-001 Draft
**Decision/qualification:** DEC-0005 Pending / DEC-0005-QUAL-001 Draft
**Evidence:** EVD-QUAL-002 maker evidence
**Maker:** Codex `/root/identity_qual_schema_blueprint`
**Checker:** Independent exact-SHA checker pending
**Branch/worktree:** `codex/QUAL-P0-02-identity-qualification` / `C:\laragon\www\bopen-worktrees\qual-p0-02-identity-qualification`
**Base SHA/tree:** `a2fc4b1f907b17911ffbd3cb8e0992b806c90bb6` / `a5a63d2fb882939f176139c9f276a8d44faaf6d9`

## Objective

Draft the immutable A-subject contracts for a provider-neutral, synthetic, two-issuer OIDC qualification. The package establishes exact issuer-plus-subject identity rules, denial coverage, redaction, deterministic evidence requirements and non-authority semantics. It does not execute qualification or select a provider.

## Allowed paths

```text
contracts/qualification/identity/*.schema.json
contracts/qualification/identity/QUAL-P0-02-SCHEMA-CATALOG.json
docs/07-security/identity/DEC-0005-QUAL-001.md
docs/work-packages/QUAL-P0-02.md
docs/evidence/EVD-QUAL-002-identity-qualification.md
docs/manifests/QUAL-P0-02-PACKAGE-MANIFEST.json
tools/validate_identity_qualification.py
tests/qualification/test_identity_qualification.py
```

## Prohibited paths and actions

Shared indexes, CI, package files, lock files, canonical manifests, common QUAL-P0-00 contracts, other qualification domains, runtime/application/service/database/infrastructure/migration code, real tokens or credentials, qualification execution, provider selection, merge, release and activation are prohibited.

## Deliverables and acceptance criteria

1. Eight closed Draft identity qualification schemas and one digest-pinned offline catalog.
2. Exact import of the accepted QUAL-P0-00 catalog without network fallback.
3. `qualification_only=true`, `synthetic_data_only=true`, deterministic provenance and all downstream effects `NONE` on every identity record.
4. Exact issuer and subject identity keys; email/domain/group/role claims never link identities or establish tenant authority.
5. OIDC mix-up, replay, rotation, link, lifecycle, redaction and migration negative categories are mandatory and skipped cases cannot pass.
6. Raw-byte package manifest, focused tests, full tests, repository/security checks and independent exact-SHA review.
7. Every authority, PG-G0, provider approval, production implementation, merge, release and runtime effect remains false.

## A/B/C boundary

This commit is A: schemas, catalog, documentation, validator and tests only. B must be A's direct child and add only synthetic run evidence bound to A. C must be B's direct child and add only the common checker receipt reviewing A+B. No receipt exists in A or B. Any later decision projection is D, outside the receipt and non-authoritative.

## Checks

Run the focused qualification suite, full Python discovery, identity/common/catalog/repository/contract/program/authority validators, clean-room, secret, supply-chain, Python compilation and `git diff --check`. Aggregate shared-manifest routing remains integration-owned and is not modified here.

## Stop conditions

Stop on a real identity value or credential, runtime behavior, online schema resolution, shared-surface edit, claim-based linking, tenant-authority derivation, missing mandatory negative, false downstream effect, provider-selection claim or any self-acceptance.

## Risks and rollback

JSON Schema cannot execute OIDC or prove Git lineage. The semantic validator covers the static subject invariants; B and C remain required for evidence and independent technical acceptance. Rollback is deletion of this isolated branch/worktree; no runtime or protected branch is changed.

## Extend-only change note

Reason: identity strategy needs bounded evidence before selection. Benefit of QUAL-P0-00: it provides reusable exact-binding and checker semantics. Expected outcome: DEC-0005 receives independently reproducible technical input without pre-authorizing a provider or production implementation.
