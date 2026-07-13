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

## R1 observations - 2026-07-13

### Observation

- Team, owner membership and webhook application provisioning are separate operations without an observed transaction boundary.
- Leave checks for at least one owner, but direct removal/demotion does not show an equivalent atomic invariant.
- Membership list/remove declarations exist; role transition, leave, cross-team identifiers and removed-session denial are not executed as R1 runtime evidence.
- Event/audit coverage differs by operation and does not provide a complete correlated membership lifecycle.

### Inference

bOPEN tenant provisioning and owner invariants require database-enforced or transactionally serialized behavior. Membership transition authorization must be tested across actor role, target role, tenant context and concurrent mutation.

### Decision status

Research input only. RES-P0-06 trace is complete, but state-change acceptance is partial and G3 remains open.
