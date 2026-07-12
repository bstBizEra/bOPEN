# Authorization Analysis

## Upstream baseline

Roles:
- `OWNER`
- `ADMIN`
- `MEMBER`

Resources include team, team member, invitation, SSO, directory sync, audit log, webhook, payments and API key. Actions include create, update, read, delete and leave. Owner has broad access; admin has broad management access excluding payments in the observed permission table; member can read and leave the team.

## Strengths

- explicit resource/action vocabulary;
- centralized permission map;
- authorization checks placed after team-access resolution;
- understandable role semantics for a starter kit.

## Gaps

- no explicit deny;
- no policy precedence;
- no scoped role assignment beyond team;
- no conditions;
- no resource relationship model;
- no delegated or temporary grant;
- no decision reason or policy version;
- no agent/tool grant;
- role and membership tightly coupled;
- broad wildcard permissions.

## bOPEN target

```text
Decision = evaluate(
  principal,
  membership,
  active_context,
  action,
  resource,
  role_assignments,
  relationships,
  conditions,
  platform_policy,
  tenant_policy
)
```

## Disposition

`ADAPT`: use BoxyHQ as the RBAC minimum reference, not as the bOPEN authorization ceiling.
