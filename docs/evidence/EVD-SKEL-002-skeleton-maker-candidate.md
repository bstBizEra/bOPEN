# EVD-SKEL-002 — SKEL-P0-01 Skeleton Maker Candidate

**Status:** Maker candidate; draft; not accepted. Independent exact-SHA checker review (Codex) pending.
**Work package:** `docs/work-packages/SKEL-P0-01.md` (Proposed; not accepted)
**Phase:** PG-P0 (preparation/review only)
**Maker:** Claude (BST-SA Motor worker agent; `claude-opus-4-8` session)
**Provenance:** The candidate bytes were generated in this session by Claude Opus 4.8. This is a truthful maker attribution; no other runtime performed the maker role.
**Independent checker:** BST-Codex-Motor — must review the exact final candidate SHA (authored none of these bytes).
**Base commit:** `29949f460345a55b8f8079cad802d6ca85cbe46e` (governed PG-P0 `ACTIVE` substrate)
**Base tree:** `463901cf45f3d264a392484a95dfaad139be7339`

## Scope observation (recorded for the checker)

On the governed base the eight clean zones, their scoped `AGENTS.md`, the governance
validators, the pnpm/turbo workspace and the governance contract schemas already
exist. The genuine SKEL-P0-01 delta is therefore narrow and additive:

1. Draft platform/event/audit contract shells under `contracts/` (11 shells), each
   `status: draft`, `bopen://…draft` `$id`, with control/stability/traceability blocks.
2. Typed, type-only package roots `packages/kernel-contracts` and `packages/kernel-testing`.
3. Fail-closed skeleton test tiers `tests/{unit,contract,integration,tenant_isolation,authorization}`.
4. `tools/validate_skeleton.py` (dependency-free, LF-normalized — no raw-byte hashing) wired into `pnpm validate`.
5. Documentation/traceability: this evidence, `docs/manifests/SKEL-P0-01-traceability.json`, and
   append-only `CHANGELOG`/`EVIDENCE-INDEX`/`DOCUMENT-STATUS` entries with the `GOV-P0-02`
   document manifest rebound in the same commit.

## Traceability

All requirement IDs are resolved from the normative Draft bodies present on this base
(`BOPEN-REQ-001` requirement catalog; `BOPEN-TENANT/AUTHZ/ENT/MOD/PARTY-001`, `BOPEN-ARCH-001`).
No identifier was invented. See `docs/manifests/SKEL-P0-01-traceability.json`.

## Governance boundary

- Additive only. No signed byte changes: the five root-control surfaces, signed dockets,
  registers (`docs/00-governance/registers/`), signing passes and PG-G0 outcomes are byte-unchanged.
  `GOV-P0-03` is untouched (none of its pinned files changed).
- Every contract shell is `draft` and not a stable dependency; zero production logic in kernel zones.
- No migration, merge, release, deployment, runtime activation, secret, live endpoint, MCP/plugin
  enablement, or push is performed or authorized by this candidate.

## Exact-SHA verification (maker, at the candidate SHA, clean worktree, short path)

- `pnpm validate` — full governed chain incl. `validate_skeleton.py`: exit 0.
- `python -m unittest discover -s tests -p 'test_*.py'` — full suite green.
- `python tools/validate_skeleton.py --check all` — 5 groups pass, 0 failures.
- Negative fixtures (`tests/tools/test_validate_skeleton.py`): business-logic injection denied;
  draft→active promotion denied.
- `git diff --check` clean; worktree clean at the exact candidate SHA.

The exact candidate SHA is recorded in the maker handoff accompanying this commit.

## Disposition

This record does not accept itself. SKEL-P0-01 remains **Proposed; not accepted** pending
independent BST-Codex-Motor exact-SHA acceptance and attributable Human Engineering Authority disposition.

## Append-only correction - 2026-07-24 - integrated successor (I01)

This record was written at candidate `ca92c7c`. Two conformance modules were
subsequently prepared and integrated; the following statements in the
"Governance boundary" section above are **superseded** and were accurate only at
`ca92c7c`:

- *"the five root-control surfaces ... are byte-unchanged"* — **superseded.** Module
  M-B appends one `## SKEL-P0-01 maker candidate event` block (+521 bytes) to each of
  `Roadmap.md`, `Backlog.md`, `Master_Standards.md`, `Progress_Log.md` and
  `Recap_Today.md`. Every append is an exact byte-prefix extension; no existing byte
  is modified or reordered. `validate_root_control_surfaces.py --check` passes and
  `tests.governance.test_root_control_surfaces` is green (16 tests). The append is
  permissible because all five paths are listed in the docket validator's
  `SIGNED_TRANSFORM_PATHS` allowlist.
