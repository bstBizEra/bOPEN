# EVD-BOOT-011 - bGitea protected review activation

**Work package:** `BOOT-P0-01` / `BOOT-P0-08`  
**Generated:** 2026-07-13T02:40:47+07:00  
**Environment:** Windows host, bGitea 1.26.4, `bizera-wsl`, rootless Podman 4.6.2, Gitea Runner 2.0.1  
**Source/commit:** Branch `motor/BOOT-P0-01-github-reconciliation`, pre-commit activation evidence  
**Agent ID:** bCodex (BST Motor)

## Procedure

1. Backed up the local Gitea configuration and SQLite database before host-control changes.
2. Confirmed the private repository `bst-sa/bopen` and configured the credential-free local remote `origin` as `http://localhost:3030/bst-sa/bopen.git`.
3. Seeded Gitea `main` from reviewed GitHub baseline `9a80f9d042f1ed176c9939bae57953443d0c5964` without rewriting GitHub history.
4. Created separated `bopen-architects`, `bopen-engineers`, and `bopen-reviewers` teams, each with one matching fenced bstSA account and repository-only access.
5. Installed Gitea Runner 2.0.1 from the official release and verified the published SHA-256 checksum before installation.
6. Registered `bst-bopen-runner` at repository scope and removed the reusable registration token after successful registration.
7. Started the runner and rootless Podman API as unprivileged WSL services using a mode-0600 Unix socket and no TCP listener.
8. Applied the initial `main` branch rule through the authenticated Gitea API.

## Expected result

The private local source of truth has separated implementation and review identities, a protected `main`, containerized governance CI, and no credential embedded in repository configuration or Git remotes.

## Actual result

| Control | Observed state |
|---|---|
| Repository | `bst-sa/bopen`, private |
| Local remote | `origin` -> `http://localhost:3030/bst-sa/bopen.git` |
| Stable baseline | Gitea `main` = `9a80f9d042f1ed176c9939bae57953443d0c5964` |
| Teams | Architect ID 6, Engineer ID 7, Reviewer ID 8; membership and repository scope verified |
| Direct push | Disabled |
| Force push | Disabled |
| Required approval | One approval, restricted to `bopen-reviewers` |
| Merge authority | Restricted to `bopen-reviewers` |
| Review freshness | Stale approvals dismissed; rejected, outdated, and outstanding official reviews block merge |
| Administrator bypass | Disabled |
| Runner | `bst-bopen-runner`, repository-scoped, label `ubuntu-latest`, capacity 1 |
| Isolation | Rootless Podman over `/run/bst-gitea-runner/podman.sock`; no Podman network listener; host job networking documented under RSK-012 |
| Runner binary | SHA-256 `7c5413504a457726be2f32aca133028097cc91315df99761754b98c704fcce84` |
| Secret custody | Bootstrap PAT and runner state mode 0600; registration token removed; no token value logged |

The first run failed before checkout because this WSL kernel has no `/dev/net/tun`, which rootless Podman requires for its default slirp network. The runner was kept rootless and switched to host job networking; Gitea remained bound to the Windows loopback and no listener was added. RSK-012 records the reduced job-network separation for SecB review.

The rerun at head `535e98ff40409c5ae8256e38b05eca759ac91545` completed successfully as Actions run 17/job 33. Repository, contract, clean-room, secret, supply-chain, and all 21 bootstrap tests passed. Commit status reported the exact context `Bootstrap Governance / validate (pull_request)`, which was then added to the existing `main` protection rule and verified as enabled. This sequence prevented an unobserved or misspelled context from deadlocking the repository.

## Artifacts and external receipts

- `CODEOWNERS`
- `.github/CODEOWNERS`
- `.gitea/workflows/governance.yml`
- `docs/decisions/DEC-0008.md`
- SecB incident review: `https://github.com/bstBizEra/bstAH/issues/138`
- bstSA SARCHI handoff: `https://github.com/bstBizEra/bst-sa/issues/401`

The host hardening receipt records the pre-change backup hashes, loopback binding, disabled public registration, ACL recovery incident, and remaining service-identity and installed-secret decisions. Credential values are excluded from all receipts.

## Reviewer

Gitea pull request #1 and the required successful governance context are active. Independent Reviewer approval and the protected human-authorized merge remain required. bOPEN Architecture Authority retains B7 approval.

## Decision

Proceed only with independent review of the final branch SHA and protected merge. Production kernel implementation remains unauthorized until the separate BOPEN-RES-001 G7 and normative approval conditions pass.
