# Runbook — Pinned Research Clone

1. Confirm source record and approved commit.
2. Clone into `research/upstream/<source>`.
3. Checkout detached approved SHA.
4. Verify license and repository state.
5. Do not commit upstream source.
6. Record environment and runtime evidence.

## DEC-0009 execution refinement

For this repository, execute the logical `research/upstream/<source>` zone in an approved external ephemeral workspace at `C:\laragon\www\bopen-research\<operator-run>\01-boxyhq\upstream`. Do not place a physical clone in the bOPEN Git worktree. Store raw logs beside the external operator workspace and publish only sanitized receipts.
