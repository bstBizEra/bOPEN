---
name: bopen-git-governance
description: Apply bOPEN worktree, branch, commit, evidence and protected-branch controls to authorized Git work.
---

# bOPEN Git Governance

Use this skill for Git policy, repository inspection, change review and evidence
handoff. Delegate worktree creation, retention and removal to
`bopen-worktree-management`. It does not grant merge, release or deployment
authority.

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

## Isolated worktree boundary

Invoke `bopen-worktree-management` as the single owner of worktree creation,
inspection, retention and removal. This skill verifies the resulting branch,
base commit and Git policy before work begins. Freeze shared contracts before
parallel consumers begin; the integration owner resolves cross-worktree
contract conflicts.

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

## Protected operations

Do not direct-push to `main`, force-push, bypass required checks, rewrite history,
merge without independent review, or delete a worktree before evidence and closure
decisions are retained. A passing test is not merge or release authorization.
