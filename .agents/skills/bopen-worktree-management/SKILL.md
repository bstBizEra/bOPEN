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

## Handoff

The receiver independently verifies repository, branch, worktree, base/head SHAs,
changed files, commands, tests, evidence paths, findings, residual risks and
blocked items. Do not transfer ownership by chat claim alone.

## Retention and removal

Two worktree kinds have opposite rules. Decide which you have before removing anything.

- **Work worktree** - where authored work happens over time. Retain it until evidence, independent
  review and merge/closure decisions are recorded. Before removal, confirm no uncommitted changes and
  preserve required references. Do not use `git worktree remove`, deletion, reset or force operations
  as a substitute for an unresolved review.
- **Apply worktree** - a disposable checkout created to execute one pre-approved change and destroyed
  in the same session. It authors nothing, so there is no unresolved review to suppress; its
  abort-safety model DEPENDS on destruction.

For an apply worktree, retention and removal are asymmetric:

- **Success** - RETAIN the apply worktree until the recognition decision is recorded.
  Print `git status --short --branch` and `git log -1` so the retained state is evidenced;
  never assert cleanliness from narrative.
- **Any failure (apply, validation, or a refused compare-and-swap)** - REMOVE it. There is no
  authorized evidence to retain, and after a refused compare-and-swap the execution commit is an
  unreferenced orphan that must not be left reachable or pushable. Record the orphan SHA and the
  failure reason in the run output before removing.

Never retry in place after an abort: an aborted run leaves modified files, and a later bare commit
in that directory would commit tampered content without re-running any gate. Destroy and restart.

## Path length

Use a SHORT worktree path. Deep paths exceed the Windows MAX_PATH limit and cause validators to
report FALSE staleness failures. See `bopen-windows-toolchain`.

## Hygiene

Prune regularly. Registered worktrees whose directories no longer exist can make `worktree add`
and `prune` misbehave and keep superseded commits reachable. Audit with
`git worktree list --porcelain` before starting governed work.

## Stop conditions

- dirty worktree not owned by the current work item;
- path or branch collision;
- contract conflict between parallel worktrees;
- missing handoff or evidence envelope;
- checker is not independent;
- cleanup of a WORK worktree requested before closure evidence exists. (This does not apply to an
  apply worktree, whose destruction on failure is required, not premature.)
