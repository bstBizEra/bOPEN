---
name: bopen-git-governance
description: Apply bOPEN worktree, branch, commit, evidence and protected-branch controls to authorized Git work.
---

# bOPEN Git Governance

Use this skill for repository inspection, isolated worktree setup, change review
and evidence handoff. It does not grant merge, release or deployment authority.

## Preconditions

1. Run `bopen-governance-check`.
2. Confirm work item, authorization, owner, checker, base commit, allowed paths,
   evidence destination and rollback plan.
3. Use one authorized work item per worktree.
4. Never reuse a dirty worktree or modify another agent's claimed worktree.

## Read-only inspection

```powershell
git status --short --branch
git log -1 --oneline
git worktree list --porcelain
git branch -vv
git diff --check
```

## Isolated worktree

Use the repository worktree convention:

```powershell
git worktree add `
  ..\bopen-worktrees\<work-item>-<slug> `
  -b codex/<work-item>-<slug> `
  <base-sha>
```

Freeze shared contracts before parallel consumers begin. The integration owner
resolves cross-worktree contract conflicts.

## Review and handoff

Bind all claims to exact SHAs, not branch names:

```powershell
git diff --stat <base-sha>...HEAD
git diff --name-status <base-sha>...HEAD
git log --oneline <base-sha>..HEAD
npm run validate
npm run test:governance
git status --short
```

Record the handoff contract with repository, branch, worktree, base/head commits,
changed files, commands, tests, evidence paths, findings, residual risks and
authorization status.

## Authorized apply (compare-and-swap)

An apply that mutates a governed register is a human act. Prepare it, prove it, hand it over.

- Pre-flight: assert the branch head equals the exact expected-old SHA, and assert the patch
  digest equals the independently proven digest, before creating a worktree.
- Gate every check; commit ONLY if all pass. Gate signature verification on BOTH exit code and
  expected stdout - a forged signature can pass every other validator and the whole test suite.
- Move the ref with `git update-ref <ref> <new> <expected-old>`. Use the literal expected-old SHA.
  A refused compare-and-swap must leave the other actor's value untouched and the execution
  commit orphaned.
- Worktree retention after an apply is asymmetric and is owned by `bopen-worktree-management`.
- A coordinated governed change is ONE commit. Never split it into incremental commits.

## Protected operations

Do not direct-push to `main`, force-push, bypass required checks, rewrite history,
merge without independent review, or delete a worktree before evidence and closure
decisions are retained. A passing test is not merge or release authorization.

Run validators from a SHORT worktree path; deep paths produce false failures. Write governed files
as explicit UTF-8 with LF. See `bopen-windows-toolchain` and `bopen-phase-closure`.
