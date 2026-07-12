# Branching

Use short-lived branches named by work package. Main is protected. Direct pushes, force pushes and bypass of required checks are prohibited except approved emergency procedure.

## Phase 0 branch pattern

Use branches that include the agent or owner, work-package ID and short purpose:

```text
<agent>/<WORK-PACKAGE-ID>-<short-purpose>
```

Example:

```text
motor/BOOT-P0-09-local-source-control
```

Working branches are pushed to local bGitea (`origin`) for review and validation. GitHub (`github`) receives only stable `main`, approved release branches or tags after validation evidence is attached.
