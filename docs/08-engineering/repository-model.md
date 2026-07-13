# Repository Model

The repository is a governed monorepo. Shared contracts and documentation remain close to implementation. Runtime deployment boundaries may differ from repository boundaries.

## Source-control topology

The local development source of truth is the private bGitea repository. In local clones, configure `origin` to the bGitea repository once the repository URL is assigned.

GitHub is the stable publication remote. Configure it as `github` and push only protected `main`, release branches, signed or reviewed tags, and approved release artifacts after repository validation and work-package evidence are complete.

This split keeps local build activity fast and private while preserving a stable external history. Do not use GitHub as the experimental branch target, and do not push unreviewed Phase 0 bootstrap work to the stable remote.

Expected local remote model:

```text
origin  -> local bGitea, working branches and integration review
github  -> GitHub stable mirror, protected main and releases only
```

At the first EVD-BOOT-004 check, this working copy had no configured remotes. The active remotes are now `origin` at `http://localhost:3030/bst-sa/bopen.git` and `github` at `https://github.com/bstBizEra/bOPEN.git`. Credentials are not embedded in either URL. EVD-BOOT-011 records creation and control verification for the private Gitea repository.

The current local bootstrap history and GitHub `main` history are unrelated. Stable publication to GitHub requires an approved reconciliation path before `main` is pushed or protected. Do not force-push over GitHub `main` unless an approved emergency or repository replacement decision explicitly authorizes it.

The local bGitea service is available only through the host loopback at `http://localhost:3030/`, with login at `http://localhost:3030/user/login`. Gitea `main` was seeded from GitHub baseline `9a80f9d042f1ed176c9939bae57953443d0c5964` and is protected against direct and force pushes. Working changes enter through Gitea pull requests; reviewed stable versions are published separately to GitHub.
