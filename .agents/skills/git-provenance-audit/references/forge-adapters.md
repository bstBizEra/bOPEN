# Forge adapters

Use only installed connectors or official read-only APIs. Never place tokens,
authorization headers, cookies, or credential-bearing URLs in evidence.

Collect a raw response and a separate normalized fact record. Include:

- forge type, base URL, repository ID and normalized repository path;
- API version, query time, pagination and retention boundary;
- target branch rules, required checks, review count and bypass actors;
- immutable review or merge-request revision;
- reviewer identities and dismissal or supersession events;
- merge actor, method, resulting commit and server audit event when available.

| Forge | Review object | Policy surface |
| --- | --- | --- |
| GitHub | Pull request and review | Rulesets/branch protection and audit log |
| GitLab | Merge request and approvals | Protected branches/approval rules/audit events |
| Gitea/Forgejo | Pull request and review | Branch protection and repository activity |
| Bitbucket | Pull request | Branch restrictions and audit log |
| Azure Repos | Pull request | Branch policies and audit log |

If policy history, audit events, repository ID, or an immutable review revision
cannot be accessed, mark that claim `BLOCKED_ACCESS` or `INDETERMINATE`; do not
infer it from a UI badge.
