# EVD-BOOT-004 - Bootstrap Governance Recovery

**Work package:** BOOT-P0-02, BOOT-P0-03, BOOT-P0-05  
**Generated:** 2026-07-21T16:35:57+07:00  
**Environment:** Windows PowerShell, Python 3.13, pnpm 11.9.0  
**Source/commit:** `a908bbea1975ffc52a636765cd9f823dfeb978eb` on `codex/bootstrap-recovery-20260721`  
**Worktree:** `C:\laragon\www\bopen-worktrees\bootstrap-recovery`  
**Agent IDs:** Codex coordinator; `root_adapter_repair` maker; `document_status_repair` maker; `independent_checker` checker

## Authority and scope

The user directed Codex on 2026-07-21 to proceed with the bounded bootstrap recovery
using parallel subagents and a Git worktree. The authorized scope is limited to restoring
the governed root instruction file, preserving the Antigravity adapter at a
Windows-safe path, correcting non-authorizing controlled-document status fields, and
producing validation evidence. Production kernel logic, authority promotion, merge,
push, release, deployment and activation are excluded.

## Procedure

1. Verified GitHub MCP access to `bstBizEra/bOPEN` and local GitHub authentication.
2. Created the isolated branch and worktree from local baseline `a908bbe`.
3. Copied the existing uncommitted governance overlay into the isolated worktree without
   changing `C:\laragon\www\bopen`.
4. Restored canonical root `AGENTS.md` and moved the byte-preserved Antigravity adapter
   to `.agents/ANTIGRAVITY.md`.
5. Updated the adapter references and scoped manifest hashes.
6. Added explicit `PROPOSED - NO IMPLEMENTATION AUTHORITY` status fields to the six
   controlled documents rejected by the validator.
7. Regenerated `docs/DOCUMENT-MANIFEST.json`; 237 controlled records were written.
8. Ran repository, clean-room, governance, package-wrapper and whitespace checks.

## Expected result

The isolated bootstrap overlay passes repository validation without weakening the
clean-room or production implementation gates. The original checkout remains unchanged.

## Actual result

- `python tools/validate_repository.py`: PASS, 26 mandatory paths and invariants.
- `python tools/check_clean_room.py`: PASS.
- `python -m unittest discover -s tests/governance -p "test_*.py" -v`: PASS, 5 tests.
- `pnpm validate`: PASS.
- `pnpm test:governance`: PASS, 5 tests.
- `python tools/generate_document_manifest.py`: PASS, 237 records.
- `git diff --check`: PASS.
- Dedicated `gitleaks` scan: NOT RUN; executable unavailable in this environment.
- Production and research source path status check: no changes.
- Original checkout remains on `main` with its pre-existing overlay unchanged.

## Artifacts and changed scope

- Canonical instructions: `AGENTS.md` restored to the baseline blob.
- Antigravity adapter: `.agents/ANTIGRAVITY.md`.
- Adapter references: `README.md`, `docs/02-agents/HARNESS-MATRIX.md`, `MANIFEST.json`.
- Status-only repairs:
  - `docs/01-program/BOPEN-GOAL-001_v0.1.md`
  - `docs/01-program/BOPEN-SCHEDULE-001_v0.1.md`
  - `docs/02-agents/BOPEN-AGENT-001_v0.1.md`
  - `docs/03-loop/BOPEN-LOOP-001_v0.1.md`
  - `docs/04-skills/BOPEN-SKILL-001_v0.1.md`
  - `docs/08-design/BOPEN-DESIGN-001_v0.1.md`

## Independent review and residual risks

- Initial checker verdict: `REQUEST_CHANGES` because root and document manifests were
  stale and root README/governance wording implied authority promotion.
- Maker rework completed: `README.md` and `GOVERNANCE.md` now retain BOPEN-BOOT-001 as
  the approved bootstrap authority and mark the new governance pack as proposed with no
  implementation authority.
- Root `MANIFEST.json` integrity: PASS for all 64 unique entries after refreshing the
  eight stale entries identified by the checker.
- Final checker verdict: `ACCEPT` for the reviewed local bootstrap-recovery bytes.
  This is technical acceptance only; remote integration remains `HOLD`.
- GitHub `main` is the unrelated initial commit `9a80f9d`; local baseline `a908bbe` has no
  common ancestor with it. Push, pull request and merge remain blocked pending a governed
  history-reconciliation decision.
- The configured local Gitea `origin` is a third history and failed authentication during
  this session. It must not be conflated with GitHub.
- `Master_Standards.md` is referenced by the supplied organism-level instructions but is
  absent from the repository. No replacement was invented.
- Much of the governance overlay remains untracked relative to local baseline `a908bbe`;
  any future staging operation must select and review the intended aggregate explicitly.
- Heuristic secret-pattern scan by the checker found no matches. A dedicated scanner is
  unavailable in this environment.

## Reviewer

`independent_checker` subagent; initial `REQUEST_CHANGES`, final local technical verdict
`ACCEPT`, remote integration `HOLD`.

## Decision

Maker rework verification is complete. This evidence does not accept the work packages, approve
the proposed governance artifacts, authorize production kernel implementation, or permit
commit, push, pull request, merge, release, deployment or activation.
