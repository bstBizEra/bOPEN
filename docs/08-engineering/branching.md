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

## Local protected review

Gitea `main` blocks direct and force pushes, requires one current approval from `bopen-reviewers`, restricts merges to that team, and denies administrator bypass. `bopen-architects` owns architecture and governed-document paths, `bopen-engineers` owns implementation paths, and `bopen-reviewers` owns security, contracts, infrastructure, research, and Gitea workflow review through the root `CODEOWNERS` file.

The repository-scoped `bst-bopen-runner` executes `.gitea/workflows/governance.yml` with capacity one in rootless containers. Required status-check context names must be observed from an actual pull-request run before being added to branch protection. On this WSL host, jobs use host networking because `/dev/net/tun` is unavailable; Gitea remains loopback-only, no Podman TCP listener is enabled, and RSK-012 tracks the reduced job-network separation.
