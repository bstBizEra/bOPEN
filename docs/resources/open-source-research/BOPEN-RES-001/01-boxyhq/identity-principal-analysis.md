# Identity and Principal Analysis

## Strong patterns

- Global user record independent of team.
- Linked provider accounts separated from user.
- Sessions separated from user.
- Email verification and password reset modeled independently.
- Multiple team memberships available from one user.

## Limitations for bOPEN

`User` represents only a human account. bOPEN must support:

- service accounts;
- API clients/applications;
- agents;
- devices;
- system principals;
- credential rotation and revocation;
- principal status independent from membership status;
- principal-to-party linkage.

## API key finding

A team-bound `ApiKey` is useful for tenant-scoped automation, but it does not establish who or what is acting. bOPEN should require:

```text
Service Principal
  -> Credential
  -> Tenant Membership or Grant
  -> Role/Capability Assignment
  -> Session/Token
  -> Audit Actor
```

## Decision proposal

Adopt the global-human-user pattern. Reject the idea that user and API key together are sufficient as the bOPEN principal kernel.
