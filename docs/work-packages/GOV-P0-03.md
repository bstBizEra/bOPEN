# GOV-P0-03 — Exact Root Control Surfaces

**Document ID:** GOV-P0-03
**Version:** 0.1
**Status:** Draft; authorized for drafting only; not accepted
**Owner:** Engineering Authority
**Issued:** 2026-07-21
**Authorization source:** Explicit user-level DEC-0012 option 1 instruction received 2026-07-21
**Authorization expiry:** 2026-08-21T23:59:59+07:00
**Accepted by/at:** Not accepted; no repository authority is inferred
**Lifecycle:** PG-G0 proposal; inactive; no gate passage
**Dependencies:** GOV-P0-02 exact head `82ed6b38b118aab14a9961c5d75a33e515cb136a`; DEC-0012 option 1
**Governing artifacts:** Current user instruction; AGENTS.md; BOPEN-BOOT-001; BOPEN-GOAL-001 Draft; BOPEN-GOV-001 Draft
**Decision reference:** DEC-0012 option 1 only
**Evidence reference:** EVD-GOV-003
**Maker:** `/root/gov_p0_03_preflight`
**Checker:** Different-agent exact-SHA review required
**Branch/worktree:** `codex/GOV-P0-03-root-controls` / `C:\laragon\www\bopen-worktrees\gov-p0-03-root-controls`
**Base SHA:** `82ed6b38b118aab14a9961c5d75a33e515cb136a`
**Base tree:** `cad6b595fb74a70cc706a78d45778e15524aebd9`

## Objective

Create and validate the five exact root instruction surfaces as append-only, Draft and Inactive locators or ledgers without changing any gate, approval, merge, release, runtime or production state.

## Allowed paths

- `Roadmap.md`
- `Master_Standards.md`
- `Progress_Log.md`
- `Backlog.md`
- `Recap_Today.md`
- `docs/decisions/DEC-0012.md` by append-only disposition only
- `contracts/governance/root-control-surface.schema.json`
- `docs/work-packages/GOV-P0-03.md`
- `docs/evidence/EVD-GOV-003-root-control-surfaces.md`
- `docs/manifests/GOV-P0-03-PACKAGE-MANIFEST.json`
- `tools/validate_root_control_surfaces.py`
- `tests/governance/test_root_control_surfaces.py`

## Prohibited paths

All paths not listed above, including shared indexes, CI and package files, `AGENTS.md`, `docs/DOCUMENT-MANIFEST.json`, authority registers and dockets, `apps/`, `services/`, `packages/`, `infrastructure/`, research execution, migrations, runtime configuration, credentials and production data.

## In scope

- atomic same-commit genesis of the five exact-case root files;
- draft extracted-record schema;
- fail-closed metadata, link, state, manifest and append-only validation;
- negative tests and reproducible maker evidence;
- an append-only DEC-0012 option 1 user-instruction disposition.

## Out of scope

DEC-0012 manifest-option disposition; accepting GOV-P0-03; approving any normative artifact, identity, register, authority matrix or technology; passing BOOT-B7, PG-G0 or research G7; reconciling PR branches; merging; runtime implementation; release; deployment; production activation.

## Deliverables

1. Five Draft and Inactive root controls with cross-links and unresolved global-config disclosure.
2. Draft root-control schema, validator and negative test suite.
3. Versioned package manifest and EVD-GOV-003 maker evidence.
4. Append-only DEC-0012 option 1 disposition.

## Acceptance criteria

- exact filenames, casing, regular-file type and UTF-8/LF content validate;
- all five files carry unique governed IDs and required provenance;
- all five files are introduced by the same commit and later revisions preserve the complete prior byte prefix;
- all root cross-links and instruction-level config references exist;
- missing global config remains `UNRESOLVED_EXTERNAL_DEPENDENCY`;
- no mutable backlog checkbox or in-place status convention exists;
- PG-G0, production implementation, merge and release flags remain false;
- the package manifest exactly binds every authorized package file except itself;
- focused and full validation pass;
- a different agent reviews the exact final commit and tree.

## Required checks and evidence

Run the focused GOV-P0-03 tests, full Python suite, repository and contract validators, deterministic program and authority reports, the existing GOV-P0-02 document-manifest check, clean-room, secret and supply-chain checks, `git diff --check`, and exact-path scope audit. Record executed results only in EVD-GOV-003.

## Stop conditions

Stop on authorization expiry, base mismatch, any out-of-scope path, non-atomic root genesis, rewrite or truncation, invented config or authority, effective status, stale package manifest, test weakening, or any gate, merge, release, runtime or production claim.

## Risks and rollback

Risk: a root locator is mistaken for approved governance. Control: every root surface is Draft, Inactive and carries explicit false authority flags. Risk: shared indexes remain stale because this package is prohibited from editing them. Control: record the deferred reconciliation as a residual risk and do not claim repository-wide documentation closure. Rollback before merge is deletion of the isolated proposal branch/worktree; no protected or runtime state is changed.

## Completion record

Maker implementation and independent exact-SHA review are pending. This package cannot accept itself.

## Extend-only change note

Reason: exact root instruction paths were missing and similarly named controlled documents could not be silently substituted. Benefit of the old phase: the existing `docs/` hierarchy retained stable bootstrap history and kept the discrepancy visible. Expected outcome: exact paths become deterministic, append-only control surfaces without changing the authority or phase boundary.

## Append-only maker completion note — 2026-07-21

Maker implementation is complete within the exact allowed path set. Focused tests pass 11/11 and the full suite passes 158/158. Repository, contract, program-control, deterministic-report, clean-room, secret, supply-chain and diff checks pass. The historical GOV-P0-02 document-manifest check remains fail-closed and stale because DEC-0012 manifest handling is outside this option-1-only package and the prior snapshot may not be overwritten.

Independent exact-SHA technical review remains required. This note does not accept GOV-P0-03 or authorize any gate, merge, release, runtime or production action.

## Append-only exact-byte checker rework — 2026-07-22

Independent review rejected the first maker commit because newline normalization allowed distinct raw bytes to share a package-manifest digest and text-mode Git output concealed line-ending-only history rewrites. The bounded successor replaces both comparisons with raw-byte operations and adds dedicated negative tests for CRLF manifest drift and CRLF-to-LF append-only rewriting.

Reason: manifest and append-only controls must bind repository bytes exactly. Benefit of the prior phase: all non-byte governance invariants and atomic genesis behavior already passed. Expected outcome: a successor exact-SHA checker can reproduce fail-closed byte integrity without broadening package scope or authority.

## Append-only acceptance record — 2026-07-22

**Accepted by:** HUMAN-OPERATOR-001 (Engineering Authority, DIRECT)
**Accepted at:** 2026-07-22T23:35:00+07:00
**Acceptance ref:** docs/00-governance/signing/SIGNING-PASS-1.md#B4
**Concurrence:** Owning Artifact Authority — same operator per the approved identity register solo-operator independence disclosure
**Technical basis:** independent exact-SHA receipt EVD-GOV-004 (Claude) for candidate a29ec1d8ab28d38621dc4db176b7b2abf2ea44cb

Source: explicit operator confirmation recorded in the current Claude Code session (2026-07-22). Root-ledger activation (packet item B6) is confirmed by the operator but deferred: the GOV-P0-03 validator pins Status Draft / Lifecycle Inactive, so activation requires a reviewed validator revision in the docket v0.2 batch. This acceptance approves no gate and no production implementation.
