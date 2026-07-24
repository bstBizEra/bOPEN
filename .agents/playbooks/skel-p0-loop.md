# SKEL-P0 Loop Playbook (draft)

1. **C0 Inspect:** read authority, phase, package, allowed paths and worktree policy.
2. **C1 Plan:** bind maker/checker, exact base, tests, evidence, rollback and expiry.
3. **C2 Build:** maker changes only allowed paths in its isolated worktree.
4. **C3 Review:** independent checker reproduces the exact SHA and runs adversarial checks.
5. **C4 Validate:** validator records every command, exit code and residual risk.
6. **C5 Handoff:** send structured evidence to the operator/Human Authority.

There is no automatic C6 merge or activation. A new work item and separate authority
are required for any integration or runtime action.
