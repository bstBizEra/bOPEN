---
name: bopen-governance-check
description: Validate bOPEN authority, phase gates, scope, required artifacts, maker-checker separation and stop conditions before repository mutation.
---

# bOPEN Governance Check

1. Identify project, phase and work item.
2. Verify authorization, owner, expiry and allowed paths.
3. Read linked requirements, ADRs, security and tenancy controls.
4. Confirm worktree, maker, checker, tests, evidence destination and rollback.
5. Report missing controls as blockers.
6. Do not mutate files until all mandatory checks pass.
