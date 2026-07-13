# Tenant and Membership Analysis

## Direct evidence

- `Team` is the primary shared organizational boundary.
- `TeamMember` relates `User` and `Team`.
- `(teamId, userId)` is unique.
- Team creation adds the creator as `OWNER`.
- Invitations create memberships only upon acceptance.

## bOPEN adoption

Adopt:
- global identity plus membership relation;
- owner membership during tenant provisioning;
- explicit invitation before membership;
- uniqueness of principal-tenant membership.

Adapt:
- move role assignments out of the membership core;
- add membership state and effective dates;
- add join source and invitation linkage;
- add organization/workspace scopes;
- add membership suspension, leave, removal and reactivation transitions;
- add audit, actor and reason fields.

Reject:
- treating team deletion cascade as a complete tenant termination policy;
- treating `Team` as sufficient for tenant commercial, security and isolation governance.

## Target membership state machine

```text
INVITED -> ACTIVE -> SUSPENDED -> ACTIVE
    |         |          |
    v         v          v
 EXPIRED    LEFT      REMOVED
 REVOKED
 DECLINED
```
