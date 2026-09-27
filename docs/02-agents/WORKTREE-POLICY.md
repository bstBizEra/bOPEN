# Worktree Policy

1. One authorized work item per worktree.
2. Worktree path: `../bopen-worktrees/<work-item-id>-<slug>`.
3. Branch: `work/<work-item-id>/<slug>`.
4. Evidence path: `../bopen-evidence/<work-item-id>/`.
5. Never reuse a dirty worktree for a new work item.
6. Freeze shared contracts before parallel consumers begin.
7. Integration owner resolves cross-worktree contract conflicts.
8. Delete worktrees only after evidence, merge/closure decision and reference retention.
