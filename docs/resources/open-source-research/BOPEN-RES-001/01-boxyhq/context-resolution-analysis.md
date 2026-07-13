# Context Resolution Analysis

## Research objective

Determine how BoxyHQ selects a current team, prevents arbitrary slug substitution and carries team identity through UI, API, model, event and audit layers.

## Required trace

- route parameter or selected team source;
- session identity source;
- membership lookup;
- team access error behavior;
- downstream `teamId` propagation;
- event/audit tenant attribution;
- switch-team UX and stale-context handling;
- API-key team context;
- SSO-derived team context.

## bOPEN target context

```text
Context {
  platform_id,
  tenant_id,
  organization_scope?,
  workspace_id?,
  resource_scope?,
  principal_id,
  membership_id?,
  auth_session_id,
  assurance_level,
  correlation_id
}
```

## Acceptance tests

- valid member accesses own team;
- non-member uses a valid foreign team slug;
- user is removed while session remains active;
- team is suspended;
- two browser tabs use different tenant contexts;
- API key attempts a different tenant;
- invitation token is replayed;
- SSO user belongs to multiple teams.

## Status

Initial evidence indicates team access is resolved before permission checks, but complete runtime proof remains required for G4.
