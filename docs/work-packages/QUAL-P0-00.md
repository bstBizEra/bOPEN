# QUAL-P0-00 — Common Qualification Evidence Envelope

**Version:** 0.1
**Status:** Drafting authorized; not accepted
**Owner:** Engineering Authority
**Dependencies:** GOV-P0-02 proposal at `82ed6b38b118aab14a9961c5d75a33e515cb136a`; Program Goal v0.2
**Governing artifacts:** BOPEN-GOV-001 Draft; BOPEN-GOAL-001 Draft; PG-O1, PG-O7 and PG-O8 requirements
**Authorization source:** Explicit user authorization to draft QUAL-P0-00 through 2026-08-21 only
**Accepted by/at:** Pending attributable Human Engineering Authority disposition
**Maker:** Codex `/root/tech_qual_schema_blueprint`
**Checker:** Independent exact-SHA checker pending
**Branch/worktree:** `codex/QUAL-P0-00-common` / `C:\laragon\www\bopen-worktrees\qual-p0-00-common`
**Base SHA:** `82ed6b38b118aab14a9961c5d75a33e515cb136a`
**Base tree:** `cad6b595fb74a70cc706a78d45778e15524aebd9`
**Expiry:** 2026-08-21T00:00:00+07:00

## Objective

Draft a reusable, fail-closed and technology-neutral evidence envelope for bounded qualification packages. The contract set binds exact repository objects, environment manifests, artifacts, provenance, redaction, requirement coverage and independent technical review without creating governance, gate, technology, identity, merge, release or runtime authority.

## In scope

- nine closed Draft 2020-12 common schemas;
- a digest-pinned, network-denying offline schema catalog;
- exact commit/tree, normalized path, SHA-256, environment and provenance controls;
- requirement, governing artifact, ADR, exception and gate-context coverage fields;
- maker–checker separation and immutable A subject → B evidence → C receipt semantics;
- a standard-library deterministic validator and adversarial tests;
- bounded maker evidence and an immutable package manifest.

## Out of scope

Technology- or identity-specific scorecards; qualification execution; real credentials; production business logic; approval of any normative artifact, work package, gate, technology stack or identity provider; merge, release, deployment or runtime activation; shared CI, package scripts, indexes, registers and canonical manifests.

## Allowed paths

```text
contracts/qualification/common/*.schema.json
contracts/qualification/common/QUAL-P0-00-SCHEMA-CATALOG.json
docs/work-packages/QUAL-P0-00.md
docs/evidence/EVD-QUAL-001-qualification-common.md
docs/manifests/QUAL-P0-00-PACKAGE-MANIFEST.json
tools/validate_qualification_common.py
tests/qualification/__init__.py
tests/qualification/test_qualification_common.py
```

## Prohibited paths

Shared indexes, status surfaces, CI workflows, `package.json`, lock files, canonical manifests, other qualification domains, application/runtime zones, infrastructure, migrations, upstream research sources, production data and secrets.

## Deliverables

1. Offline-resolvable common schema set and pinned catalog.
2. Deterministic semantic validator covering contract closure and non-schema invariants.
3. Positive and adversarial tests including digest/ref failures, secrets, self-review and A→B→C lineage.
4. EVD-QUAL-001 maker evidence and a bounded immutable package manifest.

## Acceptance criteria

- every catalog path and schema reference resolves locally through a pinned digest;
- network fallback, duplicate IDs, cycles, malformed paths, symlinks and digest drift fail closed;
- subject commit/tree and environment manifest bindings are reproducible;
- direct coverage requires evidence while partial, deferred and uncovered claims cannot imply passage;
- production credentials are prohibited and secret scanning must pass;
- maker and checker identity and session cannot collapse;
- snapshot B is a direct child of A and receipt snapshot C is a direct child of B;
- the receipt is absent from B and C changes only the receipt path;
- every authority, gate, technology, identity, merge, release and runtime flag remains false;
- all package-local and non-integration-owned repository checks pass and an independent checker reviews the exact final SHA;
- aggregate `npm run validate` remains explicitly `BLOCKED_UNTIL_QUAL_INTEG_001` because its historical shared manifest cannot be changed in this lane.

## Required checks/evidence

Focused QUAL-P0-00 tests; full Python test discovery; contract and repository validators; program and authority reports; package-manifest check; clean-room, secret and supply-chain checks; `git diff --check`; exact-SHA independent review. Run aggregate `npm run validate` only to confirm its explicit `BLOCKED_UNTIL_QUAL_INTEG_001` disposition at the integration-owned historical manifest.

## Stop conditions

Stop if scope enters a shared integration surface or runtime zone, an online schema resolver is introduced, a receipt self-binds its containing commit, a maker acts as checker, a credential is serialized, a partial coverage claim becomes a pass, or any authority/effect flag becomes true.

## Risks and rollback

JSON Schema cannot prove Git ancestry, byte digests, cross-document ordering or reviewer independence. The dedicated semantic validator supplies these checks. This remains a draft contract and is not a stable dependency until accepted. Rollback is deletion of the isolated branch/worktree; no runtime or protected branch is changed.

## Extend-only change note

Reason: technology and identity qualification proposals need one reusable evidence grammar rather than divergent envelopes. Benefit of the prior phase: GOV-P0-02 established exact-SHA, fail-closed and non-authority patterns. Expected outcome: later qualification packages can reuse a bounded offline contract while remaining unable to approve themselves or pass program gates.

## Completion record

Maker implementation and local evidence are prepared on the isolated branch. Independent exact-SHA technical review and Human Engineering Authority acceptance remain pending. This package cannot accept itself.

## Append-only checker rework — 2026-07-22

The first maker commit `2e3faf6c6b310f60b5aa763fe3f29886307f3c41` received `REQUEST_CHANGES`. Package hashing normalized line endings, local JSON Pointer targets and reference cycles were not validated, terminal receipts could omit external storage binding, and merge commits could satisfy the first-parent lineage checks.

Reason: those gaps allowed byte drift, unresolved contract targets or ambiguous evidence ancestry to survive a narrow check. Benefit of the prior phase: offline catalog digests, exact subject bindings, redaction, coverage and non-authority controls were already established. Expected outcome: the successor binds raw bytes, resolves every pointer offline, rejects reference cycles, requires externally supplied terminal receipt storage, and permits exactly one parent at B and C.

The aggregate npm validation state is `BLOCKED_UNTIL_QUAL_INTEG_001`; no passing package-local check may be reported as aggregate repository acceptance.