- *"`GOV-P0-03` is untouched"* — **superseded.** M-B rebinds
  `docs/manifests/GOV-P0-03-PACKAGE-MANIFEST.json` via `--write-manifest`, closing
  acceptance criterion 5 ("ledgers extended append-only with manifest rebound
  atomically"). `docs/00-governance/**` (registers, signing passes, dockets) remains
  byte-unchanged.

Modules integrated:

- **M-A** `4ee134b6e8b0ae64e23f8e91d9778919fc50d36b` — maker **BST-Codex-Motor**
  (bytes authored by codex-cli / gpt-5.6-sol). Replaces filename/suffix runtime
  detection with stdlib `ast` parsing for Python and an import/export heuristic for
  TS/JS, closing the scope-item-5 "import/AST heuristics" gap. Verification and the
  commit were performed by Claude after the Codex sandboxed test run hung on the
  pre-existing stale-manifest failure described below; no Codex bytes were altered.
- **M-B** `6491a4580a040b2f71af4912dfd5c9f51c06672d` — maker Claude
  (`claude-opus-4-8`) subagent. Root-ledger appends and `GOV-P0-03` rebind.

### Known defect carried by this candidate (not introduced by it)

`tools/generate_document_manifest.py` stamps `generated` with
`datetime.now(timezone.utc).date()`. The committed manifest therefore goes stale at
every UTC midnight even when all records are byte-identical, so `pnpm validate`
becomes red for a frozen SHA with zero byte changes. This **breaks exact-SHA
reproducibility** and was observed directly: `ca92c7c` verified green on 2026-07-23
UTC and failed `manifest snapshot stale` on 2026-07-24 UTC. Regenerating the
manifest in this commit makes the successor green today; it is a patch, not a fix.
A content-derived `generated` value is required. `tools/generate_document_manifest.py`
is outside SKEL-P0-01's allowed paths, so the fix is referred for operator
disposition rather than made here.

Secondary: `Path.write_text()` in the manifest writers applies platform newline
translation and emits CRLF on Windows, silently violating the repository `eol=lf`
policy. Manifests in this candidate were written as LF.

### Independence note

M-A bytes were authored by Codex and M-B/skeleton bytes by Claude. Neither agent is
therefore an independent checker of this integrated candidate as a whole; a fresh
reviewer that authored none of these bytes is required for the exact-SHA receipt.

## Append-only correction - 2026-07-24 - conformance-review findings (I02)

Two findings from the independent conformance reviews of candidate `b138c76` are
corrected here (append-only; the original lines above are preserved as the reviewers
saw them):

- **Stale test path (Claude review, LOW).** Line 47 above cites the negative fixtures
  at `tests/tools/test_validate_skeleton.py`. That path is stale from before the
  `tests/tools/` -> `tests/skeleton/` rename (the rename was required because a
  `tests/tools/` package shadowed the top-level `tools` import). The correct, current
  path is **`tests/skeleton/test_validate_skeleton.py`**; the business-logic-injection
  and draft->active-promotion denials it describes are present and green there.

- **M-B author provenance (Claude review, MEDIUM).** Module M-B (commit
  `6491a4580a040b2f71af4912dfd5c9f51c06672d`) carries the git author trailer
  `BST-Codex-Motor` — the repository's default configured identity, which the Claude
  subagent inherited when it committed. The actual byte-maker of M-B was a **Claude
  (`claude-opus-4-8`) subagent**, as stated in the I01 record. The authoritative
  provenance is this evidence record; the git trailer is inaccurate for M-B and should
  be read as the inherited default, not the maker. Module M-A (`4ee134b`) is correctly
  attributed to BST-Codex-Motor (bytes authored by codex-cli / gpt-5.6-sol). A history
  rewrite to align M-B's author trailer with its byte-maker is available on operator
  request; it was not performed here because it would change the M-B and integration
  SHAs and invalidate the completed conformance reviews, and because the authoritative
  provenance record is already correct.

Both conformance reviews concurred on substance (skeleton-only; signed surfaces
byte-unchanged; contracts valid with resolving requirement IDs) and both explicitly
recorded that NEITHER is the independent whole-candidate exact-SHA receipt: Codex
authored M-A and Claude authored the remainder. A fresh reviewer that authored none of
these bytes remains required. Codex additionally could not execute `pnpm validate` in
its read-only sandbox (pnpm requires write access to its store); the gate is confirmed
exit 0 by two other executions (the I01 maker run and the Claude conformance run) on
2026-07-24 UTC.
