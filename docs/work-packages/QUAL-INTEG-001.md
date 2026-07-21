# QUAL-INTEG-001 — Non-Merge Review Candidate Composition

**Document ID:** QUAL-INTEG-001
**Version:** 0.1
**Status:** Draft; authorized integration preparation only; not accepted
**Owner:** Engineering Authority
**Issued:** 2026-07-22
**Authorization source:** Explicit user-level QUAL-INTEG-001 integration-maker instruction
**Accepted by/at:** Not accepted; independent exact-SHA review pending
**Lifecycle:** Non-merge review candidate; inactive; no gate passage
**Dependencies:** PR8 `82ed6b38b118aab14a9961c5d75a33e515cb136a`; accepted GOV-P0-03, QUAL-P0-00, TECH-P0-01, QUAL-P0-02 and RES-P0-05 source chains
**Governing artifacts:** Current user instruction; AGENTS.md; DEC-0012 option 1; BOPEN-GOV-001 Draft
**Evidence reference:** EVD-QUAL-INTEG-001
**Maker:** `/root/gov_p0_03_preflight`
**Checker:** Different-agent exact-SHA and aggregate review required
**Branch/worktree:** `codex/QUAL-INTEG-001-review-candidate` / `C:\laragon\www\bopen-worktrees\qual-integ-001-review-candidate`
**Base SHA/tree:** `82ed6b38b118aab14a9961c5d75a33e515cb136a` / `cad6b595fb74a70cc706a78d45778e15524aebd9`

## Objective

Compose exact accepted proposal chains into one isolated review candidate, reconstruct PR7 without changing its source history, preserve package-local bytes and fail-closed controls, and make the aggregate validation surface deterministic and independently reviewable.

## Authorized composition

1. GOV-P0-03: `651951f`, `a29ec1d`.
2. QUAL-P0-00: `2e3faf6`, `a2fc4b1`.
3. TECH-P0-01: `1673684`, `7b11f9d`.
4. QUAL-P0-02 identity: `e4b421f`, `74daac8`, as a sibling source lineage from QUAL-P0-00.
5. RES-P0-05: `8bc3e2a`, `952e9b3`, `f501cdc`, `4b1cb21`, reconstructed with shared-path union and immutable manifest redirection.

## Allowed paths

- the exact union of paths changed by the bound source chains;
- shared integration surfaces: `README.md`, document status/coverage/traceability/artifact/decision/evidence/work-package/changelog indexes, `.gitignore`, `package.json`, both governance workflows, `tools/validate_repository.py`, and `tools/generate_document_manifest.py`;
- `docs/manifests/RES-P0-05-DOCUMENT-MANIFEST.json`, `docs/manifests/QUAL-INTEG-001-INTEGRATION-MANIFEST.json`, `docs/manifests/QUAL-INTEG-001-AGGREGATE-MANIFEST.json`, and `docs/manifests/MANIFEST-INDEX.jsonl`;
- this work package, EVD-QUAL-INTEG-001, deterministic readiness report, validator/report tools and integration tests.

## Prohibited paths and actions

No runtime applications, services, packages, infrastructure, migrations, production data or credential material. Do not rewrite any source commit, force-push, overwrite `docs/DOCUMENT-MANIFEST.json` or an existing `docs/manifests/` snapshot, execute qualification or research runtime activity, approve a technology, pass a gate, merge, release, deploy or activate production.

## Deliverables

1. Linear replay mapping with full or scoped stable patch-ID evidence.
2. Per-file conflict ledger and exact preserved source-package bytes.
3. Immutable historical snapshot index plus a separate current aggregate manifest.
4. Aggregate package/workflow/repository validation DAG.
5. Deterministic validator, readiness report, negative tests and EVD-QUAL-INTEG-001.

## Acceptance criteria

- all twelve source commits map to replay commits and preserve full patch IDs or explicitly scoped patch IDs where shared manifest/index paths were reconciled;
- TECH-P0-01 and QUAL-P0-02 sibling lineage from QUAL-P0-00 remains explicit;
- accepted package-local files are byte-identical to their source heads;
- canonical and historical manifest bytes are immutable and Git-object bound;
- PR7 final canonical-manifest bytes exist only as the separate RES-P0-05 snapshot;
- no tracked conflict marker remains;
- workflow, package and repository validation retain the semantic union of every accepted package;
- the pre-integration floor of 222 tests remains passing and integration tests increase it;
- all authority, gate, merge, release, runtime and production flags remain false.

## Required checks/evidence

Run the integration validator/report, immutable manifest-index check, every package validator, research G3 validator, repository/contract/program/docket validation, full tests, `npm run validate`, clean-room, secret, supply-chain and `git diff --check`. Report writers and research inventory writers are not validation commands.

## Stop conditions

Stop on source/replay mismatch, package-local byte drift, missing history, unresolved conflict, snapshot overwrite, conflict-marker residue, validation weakening, runtime execution or any approval/gate/merge/release claim.

## Risks and rollback

Risk: conflict resolution can silently drop a control. Control: explicit union assertions and per-file ledger. Risk: mutable manifest generation can rewrite history. Control: Git-object-bound immutable index and separate current aggregate. Rollback: delete the isolated candidate branch/worktree before any merge; source branches and protected state remain unchanged.

## Completion record

Maker validation and independent exact-SHA review are pending. This Draft candidate cannot accept or merge itself.

### Append-only maker completion record â€” 2026-07-22T01:32:30+07:00

Maker validation completed with a 230/230 full-suite result and all aggregate/package/security checks passing. Independent exact-SHA review remains pending. Status remains Draft and Inactive; this record creates no acceptance, merge, gate, release, runtime or production authority.
