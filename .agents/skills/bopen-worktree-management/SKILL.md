---
name: bopen-worktree-management
description: Manage the lifecycle of an authorized bOPEN Git worktree without cross-agent interference or premature cleanup.
---

# bOPEN Worktree Management

Use one isolated worktree for one authorized work item. This skill manages
worktree lifecycle only; it does not authorize implementation, merge or release.

## Preflight

Before creating or entering a worktree, confirm:

- work-item ID and approved scope;
- assigned maker and independent checker;
- base commit SHA;
- allowed paths and evidence destination;
- rollback and retention requirements;
- shared contracts are frozen for parallel consumers.

Stop on missing, expired or mismatched authority.

## Create

```powershell
git worktree add `
  ..\bopen-worktrees\<work-item>-<slug> `
  -b codex/<work-item>-<slug> `
  <base-sha>
```

Record the absolute path, branch, base SHA and owner in the handoff record.

## Inspect

```powershell
git worktree list --porcelain
git -C <worktree-path> status --short --branch
git -C <worktree-path> log -1 --oneline
```

Never assume a worktree is clean from its branch name or prior narrative.

## Worktree ownership transfer

This skill transfers only lifecycle custody of the worktree. The receiver
independently verifies repository, absolute worktree path, branch, base/head
SHAs, current owner and clean/dirty state. `bopen-git-governance` exclusively
owns the change, review and evidence handoff. Do not transfer lifecycle custody
by chat claim alone.

## Retention and removal

Retain the worktree until evidence, independent review and merge/closure decisions
are recorded. Before removal, confirm no uncommitted changes and preserve required
references. Do not use `git worktree remove`, deletion, reset or force operations
as a substitute for an unresolved review.

## Stop conditions

- dirty worktree not owned by the current work item;
- path or branch collision;
- contract conflict between parallel worktrees;
- missing handoff or evidence envelope;
- checker is not independent;
- cleanup requested before closure evidence exists.
