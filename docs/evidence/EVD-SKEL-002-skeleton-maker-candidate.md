# EVD-SKEL-002 — SKEL-P0-01 Skeleton Maker Candidate (sole-maker)

**Status:** Maker candidate; draft; not accepted. Independent exact-SHA checker review pending.
**Work package:** `docs/work-packages/SKEL-P0-01.md` (Proposed; not accepted)
**Phase:** PG-P0 (preparation/review only)
**Sole maker:** Claude (BST-SA Motor worker agent; `claude-opus-4-8`)
**Independent checker:** BST-Codex-Motor — must review the exact final candidate SHA.
**Base commit:** `29949f460345a55b8f8079cad802d6ca85cbe46e` (governed PG-P0 `ACTIVE` substrate)
**Base tree:** `463901cf45f3d264a392484a95dfaad139be7339`

## Why this candidate is sole-maker

An earlier integrated candidate (`8927b258…`) was **BLOCKED for acceptance** on a
non-waivable checker-independence control: the work package designates BST-Codex-Motor as
the independent checker, but that lineage included module M-A whose bytes were authored by
Codex — so Codex could not honestly be the independent checker of the whole candidate.

This candidate resolves the block structurally by restoring the work package's original
maker/checker design: **every byte here is authored solely by Claude.** The runtime/
business-logic detector in `tools/validate_skeleton.py` (previously Codex's M-A) is
re-authored in full by the maker; no third-party bytes are inherited. Codex, having
authored none of this candidate, is therefore a legitimate independent checker of it.

## Delivered (additive on the governed base)

1. Eleven draft contract shells (`contracts/platform,events,audit`), each `status: draft`,
   `bopen://…draft` `$id`, with control/stability/traceability blocks; requirement IDs
   resolved from `BOPEN-REQ-001` (none invented) — see `docs/manifests/SKEL-P0-01-traceability.json`.
2. Typed, type-only package roots `@bopen/kernel-contracts` and `@bopen/kernel-testing`.
3. Five fail-closed test tiers with **recursive** guards — an implementation at any depth
   (not only top level) fails closed unless its negative-test manifest is armed.
4. `tools/validate_skeleton.py`: dependency-free, LF-normalized (no raw-byte hashing),
   AST-based Python detection + a TS/JS import/declaration heuristic, wired into `pnpm validate`.
   Negative fixtures deny business logic, TS runtime, draft→active promotion and nested
   implementations, and confirm `.d.ts`/empty `__init__.py`/`__pycache__` are not false positives.
5. Documentation/traceability: this evidence, the traceability manifest, append-only
   root-ledger events with the `GOV-P0-03` package manifest rebound, DOCUMENT-STATUS,
   EVIDENCE-INDEX, CHANGELOG, work-package registration, and the `GOV-P0-02` document
   manifest rebound in the same commit.

## Governance boundary

Additive only; the five root-control ledgers are exact byte-prefix extensions of the base;
`docs/00-governance/**` (registers, signing passes, dockets) and PG-G0 outcomes are
byte-unchanged. Every shell is `draft` and not a stable dependency; zero production logic in
kernel zones. No migration, merge, release, deployment, runtime activation, secret, live
endpoint, or push is performed or authorized.

## Provenance

All bytes authored by Claude (`claude-opus-4-8`). This is a truthful sole-maker attribution;
no other runtime authored any part of this candidate. The independent Codex conformance
review that surfaced the nested-guard requirement (on the superseded `8927b258` lineage) is
credited as the source of that hardening; the byte-level implementation here is the maker's own.

## Disposition

This record does not accept itself. SKEL-P0-01 remains **Proposed; not accepted** pending an
independent BST-Codex-Motor exact-SHA receipt and attributable Human Engineering Authority disposition.

## Append-only remediation - 2026-07-24 - independent REJECT of a1990fc5 (two findings)

An independent BST-Codex-Motor exact-SHA review REJECTED the prior sole-maker candidate
`a1990fc5…` with two blocking findings, both remediated in this successor:

1. **Runtime-detection bypass (SKEL-P0-01 allowed/prohibited boundary).** A paren-less
   one-line arrow (`export const inc = n => n + 1`) in a kernel zone passed the content
   heuristic and `pnpm validate`. Fixed fail-closed: TypeScript/JavaScript type
   declarations must be `.d.ts`; any other script file in a kernel zone is treated as
   runtime regardless of content, so no runtime construct can bypass. Regression fixtures
   added (paren-less arrow denied; a plain `.ts` denied even if type-looking).
2. **Out-of-scope file.** `pnpm-lock.yaml` had changed (pnpm mutated it during a
   `pnpm validate` run) outside the work package's allowed paths. Reverted to the base
   `29949f46` blob; the candidate no longer touches the lockfile. Verification is run via
   python directly (not `pnpm`) so the lockfile is not re-mutated.

The independent Codex REJECT is credited as the source of both fixes; the byte-level
remediation is the sole maker's own (Claude, `claude-opus-4-8`). A fresh independent
Codex exact-SHA review of this successor is required before acceptance is eligible.

## Append-only remediation - 2026-07-24 - independent REJECT of 0cf5f9cd (reproducibility)

An independent BST-Codex-Motor exact-SHA review REJECTED `0cf5f9cd` with two reproducibility
blockers, both remediated in this successor (see the SKEL-P0-01 scope amendment):

1. **Canonical gate dirtied the candidate.** `pnpm validate` added four importer entries to
   `pnpm-lock.yaml` (the new workspace packages were not in the lockfile). Fixed by
   committing the reconciled lockfile; `pnpm validate` is now verified STABLE (identical
   lockfile hash across repeated runs — it no longer mutates the worktree).
2. **Manifest wall-clock dependency.** Integrated the manifest reproducibility fix into
   `tools/generate_document_manifest.py`: `--check` adopts the committed `generated` date
   (date-invariant) while still failing on content drift; write mode uses LF. Regression
   test added. The frozen SHA no longer fails after UTC midnight.

Scope was extended append-only to include `pnpm-lock.yaml` and
`tools/generate_document_manifest.py` (recorded in the work package), in response to the
independent findings. The independent Codex REJECT is credited as the source; the byte-level
remediation is the sole maker's own (Claude). A fresh independent Codex review of this
successor is required before acceptance is eligible.
